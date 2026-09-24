#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="$repo_dir/.venv"

if [[ "$(uname -s)" == Darwin ]] && ! command -v stockfish >/dev/null 2>&1; then
    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew is required to install Stockfish. Install Homebrew and run this script again." >&2
        exit 1
    fi
    brew install stockfish
fi

if [[ ! -d "$venv_dir" ]]; then
    python3 -m venv "$venv_dir"
fi

"$venv_dir/bin/python" -m pip install python-chess stockfish nicegui
