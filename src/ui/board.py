from base64 import b64encode
from functools import lru_cache

import chess
import chess.svg
from nicegui import ui

from src.game.position import starting_piece


def square_color(row: int, column: int) -> str:
    return 'light' if (row + column) % 2 == 0 else 'dark'


def square_name(row: int, column: int) -> str:
    return f'{chr(ord("a") + column)}{8 - row}'


@lru_cache(maxsize=12)
def piece_image(piece: chess.Piece) -> str:
    svg = chess.svg.piece(piece).encode()
    return f'data:image/svg+xml;base64,{b64encode(svg).decode()}'


def main() -> None:
    ui.add_css('''
        .chess-layout { display: grid; grid-template-columns: 20px auto; grid-template-rows: auto 20px; width: max-content; }
        .rank-labels { display: grid; grid-template-rows: repeat(8, 1fr); }
        .file-labels { grid-column: 2; display: grid; grid-template-columns: repeat(8, 1fr); }
        .axis-label { display: flex; align-items: center; justify-content: center; font-size: 14px; line-height: 1; }
        .chess-board { display: grid; grid-template-columns: repeat(8, 1fr); width: min(calc(90vw - 24px), calc(90dvh - 20px), 640px); }
        .chess-square { aspect-ratio: 1; position: relative; }
        .chess-square.light { background: #f0d9b5; }
        .chess-square.dark { background: #b58863; }
        .chess-piece { position: absolute; inset: 5%; width: 90%; height: 90%; }
    ''')
    with ui.element('div').classes('chess-layout'):
        with ui.element('div').classes('rank-labels'):
            for rank in range(8, 0, -1):
                ui.label(str(rank)).classes('axis-label')
        with ui.element('div').classes('chess-board').props('aria-label="Chess board"'):
            for row in range(8):
                for column in range(8):
                    with ui.element('div').classes(f'chess-square {square_color(row, column)}'):
                        piece = starting_piece(square_name(row, column))
                        if piece:
                            ui.image(piece_image(piece)).classes('chess-piece').props(f'alt="{"white" if piece.color else "black"} {chess.piece_name(piece.piece_type)}"')
        with ui.element('div').classes('file-labels'):
            for file in 'abcdefgh':
                ui.label(file).classes('axis-label')
    ui.run(native=True, title='ChessWithJev')


if __name__ in {'__main__', '__mp_main__'}:
    main()
