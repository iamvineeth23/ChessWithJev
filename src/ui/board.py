import sys
import shutil
import os
from collections.abc import MutableMapping

import chess
from nicegui import app, ui

from src.game.position import Position
from src.ui.analysis import evaluation_chart_svg, latest_game_evaluations, latest_game_players
from src.ui.board_assets import BOARD_CSS, DEBUG_VIEWPORT_HTML, MOVE_LOG_SCRIPT
from src.ui.board_view import BoardView, move_history, piece_image, square_color, square_name


def lock_window_aspect_ratio() -> None:
    import webview
    from PyObjCTools import AppHelper

    window = webview.windows[0]
    window.events.shown.wait()

    def lock() -> None:
        window.native.setContentMinSize_((800, 600))
        window.native.setContentSize_((1100, 786))
        window.native.setContentAspectRatio_((1100, 786))

    AppHelper.callAfter(lock)


def game_snapshot(view: BoardView) -> dict[str, object]:
    return {
        'white': view.players[chess.WHITE],
        'black': view.players[chess.BLACK],
        'white_elo': view.stockfish_elos[chess.WHITE],
        'black_elo': view.stockfish_elos[chess.BLACK],
        'position': view.position.snapshot(),
    }


def saved_game(storage: MutableMapping[str, object]) -> tuple[Position, str, str, int, int] | None:
    game = storage.get('game')
    if not isinstance(game, dict):
        return None
    white, black = game.get('white'), game.get('black')
    if white not in {'human', 'random', 'stockfish'} or black not in {'human', 'random', 'stockfish'}:
        return None
    position = Position()
    if not position.restore(game.get('position')):
        return None
    white_elo, black_elo = game.get('white_elo', 1500), game.get('black_elo', 1500)
    if not isinstance(white_elo, int) or not isinstance(black_elo, int):
        return None
    return position, white, black, white_elo, black_elo


def build_page(storage: MutableMapping[str, object]) -> None:
    ui.add_body_html(MOVE_LOG_SCRIPT)
    if '-d' in sys.argv[1:]:
        ui.add_body_html(DEBUG_VIEWPORT_HTML)
    ui.add_css(BOARD_CSS)
    with ui.element('div').classes('app-shell'):
        with ui.element('header').classes('app-header'):
            with ui.element('div'):
                ui.label('LOCAL CHESS TERMINAL / V.01').classes('app-kicker')
                ui.label('CHESS WITH JEV').classes('app-title')
            header_actions = ui.element('div').classes('header-actions')
            header_actions.visible = False
            ui.label('● SYSTEM ONLINE').classes('header-mark')
        content = ui.element('main')
        footer = ui.label(chess.STARTING_FEN).classes('footer-note').props('title="Click to copy FEN" aria-label="Current FEN; click to copy"').on('click', js_handler='''(...args) => {
            const text = args[0].currentTarget.textContent;
            const fallback = () => {
                const input = document.createElement('textarea');
                input.value = text;
                document.body.appendChild(input);
                input.select();
                document.execCommand('copy');
                input.remove();
            };
            navigator.clipboard?.writeText(text).catch(fallback) ?? fallback();
        }''')

    def show_landing(clear_game: bool = False) -> None:
        if clear_game:
            storage.pop('game', None)
        header_actions.clear()
        header_actions.visible = False
        footer.visible = False
        content.clear()
        content.classes(remove='game-page')
        with content:
            with ui.element('section').classes('landing'):
                ui.label('SELECT PLAYERS').classes('landing-title')
                def player_row(label: str, value: str):
                    with ui.element('div').classes('player-row'):
                        player = ui.select(['human', 'random', 'stockfish'], value=value, label=label).props(f'outlined popup-content-class="player-options" aria-label="{label} player"')
                        elo = ui.select([1320, 1500, 1800, 2100, 2400, 2700, 3000, 3190], value=1500, label='ELO').classes('elo-select').props(f'outlined popup-content-class="player-options" aria-label="{label} ELO"')
                        elo.visible = value == 'stockfish'
                        player.on('update:model-value', lambda: setattr(elo, 'visible', player.value == 'stockfish'))
                    return player, elo

                white, white_elo = player_row('White', 'human')
                black, black_elo = player_row('Black', 'random')
                ui.button('START GAME', on_click=lambda: show_game(white.value, black.value, white_elo.value, black_elo.value), color=None).classes('terminal-button new-game-button')

    def show_game(white: str, black: str, white_elo: int = 1500, black_elo: int = 1500, position: Position | None = None) -> None:
        if not shutil.which('stockfish'):
            ui.notify('Stockfish executable not found. Run bash scripts/setup.sh first.', type='negative')
            return
        view = BoardView(position=position, white=white, black=black, white_elo=white_elo, black_elo=black_elo,
                         on_change=lambda changed: storage.__setitem__('game', game_snapshot(changed)), recording='-r' in sys.argv[1:])
        view.fen_label = footer
        footer.set_text(view.position.board.fen())
        footer.visible = True
        header_actions.clear()
        header_actions.visible = True
        content.clear()
        with header_actions:
            ui.button('MAIN MENU', on_click=lambda: (view.pause_random(), view.controller.close(), show_landing(True)), color=None).classes('terminal-button')
        with content.classes('game-page'):
            with ui.element('div').classes('game-layout'):
                with ui.element('section').classes('board-panel'):
                    with ui.element('div').classes('status-strip'):
                        view.render_status()
                    with ui.element('div').classes('board-heading'):
                        ui.label(f'WHITE / {white.upper()}  ·  BLACK / {black.upper()}').classes('board-players')
                    with ui.element('div').classes('chess-layout'):
                        view.render_evaluation()
                        with ui.element('div').classes('rank-labels'):
                            for rank in (range(1, 9) if view.black_at_bottom else range(8, 0, -1)):
                                ui.label(str(rank)).classes('axis-label')
                        view.render()
                        with ui.element('div').classes('file-labels'):
                            for file in ('hgfedcba' if view.black_at_bottom else 'abcdefgh'):
                                ui.label(file).classes('axis-label')
                with ui.element('aside').classes('game-controls'):
                    view.render_controls(header_actions)
        if white != 'human' and black == 'human':
            view.random_step()

    restored = saved_game(storage)
    if restored:
        show_game(restored[1], restored[2], restored[3], restored[4], restored[0])
    else:
        storage.pop('game', None)
        show_landing()


@ui.page('/')
def page() -> None:
    build_page(app.storage.user)


def main() -> None:
    if '-d' in sys.argv[1:]:
        Position().print_legal_moves()
    if sys.platform == 'darwin':
        app.native.start_args['func'] = lock_window_aspect_ratio
    ui.run(native=True, title='ChessWithJev', window_size=(1100, 786), reconnect_timeout=60,
           storage_secret=os.environ.get('CHESSWITHJEV_STORAGE_SECRET', 'chesswithjev-local-state'))


if __name__ in {'__main__', '__mp_main__'}:
    main()
