#!/usr/bin/env bash
# Bootstrap a local dev environment with uv (no system pip/venv required).
# Requires Python 3.12+ on PATH as `python3`. Windows: use manual venv steps in README for now.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

UV_BIN="${ROOT}/.tools/uv"
VENV="${ROOT}/.venv"
CLEAR=0

usage() {
  cat <<'EOF'
Usage: scripts/bootstrap-linux.sh [OPTIONS]

Create or refresh .venv using a project-local uv binary in .tools/uv.

Options:
  --clear   Remove and recreate .venv before installing dependencies
  -h, --help  Show this help

After bootstrap:
  source .venv/bin/activate
  # Download oracle bulk JSON (see README), then:
  mtg-deck-tools import
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clear) CLEAR=1 ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Install Python 3.12+ and retry." >&2
  exit 1
fi

PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MAJOR="${PY_VERSION%%.*}"
PY_MINOR="${PY_VERSION#*.}"
if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 12 ]]; then
  echo "Python 3.12+ required; found $PY_VERSION" >&2
  exit 1
fi

arch="$(uname -m)"
case "$arch" in
  x86_64 | amd64) UV_ARCH="x86_64" ;;
  aarch64 | arm64) UV_ARCH="aarch64" ;;
  *)
    echo "Unsupported architecture: $arch" >&2
    exit 1
    ;;
esac

mkdir -p "${ROOT}/.tools"
UV_URL="https://github.com/astral-sh/uv/releases/latest/download/uv-${UV_ARCH}-unknown-linux-gnu.tar.gz"
TMP_TAR="${ROOT}/.tools/uv.tar.gz"

if [[ ! -x "$UV_BIN" ]]; then
  echo "Downloading uv (${UV_ARCH})..."
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$UV_URL" -o "$TMP_TAR"
  elif python3 -c "import urllib.request" 2>/dev/null; then
    python3 - "$UV_URL" "$TMP_TAR" <<'PY'
import sys
import urllib.request

url, dest = sys.argv[1], sys.argv[2]
req = urllib.request.Request(url, headers={"User-Agent": "mtg-deck-tools-bootstrap"})
with urllib.request.urlopen(req) as resp, open(dest, "wb") as out:
    out.write(resp.read())
PY
  else
    echo "Need curl or python3 with urllib to download uv." >&2
    exit 1
  fi
  tar -xzf "$TMP_TAR" -C "${ROOT}/.tools" --strip-components=1 uv
  rm -f "$TMP_TAR"
  chmod +x "$UV_BIN"
fi

echo "Using $($UV_BIN --version)"

VENV_ARGS=(venv "$VENV" --python python3)
if [[ "$CLEAR" -eq 1 ]]; then
  VENV_ARGS+=(--clear)
fi
"$UV_BIN" "${VENV_ARGS[@]}"

"$UV_BIN" pip install -e ".[dev]"

cat <<EOF

Bootstrap complete.
  Activate:  source .venv/bin/activate
  CLI:       mtg-deck-tools --help

Next: download Scryfall oracle bulk JSON (README → External data), then run:
  mtg-deck-tools import
  mtg-deck-tools stats
EOF
