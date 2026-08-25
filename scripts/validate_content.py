from pathlib import Path


def main() -> int:
    content_root = Path(__file__).resolve().parents[1] / "content"
    unexpected = sorted(
        path.relative_to(content_root)
        for path in content_root.rglob("*")
        if path.is_file() and path.name != "README.md"
    )
    if unexpected:
        print("Milestone 1 does not accept content packages:")
        for path in unexpected:
            print(f"- {path}")
        return 1
    print("Content validation passed: no publishable content packages are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
