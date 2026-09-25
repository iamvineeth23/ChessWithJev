import runpy
from src.ui.board import square_color
from src.ui import board
from unittest.mock import MagicMock, patch


def test_board_colors() -> None:
    colors = [[square_color(row, column) for column in range(8)] for row in range(8)]
    assert all(colors[row][column] != colors[row][column + 1] for row in range(8) for column in range(7))
    assert all(colors[row][column] != colors[row + 1][column] for row in range(7) for column in range(8))
    assert colors[0][0] == colors[7][7] == 'light'
    assert colors[7][0] == 'dark'  # a1


def test_board_opens_native_window() -> None:
    with patch.object(board.ui, 'add_css'), patch.object(board.ui, 'element', return_value=MagicMock()), patch.object(board.ui, 'run') as run:
        runpy.run_path(board.__file__, run_name='__mp_main__')
    run.assert_called_once_with(native=True, title='ChessWithJev')
