#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGE_NAME="editor_focus_mode.ankiaddon"
PACKAGE_PATH="$ROOT_DIR/$PACKAGE_NAME"
LATEST_TAG="$(git -C "$ROOT_DIR" tag --list 'v*' --sort=-version:refname | head -n 1)"
LATEST_CHANGELOG="$({
  python3 - "$ROOT_DIR" <<'PY'
from pathlib import Path
import re
import sys

text = (Path(sys.argv[1]) / 'CHANGELOG.md').read_text(encoding='utf-8')
match = re.search(r'^##\s+([^\n]+)', text, re.MULTILINE)
print(match.group(1) if match else 'Unreleased')
PY
} )"

cd "$ROOT_DIR"

echo "Validating Python files..."
python3 -m py_compile \
  __init__.py \
  field_visibility.py \
  config.py \
  browser_utils.py \
  layout_dialog.py

echo "Building $PACKAGE_NAME..."
rm -f "$PACKAGE_PATH"
zip -r "$PACKAGE_PATH" . \
  -x './__pycache__/*' \
     './meta.json' \
     './field_visibility_debug.txt' \
     './editor_focus_mode.code-workspace' \
     './docs/ignore this. just for me/*' \
     './docs/assets/*' \
     './.git/*' \
     './.vscode/*' \
     './.DS_Store' \
     './docs/.DS_Store' \
     './*.ankiaddon' >/dev/null

echo
echo "Release package ready: $PACKAGE_PATH"
echo "Latest git tag: ${LATEST_TAG:-none}"
echo "Top changelog entry: $LATEST_CHANGELOG"
echo
echo "Next steps:"
echo "1. Review CHANGELOG.md and README.md if needed."
echo "2. Commit any remaining release changes."
echo "3. Create a git tag if you are cutting a new version."
echo "4. Upload $PACKAGE_NAME to the existing AnkiWeb add-on page."
