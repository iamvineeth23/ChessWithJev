# Graph Report - ChessWithJev  (2026-09-26)

## Corpus Check
- Corpus is ~3,832 words - fits in a single context window. You may not need a graph.

## Summary
- 73 nodes · 124 edges · 9 communities (7 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Chess Rules and Position
- Board Controls and History
- Project Setup and Stack
- TypeSafe AI Concepts
- Board State Tests
- Board Rendering Tests
- Piece and Square Rendering
- Application Entry Points
- Setup Script

## God Nodes (most connected - your core abstractions)
1. `BoardView` - 22 edges
2. `Position` - 19 edges
3. `ChessWithJev chess app` - 9 edges
4. `TypeSafe` - 7 edges
5. `piece_image()` - 6 edges
6. `move_history()` - 6 edges
7. `square_name()` - 5 edges
8. `square_color()` - 4 edges
9. `Environment setup` - 4 edges
10. `test_starting_pieces()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `test_clicks_move_only_legal_pieces()` --calls--> `BoardView`  [EXTRACTED]
  tests/test_board.py → src/ui/board.py
- `test_all_promotion_choices_are_legal()` --calls--> `Position`  [EXTRACTED]
  tests/test_board.py → src/game/position.py
- `test_check_checkmate_stalemate_and_draw_status()` --calls--> `Position`  [EXTRACTED]
  tests/test_board.py → src/game/position.py
- `test_claimable_and_automatic_draws()` --calls--> `Position`  [EXTRACTED]
  tests/test_board.py → src/game/position.py
- `test_move_history_preserves_move_numbers_from_custom_position()` --calls--> `Position`  [EXTRACTED]
  tests/test_board.py → src/game/position.py

## Import Cycles
- None detected.

## Communities (9 total, 2 thin omitted)

### Community 0 - "Chess Rules and Position"
Cohesion: 0.13
Nodes (10): Outcome, Position, Board, PieceType, Square, test_all_promotion_choices_are_legal(), test_check_checkmate_stalemate_and_draw_status(), test_claimable_and_automatic_draws() (+2 more)

### Community 1 - "Board Controls and History"
Cohesion: 0.22
Nodes (4): move_history(), Board, PieceType, test_move_history_preserves_move_numbers_from_custom_position()

### Community 2 - "Project Setup and Stack"
Cohesion: 0.33
Nodes (9): ChessWithJev chess app, Chess and AI logic separated from GUI, NiceGUI, pytest, python-chess, Stockfish evaluation or comparison, BoardView position updates, Board launch command (+1 more)

### Community 3 - "TypeSafe AI Concepts"
Cohesion: 0.29
Nodes (8): Choice primitive, Code owned workflow, Jev System One model, Live TypeSafe documentation, Noul primitive, Score primitive, Typed judgments and probabilities, TypeSafe

### Community 4 - "Board State Tests"
Cohesion: 0.25
Nodes (8): BoardView, test_castling_and_en_passant_update_all_affected_squares(), test_move_history_and_new_game(), test_move_updates_only_changed_squares(), test_programmatic_position_updates_refresh_board(), test_promotion_and_external_position_reset(), test_real_nicegui_promotion_draw_and_status_controls(), test_render_uses_current_position()

### Community 5 - "Board Rendering Tests"
Cohesion: 0.36
Nodes (6): square_color(), square_name(), test_board_colors(), test_clicks_move_only_legal_pieces(), test_square_coordinates(), test_starting_pieces()

### Community 6 - "Piece and Square Rendering"
Cohesion: 0.33
Nodes (4): Piece, piece_image(), Square, test_piece_images_are_distinct_svgs()

## Knowledge Gaps
- **6 isolated node(s):** `setup.sh script`, `Live TypeSafe documentation`, `Choice primitive`, `Noul primitive`, `Score primitive` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 19 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Position` connect `Chess Rules and Position` to `Board Controls and History`, `Board State Tests`, `Board Rendering Tests`, `Application Entry Points`?**
  _High betweenness centrality (0.223) - this node is a cross-community bridge._
- **Why does `BoardView` connect `Board State Tests` to `Chess Rules and Position`, `Board Controls and History`, `Board Rendering Tests`, `Piece and Square Rendering`, `Application Entry Points`?**
  _High betweenness centrality (0.203) - this node is a cross-community bridge._
- **Why does `ChessWithJev chess app` connect `Project Setup and Stack` to `TypeSafe AI Concepts`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **What connects `setup.sh script`, `Live TypeSafe documentation`, `Choice primitive` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Chess Rules and Position` be split into smaller, more focused modules?**
  _Cohesion score 0.13071895424836602 - nodes in this community are weakly interconnected._