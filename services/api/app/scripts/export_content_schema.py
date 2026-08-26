import sys
from pathlib import Path

from app.content.loader import content_schema_json


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.export_content_schema <output-path>")
        return 2
    output_path = Path(sys.argv[1])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content_schema_json(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
