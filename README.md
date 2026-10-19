# ChessWithJev

![title](docs/images/banner.png)

A desktop chess application built with NiceGUI to review how good `Jev` from [typesafe.ai](https://typesafe.ai) is at decision making for Chess. Play against `Jev` as human, Stockfish, random moves, or even `Jev`; compare Stockfish analysis; and export completed games as PGN.

Feel free to clone or fork to add support. This is just a hobby project, so don't rely on fast response to any issues. Fast fixes == Fork and do it yourself!

## Requirements

- Python 3.12 or newer
- [Stockfish](https://stockfishchess.org/download/) on your `PATH` or at `/usr/games/stockfish` on Linux
- Homebrew on macOS if the setup script needs to install Stockfish
- On Linux: Debian/Ubuntu with `apt`, sudo access, and a graphical desktop session

**Note:** while Linux maybe supported, I have not yet tested it.

## Install

Clone the repository, then run:

```bash
bash scripts/setup.sh
```

The script creates a local `.venv` and installs the Python dependencies. On macOS, it installs Stockfish with Homebrew when necessary. On Linux, it uses apt to install Stockfish, venv support, and Qt system libraries, then installs the Qt webview backend in `.venv`. Use a Python 3.12+ installation as `python3`; run setup as your regular user (sudo is used for apt only).

## Configure Jev

Jev is optional (if this is not your goal, although why?). It is used only when you select `jev` as a player in the application.

1. Create an API key in your TypeSafe account.
2. Set it in the shell where you will launch the application:

   ```bash
   export JEV_API_KEY="your-api-key"
   ```

   OR

   Create a `.env` file with similar to `.env.example` and add your Jev API key in it. Then run the following:

   ```
   set -a
   source .env
   set +a
   ```

3. Start the app from that same shell.

    ```bash
    .venv/bin/chess
    ```

## Game files

- `gamelog/latest.json` contains the most recently completed game. After Undo, it follows the revised game, including replacement moves.
- **Save** writes dated JSON and PGN copies under `gamelog/rec/`.
- Each JSON log records every move with the Stockfish evaluation after it (`evaluation.wdl_expectation_white`), the top 5 alternative moves Stockfish proposed for that ply as shown in the Move Analysis tab (`stockfish_top_moves`, `null` until that ply has been analysed), the Stockfish eval of the actually played move (`stockfish_played_score_white`, same scale/condition as the top moves, for deriving centipawn loss), and when Jev is a player, Jev's `confidence` in each of its own moves plus its top 5 move recommendations with their probabilities (`jev_top_moves`, absent on other players' moves).
- **Export PGN** writes the current game under `gamelog/pgn/`.

## Development

Run the test suite with:

```bash
.venv/bin/python -m pytest -q
```

## Jev implemenation idea

The idea was simple to use the `choice` of `jev` to rate all available legal moves and choose the best one.

i.e 
```
Chess position (FEN) → Generate legal moves → Jev Choice → Rank moves → Play highest-rated move
```

This works because of a well-known chess composition by Nenad Petrović demonstrated a position with `218` legal moves that can actually be reached through a legal sequence of moves from the standard game start. 
As of 04.10.2026, latest `jev` can handle up to 256 choices.