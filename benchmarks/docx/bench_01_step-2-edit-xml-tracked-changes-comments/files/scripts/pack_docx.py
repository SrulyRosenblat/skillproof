#!/usr/bin/env python3
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: pack_docx.py <package_dir> <output_docx>", file=sys.stderr)
        return 2
    package_dir = Path(sys.argv[1])
    output_docx = Path(sys.argv[2])
    if not package_dir.is_dir():
        print(f"missing package directory: {package_dir}", file=sys.stderr)
        return 2
    output_docx.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_docx, "w", compression=ZIP_DEFLATED) as zf:
        for path in sorted(package_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(package_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
