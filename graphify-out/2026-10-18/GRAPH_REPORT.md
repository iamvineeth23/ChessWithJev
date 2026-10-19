# Graph Report - ChessWithJev  (2026-10-18)

## Corpus Check
- 22 files · ~61,385 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 283 nodes · 629 edges · 19 communities (11 shown, 8 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 31 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c0243bee`
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

## God Nodes (most connected - your core abstractions)
1. `BoardView` - 106 edges
2. `Position` - 38 edges
3. `GameController` - 30 edges
4. `write_game_log()` - 16 edges
5. `build_page()` - 14 edges
6. `write_pgn()` - 12 edges
7. `confidence_chart_svg()` - 11 edges
8. `restore_analysis()` - 11 edges
9. `evaluation_chart_svg()` - 10 edges
10. `latest_game_evaluations()` - 8 edges

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

## Communities (19 total, 8 thin omitted)

### Community 0 - "GameController"
Cohesion: 0.11
Nodes (12): SimpleEngine, GameController, Board, Move, Score, test_controller_accepts_moves_from_any_caller(), test_history_reuses_analysis_without_loading_or_engine_calls(), test_move_analysis_reuses_played_option_and_preserves_mate_score() (+4 more)

### Community 1 - "write_game_log"
Cohesion: 0.12
Nodes (23): Color, export_pgn(), Board, Move, Path, write_game_log(), write_pgn(), prevent_game_log_writes() (+15 more)

### Community 3 - "test_board.py"
Cohesion: 0.07
Nodes (57): confidence_chart_svg(), Return an SVG chart of Jev's confidence (0=0% to 1=100%) at each move it played., game_snapshot(), BoardView, move_log_text(), parametrize, Selecting a tab by its name alone must also refresh the prev/next arrow…, test_all_player_combinations_apply_each_move_before_async_analysis() (+49 more)

### Community 4 - "board.py"
Cohesion: 0.11
Nodes (26): Piece, stockfish_path(), evaluation_chart_svg(), latest_game_evaluations(), latest_game_players(), Path, Return each logged position as a balance percentage: Black -100 to White +100., build_page() (+18 more)

### Community 5 - "test_analysis_state.py"
Cohesion: 0.28
Nodes (13): analysis_snapshot(), decode_score(), encode_score(), Score, restore_analysis(), parametrize, test_analysis_score_survives_json_round_trip(), test_invalid_saved_analysis_is_ignored() (+5 more)

### Community 6 - "Position"
Cohesion: 0.08
Nodes (16): Outcome, Position, Board, PieceType, Square, test_all_promotion_choices_are_legal(), test_check_checkmate_stalemate_and_draw_status(), test_claimable_and_automatic_draws() (+8 more)

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

## Knowledge Gaps
- **12 isolated node(s):** `$schema`, `setup.sh script`, `Export PGN`, `Move Analysis`, `Setup Script` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 51 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `BoardView` (3× useful, score=2.902267956) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BoardView` connect `test_board.py` to `GameController`, `write_game_log`, `.sync`, `board.py`, `Position`, `Board`?**
  _High betweenness centrality (0.310) - this node is a cross-community bridge._
- **Why does `Position` connect `Position` to `GameController`, `write_game_log`, `test_board.py`, `board.py`, `Board`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Why does `GameController` connect `GameController` to `write_game_log`, `test_board.py`, `board.py`, `Position`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `BoardView` (e.g. with `game_snapshot()` and `GameController`) actually correct?**
  _`BoardView` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Position` (e.g. with `GameController` and `build_page()`) actually correct?**
  _`Position` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `GameController` (e.g. with `Position` and `BoardView`) actually correct?**
  _`GameController` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `write_game_log()` (e.g. with `.analyse_position()` and `.save_game()`) actually correct?**
  _`write_game_log()` has 5 INFERRED edges - model-reasoned connections that need verification._