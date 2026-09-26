import runpy
from base64 import b64decode
import chess
import pytest
from src.game.position import Position
from src.ui.board import BoardView, lock_window_aspect_ratio, move_history, piece_image, square_color, square_name
from src.ui import board
from unittest.mock import MagicMock, patch


def test_board_colors() -> None:
    colors = [[square_color(row, column) for column in range(8)] for row in range(8)]
    assert all(colors[row][column] != colors[row][column + 1] for row in range(8) for column in range(7))
    assert all(colors[row][column] != colors[row + 1][column] for row in range(7) for column in range(8))
    assert colors[0][0] == colors[7][7] == 'light'
    assert colors[7][0] == 'dark'  # a1


@pytest.mark.parametrize('debug', [False, True])
def test_board_opens_native_window(debug: bool) -> None:
    with patch.object(board.sys, 'argv', ['chess', '-d'] if debug else ['chess']), patch.object(board.ui, 'add_body_html') as add_body_html, patch.object(board.ui, 'add_css'), patch.object(board.ui, 'element', return_value=MagicMock()), patch.object(board.ui, 'label') as label, patch.object(board.ui, 'image') as image, patch.object(board.ui, 'dialog', return_value=MagicMock()), patch.object(board.ui, 'card', return_value=MagicMock()), patch.object(board.ui, 'row', return_value=MagicMock()), patch.object(board.ui, 'button', return_value=MagicMock()), patch.object(board.ui, 'run') as run:
        runpy.run_path(board.__file__, run_name='__mp_main__')
    assert add_body_html.called == debug
    if debug:
        assert 'window.innerWidth' in add_body_html.call_args.args[0]
        assert "addEventListener('resize', updateSize)" in add_body_html.call_args.args[0]
    run.assert_called_once_with(native=True, title='ChessWithJev', window_size=(900, 643))
    labels = [call.args[0] for call in label.call_args_list]
    assert labels[5:13] == list('87654321')
    assert labels[13:21] == list('abcdefgh')
    assert labels[-7:] == ['SYSTEM STATUS', 'White to move', 'MOVE LOG', '01 / LIVE', 'No moves yet', 'CHOOSE PROMOTION', 'CHESS WITH JEV  /  LOCAL SESSION']
    assert len(labels) == 28
    assert image.call_count == 32


def test_native_window_keeps_its_starting_aspect_ratio() -> None:
    window = MagicMock()
    with patch('webview.windows', [window]), patch('PyObjCTools.AppHelper.callAfter', side_effect=lambda callback: callback()):
        lock_window_aspect_ratio()
    window.events.shown.wait.assert_called_once_with()
    window.native.setContentMinSize_.assert_called_once_with((800, 600))
    window.native.setContentSize_.assert_called_once_with((900, 643))
    window.native.setContentAspectRatio_.assert_called_once_with((900, 643))


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
    with patch.object(view, 'sync'):
        view.click_square(chess.E7)  # black cannot move first
        assert view.selected is None
        view.click_square(chess.E2)
        assert view.selected == chess.E2
        view.click_square(chess.E5)  # illegal pawn move
        assert view.position.board.fen() == chess.Board().fen()
        view.click_square(chess.E2)
        view.click_square(chess.E4)
        assert view.position.board.piece_at(chess.E4) == chess.Piece.from_symbol('P')
        assert view.position.board.turn == chess.BLACK
        view.click_square(chess.E4)  # white cannot move twice
        assert view.selected is None
        view.click_square(chess.E7)
        view.click_square(chess.E5)
        assert view.position.board.piece_at(chess.E5) == chess.Piece.from_symbol('p')


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
    view.click_square(chess.E2)
    assert not any(element.clear.called for element in elements)
    view.click_square(chess.E4)
    changed = {square for square, element in view.squares.items() if element.clear.called}
    assert changed == {chess.E2, chess.E4}


def test_only_legal_moves_are_printed(capsys) -> None:
    position = Position()
    assert not position.move(chess.E2, chess.E5)
    assert capsys.readouterr().out == ''
    assert position.move(chess.E2, chess.E4)
    assert position.move(chess.E7, chess.E5)
    assert capsys.readouterr().out == 'e4\ne5\n'


def test_castling_and_en_passant_update_all_affected_squares() -> None:
    view = BoardView()
    view.squares = {square: MagicMock() for square in chess.SQUARES}
    view.shown_pieces = {square: view.position.board.piece_at(square) for square in chess.SQUARES}
    view.promotion_dialog = MagicMock()
    view.set_fen('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1')
    for element in view.squares.values():
        element.reset_mock()
    view.click_square(chess.E1)
    view.click_square(chess.G1)
    assert view.position.board.piece_at(chess.F1) == chess.Piece.from_symbol('R')
    assert view.position.board.piece_at(chess.G1) == chess.Piece.from_symbol('K')
    assert {square for square, element in view.squares.items() if element.clear.called} == {chess.E1, chess.F1, chess.G1, chess.H1}
    view.set_fen('7k/8/8/3pP3/8/8/8/K7 w - d6 0 1')
    for element in view.squares.values():
        element.reset_mock()
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
    assert view.status_label.text == 'White to move'
    assert not view.claim_button.visible
    assert not view.undo_button.enabled
    assert not view.redo_button.enabled
    click(view.squares[chess.E2])
    click(view.squares[chess.E4])
    assert view.undo_button.enabled
    click(view.undo_button)
    assert view.history_label.text == 'No moves yet'
    assert view.redo_button.enabled
    click(view.redo_button)
    assert view.history_label.text == '1. e4'

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


def test_move_history_and_new_game() -> None:
    view = BoardView()
    view.render_controls()
    view.position.move(chess.E2, chess.E4)
    view.position.move(chess.C7, chess.C5)
    view.sync()
    assert view.history_label.text == '1. e4\n1... c5'
    assert view.status_label.text == 'White to move'
    view.new_game()
    assert view.position.board.fen() == chess.STARTING_FEN
    assert view.history_label.text == 'No moves yet'


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
    assert view.history_label.text == '1. e4'
    assert view.status_label.text == 'Black to move'
    assert view.position.board.piece_at(chess.E5) is None
    view.redo()
    assert view.history_label.text == '1. e4\n1... e5'
    assert view.position.board.piece_at(chess.E5) == chess.Piece.from_symbol('p')
    view.undo()
    assert view.position.move(chess.C7, chess.C5)
    view.sync()
    view.redo()
    assert view.history_label.text == '1. e4\n1... c5'
    view.new_game()
    assert not view.position.redo_stack
    assert view.history_label.text == 'No moves yet'


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
