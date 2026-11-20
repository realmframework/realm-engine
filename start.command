#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if ! command -v uv >/dev/null 2>&1; then
  echo "Error: 'uv' is not installed. Install it from https://docs.astral.sh/uv/"
  exit 1
fi
exec uv run python main.py --desktop "$@"
