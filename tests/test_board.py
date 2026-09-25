import runpy
from base64 import b64decode
import chess
from src.game.position import Position
from src.ui.board import BoardView, piece_image, square_color, square_name
from src.ui import board
from unittest.mock import MagicMock, patch


def test_board_colors() -> None:
    colors = [[square_color(row, column) for column in range(8)] for row in range(8)]
    assert all(colors[row][column] != colors[row][column + 1] for row in range(8) for column in range(7))
    assert all(colors[row][column] != colors[row + 1][column] for row in range(7) for column in range(8))
    assert colors[0][0] == colors[7][7] == 'light'
    assert colors[7][0] == 'dark'  # a1


def test_board_opens_native_window() -> None:
    with patch.object(board.ui, 'add_css'), patch.object(board.ui, 'element', return_value=MagicMock()), patch.object(board.ui, 'label') as label, patch.object(board.ui, 'image') as image, patch.object(board.ui, 'run') as run:
        runpy.run_path(board.__file__, run_name='__mp_main__')
    run.assert_called_once_with(native=True, title='ChessWithJev')
    labels = [call.args[0] for call in label.call_args_list]
    assert labels[:8] == list('87654321')
    assert labels[-8:] == list('abcdefgh')
    assert len(labels) == 16
    assert image.call_count == 32


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
    with patch.object(view, 'sync'):
        view.set_fen('7k/P7/8/8/8/8/8/K7 w - - 0 1')
        view.click_square(chess.A7)
        view.click_square(chess.A8)
        assert view.position.board.piece_at(chess.A8) == chess.Piece.from_symbol('Q')
        view.click_square(chess.H8)
        view.set_fen(chess.STARTING_FEN)
        assert view.selected is None


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
