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

The 8×8 board opens in a native window with classic SVG pieces in their starting positions, ranks on the left, and files below. Run the setup script again to create the `chess` launcher in an existing environment.

Two people can play by clicking a piece and then its destination. The selected square is outlined; click it again to cancel or click another piece of the same color to change selection. Illegal moves leave the board unchanged. Pawns promote to a queen automatically.
Each legal move is printed to the terminal in standard algebraic notation.

To change the displayed position in code, keep a reference to `BoardView` and call `set_fen(fen)` or `set_board(chess_board)`. Both update the python-chess position and refresh the board. Call these methods from the NiceGUI UI context.
