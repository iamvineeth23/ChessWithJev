import runpy
from base64 import b64decode
from datetime import date
from pathlib import Path
import json
import chess
import chess.engine
import pytest
from src.game.position import Position
from src.game.controller import GameController
from src.ui.analysis import evaluation_chart_svg, latest_game_evaluations, latest_game_players
from src.ui.board import (BoardView, build_page, lock_window_aspect_ratio, move_history, piece_image, square_color,
                          square_name)
from src.ui import board
from src.ui import board_view
from src.ui.board_assets import MOVE_LOG_SCRIPT
from src.game.log import write_game_log
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def prevent_game_log_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(board_view, 'write_game_log', MagicMock())


def move_log_text(view: BoardView) -> str:
    return '\n'.join(label.text for label in view.history_labels)


def test_board_colors() -> None:
    colors = [[square_color(row, column) for column in range(8)] for row in range(8)]
    assert all(colors[row][column] != colors[row][column + 1] for row in range(8) for column in range(7))
    assert all(colors[row][column] != colors[row + 1][column] for row in range(7) for column in range(8))
    assert colors[0][0] == colors[7][7] == 'light'
    assert colors[7][0] == 'dark'  # a1


def test_analysis_chart_uses_each_logged_evaluation_and_marks_balance(tmp_path: Path) -> None:
    path = tmp_path / 'latest.json'
    path.write_text(json.dumps({'players': {'white': {'type': 'random'}, 'black': {'type': 'stockfish', 'elo': 2100}}, 'moves': [
        {'evaluation': {'wdl_expectation_white': 0.25}},
        {'evaluation': {'wdl_expectation_white': 0.5}},
        {'evaluation': {'wdl_expectation_white': 0.75}},
        {'evaluation': {'wdl_expectation_white': None}},
    ]}))
    evaluations = latest_game_evaluations(path)
    assert evaluations == [-50, 0, 50]
    assert latest_game_players(path) == 'White: Random | Black: Stockfish [2100]'
    chart = evaluation_chart_svg(evaluations)
    assert '0% EVEN' in chart
    assert 'chart-player-white">WHITE' in chart and 'chart-player-black">BLACK' in chart
    assert '1</text>' in chart and '>3</text>' in chart
    assert '100.0,391.0 570.0,274.0 1040.0,157.0' in chart


def test_analysis_helpers_remain_available_from_board() -> None:
    assert board.latest_game_evaluations is latest_game_evaluations
    assert board.latest_game_players is latest_game_players
    assert board.evaluation_chart_svg is evaluation_chart_svg


def test_board_view_names_remain_available_from_board() -> None:
    assert board.BoardView is board_view.BoardView
    assert board.move_history is board_view.move_history
    assert board.piece_image is board_view.piece_image
    assert board.square_color is board_view.square_color
    assert board.square_name is board_view.square_name


def test_analysis_without_a_completed_log_shows_the_requested_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    notify = MagicMock()
    monkeypatch.setattr(board_view, 'latest_game_evaluations', lambda: [])
    monkeypatch.setattr(board_view.ui, 'notify', notify)

    BoardView().show_analysis()

    notify.assert_called_once_with('Run a game. Last game log not available', type='warning')


@pytest.mark.parametrize('debug', [False, True])
def test_board_opens_native_window(debug: bool) -> None:
    with patch.object(board.sys, 'argv', ['chess', '-d'] if debug else ['chess']), patch.object(board.ui, 'run') as run:
        runpy.run_path(board.__file__, run_name='__mp_main__')
    run.assert_called_once_with(native=True, title='ChessWithJev', window_size=(1100, 786), reconnect_timeout=60,
                                storage_secret='chesswithjev-local-state')


def test_native_window_keeps_its_starting_aspect_ratio() -> None:
    window = MagicMock()
    with patch('webview.windows', [window]), patch('PyObjCTools.AppHelper.callAfter', side_effect=lambda callback: callback()):
        lock_window_aspect_ratio()
    window.events.shown.wait.assert_called_once_with()
    window.native.setContentMinSize_.assert_called_once_with((800, 600))
    window.native.setContentSize_.assert_called_once_with((1100, 786))
    window.native.setContentAspectRatio_.assert_called_once_with((1100, 786))


def test_move_log_observer_follows_a_replaced_game_panel() -> None:
    source = MOVE_LOG_SCRIPT
    assert 'let moveLog;' in source
    assert 'if (!log || log === moveLog) return;' in source
    assert 'moveLogObserver?.disconnect();' in source


def test_piece_images_are_distinct_svgs() -> None:
    images = [piece_image(chess.Piece(piece_type, color))
              for color in chess.COLORS for piece_type in chess.PIECE_TYPES]
    assert len(set(images)) == 12
    assert all(b'<svg ' in b64decode(image.split(',', 1)[1]) for image in images)


def test_square_coordinates() -> None:
    assert square_name(0, 0) == 'a8'
    assert square_name(0, 7) == 'h8'
    assert square_name(7, 0) == 'a1'
    assert square_name(7, 7) == 'h1'
    assert square_name(0, 0, flipped=True) == 'h1'
    assert square_name(7, 7, flipped=True) == 'a8'


def test_human_black_rotates_the_board() -> None:
    view = BoardView(white='random', black='human')
    view.render()

    assert list(view.squares)[:2] == [chess.H1, chess.G1]
    assert list(view.squares)[-2:] == [chess.B8, chess.A8]

    both_human = BoardView(white='human', black='human')
    both_human.render()
    assert list(both_human.squares)[:2] == [chess.A8, chess.B8]


def test_starting_pieces() -> None:
    position = Position()
    expected = ['rnbqkbnr', 'pppppppp', '........', '........',
                '........', '........', 'PPPPPPPP', 'RNBQKBNR']
    actual = [''.join((position.board.piece_at(chess.parse_square(square_name(row, column))).symbol()
                       if position.board.piece_at(chess.parse_square(square_name(row, column))) else '.')
                      for column in range(8)) for row in range(8)]
    assert actual == expected


def test_programmatic_position_updates_refresh_board() -> None:
    view = BoardView()
    with patch.object(view, 'sync') as refresh:
        view.set_fen('8/8/8/8/8/8/8/K6k w - - 0 1')
        assert view.position.board.piece_at(chess.A1) == chess.Piece.from_symbol('K')
        refresh.assert_called_once_with()
        replacement = chess.Board.empty()
        replacement.set_piece_at(chess.E4, chess.Piece.from_symbol('q'))
        view.set_board(replacement)
        assert view.position.board.piece_at(chess.E4) == chess.Piece.from_symbol('q')
        assert refresh.call_count == 2


def test_render_uses_current_position() -> None:
    view = BoardView()
    view.position.set_fen('8/8/8/8/8/8/8/K6k w - - 0 1')
    with patch.object(board.ui, 'element', return_value=MagicMock()), patch.object(board.ui, 'image') as image:
        view.render()
    assert image.call_count == 2


def test_clicks_move_only_legal_pieces() -> None:
    view = BoardView()
    with patch.object(view, 'sync'), patch('src.game.controller.random.choice', side_effect=lambda moves: next(move for move in moves if move.uci() == 'e7e5')):
        view.click_square(chess.E7)  # black cannot move first
        assert view.selected is None
        view.click_square(chess.E2)
        assert view.selected == chess.E2
        view.click_square(chess.E5)  # illegal pawn move
        assert view.position.board.fen() == chess.Board().fen()
        view.click_square(chess.E2)
        view.click_square(chess.E4)
        assert view.position.board.piece_at(chess.E4) == chess.Piece.from_symbol('P')
        assert view.position.board.turn == chess.WHITE
        assert [move.uci() for move in view.position.board.move_stack] == ['e2e4', 'e7e5']
        view.click_square(chess.E7)
        assert view.selected is None
        assert view.position.board.piece_at(chess.E5) == chess.Piece.from_symbol('p')


def test_controller_accepts_moves_from_any_caller() -> None:
    controller = GameController()
    assert not controller.play(chess.Move.from_uci('e2e5'))
    assert controller.position.board.fen() == chess.STARTING_FEN
    assert controller.play(chess.Move.from_uci('e2e4'))
    assert controller.play(chess.Move.from_uci('e7e5'))
    assert [move.uci() for move in controller.position.board.move_stack] == ['e2e4', 'e7e5']


def test_random_black_move_uses_legal_moves_and_stops_at_game_end() -> None:
    controller = GameController()
    assert not controller.play_random_black_move()
    assert controller.play(chess.Move.from_uci('f2f3'))
    with patch('src.game.controller.random.choice', side_effect=lambda moves: next(move for move in moves if move.uci() == 'e7e5')):
        assert controller.play_random_black_move()
    assert controller.play(chess.Move.from_uci('g2g4'))
    with patch('src.game.controller.random.choice', side_effect=lambda moves: next(move for move in moves if move.uci() == 'd8h4')):
        assert controller.play_random_black_move()
    assert controller.position.status() == 'Checkmate — Black wins'
    assert not controller.play_random_black_move()


def test_human_cannot_move_black_and_mate_ends_before_reply() -> None:
    view = BoardView()
    view.set_fen('7k/8/5KQ1/8/8/8/8/8 w - - 0 1')
    with patch('src.game.controller.random.choice') as choose:
        view.click_square(chess.G6)
        view.click_square(chess.G7)
    assert view.position.status() == 'Checkmate — White wins'
    choose.assert_not_called()
    assert len(view.position.board.move_stack) == 1
    view.set_fen('7k/8/8/8/8/8/8/K7 b - - 0 1')
    view.click_square(chess.H8)
    assert view.selected is None


def test_evaluation_tabs_share_the_existing_window() -> None:
    from nicegui import ui
    with ui.element('div') as container:
        view = BoardView(white='human', black='human')
        with patch.object(view, 'sync_evaluation_plot'):
            view.render_controls()
    tabs = next(element for element in container.descendants() if isinstance(element, ui.tabs))
    panels = next(element for element in container.descendants() if isinstance(element, ui.tab_panels))
    assert [element._props['label'] for element in tabs.default_slot.children] == ['Evaluation Plot', 'Jev Predictions']
    assert panels.value is tabs.default_slot.children[0]
    assert 'move-placeholder-panel' in panels.parent_slot.parent._classes
    evaluation, predictions = panels.default_slot.children
    assert view.evaluation_plot in evaluation.descendants()
    expand = next(element for element in evaluation.descendants() if isinstance(element, ui.button) and element._props.get('aria-label') == 'Toggle evaluation plot fullscreen')
    assert expand._props['aria-label'] == 'Toggle evaluation plot fullscreen'
    dialog = view.fullscreen_evaluation_plot.parent_slot.parent.parent_slot.parent
    assert dialog._props['maximized']
    next(iter(expand._event_listeners.values())).handler(None)
    assert dialog.value
    exit_button = next(element for element in dialog.descendants() if isinstance(element, ui.button))
    next(iter(exit_button._event_listeners.values())).handler(None)
    assert not dialog.value
    assert not predictions.default_slot.children
    tabs.set_value('Jev Predictions')
    assert panels.value == 'Jev Predictions'
    tabs.set_value('Evaluation Plot')
    assert panels.value == 'Evaluation Plot'


def test_programmatic_move_refreshes_board_view() -> None:
    view = BoardView()
    view.render_controls()
    view.fen_label = MagicMock()
    assert view.play_move(chess.Move.from_uci('e2e4'))
    assert move_log_text(view) == '1. e4'
    assert view.status_label.text == 'Black to move'
    view.fen_label.set_text.assert_called_with(view.position.board.fen())


def test_promotion_and_external_position_reset() -> None:
    view = BoardView()
    view.promotion_dialog = MagicMock()
    with patch.object(view, 'sync'):
        view.set_fen('7k/P7/8/8/8/8/8/K7 w - - 0 1')
        view.click_square(chess.A7)
        view.click_square(chess.A8)
        assert view.pending_promotion == (chess.A7, chess.A8)
        assert view.position.board.piece_at(chess.A7) == chess.Piece.from_symbol('P')
        view.choose_promotion(chess.KNIGHT)
        assert view.position.board.piece_at(chess.A8) == chess.Piece.from_symbol('N')
        view.click_square(chess.H8)
        view.set_fen(chess.STARTING_FEN)
        assert view.selected is None


def test_all_promotion_choices_are_legal() -> None:
    for piece_type in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
        position = Position()
        position.set_fen('7k/P7/8/8/8/8/8/K7 w - - 0 1')
        assert not position.move(chess.A7, chess.A8)
        assert position.move(chess.A7, chess.A8, promotion=piece_type)
        assert position.board.piece_at(chess.A8) == chess.Piece(piece_type, chess.WHITE)


def test_move_updates_only_changed_squares() -> None:
    view = BoardView()
    elements = [MagicMock() for _ in chess.SQUARES]
    view.squares = dict(zip(chess.SQUARES, elements))
    view.shown_pieces = {square: view.position.board.piece_at(square) for square in chess.SQUARES}
    with patch('src.game.controller.random.choice', side_effect=lambda moves: next(move for move in moves if move.uci() == 'e7e5')):
        view.click_square(chess.E2)
        assert not any(element.clear.called for element in elements)
        view.click_square(chess.E4)
    changed = {square for square, element in view.squares.items() if element.clear.called}
    assert changed == {chess.E2, chess.E4, chess.E7, chess.E5}


def test_only_legal_moves_are_printed(capsys) -> None:
    position = Position()
    assert not position.move(chess.E2, chess.E5)
    assert capsys.readouterr().out == ''
    assert position.move(chess.E2, chess.E4)
    assert position.move(chess.E7, chess.E5)
    assert capsys.readouterr().out == 'e4\ne5\n'


def test_print_legal_moves_uses_the_current_position(capsys) -> None:
    position = Position()
    position.set_fen('8/8/8/8/8/8/8/K6k w - - 0 1')
    position.print_legal_moves()
    assert capsys.readouterr().out == "['Kb2', 'Ka2', 'Kb1']\n"


def test_debug_prints_legal_moves_after_each_move(capsys) -> None:
    position = Position()
    with patch('src.game.position.sys.argv', ['chess', '-d']):
        assert position.move(chess.E2, chess.E4)
    assert capsys.readouterr().out == "e4\n['Nh6', 'Nf6', 'Nc6', 'Na6', 'h6', 'g6', 'f6', 'e6', 'd6', 'c6', 'b6', 'a6', 'h5', 'g5', 'f5', 'e5', 'd5', 'c5', 'b5', 'a5']\n"


def test_castling_and_en_passant_update_all_affected_squares() -> None:
    view = BoardView()
    view.squares = {square: MagicMock() for square in chess.SQUARES}
    view.shown_pieces = {square: view.position.board.piece_at(square) for square in chess.SQUARES}
    view.promotion_dialog = MagicMock()
    view.set_fen('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1')
    for element in view.squares.values():
        element.reset_mock()
    with patch.object(view.controller, 'play_random_move'):
        view.click_square(chess.E1)
        view.click_square(chess.G1)
    assert view.position.board.piece_at(chess.F1) == chess.Piece.from_symbol('R')
    assert view.position.board.piece_at(chess.G1) == chess.Piece.from_symbol('K')
    assert {square for square, element in view.squares.items() if element.clear.called} == {chess.E1, chess.F1, chess.G1, chess.H1}
    view.set_fen('7k/8/8/3pP3/8/8/8/K7 w - d6 0 1')
    for element in view.squares.values():
        element.reset_mock()
    with patch.object(view.controller, 'play_random_move'):
        view.click_square(chess.E5)
        view.click_square(chess.D6)
    assert view.position.board.piece_at(chess.D5) is None
    assert view.position.board.piece_at(chess.D6) == chess.Piece.from_symbol('P')
    assert {square for square, element in view.squares.items() if element.clear.called} == {chess.E5, chess.D5, chess.D6}


def test_check_checkmate_stalemate_and_draw_status() -> None:
    position = Position()
    position.set_fen('7k/6Q1/6K1/8/8/8/8/8 b - - 0 1')
    assert position.status() == 'Checkmate — White wins'
    assert not position.move(chess.H8, chess.H7)
    position.set_fen('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')
    assert position.status() == 'Stalemate — draw'
    position.set_fen('7k/8/6K1/8/8/8/8/8 w - - 0 1')
    assert position.status() == 'Draw — insufficient material'
    position.set_fen('7k/8/8/8/8/8/7R/K7 b - - 0 1')
    assert position.status() == 'Black to move — check'


def test_claimable_and_automatic_draws() -> None:
    position = Position()
    position.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 100 1')
    assert position.claim_draw()
    assert position.status() == 'Draw — 50-move rule'
    assert not position.move(chess.G2, chess.G3)
    position.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 150 1')
    assert position.status() == 'Draw — 75-move rule'
    assert not position.claim_draw()


def test_threefold_claim_and_fivefold_automatic_draw(capsys) -> None:
    position = Position()
    cycle = [(chess.G1, chess.F3), (chess.G8, chess.F6),
             (chess.F3, chess.G1), (chess.F6, chess.G8)]
    for _ in range(2):
        for source, target in cycle:
            assert position.move(source, target)
    assert position.claim_draw()
    assert position.status() == 'Draw — threefold repetition'
    position.set_fen(chess.STARTING_FEN)
    for _ in range(4):
        for source, target in cycle:
            assert position.move(source, target)
    assert position.status() == 'Draw — fivefold repetition'
    assert not position.move(chess.E2, chess.E4)
    capsys.readouterr()


def test_real_nicegui_promotion_draw_and_status_controls() -> None:
    def click(element) -> None:
        listener = next(iter(element._event_listeners.values()))
        element.client.handle_event({'id': element.id, 'listener_id': listener.id, 'args': []})

    view = BoardView()
    view.render()
    view.render_controls()
    assert len(view.squares) == 64
    action_panel = max((element for element in view.squares[chess.A1].client.elements.values()
                        if 'board-actions' in element._classes), key=lambda element: element.id)
    assert not any(element._props.get('aria-label') == 'Analysis' for element in action_panel.descendants())
    action_buttons = [element for element in action_panel.descendants()
                      if element._props.get('aria-label') in {'Undo move', 'Redo move', 'Previous move in history', 'Next move in history'}]
    assert [button._props['aria-label'] for button in action_buttons] == ['Undo move', 'Redo move', 'Previous move in history', 'Next move in history']
    assert not any(element._props.get('aria-label') == 'Record game log' for element in action_panel.descendants())
    assert view.status_label.text == 'White to move'
    assert not view.claim_button.visible
    assert not view.undo_button.enabled
    assert not view.redo_button.enabled
    click(view.squares[chess.E2])
    click(view.squares[chess.E4])
    assert view.undo_button.enabled
    click(view.undo_button)
    assert move_log_text(view) == 'No moves yet'
    assert view.redo_button.enabled
    click(view.redo_button)
    assert move_log_text(view).startswith('1. e4\n1... ')

    view.set_fen('7k/P7/8/8/8/8/8/K7 w - - 0 1')
    click(view.squares[chess.A7])
    click(view.squares[chess.A8])
    assert view.promotion_dialog.value
    assert view.position.board.piece_at(chess.A7) == chess.Piece.from_symbol('P')
    knight_button = next(element for element in view.promotion_dialog.descendants()
                         if element._props.get('label') == 'Knight')
    click(knight_button)
    assert not view.promotion_dialog.value
    assert view.position.board.piece_at(chess.A8) == chess.Piece.from_symbol('N')
    assert view.status_label.text == 'Draw — insufficient material'

    view.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 100 1')
    assert view.claim_button.visible
    click(view.claim_button)
    assert view.status_label.text == 'Draw — 50-move rule'
    assert not view.claim_button.visible
    click(view.squares[chess.G2])
    assert view.selected is None

    view.set_fen('7k/8/8/8/8/8/7R/K7 b - - 0 1')
    assert view.status_label.text == 'Black to move — check'
    view.set_fen('7k/6Q1/6K1/8/8/8/8/8 b - - 0 1')
    assert view.status_label.text == 'Checkmate — White wins'


def test_recording_can_start_enabled() -> None:
    view = BoardView(recording=True)
    view.render()
    assert view.recording
    assert not any(element._props.get('aria-label') == 'Record game log' for element in view.squares[chess.A1].client.elements.values())


def test_move_history_and_new_game() -> None:
    view = BoardView()
    view.render_controls()
    view.position.move(chess.E2, chess.E4)
    view.position.move(chess.C7, chess.C5)
    view.sync()
    assert move_log_text(view) == '1. e4\n1... c5'
    assert view.status_label.text == 'White to move'
    view.new_game()
    assert view.position.board.fen() == chess.STARTING_FEN
    assert move_log_text(view) == 'No moves yet'


def test_move_history_preserves_move_numbers_from_custom_position() -> None:
    position = Position()
    position.set_fen('7k/8/8/8/8/8/6R1/K7 b - - 0 12')
    position.move(chess.H8, chess.H7)
    assert move_history(position.board) == '12... Kh7'


def test_move_log_columns_and_current_tile() -> None:
    view = BoardView(white='human', black='human')
    view.render_controls()
    for san in ('c3', 'Na6', 'Nf3', 'Nb4'):
        view.position.board.push_san(san)
    view.sync()
    assert [label.text for label in view.history_labels] == ['1. c3', '1... Na6', '2. Nf3', '2... Nb4']
    assert [label._style['grid-column'] for label in view.history_labels] == ['1', '2', '1', '2']
    assert ['current-move' in label._classes for label in view.history_labels] == [False, False, False, True]
    view.set_fen('7k/8/8/8/8/8/6R1/K7 b - - 0 12')
    view.position.board.push_san('Kh7')
    view.sync()
    assert view.history_labels[0]._style['grid-column'] == '2'


def test_click_move_log_previews_board_and_analysis() -> None:
    from nicegui import ui

    view = BoardView(white='human', black='human')
    view.render()
    view.render_controls()
    for san in ('c3', 'Na6', 'Nf3', 'Nb4'):
        view.position.board.push_san(san)
    view.sync()
    live_fen = view.position.board.fen()
    with patch.object(view, 'render_move_analysis') as analysis:
        for index in (1, 3, 2, 4):
            button = view.history_labels[index - 1]
            listener = next(listener for listener in button._event_listeners.values() if listener.type == 'click')
            ui.context.client.handle_event({'id': button.id, 'listener_id': listener.id, 'args': []})
            expected = view.position.board.copy()
            while len(expected.move_stack) > index:
                expected.pop()
            assert (view.preview_board or view.position.board).fen() == expected.fen()
            assert view.analysis_position == expected.fen()
            assert analysis.call_args.args[0].fen() == expected.fen()
            assert 'current-move' in view.history_labels[index - 1]._classes
            assert view.position.board.fen() == live_fen
        assert view.preview_index is None


def test_undo_redo_updates_board_history_and_status() -> None:
    view = BoardView()
    view.render_controls()
    assert view.position.move(chess.E2, chess.E4)
    assert view.position.move(chess.E7, chess.E5)
    view.sync()
    view.undo()
    assert move_log_text(view) == 'No moves yet'
    assert view.status_label.text == 'White to move'
    assert view.position.board.piece_at(chess.E5) is None
    view.redo()
    assert move_log_text(view) == '1. e4\n1... e5'
    assert view.position.board.piece_at(chess.E5) == chess.Piece.from_symbol('p')
    view.undo()
    assert view.position.move(chess.E2, chess.E4)
    assert view.position.move(chess.C7, chess.C5)
    view.sync()
    view.redo()
    assert move_log_text(view) == '1. e4\n1... c5'
    view.new_game()
    assert not view.position.redo_stack
    assert move_log_text(view) == 'No moves yet'


def test_history_buttons_preview_without_changing_live_game() -> None:
    from nicegui import ui

    view = BoardView(white='human', black='human')
    view.render()
    view.render_controls()
    view.fen_label = MagicMock()
    for move in ('e2e4', 'e7e5', 'g1f3'):
        assert view.play_move(chess.Move.from_uci(move))
    assert 'current-move' in view.history_labels[-1]._classes
    assert {'last-move' in view.squares[square]._classes for square in (chess.G1, chess.F3)} == {True}
    live_fen = view.position.board.fen()
    live_moves = view.position.board.move_stack.copy()
    live_redo = view.position.redo_stack.copy()
    live_log = move_log_text(view)

    button = view.history_back_button
    listener = next(iter(button._event_listeners.values()))
    ui.context.client.handle_event({'id': button.id, 'listener_id': listener.id, 'args': []})
    assert view.preview_index == 2
    assert 'current-move' in view.history_labels[1]._classes
    assert 'current-move' not in view.history_labels[2]._classes
    assert {'last-move' in view.squares[square]._classes for square in (chess.E7, chess.E5)} == {True}
    assert 'last-move' not in view.squares[chess.G1]._classes
    view.fen_label.set_text.assert_called_with(view.preview_board.fen())
    assert view.shown_pieces[chess.G1] == chess.Piece.from_symbol('N')
    assert view.shown_pieces[chess.F3] is None
    assert view.status_label.text == 'Viewing move 2 / 3'
    assert not view.undo_button.enabled
    assert not view.redo_button.enabled
    assert view.history_forward_button.enabled
    assert not view.play_human_move(chess.Move.from_uci('g1f3'))
    view.click_square(chess.G1)
    view.undo()
    view.redo()
    assert view.selected is None

    view.step_history(-1)
    view.step_history(-1)
    assert view.preview_index == 0
    assert not any('current-move' in label._classes for label in view.history_labels)
    assert not any('last-move' in square._classes for square in view.squares.values())
    assert not view.history_back_button.enabled
    view.step_history(1)
    view.step_history(1)
    view.step_history(1)
    assert view.preview_board is None
    view.fen_label.set_text.assert_called_with(live_fen)
    assert view.shown_pieces[chess.F3] == chess.Piece.from_symbol('N')
    assert not view.history_forward_button.enabled
    assert view.position.board.fen() == live_fen
    assert view.position.board.move_stack == live_moves
    assert view.position.redo_stack == live_redo
    assert move_log_text(view) == live_log


def test_history_preview_pauses_computer_game_and_resets_on_new_game() -> None:
    view = BoardView(white='random', black='random')
    view.render()
    view.render_controls()
    assert view.play_move(chess.Move.from_uci('e2e4'))
    view.toggle_random()
    assert view.random_timer.active
    assert view.history_panel._props['data-scroll-resume'] == '1'
    view.step_history(-1)
    assert not view.random_timer.active
    with patch.object(view.controller, 'play_random_move') as play_random:
        view.random_step()
    play_random.assert_not_called()
    view.new_game()
    assert view.preview_board is None
    assert view.position.board.fen() == chess.STARTING_FEN
    assert not view.history_back_button.enabled


def test_computer_game_resumes_from_live_position_while_viewing_history() -> None:
    view = BoardView(white='random', black='random')
    view.render_controls()
    for san in ('e4', 'e5', 'Nf3'):
        view.position.board.push_san(san)
    live_fen = view.position.board.fen()
    view.select_history(1)
    assert view.random_button.enabled
    view.toggle_random()
    assert view.preview_board is None and view.preview_index is None
    assert view.position.board.fen() == live_fen
    assert view.random_timer.active
    assert view.history_panel._props['data-scroll-resume'] == '1'
    with patch.object(view.controller, 'play_random_move', return_value=False) as play_random:
        view.random_step()
    play_random.assert_called_once()


def test_undo_reopens_finished_game() -> None:
    position = Position()
    for source, target in [(chess.F2, chess.F3), (chess.E7, chess.E5),
                           (chess.G2, chess.G4), (chess.D8, chess.H4)]:
        assert position.move(source, target)
    assert position.status() == 'Checkmate — Black wins'
    assert position.undo()
    assert position.status() == 'Black to move'
    assert position.redo()
    assert position.status() == 'Checkmate — Black wins'


def test_player_combinations_and_random_opening() -> None:
    human = BoardView(white='human', black='human')
    with patch.object(human, 'sync'):
        assert human.play_human_move(chess.Move.from_uci('e2e4'))
        assert human.play_human_move(chess.Move.from_uci('e7e5'))
    assert len(human.position.board.move_stack) == 2

    mixed = BoardView(white='random', black='human')
    with patch.object(mixed, 'sync'), patch('src.game.controller.random.choice', side_effect=lambda moves: next(move for move in moves if move.uci() == ('e2e4' if any(move.uci() == 'e2e4' for move in moves) else 'g1f3'))):
        mixed.new_game()
        assert [move.uci() for move in mixed.position.board.move_stack] == ['e2e4']
        mixed.undo()  # keep the required random opening
        assert len(mixed.position.board.move_stack) == 1
        assert mixed.play_human_move(chess.Move.from_uci('e7e5'))
        assert [move.uci() for move in mixed.position.board.move_stack] == ['e2e4', 'e7e5', 'g1f3']
        mixed.undo()
        assert [move.uci() for move in mixed.position.board.move_stack] == ['e2e4']


def test_stockfish_plays_for_either_color_and_stops_at_game_end() -> None:
    engine = MagicMock()
    engine.play.return_value.move = chess.Move.from_uci('e7e5')
    with patch('src.game.controller.chess.engine.SimpleEngine.popen_uci', return_value=engine) as open_engine:
        view = BoardView(white='human', black='stockfish', black_elo=2100)
        with patch.object(view, 'sync'):
            assert view.play_human_move(chess.Move.from_uci('e2e4'))
        assert [move.uci() for move in view.position.board.move_stack] == ['e2e4', 'e7e5']
        assert open_engine.call_count == 1
        engine.configure.assert_called_once_with({'UCI_LimitStrength': True, 'UCI_Elo': 2100})
        view.set_fen('7k/6Q1/6K1/8/8/8/8/8 b - - 0 1')
        assert not view.controller.play_stockfish_move()
        assert open_engine.call_count == 1

        engine.play.return_value.move = chess.Move.from_uci('e2e4')
        opening = BoardView(white='stockfish', black='human')
        with patch.object(opening, 'sync'):
            opening.new_game()
        assert [move.uci() for move in opening.position.board.move_stack] == ['e2e4']
        opening.undo()
        assert len(opening.position.board.move_stack) == 1


def test_stockfish_and_random_can_play_each_other() -> None:
    view = BoardView(white='stockfish', black='random')
    view.render_controls()
    with patch.object(view.controller, 'play_stockfish_move', side_effect=lambda _elo: view.controller.play(chess.Move.from_uci('e2e4'))), patch.object(view.controller, 'play_random_move', side_effect=lambda: view.controller.play(chess.Move.from_uci('e7e5'))):
        view.toggle_random()
        view.random_step()
        view.random_step()
    assert [move.uci() for move in view.position.board.move_stack] == ['e2e4', 'e7e5']
    view.new_game()
    assert not view.random_timer.active


def test_evaluation_bar_tracks_position_and_reuses_unchanged_score() -> None:
    view = BoardView(white='human', black='human')
    with patch.object(view.controller, 'white_expectation', side_effect=[0.5, 0.8]) as evaluate:
        view.render_evaluation()
        assert view.eval_fill._style['height'] == '50.0%'
        view.sync()
        assert evaluate.call_count == 1
        view.play_move(chess.Move.from_uci('e2e4'))
        assert view.eval_fill._style['height'] == '80.0%'
        view.undo()
        assert view.eval_fill._style['height'] == '50.0%'
        assert evaluate.call_count == 2
    assert view.eval_bar._props['aria-valuenow'] == '50'


def test_position_snapshot_restores_moves_redo_and_claimed_draw() -> None:
    position = Position()
    assert position.move(chess.E2, chess.E4)
    assert position.move(chess.E7, chess.E5)
    assert position.undo()
    restored = Position()
    assert restored.restore(position.snapshot())
    assert restored.board.fen() == position.board.fen()
    assert [move.uci() for move in restored.redo_stack] == ['e7e5']
    assert restored.redo()
    assert restored.board.piece_at(chess.E5) == chess.Piece.from_symbol('p')
    claimed = Position()
    claimed.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 100 1')
    assert claimed.claim_draw()
    restored_claim = Position()
    assert restored_claim.restore(claimed.snapshot())
    assert restored_claim.status() == 'Draw — 50-move rule'
    assert not Position().restore({'root_fen': 'bad', 'moves': [], 'redo': []})


def test_stockfish_evaluation_handles_scores_and_finished_games() -> None:
    controller = GameController()
    engine = MagicMock()
    engine.analyse.return_value = {'score': chess.engine.PovScore(chess.engine.Cp(200), chess.WHITE)}
    with patch('src.game.controller.chess.engine.SimpleEngine.popen_uci', return_value=engine):
        assert controller.white_expectation() > 0.5
        engine.analyse.assert_called_once_with(controller.position.board, chess.engine.Limit(depth=18))
        controller.position.set_fen('7k/6Q1/6K1/8/8/8/8/8 b - - 0 1')
        assert controller.white_expectation() == 1.0
        controller.position.set_fen('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')
        assert controller.white_expectation() == 0.5
        controller.close()
    engine.quit.assert_called_once_with()


def test_stockfish_top_moves_uses_multipv_and_white_evaluations() -> None:
    controller = GameController()
    engine = MagicMock()
    engine.analyse.return_value = [
        {'pv': [chess.Move.from_uci('e2e4')], 'score': chess.engine.PovScore(chess.engine.Cp(20), chess.WHITE)},
        {'pv': [chess.Move.from_uci('d2d4')], 'score': chess.engine.PovScore(chess.engine.Cp(10), chess.WHITE)},
    ]
    with patch('src.game.controller.chess.engine.SimpleEngine.popen_uci', return_value=engine):
        assert controller.top_moves() == [('e4', '+20'), ('d4', '+10')]
    engine.analyse.assert_called_once_with(controller.position.board, chess.engine.Limit(depth=18), multipv=5)


@pytest.mark.parametrize('purpose', ['position', 'top_moves', 'loss'])
def test_stockfish_analysis_uses_full_strength_between_elo_limited_turns(purpose: str) -> None:
    controller = GameController()
    engine = MagicMock()
    controller.engine = engine
    settings = {}
    engine.configure.side_effect = settings.update
    def play(board, limit):
        assert settings['UCI_LimitStrength'] is True
        assert settings['UCI_Elo'] == 1800
        return chess.engine.PlayResult(board.parse_san('e4' if board.turn else 'e5'), None)

    engine.play.side_effect = play
    searches = []

    def analyse(board, limit, **kwargs):
        assert settings['UCI_LimitStrength'] is False
        assert settings['Skill Level'] == 20
        assert limit == chess.engine.Limit(depth=18)
        searches.append(kwargs)
        info = {'pv': [board.parse_san('d4' if board.turn else 'd5')],
                'score': chess.engine.PovScore(chess.engine.Cp(20), chess.WHITE)}
        return [info] if 'multipv' in kwargs else info

    engine.analyse.side_effect = analyse
    assert controller.play_stockfish_move(1800)
    if purpose == 'position':
        controller.white_expectation()
        assert searches == [{}]
    elif purpose == 'top_moves':
        controller.top_moves()
        assert searches == [{'multipv': 5}]
    else:
        _, _, loss = controller.move_analysis(controller.position.board)
        assert loss == 0
        assert searches == [{'multipv': 5}, {'root_moves': [chess.Move.from_uci('e2e4')]}]
    assert controller.play_stockfish_move(1800)


def test_move_analysis_compares_the_last_move_with_its_prior_options() -> None:
    view = BoardView()
    with patch.object(view.controller, 'move_analysis', return_value=([('e4', chess.engine.Cp(20))], chess.engine.Cp(20), 0.0)) as analysis:
        view.render_controls()
        assert not list(view.move_analysis_panel.descendants())
        assert view.controller.play(chess.Move.from_uci('e2e4'))
        view.render_move_analysis(view.position.board)
        assert analysis.call_args.args[0].fen() == view.position.board.fen()
    text = {element.text for element in view.move_analysis_panel.descendants() if hasattr(element, 'text')}
    assert {'Position before 1. e4', 'Played by white (Human)', 'Eval after move', 'Eval loss', '0.00 pawns', 'Best alternatives', 'e4', 'White +0.20'} <= text


@pytest.mark.parametrize('player', ['human', 'random', 'stockfish'])
def test_move_analysis_identifies_player_in_history(player: str) -> None:
    view = BoardView(white='human', black=player)
    with patch.object(view.controller, 'move_analysis', return_value=([('e5', chess.engine.Cp(10))], chess.engine.Cp(30), 0.2)):
        view.render_controls()
        for san in ('e4', 'e5', 'Nf3'):
            view.position.board.push_san(san)
        view.select_history(2)
    text = {element.text for element in view.move_analysis_panel.descendants() if hasattr(element, 'text')}
    assert {f'Played by black ({player.title()})', 'Position before 1... e5', 'White +0.30', '0.20 pawns'} <= text


@pytest.mark.parametrize('score, expected', [
    (chess.engine.Cp(-113), 'Black +1.13'),
    (chess.engine.Cp(-81), 'Black +0.81'),
    (chess.engine.Cp(45), 'White +0.45'),
    (chess.engine.Cp(9), 'Equal'),
    (chess.engine.Cp(-9), 'Equal'),
    (chess.engine.Cp(0), 'Equal'),
    (chess.engine.Cp(10), 'White +0.10'),
    (chess.engine.Mate(-3), 'Black #3'),
    (chess.engine.Mate(3), 'White #3'),
])
def test_move_analysis_displays_advantaged_side(score, expected) -> None:
    view = BoardView()
    view.position.board.push_san('e4')
    with patch.object(view.controller, 'move_analysis', return_value=([('e4', score)], score, 0.0)):
        view.render_controls()
    text = [element.text for element in view.move_analysis_panel.descendants() if hasattr(element, 'text')]
    assert text.count(expected) == 2
    assert not any('perspective' in label for label in text)


@pytest.mark.parametrize('black_to_move, best_cp, played_cp, loss', [(False, 70, 20, 0.5), (True, 20, 70, 0.5), (False, 20, 70, 0.0)])
def test_move_analysis_loss_and_played_move_outside_top_five(black_to_move, best_cp, played_cp, loss) -> None:
    controller = GameController()
    position = chess.Board()
    if black_to_move:
        position.push_san('e4')
    previous = position.copy()
    played = position.parse_san('a6' if black_to_move else 'a3')
    alternative = position.parse_san('e5' if black_to_move else 'e4')
    position.push(played)
    engine = MagicMock()
    engine.analyse.side_effect = [
        [{'pv': [alternative], 'score': chess.engine.PovScore(chess.engine.Cp(best_cp), chess.WHITE)}],
        {'score': chess.engine.PovScore(chess.engine.Cp(played_cp), chess.WHITE)},
    ]
    with patch.object(controller, 'stockfish_engine', return_value=engine):
        options, score, actual_loss = controller.move_analysis(position)
    assert actual_loss == loss
    assert score == chess.engine.Cp(played_cp)
    assert options == [(previous.san(alternative), chess.engine.Cp(best_cp))]
    assert engine.analyse.call_args.kwargs == {'root_moves': [played]}
    assert engine.analyse.call_args.args[0].fen() == previous.fen()


def test_move_analysis_reuses_played_option_and_preserves_mate_score() -> None:
    controller = GameController()
    position = chess.Board()
    position.push_san('e4')
    engine = MagicMock()
    engine.analyse.return_value = [{'pv': [position.peek()], 'score': chess.engine.PovScore(chess.engine.Mate(3), chess.WHITE)}]
    with patch.object(controller, 'stockfish_engine', return_value=engine):
        _, score, loss = controller.move_analysis(position)
    assert score == chess.engine.Mate(3)
    assert loss is None
    assert engine.analyse.call_count == 1


def test_completed_game_logs_use_temporary_or_recording_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    position = Position()
    for move in ('f2f3', 'e7e5', 'g2g4', 'd8h4'):
        assert position.move(chess.parse_square(move[:2]), chess.parse_square(move[2:4]))
    monkeypatch.setattr('src.game.log.Path', lambda _: tmp_path / 'repo' / 'src' / 'game' / 'log.py')
    args = (position.board, {chess.WHITE: 'human', chess.BLACK: 'stockfish'},
            {chess.WHITE: 1500, chess.BLACK: 2100}, lambda board: len(board.move_stack) / 10)
    path = write_game_log(*args)
    recorded_path = write_game_log(*args, recording=True)
    log = json.loads(path.read_text())
    assert path == tmp_path / 'repo' / 'gamelog' / 'latest.json'
    assert recorded_path.parent == tmp_path / 'repo' / 'gamelog' / 'rec'
    assert recorded_path.name.startswith(f'{date.today().isoformat()}_001')
    assert json.loads((tmp_path / 'repo' / 'gamelog' / 'latest.json').read_text()) == json.loads(recorded_path.read_text())
    assert log['players']['black'] == {'type': 'stockfish', 'elo': 2100, 'model': None}
    assert log['result'] == {'winner': 'black', 'score': '0-1', 'termination': 'checkmate'}
    assert log['evaluator'] == {'engine': 'stockfish', 'depth': 18}
    first = chess.Board()
    legal_moves = [first.san(move) for move in first.legal_moves]
    first.push_uci('f2f3')
    assert log['moves'][0] == {
        'ply': 1, 'move_number': 1, 'color': 'white', 'fen_before': chess.STARTING_FEN,
        'legal_moves': legal_moves, 'move': 'f3', 'fen_after': first.fen(),
        'evaluation': {'wdl_expectation_white': 0.1},
    }
    assert log['moves'][-1]['evaluation'] == {'wdl_expectation_white': 0.4}


def test_terminal_position_writes_one_game_log() -> None:
    view = BoardView()
    for move in ('f2f3', 'e7e5', 'g2g4', 'd8h4'):
        assert view.play_move(chess.Move.from_uci(move))
    board_view.write_game_log.assert_called_once_with(view.position.board, view.players, view.stockfish_elos,
                                                      view.controller.white_expectation, False)


def test_incomplete_game_does_not_write_a_log() -> None:
    view = BoardView()
    assert view.play_move(chess.Move.from_uci('e2e4'))
    board_view.write_game_log.assert_not_called()


def test_random_vs_random_starts_pauses_and_resets() -> None:
    from nicegui import ui

    view = BoardView(white='random', black='random')
    header_actions = ui.element('div')
    view.render_controls(header_actions)
    assert view.random_button in header_actions.descendants()
    assert not view.random_timer.active
    view.toggle_random()
    assert view.random_timer.active
    view.random_step()
    assert len(view.position.board.move_stack) == 1
    view.toggle_random()
    assert not view.random_timer.active
    assert view.history_panel._props['data-scroll-resume'] == '1'
    view.new_game()
    assert not view.random_timer.active
    assert view.position.board.fen() == chess.STARTING_FEN


def test_landing_starts_game_and_returns_to_setup() -> None:
    from nicegui import ui

    storage = {}
    build_page(storage)
    client = ui.context.client

    def click(element) -> None:
        listener = next(iter(element._event_listeners.values()))
        with patch.object(board.app, 'handle_exception') as errors:
            client.handle_event({'id': element.id, 'listener_id': listener.id, 'args': []})
        errors.assert_not_called()

    selects = [element for element in client.elements.values() if type(element).__name__ == 'Select'][-4:]
    assert [select._props['label'] for select in selects] == ['White', 'ELO', 'Black', 'ELO']
    assert not selects[1].visible and not selects[3].visible
    selects[2].value = 'stockfish'
    next(listener.handler for listener in selects[2]._event_listeners.values() if listener.type == 'update:modelValue' and listener.args is None)()
    assert selects[3].visible
    selects[0].value = 'human'
    selects[2].value = 'human'
    start = max((element for element in client.elements.values() if element._props.get('label') == 'START GAME'), key=lambda element: element.id)
    click(start)
    assert storage['game']['position']['moves'] == []
    assert any(element.text == 'WHITE / HUMAN  ·  BLACK / HUMAN' for element in client.elements.values() if hasattr(element, 'text'))
    status_strip = max((element for element in client.elements.values() if 'status-strip' in element._classes), key=lambda element: element.id)
    board_panel = max((element for element in client.elements.values() if 'board-panel' in element._classes), key=lambda element: element.id)
    controls = max((element for element in client.elements.values() if 'game-controls' in element._classes), key=lambda element: element.id)
    main_menu_action = max((element for element in client.elements.values() if 'main-menu-action' in element._classes), key=lambda element: element.id)
    footer = max((element for element in client.elements.values() if 'footer-note' in element._classes), key=lambda element: element.id)
    assert footer.visible
    assert {element.text for element in status_strip.descendants() if hasattr(element, 'text')} == {'SYSTEM STATUS', 'White to move'}
    assert status_strip in board_panel.descendants()
    assert not any(element.text == 'SYSTEM STATUS' for element in controls.descendants() if hasattr(element, 'text'))
    assert [element._props.get('label') for element in main_menu_action.descendants()] == ['MAIN MENU', 'NEW GAME', 'START']
    reserved_start = main_menu_action.default_slot.children[-1]
    assert reserved_start._style['visibility'] == 'hidden'
    assert not reserved_start.enabled
    assert not any(element._props.get('label') in {'NEW GAME', 'MAIN MENU'} for element in controls.descendants())
    back = max((element for element in client.elements.values() if element._props.get('label') == 'MAIN MENU'), key=lambda element: element.id)
    click(back)
    assert 'game' not in storage
    assert max((element for element in client.elements.values() if element._props.get('label') == 'START GAME'), key=lambda element: element.id).id != start.id
    assert not footer.visible


def test_live_plot_tracks_every_move_history_branches_and_reset() -> None:
    from nicegui import ui
    view = BoardView(white='human', black='human')
    view.evaluation_plot = ui.html('')
    with patch.object(view.controller, 'move_analysis', return_value=([('best', chess.engine.Cp(0))], chess.engine.Cp(0), 0)), patch.object(view.controller, 'white_expectation', side_effect=lambda board: 0.5 + len(board.move_stack) * 0.1) as evaluate:
        view.sync()
        assert '0</text>' in view.evaluation_plot.content
        view.play_move(chess.Move.from_uci('e2e4'))
        view.play_move(chess.Move.from_uci('e7e5'))
        assert evaluate.call_count == 3
        assert view.evaluation_plot.content == evaluation_chart_svg([0, 20, 40], compact=True, recommended=[0, 0, 0])
        view.sync()
        assert evaluate.call_count == 3
        view.select_history(1)
        assert view.evaluation_plot.content == evaluation_chart_svg([0, 20], compact=True, recommended=[0, 0])
        view.select_history(2)
        view.undo()
        view.redo()
        assert evaluate.call_count == 3
        view.undo()
        view.play_move(chess.Move.from_uci('c7c5'))
        assert evaluate.call_count == 4
        view.new_game()
        assert evaluate.call_count == 5
        assert view.evaluation_plot.content == evaluation_chart_svg([0], compact=True, recommended=[0])
        view.controller.close()


def test_live_plot_fills_moves_skipped_by_automatic_reply() -> None:
    from nicegui import ui
    view = BoardView()
    view.evaluation_plot = ui.html('')
    with patch.object(view.controller, 'move_analysis', return_value=([('best', chess.engine.Cp(0))], chess.engine.Cp(0), 0)), patch.object(view.controller, 'white_expectation', return_value=0.5) as evaluate:
        view.sync()
        assert view.play_human_move(chess.Move.from_uci('e2e4'))
        assert len(view.position.board.move_stack) == 2
        assert evaluate.call_count == 3
        assert view.evaluation_plot.content == evaluation_chart_svg([0, 0, 0], compact=True, recommended=[0, 0, 0])
        view.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 100 1')
        view.claim_draw()
        assert view.position.claimed_draw


def test_automatic_turn_shows_board_before_analysis_and_waits_for_panel(monkeypatch) -> None:
    import asyncio
    from unittest.mock import AsyncMock

    container = board_view.ui.element("div")

    async def check():
        view = BoardView(white='random', black='random')
        monkeypatch.setattr(view.controller, 'white_expectation', lambda board=None: 0.5)
        monkeypatch.setattr(view.controller, 'move_analysis', lambda board: ([('e4', chess.engine.Cp(0))], chess.engine.Cp(0), 0))
        with container:
            view.render()
            view.render_controls()
        view.toggle_random()
        started, finish = asyncio.Event(), asyncio.Event()
        paints = []

        async def paint(*args, **kwargs):
            paints.append((len(view.position.board.move_stack), view.analysis_position))

        async def io_bound(callback, *args):
            started.set()
            await finish.wait()
            return await asyncio.to_thread(callback, *args)

        monkeypatch.setattr(board_view.run, 'io_bound', io_bound)
        monkeypatch.setattr(board_view.ui, 'run_javascript', AsyncMock(side_effect=paint))
        async def turn_in_context():
            with container:
                await view.automatic_turn()

        turn = asyncio.create_task(turn_in_context())
        await started.wait()
        assert len(view.position.board.move_stack) == 1
        assert view.shown_pieces == {square: view.position.board.piece_at(square) for square in view.squares}
        assert view.analysis_position == chess.STARTING_FEN
        assert 'analyzing' in view.analysis_engine_label._classes
        assert view.analysis_engine_label._props['aria-busy'] == 'true'
        assert '1.' in move_log_text(view)
        await turn_in_context()  # a second tick cannot advance while analysis is pending
        assert len(view.position.board.move_stack) == 1
        finish.set()
        await turn
        assert view.analysis_position == view.position.board.fen()
        assert paints == [(1, chess.STARTING_FEN), (1, view.position.board.fen())]
        assert not view.analysis_busy
        assert 'analyzing' not in view.analysis_engine_label._classes
        assert view.analysis_engine_label._props['aria-busy'] == 'false'
        await turn_in_context()
        assert len(view.position.board.move_stack) == 2
        assert view.analysis_position == view.position.board.fen()
        view.pause_random()

    asyncio.run(check())


@pytest.mark.parametrize('action', ['pause', 'reset', 'history', 'close', 'error', 'cancel'])
def test_automatic_turn_handles_changes_while_analysis_is_pending(monkeypatch, action) -> None:
    import asyncio
    from unittest.mock import AsyncMock

    container = board_view.ui.element("div")

    async def check():
        view = BoardView(white='random', black='random')
        monkeypatch.setattr(view.controller, 'white_expectation', lambda board=None: 0.5)
        monkeypatch.setattr(view.controller, 'move_analysis', lambda board: ([('e4', chess.engine.Cp(0))], chess.engine.Cp(0), 0))
        monkeypatch.setattr(view.controller, 'close', lambda: None)
        with container:
            view.render()
            view.render_controls()
        view.toggle_random()
        started, finish = asyncio.Event(), asyncio.Event()

        async def io_bound(callback, *args):
            started.set()
            await finish.wait()
            if action == 'error':
                raise RuntimeError('Engine failed')
            if action == 'cancel':
                return None
            return await asyncio.to_thread(callback, *args)

        monkeypatch.setattr(board_view.run, 'io_bound', io_bound)
        monkeypatch.setattr(board_view.ui, 'run_javascript', AsyncMock())
        async def turn_in_context():
            with container:
                await view.automatic_turn()

        turn = asyncio.create_task(turn_in_context())
        await started.wait()
        if action == 'pause':
            view.pause_random()
        elif action == 'reset':
            with container:
                view.new_game()
        elif action == 'history':
            with container:
                view.select_history(0)
        elif action == 'close':
            view.close()
        finish.set()
        if action == 'error':
            with pytest.raises(RuntimeError, match='Engine failed'):
                await turn
        else:
            await turn
        assert not view.analysis_busy
        assert not view.random_timer.active
        assert 'analyzing' not in view.analysis_engine_label._classes
        if action in {'reset', 'history'}:
            assert view.analysis_position == chess.STARTING_FEN
            assert not list(view.move_analysis_panel.descendants())
        if action == 'pause':
            assert len(view.position.board.move_stack) == 1
            assert view.analysis_position == view.position.board.fen()

    asyncio.run(check())


@pytest.mark.parametrize('fen,moves,expected', [
    (chess.STARTING_FEN, ['e2e4', 'e7e5'], {chess.E4: chess.E2, chess.E5: chess.E7}),
    ('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1', ['e1g1'], {chess.G1: chess.E1, chess.F1: chess.H1}),
    ('7k/8/8/3pP3/8/8/8/K7 w - d6 0 1', ['e5d6'], {chess.D6: chess.E5}),
    ('7k/P7/8/8/8/8/8/K7 w - - 0 1', ['a7a8q'], {chess.A8: chess.A7}),
    ('7k/8/8/8/8/2p5/1P6/K7 w - - 0 1', ['b2c3'], {chess.C3: chess.B2}),
])
def test_piece_animation_tracks_actual_moves(fen, moves, expected) -> None:
    view = BoardView(white='human', black='human')
    view.set_fen(fen)
    view.render()
    for move in moves:
        view.position.board.push_uci(move)
    assert view.movement_origins(view.position.board) == expected
    view.sync()
    for target, source in expected.items():
        image = list(view.squares[target])[0]
        assert 'chess-piece-moving' in image._classes
        assert '--piece-x' in image._style
    assert view.movement_origins(view.position.board) == {}
    view.position.board.pop()
    assert view.movement_origins(view.position.board) == {}


def test_piece_animation_offsets_follow_board_orientation() -> None:
    for flipped in (False, True):
        view = BoardView(white='human', black='human')
        view.black_at_bottom = flipped
        view.render()
        view.play_move(chess.Move.from_uci('e2e4'))
        image = list(view.squares[chess.E4])[0]
        assert float(image._style['--piece-y'].rstrip('%')) == pytest.approx((-1 if flipped else 1) * 200 / .9)
        view.set_fen(chess.STARTING_FEN)
        assert all('chess-piece-moving' not in image._classes
                   for square in view.squares.values() for image in square)


@pytest.mark.parametrize('fail', [False, True])
def test_human_analysis_indicator_lasts_until_calculation_finishes(monkeypatch, fail) -> None:
    import asyncio
    from unittest.mock import AsyncMock, PropertyMock

    container = board_view.ui.element('div')

    async def check():
        view = BoardView(white='human', black='human')
        monkeypatch.setattr(view.controller, 'white_expectation', lambda board=None: 0.5)
        monkeypatch.setattr(view.controller, 'move_analysis', lambda board: ([], chess.engine.Cp(0), 0))
        with container:
            view.render()
            view.render_controls()
        started, finish = asyncio.Event(), asyncio.Event()

        async def io_bound(callback, *args):
            started.set()
            await finish.wait()
            if fail:
                raise RuntimeError('Engine failed')
            return callback(*args)

        monkeypatch.setattr(board_view.run, 'io_bound', io_bound)
        monkeypatch.setattr(board_view.ui, 'run_javascript', AsyncMock())
        with patch.object(type(view.analysis_engine_label.client), 'has_socket_connection', new_callable=PropertyMock, return_value=True), patch.object(board_view.ui, 'timer') as timer:
            with container:
                assert view.play_human_move(chess.Move.from_uci('e2e4'))
                view.sync()  # repeated updates must not start another calculation
            timer.assert_called_once_with(0, view.analyse_position, once=True)
        assert view.analysis_busy
        assert 'analyzing' in view.analysis_engine_label._classes

        async def calculate():
            with container:
                await view.analyse_position()

        task = asyncio.create_task(calculate())
        await started.wait()
        assert 'analyzing' in view.analysis_engine_label._classes
        assert view.analysis_engine_label._props['aria-busy'] == 'true'
        assert len(view.position.board.move_stack) == 1
        finish.set()
        if fail:
            with pytest.raises(RuntimeError, match='Engine failed'):
                await task
        else:
            await task
            assert view.analysis_position == view.position.board.fen()
        assert not view.analysis_busy
        assert 'analyzing' not in view.analysis_engine_label._classes
        assert view.analysis_engine_label._props['aria-busy'] == 'false'

    asyncio.run(check())


@pytest.mark.parametrize('white', ['human', 'random', 'stockfish'])
@pytest.mark.parametrize('black', ['human', 'random', 'stockfish'])
def test_all_player_combinations_apply_each_move_before_async_analysis(monkeypatch, white, black) -> None:
    import asyncio
    from unittest.mock import AsyncMock, PropertyMock

    container = board_view.ui.element('div')

    async def check():
        view = BoardView(white=white, black=black, white_elo=1800, black_elo=2100)
        monkeypatch.setattr(view.controller, 'white_expectation', lambda board=None: 0.5)
        monkeypatch.setattr(view.controller, 'move_analysis', lambda board: ([], chess.engine.Cp(0), 0))
        def move():
            return view.controller.play(chess.Move.from_uci('e2e4' if view.position.board.turn else 'e7e5'))
        monkeypatch.setattr(view.controller, 'play_random_move', move)
        stockfish_elos = []
        def stockfish(elo):
            stockfish_elos.append(elo)
            return move()
        monkeypatch.setattr(view.controller, 'play_stockfish_move', stockfish)
        with container:
            view.render()
            view.render_evaluation()
            view.render_controls()
        started, finish = asyncio.Event(), asyncio.Event()
        paints = []
        async def paint(*args, **kwargs):
            paints.append(len(view.position.board.move_stack))
        async def io_bound(callback, *args):
            assert len(view.position.board.move_stack) in paints
            started.set()
            await finish.wait()
            return callback(*args)
        monkeypatch.setattr(board_view.run, 'io_bound', io_bound)
        monkeypatch.setattr(board_view.ui, 'run_javascript', AsyncMock(side_effect=paint))
        with patch.object(type(view.analysis_engine_label.client), 'has_socket_connection', new_callable=PropertyMock, return_value=True), patch.object(board_view.ui, 'timer') as timer:
            for count, player, uci in [(1, white, 'e2e4'), (2, black, 'e7e5')]:
                started.clear()
                finish.clear()
                previous_analysis = view.analysis_position
                async def turn():
                    with container:
                        if player == 'human':
                            assert view.play_human_move(chess.Move.from_uci(uci))
                            callback = timer.call_args.args[1]
                            assert callback == view.analyse_position
                            await callback()
                        else:
                            await view.automatic_turn()
                task = asyncio.create_task(turn())
                await started.wait()
                assert len(view.position.board.move_stack) == count
                assert view.shown_pieces == {square: view.position.board.piece_at(square) for square in view.squares}
                assert view.analysis_position == previous_analysis
                assert 'analyzing' in view.analysis_engine_label._classes
                assert view.analysis_engine_label._props['aria-busy'] == 'true'
                with container:
                    await view.automatic_turn()  # no overlapping move or engine command
                assert len(view.position.board.move_stack) == count
                finish.set()
                await task
                assert view.analysis_position == view.position.board.fen()
                assert not view.analysis_busy
                assert 'analyzing' not in view.analysis_engine_label._classes
                if count == 1 and white == 'human' and black != 'human':
                    assert timer.call_args.args[1] == view.automatic_turn
            assert stockfish_elos == ([1800] if white == 'stockfish' else []) + ([2100] if black == 'stockfish' else [])

    asyncio.run(check())


def test_initial_analysis_does_not_block_building_the_game(monkeypatch) -> None:
    storage = {'game': {'white': 'stockfish', 'black': 'human', 'position': Position().snapshot()}}
    monkeypatch.setattr(board.shutil, 'which', lambda name: '/usr/bin/stockfish')
    with patch.object(GameController, 'white_expectation') as evaluation, patch.object(GameController, 'move_analysis') as analysis, patch.object(GameController, 'play_stockfish_move') as opening, patch.object(board.ui, 'timer') as timer:
        build_page(storage)
    evaluation.assert_not_called()
    analysis.assert_not_called()
    opening.assert_not_called()
    callback = timer.call_args.args[1]
    assert callback.__name__ == 'analyse_position'
    assert callback.__self__.analysis_busy
    assert 'analyzing' in callback.__self__.analysis_engine_label._classes


@pytest.mark.parametrize('action', ['history', 'undo', 'redo', 'reset', 'replace', 'draw'])
def test_uncached_live_position_changes_queue_analysis(monkeypatch, action) -> None:
    from unittest.mock import PropertyMock

    view = BoardView(white='human', black='human')
    monkeypatch.setattr(view.controller, 'white_expectation', lambda board=None: 0.5)
    monkeypatch.setattr(view.controller, 'move_analysis', lambda board: ([], chess.engine.Cp(0), 0))
    view.position.board.push_uci('e2e4')
    view.position.board.push_uci('e7e5')
    if action == 'redo':
        view.position.undo()
    elif action == 'reset':
        view.position.set_board(chess.Board())  # same FEN; reset still clears the evaluation cache
    elif action == 'draw':
        view.position.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 100 1')
    view.render()
    view.render_evaluation()
    view.render_controls()
    view.move_analysis_cache.clear()
    with patch.object(type(view.analysis_engine_label.client), 'has_socket_connection', new_callable=PropertyMock, return_value=True), patch.object(board_view.ui, 'timer') as timer, patch.object(view, 'sync_analysis') as synchronous:
        if action == 'history':
            view.select_history(1)
        elif action == 'undo':
            view.undo()
        elif action == 'redo':
            view.redo()
        elif action == 'reset':
            view.new_game()
        elif action == 'replace':
            view.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 0 1')
        else:
            view.claim_draw()
            assert view.position.claimed_draw
        timer.assert_called_once_with(0, view.analyse_position, once=True)
        synchronous.assert_not_called()
    assert view.analysis_busy
    assert 'analyzing' in view.analysis_engine_label._classes


@pytest.mark.parametrize('white', ['human', 'random', 'stockfish'])
@pytest.mark.parametrize('black', ['human', 'random', 'stockfish'])
def test_start_game_event_keeps_analysis_timer_in_live_slot(monkeypatch, white, black) -> None:
    from nicegui import ui

    monkeypatch.setattr(board.shutil, 'which', lambda name: '/usr/bin/stockfish')
    client = ui.context.client
    with ui.element('div'):
        build_page({})
    selects = [element for element in client.elements.values() if type(element).__name__ == 'Select'][-4:]
    selects[0].value, selects[2].value = white, black
    start = max((element for element in client.elements.values() if element._props.get('label') == 'START GAME'), key=lambda element: element.id)
    listener = next(iter(start._event_listeners.values()))
    with patch.object(board.app, 'handle_exception') as errors:
        client.handle_event({'id': start.id, 'listener_id': listener.id, 'args': []})
    errors.assert_not_called()  # NiceGUI catches event errors instead of raising them to pytest
    assert start.is_deleted
    timer = max((element for element in client.elements.values()
                 if type(element).__name__ == 'Timer' and getattr(element.callback, '__name__', '') == 'analyse_position'), key=lambda element: element.id)
    assert not timer.is_deleted
    assert not timer.parent_slot.parent.is_deleted
    assert timer.parent_slot.parent is timer.callback.__self__.analysis_engine_label.parent_slot.parent


def test_move_log_redraw_does_not_delete_pending_analysis_timer(monkeypatch) -> None:
    from nicegui import ui
    from unittest.mock import PropertyMock

    view = BoardView(white='human', black='human')
    monkeypatch.setattr(view.controller, 'white_expectation', lambda board=None: 0.5)
    monkeypatch.setattr(view.controller, 'move_analysis', lambda board: ([], chess.engine.Cp(0), 0))
    view.position.board.push_uci('e2e4')
    view.position.board.push_uci('e7e5')
    view.render()
    view.render_evaluation()
    view.render_controls()
    view.move_analysis_cache.clear()
    entry = view.history_labels[0]
    listener = next(iter(entry._event_listeners.values()))
    with patch.object(type(entry.client), 'has_socket_connection', new_callable=PropertyMock, return_value=True), patch.object(board.app, 'handle_exception') as errors:
        entry.client.handle_event({'id': entry.id, 'listener_id': listener.id, 'args': []})
    errors.assert_not_called()
    assert entry.is_deleted
    timer = next(element for element in ui.context.client.elements.values()
                 if type(element).__name__ == 'Timer' and element.callback == view.analyse_position)
    assert not timer.is_deleted
    assert timer.parent_slot.parent is view.analysis_engine_label.parent_slot.parent
    assert view.preview_index == 1
    assert view.analysis_busy


@pytest.mark.parametrize('white', ['human', 'random', 'stockfish'])
@pytest.mark.parametrize('black', ['human', 'random', 'stockfish'])
def test_history_reuses_analysis_without_loading_or_engine_calls(monkeypatch, white, black) -> None:
    import asyncio
    from unittest.mock import AsyncMock, PropertyMock

    container = board_view.ui.element('div')
    view = BoardView(white=white, black=black)
    evaluation = MagicMock(return_value=0.5)
    analysis = MagicMock(return_value=([('e4', chess.engine.Cp(20))], chess.engine.Cp(20), 0))
    monkeypatch.setattr(view.controller, 'white_expectation', evaluation)
    monkeypatch.setattr(view.controller, 'move_analysis', analysis)
    monkeypatch.setattr(board_view.ui, 'run_javascript', AsyncMock())

    async def worker(callback, *args):
        return callback(*args)

    monkeypatch.setattr(board_view.run, 'io_bound', worker)

    async def play():
        with container:
            view.render()
            view.render_evaluation()
            view.render_controls()
            for move in ['e2e4', 'e7e5']:
                view.position.board.push_uci(move)
                await view.analyse_position()

    asyncio.run(play())
    evaluation.reset_mock()
    analysis.reset_mock()
    with container, patch.object(type(view.analysis_engine_label.client), 'has_socket_connection', new_callable=PropertyMock, return_value=True), patch.object(board_view.ui, 'timer') as timer:
        for target in [1, 0, 2, 1, 2]:
            view.select_history(target)
            assert not view.analysis_busy
            assert 'analyzing' not in view.analysis_engine_label._classes
            assert view.analysis_position == (view.preview_board or view.position.board).fen()
        timer.assert_not_called()
    evaluation.assert_not_called()
    analysis.assert_not_called()
    view.controller.close()


def test_move_analysis_cache_distinguishes_history_and_clears_on_replacement() -> None:
    view = BoardView(white='human', black='human')
    first = chess.Board()
    second = chess.Board()
    for move in ['g1f3', 'g8f6', 'b1c3', 'b8c6']:
        first.push_uci(move)
    for move in ['b1c3', 'b8c6', 'g1f3', 'g8f6']:
        second.push_uci(move)
    assert first.fen() == second.fen()
    with patch.object(view.controller, 'move_analysis', return_value=([], chess.engine.Cp(0), 0)) as analysis:
        view.cached_move_analysis(first)
        view.cached_move_analysis(second)
        view.cached_move_analysis(first)
        assert analysis.call_count == 2
        view.set_board(first)
        assert not view.move_analysis_cache
        view.cached_move_analysis(first)
        view.set_fen(chess.STARTING_FEN)
        assert not view.move_analysis_cache


def test_live_plot_uses_best_alternative_in_white_perspective() -> None:
    from nicegui import ui
    view = BoardView(white='human', black='human')
    view.evaluation_plot = ui.html('')
    view.position.board.push_uci('e2e4')
    view.position.board.push_uci('e7e5')
    view.fullscreen_evaluation_plot = ui.html('')
    scores = [chess.engine.Cp(100), chess.engine.Cp(-100)]
    with patch.object(view.controller, 'white_expectation', return_value=0.5), patch.object(
        view.controller, 'move_analysis', side_effect=[([('best', score)], chess.engine.Cp(0), 0) for score in scores]
    ) as analyse:
        view.sync_evaluation_plot(view.position.board)
        expected = [0, *(200 * score.wdl().expectation() - 100 for score in scores)]
        assert view.evaluation_plot.content == evaluation_chart_svg([0, 0, 0], compact=True, recommended=expected)
        view.sync_evaluation_plot(view.position.board)
        assert analyse.call_count == 2
        assert 'chart-recommended' in view.evaluation_plot.content
        assert view.fullscreen_evaluation_plot.content == view.evaluation_plot.content
