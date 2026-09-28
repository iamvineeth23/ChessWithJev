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
    analysis_button = next(element for element in action_panel.descendants() if element._props.get('aria-label') == 'Analysis')
    assert 'analysis-button' in analysis_button._classes
    action_buttons = [element for element in action_panel.descendants()
                      if element._props.get('aria-label') in {'Undo move', 'Redo move', 'Previous move in history', 'Next move in history'}]
    assert [button._props['aria-label'] for button in action_buttons] == ['Undo move', 'Redo move', 'Previous move in history', 'Next move in history']
    record_button = next(element for element in action_panel.descendants() if element._props.get('aria-label') == 'Record game log')
    assert record_button._props['label'] == 'REC'
    click(record_button)
    assert view.recording
    assert 'recording' in record_button._classes
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
    assert view.record_button._props['aria-pressed'] == 'true'
    assert 'recording' in view.record_button._classes


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
    view.step_history(-1)
    assert not view.random_timer.active
    with patch.object(view.controller, 'play_random_move') as play_random:
        view.random_step()
    play_random.assert_not_called()
    view.new_game()
    assert view.preview_board is None
    assert view.position.board.fen() == chess.STARTING_FEN
    assert not view.history_back_button.enabled


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
    with patch.object(view.controller, 'white_expectation', side_effect=[0.5, 0.8, 0.2]) as evaluate:
        view.render_evaluation()
        assert view.eval_fill._style['height'] == '50.0%'
        view.sync()
        assert evaluate.call_count == 1
        view.play_move(chess.Move.from_uci('e2e4'))
        assert view.eval_fill._style['height'] == '80.0%'
        view.undo()
        assert view.eval_fill._style['height'] == '20.0%'
    assert view.eval_bar._props['aria-valuenow'] == '20'


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
        engine.analyse.assert_called_once_with(controller.position.board, chess.engine.Limit(time=0.1))
        controller.position.set_fen('7k/6Q1/6K1/8/8/8/8/8 b - - 0 1')
        assert controller.white_expectation() == 1.0
        controller.position.set_fen('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')
        assert controller.white_expectation() == 0.5
        controller.close()
    engine.quit.assert_called_once_with()


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
    assert log['evaluator'] == {'engine': 'stockfish', 'time_limit_seconds': 0.1}
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
    view = BoardView(white='random', black='random')
    view.render_controls()
    assert not view.random_timer.active
    view.toggle_random()
    assert view.random_timer.active
    view.random_step()
    assert len(view.position.board.move_stack) == 1
    view.toggle_random()
    assert not view.random_timer.active
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
        client.handle_event({'id': element.id, 'listener_id': listener.id, 'args': []})

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
    header_actions = max((element for element in client.elements.values() if 'header-actions' in element._classes), key=lambda element: element.id)
    footer = max((element for element in client.elements.values() if 'footer-note' in element._classes), key=lambda element: element.id)
    assert footer.visible
    assert {element.text for element in status_strip.descendants() if hasattr(element, 'text')} == {'SYSTEM STATUS', 'White to move'}
    assert status_strip in board_panel.descendants()
    assert not any(element.text == 'SYSTEM STATUS' for element in controls.descendants() if hasattr(element, 'text'))
    assert [element._props.get('label') for element in header_actions.descendants()] == ['MAIN MENU', 'NEW GAME']
    assert not any(element._props.get('label') in {'NEW GAME', 'MAIN MENU'} for element in controls.descendants())
    back = max((element for element in client.elements.values() if element._props.get('label') == 'MAIN MENU'), key=lambda element: element.id)
    click(back)
    assert 'game' not in storage
    assert max((element for element in client.elements.values() if element._props.get('label') == 'START GAME'), key=lambda element: element.id).id != start.id
    assert not footer.visible
