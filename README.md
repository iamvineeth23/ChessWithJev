# ChessWithJev

Note: developed and tested primarily on MacOS.

Set up the Python environment:

```bash
bash scripts/setup.sh
```

The script creates `.venv` if needed and installs `python-chess`, `stockfish`, `nicegui[native]`, and `pytest`. On macOS, it also installs the Stockfish engine with Homebrew if the executable is missing. Install Homebrew first if needed.

Run the board:

```bash
.venv/bin/chess
```

The empty 8×8 board opens in a native window. Run the setup script again to create the `chess` launcher in an existing environment.
