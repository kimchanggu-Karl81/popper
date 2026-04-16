import argparse
import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_BASE_DIR = BASE_DIR / "data" / "output" / "monthly-report"


REQUIRED_INPUTS = [
    "report_master.xlsx",
    "asset_market_perf.csv",
    "fund_performance.csv",
    "allocation_model.csv",
    "comment_input.xlsx",
]


def parse_args():
    parser = argparse.ArgumentParser(description="월간 투자전략 보고서 초안 생성")
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


def check_input_files() -> list[dict]:
    results = []
    for filename in REQUIRED_INPUTS:
        file_path = INPUT_DIR / filename
        results.append(
            {
                "file_name": filename,
                "path": str(file_path),
                "exists": file_path.exists(),
            }
        )
    return results


def build_report_summary(report_month: str, mode: str, input_status: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existing_count = sum(1 for item in input_status if item["exists"])
    missing_files = [item["file_name"] for item in input_status if not item["exists"]]

    lines = [
        "월간 투자전략 보고서 초안 생성 결과",
        "=" * 40,
        f"생성 시각: {now}",
        f"보고서 대상월: {report_month}",
        f"실행 모드: {mode}",
        "",
        "[입력 파일 점검 결과]",
        f"총 필요 파일 수: {len(input_status)}",
        f"존재하는 파일 수: {existing_count}",
        f"누락된 파일 수: {len(missing_files)}",
        "",
    ]

    for item in input_status:
        status = "존재" if item["exists"] else "누락"
        lines.append(f"- {item['file_name']}: {status}")

    lines.extend(
        [
            "",
            "[포함 예정 섹션]",
            "- 표지",
            "- 주요 자산 시장 점검",
            "- 자산배분 전략",
            "- 추천 펀드",
            "- 성과 요약",
            "",
        ]
    )

    if missing_files:
        lines.append("[주의]")
        lines.append("일부 입력 파일이 없어서 실제 보고서 생성 단계에서는 실패할 수 있습니다.")
        lines.append("누락 파일을 먼저 업로드하거나 저장소에 추가해야 합니다.")
    else:
        lines.append("[상태]")
        lines.append("기본 입력 파일이 모두 확인되었습니다. 다음 단계 구현이 가능합니다.")

    return "\n".join(lines)


def build_report_metadata(report_month: str, mode: str, input_status: list[dict]) -> dict:
    return {
        "generated_at": datetime.now().isoformat(),
        "report_month": report_month,
        "mode": mode,
        "base_dir": str(BASE_DIR),
        "input_dir": str(INPUT_DIR),
        "required_inputs": input_status,
        "next_steps": [
            "입력 데이터 실제 파싱 추가",
            "차트 생성 로직 추가",
            "PPTX 보고서 생성 로직 추가",
            "PDF 변환 단계 추가",
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


def main():
    args = parse_args()

    paths = ensure_directories(args.month, args.mode)
    input_status = check_input_files()
    summary_text = build_report_summary(args.month, args.mode, input_status)
    metadata = build_report_metadata(args.month, args.mode, input_status)

    write_outputs(paths, summary_text, metadata)

    print("월간 보고서 초안 생성이 완료되었습니다.")


if __name__ == "__main__":
    main()
