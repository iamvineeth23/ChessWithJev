---
type: "query"
date: "2026-09-28T11:22:54.859136+00:00"
question: "Why does BoardView connect Board View Tests to Position State, Game Interaction Flow, Analysis and Page Setup, Game Controller Engines, Game Logging Tests, Piece Rendering?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["BoardView", "Position", "GameController", "build_page", ".sync", ".play_human_move", ".render", ".show_analysis", "test_board.py"]
---

# Q: Why does BoardView connect Board View Tests to Position State, Game Interaction Flow, Analysis and Page Setup, Game Controller Engines, Game Logging Tests, Piece Rendering?

## Answer

Expanded from original query via graph vocabulary: [board, view, position, interaction, analysis, controller, engine, game, piece, rendering, tests]. BoardView is the UI coordination boundary at src/ui/board_view.py:L47. It holds or uses Position and GameController at L48 and L51, exposes interaction methods including play_human_move at L123, sync at L235, render at L283, and show_analysis at L314, and is constructed by build_page at src/ui/board.py:L110. This single orchestration role naturally crosses Position State, Game Interaction Flow, Analysis and Page Setup, Game Controller Engines, and Piece Rendering. The Board View Tests and Game Logging Tests communities connect because tests/test_board.py has 23 direct BoardView connections and exercises behavior spanning move synchronization, history, evaluation, analysis warnings, and completed-game logging. The Position and GameController edges are INFERRED uses; the imports, construction, methods, and test references are EXTRACTED.

## Outcome

- Signal: useful

## Source Nodes

- BoardView
- Position
- GameController
- build_page
- .sync
- .play_human_move
- .render
- .show_analysis
- test_board.py