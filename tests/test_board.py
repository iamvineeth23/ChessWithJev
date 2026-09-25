import runpy
from base64 import b64decode
import chess
from src.game.position import starting_piece
from src.ui.board import piece_image, square_color, square_name
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
    expected = ['rnbqkbnr', 'pppppppp', '........', '........',
                '........', '........', 'PPPPPPPP', 'RNBQKBNR']
    actual = [''.join((starting_piece(square_name(row, column)).symbol()
                       if starting_piece(square_name(row, column)) else '.')
                      for column in range(8)) for row in range(8)]
    assert actual == expected
