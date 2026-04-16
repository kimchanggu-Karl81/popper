import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_BASE_DIR = BASE_DIR / "data" / "output" / "monthly-report"

THEME_BLUE = RGBColor(31, 78, 121)
THEME_LIGHT_BLUE = RGBColor(221, 235, 247)
THEME_GRAY = RGBColor(242, 242, 242)
THEME_DARK = RGBColor(64, 64, 64)
WHITE = RGBColor(255, 255, 255)


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


def create_allocation_charts(allocation_df: pd.DataFrame | None, charts_dir: Path) -> dict[str, str]:
    results = {}

    if allocation_df is None or allocation_df.empty:
        return results

    for _, row in allocation_df.iterrows():
        profile = str(row["profile_type"])
        risky = float(row["risky_ratio"])
        safe = float(row["safe_ratio"])

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(
            [risky, safe],
            labels=["Risky Assets", "Safe Assets"],
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.set_title(f"{profile} Allocation")

        safe_name = profile.replace("/", "_").replace(" ", "_")
        output_path = charts_dir / f"allocation_{safe_name}.png"
        fig.savefig(output_path, bbox_inches="tight", dpi=200)
        plt.close(fig)

        results[profile] = str(output_path)

    return results


def build_report_summary(
    report_month: str,
    mode: str,
    asset_df,
    fund_df,
    allocation_df,
    asset_chart_path,
    fund_chart_path,
    allocation_chart_paths,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    asset_rows = len(asset_df) if asset_df is not None else 0
    fund_rows = len(fund_df) if fund_df is not None else 0
    allocation_rows = len(allocation_df) if allocation_df is not None else 0

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
        f"allocation_model.csv rows: {allocation_rows}",
        "",
        "[Generated charts]",
        f"asset_return_1y.png: {'created' if asset_chart_path else 'not created'}",
        f"fund_return_1y.png: {'created' if fund_chart_path else 'not created'}",
        f"allocation charts created: {len(allocation_chart_paths)}",
        "",
    ]

    if allocation_chart_paths:
        lines.append("[Allocation chart files]")
        for profile, path in allocation_chart_paths.items():
            lines.append(f"- {profile}: {path}")
        lines.append("")

    if asset_df is None or fund_df is None:
        lines.append("[Warning]")
        lines.append("Some required CSV files are missing.")
    else:
        lines.append("[Status]")
        lines.append("CSV input files loaded successfully and chart generation was attempted.")

    return "\n".join(lines)


def build_report_metadata(
    report_month: str,
    mode: str,
    asset_df,
    fund_df,
    allocation_df,
    asset_chart_path,
    fund_chart_path,
    allocation_chart_paths,
) -> dict:
    asset_summary = summarize_dataframe(asset_df, "asset_market_perf.csv")
    fund_summary = summarize_dataframe(fund_df, "fund_performance.csv")
    allocation_summary = summarize_dataframe(allocation_df, "allocation_model.csv")

    return {
        "generated_at": datetime.now().isoformat(),
        "report_month": report_month,
        "mode": mode,
        "input_dir": str(INPUT_DIR),
        "files": [
            asset_summary,
            fund_summary,
            allocation_summary,
        ],
        "charts": {
            "asset_return_1y": asset_chart_path,
            "fund_return_1y": fund_chart_path,
            "allocation_charts": allocation_chart_paths,
        },
        "next_steps": [
            "Add Excel input loading",
            "Add richer PPT layout",
            "Add commentary text automation",
            "Add PDF export",
        ],
    }


def add_textbox(
    slide,
    left,
    top,
    width,
    height,
    text,
    font_size=16,
    bold=False,
    align=PP_ALIGN.LEFT,
    font_color=THEME_DARK,
):
    textbox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = textbox.text_frame
    tf.clear()
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = font_color
    return textbox


def add_banner(slide, title_text):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0),
        Inches(0),
        Inches(10),
        Inches(0.6),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = THEME_BLUE
    shape.line.color.rgb = THEME_BLUE

    text_frame = shape.text_frame
    text_frame.clear()
    p = text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = f"  {title_text}"
    run.font.size = Pt(20)
    run.font.bold = True
    run.font.color.rgb = WHITE


def format_table_text(cell, font_size=9, bold=False, align=PP_ALIGN.CENTER, font_color=THEME_DARK):
    tf = cell.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for paragraph in tf.paragraphs:
        paragraph.alignment = align
        for run in paragraph.runs:
            run.font.size = Pt(font_size)
            run.font.bold = bold
            run.font.color.rgb = font_color


def set_column_widths(table, widths_in_inches):
    for idx, width in enumerate(widths_in_inches):
        table.columns[idx].width = Inches(width)


def style_table_header(cell):
    cell.fill.solid()
    cell.fill.fore_color.rgb = THEME_BLUE
    format_table_text(cell, font_size=11, bold=True, align=PP_ALIGN.CENTER, font_color=WHITE)


def style_table_body(cell, align):
    cell.fill.solid()
    cell.fill.fore_color.rgb = WHITE
    format_table_text(cell, font_size=9, bold=False, align=align, font_color=THEME_DARK)


def add_asset_table_slide(prs, asset_df: pd.DataFrame | None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_banner(slide, "Asset Performance Table")

    if asset_df is None or asset_df.empty:
        add_textbox(slide, 1.0, 2.0, 5.0, 1.0, "Asset table not available")
        return

    display_df = asset_df.copy()
    keep_columns = [
        "asset_name",
        "return_1m",
        "return_3m",
        "return_1y",
        "return_3y",
    ]
    display_df = display_df[keep_columns].head(5)

    display_df = display_df.rename(columns={
        "asset_name": "자산명",
        "return_1m": "1M",
        "return_3m": "3M",
        "return_1y": "1Y",
        "return_3y": "3Y",
    })

    for col in ["1M", "3M", "1Y", "3Y"]:
        if col in display_df.columns:
            display_df[col] = pd.to_numeric(display_df[col], errors="coerce").map(
                lambda x: f"{x:.2f}" if pd.notnull(x) else ""
            )

    rows = len(display_df) + 1
    cols = len(display_df.columns)

    table = slide.shapes.add_table(
        rows,
        cols,
        Inches(0.4),
        Inches(1.4),
        Inches(8.8),
        Inches(3.2),
    ).table

    set_column_widths(table, [3.2, 1.2, 1.2, 1.2, 1.2])

    for c, col_name in enumerate(display_df.columns):
        table.cell(0, c).text = str(col_name)
        style_table_header(table.cell(0, c))

    for r in range(len(display_df)):
        for c in range(cols):
            value = str(display_df.iloc[r, c])
            table.cell(r + 1, c).text = value
            align = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            style_table_body(table.cell(r + 1, c), align=align)


def add_fund_table_slide(prs, fund_df: pd.DataFrame | None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_banner(slide, "Fund Performance Table")

    if fund_df is None or fund_df.empty:
        add_textbox(slide, 1.0, 2.0, 5.0, 1.0, "Fund table not available")
        return

    display_df = fund_df.copy()
    keep_columns = [
        "fund_name",
        "risk_grade",
        "return_1y",
        "return_2y",
        "return_3y",
    ]
    display_df = display_df[keep_columns].head(5)

    display_df = display_df.rename(columns={
        "fund_name": "펀드명",
        "risk_grade": "위험등급",
        "return_1y": "1Y",
        "return_2y": "2Y",
        "return_3y": "3Y",
    })

    for col in ["1Y", "2Y", "3Y"]:
        if col in display_df.columns:
            display_df[col] = pd.to_numeric(display_df[col], errors="coerce").map(
                lambda x: f"{x:.2f}" if pd.notnull(x) else ""
            )

    rows = len(display_df) + 1
    cols = len(display_df.columns)

    table = slide.shapes.add_table(
        rows,
        cols,
        Inches(0.4),
        Inches(1.4),
        Inches(8.8),
        Inches(3.2),
    ).table

    set_column_widths(table, [4.2, 1.6, 1.0, 1.0, 1.0])

    for c, col_name in enumerate(display_df.columns):
        table.cell(0, c).text = str(col_name)
        style_table_header(table.cell(0, c))

    for r in range(len(display_df)):
        for c in range(cols):
            value = str(display_df.iloc[r, c])
            table.cell(r + 1, c).text = value
            align = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            style_table_body(table.cell(r + 1, c), align=align)


def create_pptx_report(
    report_month: str,
    mode: str,
    paths: dict[str, Path],
    summary_text: str,
    asset_df,
    fund_df,
    asset_chart_path: str | None,
    fund_chart_path: str | None,
    allocation_chart_paths: dict[str, str],
) -> Path:
    prs = Presentation()

    # Cover
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_banner(slide, "Monthly Investment Report Draft")
    add_textbox(slide, 0.8, 1.5, 8.0, 0.8, "월간 투자전략 보고서 초안", font_size=28, bold=True)
    add_textbox(slide, 0.8, 2.4, 5.0, 0.5, f"Report month: {report_month}", font_size=18)
    add_textbox(slide, 0.8, 2.9, 4.0, 0.5, f"Mode: {mode}", font_size=18)

    # Summary
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_banner(slide, "Execution Summary")
    summary_preview = "\n".join(summary_text.splitlines()[:18])
    add_textbox(slide, 0.6, 1.2, 8.8, 4.8, summary_preview, font_size=12)

    # Tables
    add_asset_table_slide(prs, asset_df)
    add_fund_table_slide(prs, fund_df)

    # Asset chart
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_banner(slide, "Asset Performance Chart")
    if asset_chart_path and Path(asset_chart_path).exists():
        slide.shapes.add_picture(asset_chart_path, Inches(0.6), Inches(1.2), width=Inches(8.5))
    else:
        add_textbox(slide, 1.0, 2.0, 5.0, 1.0, "Asset chart not available")

    # Fund chart
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_banner(slide, "Fund Performance Chart")
    if fund_chart_path and Path(fund_chart_path).exists():
        slide.shapes.add_picture(fund_chart_path, Inches(0.6), Inches(1.2), width=Inches(8.5))
    else:
        add_textbox(slide, 1.0, 2.0, 5.0, 1.0, "Fund chart not available")

    # Allocation
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_banner(slide, "Allocation Strategy")

    positions = [
        (0.3, 1.5),
        (3.4, 1.5),
        (6.5, 1.5),
    ]

    items = list(allocation_chart_paths.items())[:3]
    for (profile, chart_path), (left, top) in zip(items, positions):
        add_textbox(slide, left, top - 0.35, 2.5, 0.35, profile, font_size=12, bold=True, align=PP_ALIGN.CENTER)
        if Path(chart_path).exists():
            slide.shapes.add_picture(chart_path, Inches(left), Inches(top), width=Inches(2.5))
        else:
            add_textbox(slide, left, top, 2.5, 0.8, "Chart not available", font_size=12)

    output_path = paths["report_root"] / "monthly_report_draft.pptx"
    prs.save(output_path)
    return output_path


def write_outputs(paths: dict[str, Path], summary_text: str, metadata: dict, pptx_path: Path) -> None:
    summary_path = paths["report_root"] / "report_summary.txt"
    metadata_path = paths["report_root"] / "report_metadata.json"

    summary_path.write_text(summary_text, encoding="utf-8")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Created: {summary_path}")
    print(f"Created: {metadata_path}")
    print(f"Created: {pptx_path}")
    print("Monthly report draft generation completed.")


def main():
    args = parse_args()
    paths = ensure_directories(args.month, args.mode)

    asset_df = load_csv_if_exists(INPUT_DIR / "asset_market_perf.csv")
    fund_df = load_csv_if_exists(INPUT_DIR / "fund_performance.csv")
    allocation_df = load_csv_if_exists(INPUT_DIR / "allocation_model.csv")

    asset_chart_path = create_asset_chart(asset_df, paths["charts_dir"])
    fund_chart_path = create_fund_chart(fund_df, paths["charts_dir"])
    allocation_chart_paths = create_allocation_charts(allocation_df, paths["charts_dir"])

    summary_text = build_report_summary(
        args.month,
        args.mode,
        asset_df,
        fund_df,
        allocation_df,
        asset_chart_path,
        fund_chart_path,
        allocation_chart_paths,
    )

    metadata = build_report_metadata(
        args.month,
        args.mode,
        asset_df,
        fund_df,
        allocation_df,
        asset_chart_path,
        fund_chart_path,
        allocation_chart_paths,
    )

    pptx_path = create_pptx_report(
        args.month,
        args.mode,
        paths,
        summary_text,
        asset_df,
        fund_df,
        asset_chart_path,
        fund_chart_path,
        allocation_chart_paths,
    )

    write_outputs(paths, summary_text, metadata, pptx_path)


if __name__ == "__main__":
    main()
