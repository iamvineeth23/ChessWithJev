from nicegui import ui


def square_color(row: int, column: int) -> str:
    return 'light' if (row + column) % 2 == 0 else 'dark'


def main() -> None:
    ui.add_css('''
        .chess-board { display: grid; grid-template-columns: repeat(8, 1fr); width: min(90vw, 90dvh, 640px); }
        .chess-square { aspect-ratio: 1; }
        .chess-square.light { background: #f0d9b5; }
        .chess-square.dark { background: #b58863; }
    ''')
    with ui.element('div').classes('chess-board').props('aria-label="Chess board"'):
        for row in range(8):
            for column in range(8):
                ui.element('div').classes(f'chess-square {square_color(row, column)}')
    ui.run(native=True, title='ChessWithJev')


if __name__ in {'__main__', '__mp_main__'}:
    main()
