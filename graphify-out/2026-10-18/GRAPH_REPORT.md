# Graph Report - ChessWithJev  (2026-10-04)

## Corpus Check
- 7 files · ~14,332 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 239 nodes · 452 edges · 24 communities (13 shown, 11 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 25 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Engine Game Control
- Game Logging Tests
- Board Interaction
- Board View Tests
- Application Shell
- Board Feature Tests
- Position Game State
- Board View Rendering
- Architecture Principles
- Async Analysis Tests
- TypeSafe AI Integration
- User Documentation
- Evaluation Charts
- Move History Tests
- Move Execution API
- Setup Script
- Application Stack
- Repository Scope
- README Policy
- Chess Board
- Piece Types
- Board Squares
- Piece Type Helpers
- Square Helpers

## God Nodes (most connected - your core abstractions)
1. `BoardView` - 87 edges
2. `GameController` - 27 edges
3. `Position` - 13 edges
4. `write_game_log()` - 11 edges
5. `write_pgn()` - 8 edges
6. `build_page()` - 8 edges
7. `TypeSafe` - 7 edges
8. `move_log_text()` - 7 edges
9. `piece_image()` - 6 edges
10. `square_name()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `test_initial_analysis_does_not_block_building_the_game()` --uses--> `GameController`  [INFERRED]
  tests/test_board.py → src/game/controller.py
- `test_move_analysis_loss_and_played_move_outside_top_five()` --uses--> `GameController`  [INFERRED]
  tests/test_board.py → src/game/controller.py
- `test_square_coordinates()` --calls--> `square_name()`  [INFERRED]
  tests/test_board.py → src/ui/board_view.py
- `test_starting_pieces()` --calls--> `square_name()`  [INFERRED]
  tests/test_board.py → src/ui/board_view.py
- `test_piece_images_are_distinct_svgs()` --calls--> `piece_image()`  [INFERRED]
  tests/test_board.py → src/ui/board_view.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Board Interaction Pipeline** — graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_boardview_flow, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_position, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_sync, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_rendering [EXTRACTED 1.00]
- **BoardView UI Coordination** — graphify_out_memory_query_20260928_112254_c179070d_why_does_boardview_connect_board_view_tests_to_pos_boardview, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_position, graphify_out_memory_query_20260928_112254_c179070d_why_does_boardview_connect_board_view_tests_to_pos_gamecontroller, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_board_tests [EXTRACTED 1.00]
- **Move Log Pipeline** — graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_submission, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_position_move, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_history, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_log_tests [EXTRACTED 1.00]

## Communities (24 total, 11 thin omitted)

### Community 0 - "Engine Game Control"
Cohesion: 0.11
Nodes (14): Score, SimpleEngine, GameController, Board, Move, Position, Position, test_controller_accepts_moves_from_any_caller() (+6 more)

### Community 1 - "Game Logging Tests"
Cohesion: 0.12
Nodes (19): Color, fixture, MonkeyPatch, Board, Path, write_game_log(), write_pgn(), export_pgn() (+11 more)

### Community 3 - "Board View Tests"
Cohesion: 0.08
Nodes (23): BoardView, test_castling_and_en_passant_update_all_affected_squares(), test_click_move_log_previews_board_and_analysis(), test_clicks_move_only_legal_pieces(), test_computer_game_resumes_from_live_position_while_viewing_history(), test_evaluation_bar_tracks_position_and_reuses_unchanged_score(), test_evaluation_tabs_share_the_existing_window(), test_header_save_button_saves_live_board_and_reenables_on_failure() (+15 more)

### Community 4 - "Application Shell"
Cohesion: 0.11
Nodes (19): Piece, build_page(), game_snapshot(), lock_window_aspect_ratio(), main(), page(), Position, saved_game() (+11 more)

### Community 5 - "Board Feature Tests"
Cohesion: 0.10
Nodes (7): test_human_black_rotates_the_board(), test_jev_predictions_tab_shows_top_five_and_selected_move(), test_live_plot_fills_moves_skipped_by_automatic_reply(), test_move_analysis_cache_distinguishes_history_and_clears_on_replacement(), test_piece_animation_offsets_follow_board_orientation(), test_programmatic_position_updates_refresh_board(), test_promotion_and_external_position_reset()

### Community 6 - "Position Game State"
Cohesion: 0.15
Nodes (5): Outcome, Position, Board, PieceType, Square

### Community 7 - "Board View Rendering"
Cohesion: 0.23
Nodes (5): PieceType, move_history(), move_history_lines(), Board, test_move_history_preserves_move_numbers_from_custom_position()

### Community 8 - "Architecture Principles"
Cohesion: 0.16
Nodes (14): Chess AI GUI Separation, Scoped GUI Updates, BoardView Tests, BoardView Interaction Flow, Position, Board Rendering and Controls, BoardView Sync, Move History Formatting (+6 more)

### Community 9 - "Async Analysis Tests"
Cohesion: 0.20
Nodes (10): parametrize, test_all_player_combinations_apply_each_move_before_async_analysis(), test_automatic_turn_handles_changes_while_analysis_is_pending(), test_board_opens_native_window(), test_human_analysis_indicator_lasts_until_calculation_finishes(), test_move_analysis_displays_advantaged_side(), test_move_analysis_identifies_player_in_history(), test_move_analysis_loss_and_played_move_outside_top_five() (+2 more)

### Community 10 - "TypeSafe AI Integration"
Cohesion: 0.29
Nodes (8): Choice primitive, Code owned workflow, Jev System One model, Live TypeSafe documentation, Noul primitive, Score primitive, Typed judgments and probabilities, TypeSafe

### Community 11 - "User Documentation"
Cohesion: 0.33
Nodes (6): ChessWithJev, Export PGN, Jev, Move Analysis, Setup Script, Stockfish

### Community 12 - "Evaluation Charts"
Cohesion: 0.40
Nodes (4): latest_game_evaluations(), latest_game_players(), Path, Return each logged position as a balance percentage: Black -100 to White +100.

### Community 13 - "Move History Tests"
Cohesion: 0.33
Nodes (6): move_log_text(), test_history_buttons_preview_without_changing_live_game(), test_move_history_and_new_game(), test_programmatic_move_refreshes_board_view(), test_real_nicegui_promotion_draw_and_status_controls(), test_undo_redo_updates_board_history_and_status()

## Knowledge Gaps
- **15 isolated node(s):** `setup.sh script`, `Choice primitive`, `Noul primitive`, `Score primitive`, `Live TypeSafe documentation` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 61 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BoardView` connect `Board View Tests` to `Engine Game Control`, `Game Logging Tests`, `Board Interaction`, `Application Shell`, `Board Feature Tests`, `Board View Rendering`, `Async Analysis Tests`, `Move History Tests`?**
  _High betweenness centrality (0.280) - this node is a cross-community bridge._
- **Why does `GameController` connect `Engine Game Control` to `Game Logging Tests`, `Board View Tests`, `Application Shell`, `Board Feature Tests`, `Async Analysis Tests`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Why does `Position` connect `Position Game State` to `Game Logging Tests`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `BoardView` (e.g. with `game_snapshot()` and `GameController`) actually correct?**
  _`BoardView` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `GameController` (e.g. with `BoardView` and `test_initial_analysis_does_not_block_building_the_game()`) actually correct?**
  _`GameController` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `setup.sh script`, `Choice primitive`, `Noul primitive` to the rest of the system?**
  _15 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Engine Game Control` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._