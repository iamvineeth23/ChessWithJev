# Graph Report - ChessWithJev  (2026-10-18)

## Corpus Check
- 22 files · ~60,459 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 275 nodes · 602 edges · 24 communities (16 shown, 8 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 30 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2ad78a68`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- GameController
- write_game_log
- .sync
- test_board.py
- board.py
- test_analysis_state.py
- Position
- Board
- BoardView Interaction Flow
- test_linux_support.py
- mock_stockfish
- ChessWithJev
- graphify.js
- opencode.json
- BoardView.play_move
- setup.sh
- Application Stack
- Repository-Only Scope
- User-Facing README Policy
- parametrize
- confidence_chart_svg
- MonkeyPatch
- move_log_text
- test_evaluation_tab_arrows_follow_manual_tab_selection

## God Nodes (most connected - your core abstractions)
1. `BoardView` - 103 edges
2. `Position` - 37 edges
3. `GameController` - 30 edges
4. `write_game_log()` - 13 edges
5. `build_page()` - 13 edges
6. `write_pgn()` - 12 edges
7. `confidence_chart_svg()` - 10 edges
8. `evaluation_chart_svg()` - 10 edges
9. `latest_game_evaluations()` - 8 edges
10. `restore_analysis()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `test_initial_analysis_does_not_block_building_the_game()` --uses--> `GameController`  [INFERRED]
  tests/test_board.py → src/game/controller.py
- `test_move_analysis_loss_and_played_move_outside_top_five()` --uses--> `GameController`  [INFERRED]
  tests/test_board.py → src/game/controller.py
- `test_undo_updates_current_log_and_replacement_moves_without_changing_saved_copies()` --indirect_call--> `write_game_log()`  [INFERRED]
  tests/test_board.py → src/game/log.py
- `test_square_coordinates()` --calls--> `square_name()`  [INFERRED]
  tests/test_board.py → src/ui/board_view.py
- `test_piece_images_are_distinct_svgs()` --calls--> `piece_image()`  [INFERRED]
  tests/test_board.py → src/ui/board_view.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Board Interaction Pipeline** — graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_boardview_flow, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_position, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_sync, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_rendering [EXTRACTED 1.00]
- **BoardView UI Coordination** — graphify_out_memory_query_20260928_112254_c179070d_why_does_boardview_connect_board_view_tests_to_pos_boardview, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_position, graphify_out_memory_query_20260928_112254_c179070d_why_does_boardview_connect_board_view_tests_to_pos_gamecontroller, graphify_out_memory_query_20260926_072013_3a4a3fd3_yes_follow_these_paths_board_tests [EXTRACTED 1.00]
- **Move Log Pipeline** — graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_submission, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_position_move, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_history, graphify_out_memory_query_20260926_072050_3361236b_yes_follow_move_log_tests [EXTRACTED 1.00]

## Communities (24 total, 8 thin omitted)

### Community 0 - "GameController"
Cohesion: 0.12
Nodes (12): SimpleEngine, GameController, Board, Move, Score, test_controller_accepts_moves_from_any_caller(), test_history_reuses_analysis_without_loading_or_engine_calls(), test_move_analysis_reuses_played_option_and_preserves_mate_score() (+4 more)

### Community 1 - "write_game_log"
Cohesion: 0.22
Nodes (12): Color, export_pgn(), Board, Path, write_game_log(), write_pgn(), Path, test_completed_game_logs_use_latest_or_saved_paths() (+4 more)

### Community 2 - ".sync"
Cohesion: 0.10
Nodes (5): Piece, piece_image(), Move, Square, test_piece_images_are_distinct_svgs()

### Community 3 - "test_board.py"
Cohesion: 0.11
Nodes (28): BoardView, test_castling_and_en_passant_update_all_affected_squares(), test_click_move_log_previews_board_and_analysis(), test_clicks_move_only_legal_pieces(), test_computer_game_resumes_from_live_position_while_viewing_history(), test_evaluation_bar_tracks_position_and_reuses_unchanged_score(), test_evaluation_tab_arrows_switch_tabs(), test_evaluation_tabs_share_the_existing_window() (+20 more)

### Community 4 - "board.py"
Cohesion: 0.13
Nodes (22): stockfish_path(), evaluation_chart_svg(), latest_game_evaluations(), latest_game_players(), Path, Return each logged position as a balance percentage: Black -100 to White +100., build_page(), lock_window_aspect_ratio() (+14 more)

### Community 5 - "test_analysis_state.py"
Cohesion: 0.33
Nodes (10): analysis_snapshot(), decode_score(), encode_score(), Score, restore_analysis(), parametrize, test_analysis_score_survives_json_round_trip(), test_invalid_saved_analysis_is_ignored() (+2 more)

### Community 6 - "Position"
Cohesion: 0.08
Nodes (17): Outcome, Position, Board, PieceType, Square, test_all_promotion_choices_are_legal(), test_check_checkmate_stalemate_and_draw_status(), test_claimable_and_automatic_draws() (+9 more)

### Community 7 - "Board"
Cohesion: 0.16
Nodes (6): move_history(), move_history_lines(), Board, PieceType, Keep the prev/next tab arrows in sync with the currently selected tab., test_move_history_preserves_move_numbers_from_custom_position()

### Community 8 - "BoardView Interaction Flow"
Cohesion: 0.16
Nodes (14): Chess AI GUI Separation, Scoped GUI Updates, BoardView Tests, BoardView Interaction Flow, Position, Board Rendering and Controls, BoardView Sync, Move History Formatting (+6 more)

### Community 9 - "test_linux_support.py"
Cohesion: 0.40
Nodes (3): parametrize, test_setup_platform_dependencies(), test_stockfish_discovery()

### Community 10 - "mock_stockfish"
Cohesion: 0.50
Nodes (3): mock_stockfish(), fixture, MonkeyPatch

### Community 11 - "ChessWithJev"
Cohesion: 0.33
Nodes (6): ChessWithJev, Export PGN, Jev, Move Analysis, Setup Script, Stockfish

### Community 19 - "parametrize"
Cohesion: 0.18
Nodes (11): parametrize, test_all_player_combinations_apply_each_move_before_async_analysis(), test_automatic_turn_handles_changes_while_analysis_is_pending(), test_board_opens_native_window(), test_human_analysis_indicator_lasts_until_calculation_finishes(), test_move_analysis_displays_advantaged_side(), test_move_analysis_identifies_player_in_history(), test_move_analysis_loss_and_played_move_outside_top_five() (+3 more)

### Community 20 - "confidence_chart_svg"
Cohesion: 0.22
Nodes (9): confidence_chart_svg(), Return an SVG chart of Jev's confidence (0=0% to 1=100%) at each move it played., game_snapshot(), test_confidence_chart_maps_zero_to_one_onto_percent_axis(), test_confidence_fullscreen_chart_clears_with_inline_chart_and_disables_fullscreen(), test_confidence_plot_hides_chart_and_uncovers_message(), test_confidence_plot_tracks_jev_moves_only(), test_restored_page_shows_jev_predictions_from_snapshot() (+1 more)

### Community 21 - "MonkeyPatch"
Cohesion: 0.25
Nodes (8): prevent_game_log_writes(), fixture, MonkeyPatch, test_analysis_without_a_completed_log_shows_the_requested_warning(), test_export_pgn_and_move_log_button_use_the_live_board(), test_jev_chooses_from_every_legal_move_for_current_fen(), test_jev_failure_is_shown_without_changing_the_board(), test_jev_requires_api_key_and_rejects_an_illegal_answer()

### Community 22 - "move_log_text"
Cohesion: 0.33
Nodes (6): move_log_text(), test_history_buttons_preview_without_changing_live_game(), test_move_history_and_new_game(), test_programmatic_move_refreshes_board_view(), test_real_nicegui_promotion_draw_and_status_controls(), test_undo_redo_updates_board_history_and_status()

## Knowledge Gaps
- **12 isolated node(s):** `$schema`, `setup.sh script`, `Export PGN`, `Move Analysis`, `Setup Script` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 50 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `BoardView` (3× useful, score=2.902267956) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BoardView` connect `test_board.py` to `GameController`, `write_game_log`, `.sync`, `board.py`, `Position`, `Board`, `parametrize`, `confidence_chart_svg`, `MonkeyPatch`, `move_log_text`, `test_evaluation_tab_arrows_follow_manual_tab_selection`?**
  _High betweenness centrality (0.310) - this node is a cross-community bridge._
- **Why does `Position` connect `Position` to `GameController`, `write_game_log`, `test_board.py`, `board.py`, `Board`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `GameController` connect `GameController` to `test_board.py`, `board.py`, `Position`, `parametrize`, `MonkeyPatch`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `BoardView` (e.g. with `game_snapshot()` and `GameController`) actually correct?**
  _`BoardView` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Position` (e.g. with `GameController` and `build_page()`) actually correct?**
  _`Position` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `GameController` (e.g. with `Position` and `BoardView`) actually correct?**
  _`GameController` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `write_game_log()` (e.g. with `.analyse_position()` and `.save_game()`) actually correct?**
  _`write_game_log()` has 4 INFERRED edges - model-reasoned connections that need verification._