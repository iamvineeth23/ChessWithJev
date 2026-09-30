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

Run with `.venv/bin/chess -r` to start with REC enabled. Run with `.venv/bin/chess -d` to show the current viewport width and height in the bottom-right corner. The values update when you resize the window.

Click a move in Move Log to preview its board position and Move Analysis. Click the latest move to return to the live position. Browsing history pauses automatic play.

Evaluation Plot updates after each move with Stockfish balance: 0% is even, positive values favor White, and negative values favor Black. Move step 0 is the starting position; each step is one player’s move. Browsing history shows the plot up to the selected move.

Stockfish uses the selected ELO when playing. Position evaluations, plots, five best alternatives, and evaluation loss always use full strength, regardless of player ELO. Analysis searches to depth 18 with no time limit, using `multipv=5` for the five alternatives. Deeper analysis can take longer to update the display. Playing moves keep a 0.1-second search budget.

In computer-versus-computer games, each move appears on the board first. The app waits for its Stockfish analysis and plot to appear before making the next move. PAUSE stops further moves while the current analysis finishes.

Move Analysis shows who played the selected move, its Stockfish evaluation, evaluation loss, and five best alternatives from the preceding position. Evaluations name the advantaged side and its advantage in pawns; positions within 0.10 pawns are shown as Equal. Loss is measured for the player who moved. Alternative bars show that player's expected score. Mate scores name the winning side with `#` notation and have no pawn-loss value.

Completed games are saved as JSON files in `gamelog/`. The latest completed game is kept in `gamelog/latest.json`; with REC enabled, it is also kept in `gamelog/rec/` as `YYYY-MM-DD_001.json`. Each file records the players, result, every legal-move position, move, and Stockfish evaluation. Unfinished games are not written.

Notes:

To change the displayed position in code, keep a reference to `BoardView` and call `set_fen(fen)` or `set_board(chess_board)`. Both update the python-chess position and refresh the board. Call these methods from the NiceGUI UI context.

To submit a move in code, call `view.play_move(chess.Move.from_uci('e2e4'))` from the NiceGUI UI context. It returns `True` for a legal move and refreshes the board. `GameController.play(move)` provides the same move validation and state update without a UI.
