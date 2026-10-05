#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="$repo_dir/.venv"

platform="$(uname -s)"
dependencies=(python-chess stockfish 'nicegui[native]' pytest typesafe-sdk)
case "$platform" in
    Darwin)
        if ! command -v stockfish >/dev/null 2>&1; then
            if ! command -v brew >/dev/null 2>&1; then
                echo "Homebrew is required to install Stockfish. Install Homebrew and run this script again." >&2
                exit 1
            fi
            brew install stockfish
        fi
        ;;
    Linux)
        if ! command -v apt >/dev/null 2>&1; then
            echo "Linux setup requires apt (Debian/Ubuntu)." >&2
            exit 1
        fi
        apt_command=(apt)
        if [[ "$EUID" -ne 0 ]]; then
            apt_command=(sudo apt)
        fi
        "${apt_command[@]}" update
        "${apt_command[@]}" install -y stockfish python3-venv libxcb-cursor0 libegl1 libopengl0 libxkbcommon-x11-0
        dependencies+=('pywebview[qt]')
        ;;
esac

if [[ ! -d "$venv_dir" ]]; then
    python3 -m venv "$venv_dir"
fi

# activate="$venv_dir/bin/activate"
# if ! grep -q 'ChessWithJev activation guard' "$activate"; then
#     awk -v venv_dir="$venv_dir" '/^deactivate nondestructive$/ && !inserted {
#         print "# ChessWithJev activation guard: re-sourcing this venv must preserve PATH additions."
#         print "if [ \"${VIRTUAL_ENV:-}\" = \"" venv_dir "\" ]; then return 0; fi"
#         inserted = 1
#     } { print }' "$activate" > "$activate.tmp"
#     mv "$activate.tmp" "$activate"
# fi

"$venv_dir/bin/python" -m pip install "${dependencies[@]}"

cat > "$venv_dir/bin/chess" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_dir"
exec "$repo_dir/.venv/bin/python" -m src.ui.board "$@"
EOF
chmod +x "$venv_dir/bin/chess"
