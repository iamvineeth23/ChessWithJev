---
type: "query"
date: "2026-09-26T07:20:13.929997+00:00"
question: "yes follow these paths"
contributor: "graphify"
outcome: "useful"
source_nodes: ["BoardView", "Position", "main"]
---

# Q: yes follow these paths

## Answer

Expanded from graph vocabulary: board, view, position, move, render, piece, square, history, test, sync. BoardView is created by main in src/ui/board.py:L205. BoardView owns Position at L36-L37; click_square delegates moves to Position at L81-L95. Position validates legal moves in src/game/position.py:L43-L52. BoardView methods set_fen, set_board, choose_promotion, claim_draw, new_game, and click_square call sync, which refreshes status, history, draw controls, and changed squares at src/ui/board.py:L97-L114. render builds the board using square_name, square_color, piece_image, and click handlers at L116-L131. render_controls connects status, move_history, New Game, Claim Draw, and promotion actions at L133-L148. Tests instantiate BoardView at tests/test_board.py:L55,L68,L76,L96,L121,L142. This spans the graph communities for rules, controls/history, rendering, tests, and entry points. The graph classifies BoardView in Board State Tests due to clustering, not code ownership.

## Outcome

- Signal: useful

## Source Nodes

- BoardView
- Position
- main