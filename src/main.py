import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=False, default="2026-04")
    parser.add_argument("--mode", required=False, default="draft")
    args = parser.parse_args()

    output_dir = Path(f"data/output/monthly-report/{args.month}/{args.mode}")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "result.txt"
    output_file.write_text(
        f"Monthly report batch success\nmonth={args.month}\nmode={args.mode}\n",
        encoding="utf-8"
    )

    print(f"Created: {output_file}")

if __name__ == "__main__":
    main()
