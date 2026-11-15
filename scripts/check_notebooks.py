"""저장소 전체의 Python 문법과 노트북 형식을 검사한다. API를 호출하지 않는다."""

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    import nbformat
except ImportError:
    nbformat = None


def main():
    errors = []

    for path in sorted(ROOT.rglob("*.py")):
        if ".venv" in path.parts:
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as error:
            errors.append(f"{path}: {error}")

    for path in sorted(ROOT.rglob("*.ipynb")):
        if ".venv" in path.parts:
            continue
        notebook = json.loads(path.read_text(encoding="utf-8"))
        if nbformat is not None:
            nbformat.validate(nbformat.reads(path.read_text(encoding="utf-8"), as_version=4))
        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            try:
                ast.parse("".join(cell["source"]), filename=str(path))
            except SyntaxError as error:
                errors.append(f"{path}: {error}")

    if errors:
        print("\n".join(errors))
        return 1
    print("Python syntax OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
