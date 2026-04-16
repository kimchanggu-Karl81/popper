import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_BASE_DIR = BASE_DIR / "data" / "output" / "monthly-report"


def parse_args():
    parser = argparse.ArgumentParser(description="Monthly investment report draft generator")
    parser.add_argument("--month", required=False, default=datetime.now().strftime("%Y-%m"))
    parser.add_argument("--mode", required=False, default="draft", choices=["draft", "final"])
    return parser.parse_args()


def ensure_directories(report_month: str, mode: str) -> dict[str, Path]:
    report_root = OUTPUT_BASE_DIR / report_month / mode
    charts_dir = report_root / "charts"
    logs_dir = report_root / "logs"

    report_root.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    return {
        "report_root": report_root,
        "charts_dir": charts_dir,
        "logs_dir": logs_dir,
    }


def load_csv_if_exists(path: Path):
    if path.exists():
        return pd.read_csv(path)
    return None


def summarize_dataframe(df: pd.DataFrame | None, name: str) -> dict:
    if df is None:
        return {
            "name": name,
            "exists": False,
            "rows": 0,
            "columns": [],
        }

    return {
        "name": name,
        "exists": True,
        "rows": int(len(df)),
        "columns": list(df.columns),
    }


def create_asset_chart(asset_df: pd.DataFrame | None, charts_dir: Path) -> str | None:
    if asset_df is None or asset_df.empty:
        return None

    plot_df = asset_df.copy()
    plot_df["return_1y"] = pd.to_numeric(plot_df["return_1y"], errors="coerce")
    plot_df = plot_df.dropna(subset=["return_1y"])

    if plot_df.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(plot_df["asset_name"], plot_df["return_1y"])
    ax.set_title("Asset Performance - 1Y Return")
    ax.set_xlabel("Asset")
    ax.set_ylabel("Return (%)")
    plt.xticks(rotation=45, ha="right")

    output_path = charts_dir / "asset_return_1y.png"
    fig.savefig(output_path, bbox_inches="tight", dpi=200)
    plt.close(fig)

    return str(output_path)


def create_fund_chart(fund_df: pd.DataFrame | None, charts_dir: Path) -> str | None:
    if fund_df is None or fund_df.empty:
        return None

    plot_df = fund_df.copy()
    plot_df["return_1y"] = pd.to_numeric(plot_df["return_1y"], errors="coerce")
    plot_df = plot_df.dropna(subset=["return_1y"])

    if plot_df.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(plot_df["fund_name"], plot_df["return_1y"])
    ax.set_title("Fund Performance - 1Y Return")
    ax.set_xlabel("Fund")
    ax.set_ylabel("Return (%)")
    plt.xticks(rotation=45, ha="right")

    output_path = charts_dir / "fund_return_1y.png"
    fig.savefig(output_path, bbox_inches="tight", dpi=200)
    plt.close(fig)

    return str(output_path)


def build_report_summary(report_month: str, mode: str, asset_df, fund_df, asset_chart_path, fund_chart_path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    asset_rows = len(asset_df) if asset_df is not None else 0
    fund_rows = len(fund_df) if fund_df is not None else 0

    lines = [
        "Monthly Investment Report Draft Summary",
        "=" * 40,
        f"Generated at: {now}",
        f"Report month: {report_month}",
        f"Mode: {mode}",
        "",
        "[Input file status]",
        f"asset_market_perf.csv rows: {asset_rows}",
        f"fund_performance.csv rows: {fund_rows}",
        "",
        "[Generated charts]",
        f"asset_return_1y.png: {'created' if asset_chart_path else 'not created'}",
        f"fund_return_1y.png: {'created' if fund_chart_path else 'not created'}",
        "",
    ]

    if asset_df is not None and not asset_df.empty:
        lines.append("[Asset market preview]")
        lines.append(asset_df.head(3).to_string(index=False))
        lines.append("")

    if fund_df is not None and not fund_df.empty:
        lines.append("[Fund performance preview]")
        lines.append(fund_df.head(3).to_string(index=False))
        lines.append("")

    if asset_df is None or fund_df is None:
        lines.append("[Warning]")
        lines.append("Some required CSV files are missing.")
    else:
        lines.append("[Status]")
        lines.append("CSV input files loaded successfully and chart generation was attempted.")

    return "\n".join(lines)


def build_report_metadata(report_month: str, mode: str, asset_df, fund_df, asset_chart_path, fund_chart_path) -> dict:
    asset_summary = summarize_dataframe(asset_df, "asset_market_perf.csv")
    fund_summary = summarize_dataframe(fund_df, "fund_performance.csv")

    return {
        "generated_at": datetime.now().isoformat(),
        "report_month": report_month,
        "mode": mode,
        "input_dir": str(INPUT_DIR),
        "files": [
            asset_summary,
            fund_summary,
        ],
        "charts": {
            "asset_return_1y": asset_chart_path,
            "fund_return_1y": fund_chart_path,
        },
        "next_steps": [
            "Add Excel input loading",
            "Add allocation chart",
            "Add PPTX generation",
            "Add PDF export",
        ],
    }


def write_outputs(paths: dict[str, Path], summary_text: str, metadata: dict) -> None:
    summary_path = paths["report_root"] / "report_summary.txt"
    metadata_path = paths["report_root"] / "report_metadata.json"

    summary_path.write_text(summary_text, encoding="utf-8")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Created: {summary_path}")
    print(f"Created: {metadata_path}")
    print("Monthly report draft generation completed.")


def main():
    args = parse_args()
    paths = ensure_directories(args.month, args.mode)

    asset_df = load_csv_if_exists(INPUT_DIR / "asset_market_perf.csv")
    fund_df = load_csv_if_exists(INPUT_DIR / "fund_performance.csv")

    asset_chart_path = create_asset_chart(asset_df, paths["charts_dir"])
    fund_chart_path = create_fund_chart(fund_df, paths["charts_dir"])

    summary_text = build_report_summary(
        args.month,
        args.mode,
        asset_df,
        fund_df,
        asset_chart_path,
        fund_chart_path,
    )
    metadata = build_report_metadata(
        args.month,
        args.mode,
        asset_df,
        fund_df,
        asset_chart_path,
        fund_chart_path,
    )

    write_outputs(paths, summary_text, metadata)


if __name__ == "__main__":
    main()
