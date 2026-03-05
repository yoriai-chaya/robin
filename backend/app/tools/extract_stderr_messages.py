import argparse
import json
import sys
from pathlib import Path
from typing import List


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def extract_stderr_messages(records: List[dict]) -> List[str]:
    return [r.get("message", "") for r in records if r.get("stream") == "stderr"]


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="uv run python -m app.tools.extract_stderr_messages",
        description="Extract stderr messages from build log JSON.",
    )
    parser.add_argument("input_file", help="Input JSON file")
    parser.add_argument("output_file", help="Output JSON file")

    args = parser.parse_args()

    input_file = Path(args.input_file)
    output_file = Path(args.output_file)

    if not input_file.exists():
        print(f"Input file {input_file} does not exist.", file=sys.stderr)
        sys.exit(1)

    data = load_json(input_file)

    error_count = int(data.get("summary", {}).get("errorCount", 0))
    if error_count == 0:
        print("No errors found in the build log.")
        sys.exit(0)

    records = data.get("records", [])
    messages = extract_stderr_messages(records)

    concat = "".join(m + "\n" for m in messages)
    payload = {"message": concat}

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    print(f"Extracted error message written to {output_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()
