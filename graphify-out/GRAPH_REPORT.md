# Graph Report - ChessWithJev  (2026-09-28)

## Corpus Check
- 13 files · ~7,808 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 174 nodes · 320 edges · 19 communities (9 shown, 10 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Board View Tests
- Position State
- Game Interaction Flow
- Analysis and Page Setup
- Game Controller Engines
- Documented Board Architecture
- Game Logging Tests
- TypeSafe AI Concepts
- Piece Rendering
- README Policy
- Setup Script
- Application Stack
- ChessWithJev Project
- Repository Scope
- Application Launcher
- Game Recording
- Chess Board
- Piece Types
- Board Squares

## God Nodes (most connected - your core abstractions)
1. `BoardView` - 54 edges
2. `Position` - 36 edges
3. `GameController` - 17 edges
4. `write_game_log()` - 8 edges
5. `latest_game_evaluations()` - 8 edges
6. `TypeSafe` - 7 edges
7. `latest_game_players()` - 7 edges
8. `build_page()` - 7 edges
9. `move_log_text()` - 7 edges
10. `evaluation_chart_svg()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `BoardView API` --semantically_similar_to--> `BoardView Interaction Flow`  [INFERRED] [semantically similar]
  README.md → graphify-out/memory/query_20260926_072013_3a4a3fd3_yes_follow_these_paths.md
- `test_square_coordinates()` --calls--> `square_name()`  [INFERRED]
  tests/test_board.py → src/ui/board_view.py
- `test_piece_images_are_distinct_svgs()` --calls--> `piece_image()`  [INFERRED]
  tests/test_board.py → src/ui/board_view.py
- `test_controller_accepts_moves_from_any_caller()` --calls--> `GameController`  [EXTRACTED]
  tests/test_board.py → src/game/controller.py
- `test_random_black_move_uses_legal_moves_and_stops_at_game_end()` --calls--> `GameController`  [EXTRACTED]
  tests/test_board.py → src/game/controller.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Board Interaction Pipeline** — graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_boardview_flow, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_position, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_sync, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_rendering [EXTRACTED 1.00]
- **Move Log Pipeline** — graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_submission, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_position_move, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_history, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_log_tests [EXTRACTED 1.00]

## Communities (19 total, 10 thin omitted)

### Community 0 - "Board View Tests"
Cohesion: 0.12
Nodes (25): parametrize, BoardView, move_log_text(), test_board_opens_native_window(), test_castling_and_en_passant_update_all_affected_squares(), test_clicks_move_only_legal_pieces(), test_evaluation_bar_tracks_position_and_reuses_unchanged_score(), test_history_buttons_preview_without_changing_live_game() (+17 more)

### Community 1 - "Position State"
Cohesion: 0.08
Nodes (16): Outcome, Position, Board, PieceType, Square, test_all_promotion_choices_are_legal(), test_check_checkmate_stalemate_and_draw_status(), test_claimable_and_automatic_draws() (+8 more)

### Community 2 - "Game Interaction Flow"
Cohesion: 0.11
Nodes (7): move_history(), move_history_lines(), Board, Move, PieceType, Square, test_move_history_preserves_move_numbers_from_custom_position()

### Community 3 - "Analysis and Page Setup"
Cohesion: 0.15
Nodes (17): evaluation_chart_svg(), latest_game_evaluations(), latest_game_players(), Path, Return each logged position as a balance percentage: Black -100 to White +100., build_page(), game_snapshot(), lock_window_aspect_ratio() (+9 more)

### Community 4 - "Game Controller Engines"
Cohesion: 0.18
Nodes (6): SimpleEngine, GameController, Board, Move, test_controller_accepts_moves_from_any_caller(), test_stockfish_evaluation_handles_scores_and_finished_games()

### Community 5 - "Documented Board Architecture"
Cohesion: 0.17
Nodes (13): Chess AI GUI Separation, Scoped GUI Updates, BoardView Tests, BoardView Interaction Flow, Position, Board Rendering and Controls, BoardView Sync, Move History Formatting (+5 more)

### Community 6 - "Game Logging Tests"
Cohesion: 0.20
Nodes (9): Color, fixture, MonkeyPatch, Board, Path, write_game_log(), prevent_game_log_writes(), test_analysis_without_a_completed_log_shows_the_requested_warning() (+1 more)

### Community 7 - "TypeSafe AI Concepts"
Cohesion: 0.29
Nodes (8): Choice primitive, Code owned workflow, Jev System One model, Live TypeSafe documentation, Noul primitive, Score primitive, Typed judgments and probabilities, TypeSafe

### Community 8 - "Piece Rendering"
Cohesion: 0.25
Nodes (6): Piece, piece_image(), square_name(), test_piece_images_are_distinct_svgs(), test_square_coordinates(), test_starting_pieces()

## Knowledge Gaps
- **13 isolated node(s):** `Choice primitive`, `Noul primitive`, `Score primitive`, `Live TypeSafe documentation`, `setup.sh script` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 50 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BoardView` connect `Board View Tests` to `Position State`, `Game Interaction Flow`, `Analysis and Page Setup`, `Game Controller Engines`, `Game Logging Tests`, `Piece Rendering`?**
  _High betweenness centrality (0.248) - this node is a cross-community bridge._
- **Why does `Position` connect `Position State` to `Board View Tests`, `Game Interaction Flow`, `Analysis and Page Setup`, `Game Controller Engines`, `Game Logging Tests`, `Piece Rendering`?**
  _High betweenness centrality (0.182) - this node is a cross-community bridge._
- **Why does `GameController` connect `Game Controller Engines` to `Board View Tests`, `Position State`, `Analysis and Page Setup`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `BoardView` (e.g. with `game_snapshot()` and `GameController`) actually correct?**
  _`BoardView` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Position` (e.g. with `GameController` and `build_page()`) actually correct?**
  _`Position` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `GameController` (e.g. with `Position` and `BoardView`) actually correct?**
  _`GameController` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Choice primitive`, `Noul primitive`, `Score primitive` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._