#!/bin/sh
set -eu

REPO_URL="${PEGASUS_REPO_URL:-https://github.com/xodn348/pegasus}"
REF="${PEGASUS_REF:-main}"
INSTALL_DIR="${PEGASUS_INSTALL_DIR:-$HOME/.local/share/pegasus}"
BIN_DIR="${PEGASUS_BIN_DIR:-$HOME/.local/bin}"
PYTHON_BIN="${PYTHON:-python3}"
ARCHIVE_URL="${PEGASUS_ARCHIVE_URL:-$REPO_URL/archive/refs/heads/$REF.tar.gz}"
SOURCE_DIR="${PEGASUS_SOURCE_DIR:-}"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "pegasus install: missing required command: $1" >&2
    exit 1
  fi
}

need "$PYTHON_BIN"
need mkdir
need ln

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("pegasus install: Python 3.11+ is required")
PY

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT INT TERM

if [ -n "$SOURCE_DIR" ]; then
  if [ ! -f "$SOURCE_DIR/pyproject.toml" ]; then
    echo "pegasus install: PEGASUS_SOURCE_DIR must point to a Pegasus checkout" >&2
    exit 1
  fi
else
  need curl
  need tar
  SOURCE_DIR="$TMP_DIR/src"
  mkdir -p "$SOURCE_DIR"
  echo "Downloading Pegasus from $ARCHIVE_URL"
  curl -fsSL "$ARCHIVE_URL" | tar -xz -C "$SOURCE_DIR" --strip-components=1
fi

mkdir -p "$INSTALL_DIR" "$BIN_DIR"
VENV_DIR="$INSTALL_DIR/venv"

"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m ensurepip --upgrade >/dev/null 2>&1 || true
"$VENV_DIR/bin/python" -m pip install --upgrade "$SOURCE_DIR"
ln -sf "$VENV_DIR/bin/pegasus" "$BIN_DIR/pegasus"

if [ "${PEGASUS_INSTALL_INTEGRATIONS:-1}" != "0" ]; then
  "$BIN_DIR/pegasus" install-integrations
fi

cat <<EOF
Pegasus installed.

Installed:
- CLI: $BIN_DIR/pegasus
- Codex skill: ~/.codex/skills/pegasus/SKILL.md
- Claude Code command: ~/.claude/commands/pegasus.md

Try:
  pegasus run . --goal "Describe the project goal"
  pegasus status .

Claude Code:
  /pegasus run . --goal "Describe the project goal"

If 'pegasus' is not found, add this to your shell profile:
  export PATH="$BIN_DIR:\$PATH"
EOF
