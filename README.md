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

Run with `.venv/bin/chess -d` to show the current viewport width and height in the bottom-right corner. The values update when you resize the window.

At the start screen, choose `human`, `random`, or `stockfish` for White and Black. Stockfish moves automatically on its turns. When both players are computer controlled, use START to begin their game.

The vertical bar beside the board shows Stockfish's current position estimate in every game mode. Black is at the top and White is at the bottom; a larger section means a better expected result for that color.

Use the left and right arrows beside Undo and Redo to review recorded moves. The preview is read-only and leaves the live game unchanged; step right to the latest move to resume play.

Notes:

To change the displayed position in code, keep a reference to `BoardView` and call `set_fen(fen)` or `set_board(chess_board)`. Both update the python-chess position and refresh the board. Call these methods from the NiceGUI UI context.

To submit a move in code, call `view.play_move(chess.Move.from_uci('e2e4'))` from the NiceGUI UI context. It returns `True` for a legal move and refreshes the board. `GameController.play(move)` provides the same move validation and state update without a UI.
