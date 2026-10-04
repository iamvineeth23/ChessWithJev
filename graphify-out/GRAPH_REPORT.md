# Graph Report - ChessWithJev  (2026-10-04)

## Corpus Check
- 9 files · ~13,161 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 226 nodes · 433 edges · 22 communities (12 shown, 10 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- BoardView Behaviors
- UI Data and Assets
- Engine Controller
- BoardView Tests
- Chess Rule Tests
- Architecture Concepts
- Position State
- Game Logging Tests
- Async Analysis Tests
- App Startup
- TypeSafe Research
- History UI Tests
- Move Analysis Docs
- Setup Script
- Application Stack
- Repository Scope
- README Policy
- Board
- Piece Type
- Square
- Piece Type
- Square

## God Nodes (most connected - your core abstractions)
1. `BoardView` - 83 edges
2. `GameController` - 24 edges
3. `Position` - 13 edges
4. `write_game_log()` - 11 edges
5. `evaluation_chart_svg()` - 10 edges
6. `latest_game_evaluations()` - 8 edges
7. `build_page()` - 8 edges
8. `TypeSafe` - 7 edges
9. `latest_game_players()` - 7 edges
10. `move_log_text()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `BoardView API` --semantically_similar_to--> `BoardView`  [INFERRED] [semantically similar]
  README.md → graphify-out/memory/query_20260928_112254_c179070d_why_does_boardview_connect_board_view_tests_to_pos.md
- `test_initial_analysis_does_not_block_building_the_game()` --uses--> `GameController`  [INFERRED]
  tests/test_board.py → src/game/controller.py
- `test_move_analysis_loss_and_played_move_outside_top_five()` --uses--> `GameController`  [INFERRED]
  tests/test_board.py → src/game/controller.py
- `test_square_coordinates()` --calls--> `square_name()`  [INFERRED]
  tests/test_board.py → src/ui/board_view.py
- `test_starting_pieces()` --calls--> `square_name()`  [INFERRED]
  tests/test_board.py → src/ui/board_view.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Board Interaction Pipeline** — graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_boardview_flow, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_position, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_sync, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_rendering [EXTRACTED 1.00]
- **Move Log Pipeline** — graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_submission, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_position_move, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_history, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_log_tests [EXTRACTED 1.00]
- **BoardView UI Coordination** — graphify_out_memory_query_20260928_112254_c179070d_why_does_boardview_connect_board_view_tests_to_pos_boardview, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_position, graphify_out_memory_query_20260928_112254_c179070d_why_does_boardview_connect_board_view_tests_to_pos_gamecontroller, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_board_tests [EXTRACTED 1.00]

## Communities (22 total, 10 thin omitted)

### Community 0 - "BoardView Behaviors"
Cohesion: 0.10
Nodes (4): PieceType, Square, Board, Move

### Community 1 - "UI Data and Assets"
Cohesion: 0.11
Nodes (21): Piece, evaluation_chart_svg(), latest_game_evaluations(), latest_game_players(), Path, Return each logged position as a balance percentage: Black -100 to White +100., game_snapshot(), move_history() (+13 more)

### Community 2 - "Engine Controller"
Cohesion: 0.11
Nodes (14): Score, SimpleEngine, GameController, Board, Move, Position, Position, test_controller_accepts_moves_from_any_caller() (+6 more)

### Community 3 - "BoardView Tests"
Cohesion: 0.09
Nodes (22): BoardView, test_castling_and_en_passant_update_all_affected_squares(), test_click_move_log_previews_board_and_analysis(), test_clicks_move_only_legal_pieces(), test_computer_game_resumes_from_live_position_while_viewing_history(), test_evaluation_bar_tracks_position_and_reuses_unchanged_score(), test_evaluation_tabs_share_the_existing_window(), test_header_save_button_saves_live_board_and_reenables_on_failure() (+14 more)

### Community 4 - "Chess Rule Tests"
Cohesion: 0.11
Nodes (5): test_human_black_rotates_the_board(), test_incomplete_game_does_not_write_a_log(), test_move_analysis_compares_the_last_move_with_its_prior_options(), test_recording_can_start_enabled(), test_render_uses_current_position()

### Community 5 - "Architecture Concepts"
Cohesion: 0.13
Nodes (17): Chess AI GUI Separation, ChessWithJev, Scoped GUI Updates, BoardView Tests, BoardView Interaction Flow, Position, Board Rendering and Controls, BoardView Sync (+9 more)

### Community 6 - "Position State"
Cohesion: 0.15
Nodes (5): Outcome, Position, Board, PieceType, Square

### Community 7 - "Game Logging Tests"
Cohesion: 0.17
Nodes (11): Color, fixture, MonkeyPatch, Board, Path, write_game_log(), prevent_game_log_writes(), Path (+3 more)

### Community 8 - "Async Analysis Tests"
Cohesion: 0.20
Nodes (10): parametrize, test_all_player_combinations_apply_each_move_before_async_analysis(), test_automatic_turn_handles_changes_while_analysis_is_pending(), test_board_opens_native_window(), test_human_analysis_indicator_lasts_until_calculation_finishes(), test_move_analysis_displays_advantaged_side(), test_move_analysis_identifies_player_in_history(), test_move_analysis_loss_and_played_move_outside_top_five() (+2 more)

### Community 9 - "App Startup"
Cohesion: 0.20
Nodes (10): build_page(), lock_window_aspect_ratio(), main(), page(), Position, saved_game(), test_initial_analysis_does_not_block_building_the_game(), test_landing_starts_game_and_returns_to_setup() (+2 more)

### Community 10 - "TypeSafe Research"
Cohesion: 0.29
Nodes (8): Choice primitive, Code owned workflow, Jev System One model, Live TypeSafe documentation, Noul primitive, Score primitive, Typed judgments and probabilities, TypeSafe

### Community 11 - "History UI Tests"
Cohesion: 0.33
Nodes (6): move_log_text(), test_history_buttons_preview_without_changing_live_game(), test_move_history_and_new_game(), test_programmatic_move_refreshes_board_view(), test_real_nicegui_promotion_draw_and_status_controls(), test_undo_redo_updates_board_history_and_status()

## Knowledge Gaps
- **13 isolated node(s):** `setup.sh script`, `Choice primitive`, `Noul primitive`, `Score primitive`, `Live TypeSafe documentation` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 59 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BoardView` connect `BoardView Tests` to `BoardView Behaviors`, `UI Data and Assets`, `Engine Controller`, `Chess Rule Tests`, `Game Logging Tests`, `Async Analysis Tests`, `App Startup`, `History UI Tests`?**
  _High betweenness centrality (0.279) - this node is a cross-community bridge._
- **Why does `GameController` connect `Engine Controller` to `UI Data and Assets`, `BoardView Tests`, `Chess Rule Tests`, `Async Analysis Tests`, `App Startup`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Why does `Position` connect `Position State` to `UI Data and Assets`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `BoardView` (e.g. with `game_snapshot()` and `GameController`) actually correct?**
  _`BoardView` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `GameController` (e.g. with `BoardView` and `test_initial_analysis_does_not_block_building_the_game()`) actually correct?**
  _`GameController` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `write_game_log()` (e.g. with `.analyse_position()` and `.save_game()`) actually correct?**
  _`write_game_log()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `setup.sh script`, `Choice primitive`, `Noul primitive` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._