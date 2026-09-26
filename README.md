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

Play as White by clicking a piece and then its destination. Black replies with a random legal move. Use **Undo** and **Redo** to step through complete White and Black turns, **New Game** to reset, and **Claim Draw** when available. The status panel shows checkmate or the draw result when the game ends.

Run with `.venv/bin/chess -d` to show the current viewport width and height in the bottom-right corner. The values update when you resize the window.

Notes:

To change the displayed position in code, keep a reference to `BoardView` and call `set_fen(fen)` or `set_board(chess_board)`. Both update the python-chess position and refresh the board. Call these methods from the NiceGUI UI context.

To submit a move in code, call `view.play_move(chess.Move.from_uci('e2e4'))` from the NiceGUI UI context. It returns `True` for a legal move and refreshes the board. `GameController.play(move)` provides the same move validation and state update without a UI.
