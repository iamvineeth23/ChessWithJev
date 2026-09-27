from base64 import b64encode
from functools import lru_cache
import sys
import shutil
import os
from collections.abc import Callable, MutableMapping

import chess
import chess.svg
from nicegui import app, ui

from src.game.controller import GameController
from src.game.position import Position


def square_color(row: int, column: int) -> str:
    return 'light' if (row + column) % 2 == 0 else 'dark'


def square_name(row: int, column: int, flipped: bool = False) -> str:
    if flipped:
        row, column = 7 - row, 7 - column
    return f'{chr(ord("a") + column)}{8 - row}'


@lru_cache(maxsize=12)
def piece_image(piece: chess.Piece) -> str:
    svg = chess.svg.piece(piece).encode()
    return f'data:image/svg+xml;base64,{b64encode(svg).decode()}'


def move_history(board: chess.Board) -> str:
    return '\n'.join(move_history_lines(board)) or 'No moves yet'


def move_history_lines(board: chess.Board) -> list[str]:
    replay = board.root()
    lines = []
    for move in board.move_stack:
        prefix = f'{replay.fullmove_number}.' if replay.turn else f'{replay.fullmove_number}...'
        lines.append(f'{prefix} {replay.san(move)}')
        replay.push(move)
    return lines


def lock_window_aspect_ratio() -> None:
    import webview
    from PyObjCTools import AppHelper

    window = webview.windows[0]
    window.events.shown.wait()

    def lock() -> None:
        window.native.setContentMinSize_((800, 600))
        window.native.setContentSize_((900, 643))
        window.native.setContentAspectRatio_((900, 643))

    AppHelper.callAfter(lock)


class BoardView:
    def __init__(self, position: Position | None = None, white: str = 'human', black: str = 'random', white_elo: int = 1500, black_elo: int = 1500, on_change: Callable[['BoardView'], None] | None = None) -> None:
        if white not in {'human', 'random', 'stockfish'} or black not in {'human', 'random', 'stockfish'}:
            raise ValueError('Players must be human, random, or stockfish')
        self.controller = GameController(position)
        self.position = self.controller.position
        self.players = {chess.WHITE: white, chess.BLACK: black}
        self.stockfish_elos = {chess.WHITE: white_elo, chess.BLACK: black_elo}
        self.black_at_bottom = white != 'human' and black == 'human'
        self.on_change = on_change
        self.random_timer = None
        self.random_button = None
        self.selected: chess.Square | None = None
        self.pending_promotion: tuple[chess.Square, chess.Square] | None = None
        self.promotion_dialog = None
        self.status_label = None
        self.fen_label = None
        self.history_panel = None
        self.history_labels = []
        self.eval_fill = None
        self.eval_bar = None
        self.eval_position = None
        self.claim_button = None
        self.undo_button = None
        self.redo_button = None
        self.history_back_button = None
        self.history_forward_button = None
        self.preview_index: int | None = None
        self.preview_board: chess.Board | None = None
        self.squares = {}
        self.shown_pieces: dict[chess.Square, chess.Piece | None] = {}

    def set_fen(self, fen: str) -> None:
        self.position.set_fen(fen)
        self.preview_index = self.preview_board = None
        self.selected = None
        self.pending_promotion = None
        if self.promotion_dialog:
            self.promotion_dialog.close()
        self.sync()

    def set_board(self, board: chess.Board) -> None:
        self.position.set_board(board)
        self.preview_index = self.preview_board = None
        self.selected = None
        self.pending_promotion = None
        if self.promotion_dialog:
            self.promotion_dialog.close()
        self.sync()

    def choose_promotion(self, piece_type: chess.PieceType) -> None:
        if self.pending_promotion is None:
            return
        source, target = self.pending_promotion
        self.pending_promotion = None
        self.promotion_dialog.close()
        self.play_human_move(chess.Move(source, target, promotion=piece_type))
        self.selected = None

    def play_move(self, move: chess.Move) -> bool:
        played = self.controller.play(move)
        if played:
            self.preview_index = self.preview_board = None
            self.selected = None
            self.sync()
        return played

    def play_human_move(self, move: chess.Move) -> bool:
        if self.preview_board is not None or self.players[self.position.board.turn] != 'human' or not self.controller.play(move):
            return False
        self.selected = None
        self.automatic_step()
        self.sync()
        return True

    def automatic_step(self) -> None:
        player = self.players[self.position.board.turn]
        if player == 'random':
            self.controller.play_random_move()
        elif player == 'stockfish':
            self.controller.play_stockfish_move(self.stockfish_elos[self.position.board.turn])

    def random_step(self) -> None:
        if self.preview_board is None and not self.position.outcome() and self.players[self.position.board.turn] != 'human':
            self.automatic_step()
            self.sync()
        if self.position.outcome() and self.random_timer:
            self.random_timer.active = False
            self.random_button.set_text('START')

    def toggle_random(self) -> None:
        if self.preview_board is not None:
            return
        self.random_timer.active = not self.random_timer.active
        self.random_button.set_text('PAUSE' if self.random_timer.active else 'START')

    def pause_random(self) -> None:
        if self.random_timer:
            self.random_timer.active = False
            self.random_button.set_text('START')

    def claim_draw(self) -> None:
        if self.preview_board is not None:
            return
        if self.position.claim_draw():
            self.preview_index = self.preview_board = None
            self.selected = None
            self.sync()

    def new_game(self) -> None:
        self.pause_random()
        self.set_board(chess.Board())
        if self.players[chess.WHITE] != 'human' and self.players[chess.BLACK] == 'human':
            self.random_step()

    def undo(self) -> None:
        if self.preview_board is not None:
            return
        self.pause_random()
        self.preview_index = self.preview_board = None
        if self.players[chess.WHITE] != 'human' and self.players[chess.BLACK] == 'human' and len(self.position.board.move_stack) == 1:
            return
        if self.position.undo():
            if self.players[chess.WHITE] != self.players[chess.BLACK] and self.position.board.move_stack:
                self.position.undo()
            self.selected = None
            self.sync()

    def redo(self) -> None:
        if self.preview_board is not None:
            return
        self.pause_random()
        self.preview_index = self.preview_board = None
        if self.position.redo():
            if self.players[chess.WHITE] != self.players[chess.BLACK] and self.position.redo_stack:
                self.position.redo()
            self.selected = None
            self.sync()

    def click_square(self, square: chess.Square) -> None:
        if self.preview_board is not None or self.position.outcome() or self.pending_promotion or self.players[self.position.board.turn] != 'human':
            return
        piece = self.position.board.piece_at(square)
        if piece and piece.color == self.position.board.turn:
            self.selected = square if self.selected != square else None
        elif self.selected is not None:
            source_piece = self.position.board.piece_at(self.selected)
            if source_piece and source_piece.piece_type == chess.PAWN and chess.square_rank(square) in (0, 7) and chess.Move(self.selected, square, promotion=chess.QUEEN) in self.position.board.legal_moves:
                self.pending_promotion = (self.selected, square)
                self.promotion_dialog.open()
            else:
                if self.play_human_move(chess.Move(self.selected, square)):
                    return
                self.selected = None
        self.sync()

    def step_history(self, direction: int) -> None:
        count = len(self.position.board.move_stack)
        index = count if self.preview_index is None else self.preview_index
        target = max(0, min(count, index + direction))
        if target == index:
            return
        self.pause_random()
        self.selected = None
        self.preview_index = None if target == count else target
        self.preview_board = None
        if self.preview_index is not None:
            self.preview_board = self.position.board.root()
            for move in self.position.board.move_stack[:target]:
                self.preview_board.push(move)
        self.sync()

    def sync(self) -> None:
        board = self.preview_board or self.position.board
        if self.eval_fill:
            position = (board.fen(), self.position.claimed_draw if self.preview_board is None else None)
            if position != self.eval_position:
                percent = 100 * self.controller.white_expectation(board)
                self.eval_fill.style(f'height: {percent:.1f}%')
                self.eval_bar.props(f'aria-valuenow="{percent:.0f}" aria-valuetext="White expected score {percent:.0f} percent"')
                self.eval_position = position
        if self.status_label:
            self.status_label.set_text(f'Viewing move {self.preview_index} / {len(self.position.board.move_stack)}' if self.preview_index is not None else self.position.status())
        if self.fen_label:
            self.fen_label.set_text(board.fen())
        if self.history_panel:
            self.render_history()
        if self.claim_button:
            self.claim_button.visible = self.preview_board is None and not self.position.outcome() and self.position.board.can_claim_draw()
        if self.undo_button:
            self.undo_button.set_enabled(self.preview_board is None and bool(self.position.board.move_stack))
        if self.redo_button:
            self.redo_button.set_enabled(self.preview_board is None and bool(self.position.redo_stack))
        if self.history_back_button:
            self.history_back_button.set_enabled((self.preview_index if self.preview_index is not None else len(self.position.board.move_stack)) > 0)
        if self.history_forward_button:
            self.history_forward_button.set_enabled(self.preview_index is not None)
        if self.random_button:
            self.random_button.set_enabled(self.preview_board is None and not bool(self.position.outcome()))
        current_index = len(self.position.board.move_stack) if self.preview_index is None else self.preview_index
        current_move = self.position.board.move_stack[current_index - 1] if current_index else None
        for square, element in self.squares.items():
            element.classes(add='selected' if square == self.selected else None,
                            remove='selected' if square != self.selected else None)
            element.classes(add='last-move' if current_move and square in (current_move.from_square, current_move.to_square) else None,
                            remove='last-move' if not current_move or square not in (current_move.from_square, current_move.to_square) else None)
            piece = board.piece_at(square)
            if piece == self.shown_pieces[square]:
                continue
            element.clear()
            if piece:
                with element:
                    ui.image(piece_image(piece)).classes('chess-piece').props(f'alt="{"white" if piece.color else "black"} {chess.piece_name(piece.piece_type)}"')
            self.shown_pieces[square] = piece
        if self.on_change:
            self.on_change(self)

    def render(self) -> None:
        self.squares.clear()
        self.shown_pieces.clear()
        board = self.preview_board or self.position.board
        with ui.element('div').classes('chess-board').props('aria-label="Chess board"'):
            for row in range(8):
                for column in range(8):
                    name = square_name(row, column, self.black_at_bottom)
                    square = chess.parse_square(name)
                    element = ui.element('div').classes(f'chess-square {square_color(row, column)}').props(f'aria-label="{name}"').on('click', lambda _, square=square: self.click_square(square))
                    self.squares[square] = element
                    if square == self.selected:
                        element.classes('selected')
                    with element:
                        piece = board.piece_at(square)
                        if piece:
                            ui.image(piece_image(piece)).classes('chess-piece').props(f'alt="{"white" if piece.color else "black"} {chess.piece_name(piece.piece_type)}"')
                        self.shown_pieces[square] = piece
        with ui.element('div').classes('board-actions'):
            self.undo_button = ui.button('↶', on_click=self.undo, color=None).classes('terminal-button').props('aria-label="Undo move" title="Undo move"')
            self.redo_button = ui.button('↷', on_click=self.redo, color=None).classes('terminal-button').props('aria-label="Redo move" title="Redo move"')
            self.history_back_button = ui.button('←', on_click=lambda: self.step_history(-1), color=None).classes('terminal-button').props('aria-label="Previous move in history" title="Previous move in history"')
            self.history_forward_button = ui.button('→', on_click=lambda: self.step_history(1), color=None).classes('terminal-button').props('aria-label="Next move in history" title="Next move in history"')
            self.undo_button.set_enabled(bool(self.position.board.move_stack))
            self.redo_button.set_enabled(bool(self.position.redo_stack))
            self.history_back_button.set_enabled(bool(self.position.board.move_stack))
            self.history_forward_button.set_enabled(False)

    def render_evaluation(self) -> None:
        with ui.element('div').classes('eval-bar').props('role="meter" aria-label="Position evaluation" aria-valuemin="0" aria-valuemax="100"') as self.eval_bar:
            self.eval_fill = ui.element('div').classes('eval-white')
        self.sync()

    def render_status(self) -> None:
        ui.label('SYSTEM STATUS').classes('panel-kicker')
        self.status_label = ui.label(self.position.status()).classes('status-text').props('role="status" aria-live="polite"')

    def render_controls(self) -> None:
        if self.status_label is None:
            self.render_status()
        with ui.element('div').classes('history-heading'):
            ui.label('MOVE LOG')
            ui.label('01 / LIVE').classes('panel-meta')
        with ui.element('div').classes('move-history-panel'):
            self.history_panel = ui.element('div').classes('move-history')
        self.render_history()
        ui.button('NEW GAME', on_click=self.new_game, color=None).classes('terminal-button new-game-button')
        if all(player != 'human' for player in self.players.values()):
            self.random_timer = ui.timer(0.6, self.random_step, active=False)
            self.random_button = ui.button('START', on_click=self.toggle_random, color=None).classes('terminal-button')
        self.claim_button = ui.button('CLAIM DRAW', on_click=self.claim_draw).classes('terminal-button claim-button')
        self.claim_button.visible = not self.position.outcome() and self.position.board.can_claim_draw()
        with ui.dialog().props('persistent') as self.promotion_dialog, ui.card().classes('promotion-card'):
            ui.label('CHOOSE PROMOTION').classes('panel-kicker')
            with ui.row().classes('promotion-actions'):
                for piece_type in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
                    ui.button(chess.piece_name(piece_type).title(), on_click=lambda _, piece_type=piece_type: self.choose_promotion(piece_type)).classes('terminal-button')

    def render_history(self) -> None:
        self.history_panel.clear()
        self.history_labels = []
        current_index = len(self.position.board.move_stack) if self.preview_index is None else self.preview_index
        with self.history_panel:
            lines = move_history_lines(self.position.board)
            if not lines:
                self.history_labels.append(ui.label('No moves yet').classes('move-history-entry'))
            for index, line in enumerate(lines, 1):
                label = ui.label(line).classes('move-history-entry')
                if index == current_index:
                    label.classes('current-move').props('aria-current="step"')
                self.history_labels.append(label)


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
    ui.add_body_html('''
        <script>
            const watchMoveLog = () => {
                const log = document.querySelector('.move-history-panel');
                if (!log) return;
                attachMoveLog.disconnect();
                new MutationObserver(() => { log.scrollTop = log.scrollHeight; })
                    .observe(log, {childList: true, characterData: true, subtree: true});
            };
            const attachMoveLog = new MutationObserver(watchMoveLog);
            attachMoveLog.observe(document.body, {childList: true, subtree: true});
            watchMoveLog();
        </script>
    ''')
    if '-d' in sys.argv[1:]:
        ui.add_body_html('''
            <div id="viewport-size" style="position:fixed;right:8px;bottom:8px;z-index:1000;
                padding:4px 7px;background:#17251c;color:#a8f0b0;border:1px solid #425c48;
                font:11px monospace;pointer-events:none" aria-label="Viewport size"></div>
            <script>
                const size = document.getElementById('viewport-size');
                function updateSize() { size.textContent = `${window.innerWidth} × ${window.innerHeight}`; }
                window.addEventListener('resize', updateSize);
                updateSize();
            </script>
        ''')
    ui.add_css('''
        :root { --green: #a8f0b0; --muted: #779780; --line: #425c48; --panel: #17251c; }
        body { background: #0c1510; color: #d7e8d6; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; }
        .nicegui-content { padding: 0; }
        .app-shell { width: min(1120px, 100%); min-height: 100dvh; margin: 0 auto; padding: clamp(20px, 4vw, 44px); padding-top: 5px; box-sizing: border-box; }
        .app-header { display: flex; align-items: end; justify-content: space-between; gap: 20px; border-bottom: 1px solid var(--line); padding-bottom: 2px; }
        .app-kicker, .panel-kicker, .panel-meta, .axis-label, .footer-note { color: var(--muted); font-size: 11px; letter-spacing: .16em; }
        .app-title { color: var(--green); font-size: clamp(28px, 4vw, 46px); font-weight: 700; line-height: 1.1; letter-spacing: -.06em; text-shadow: 0 0 24px #72e98940; }
        .header-mark { border: 1px solid var(--line); color: var(--green); padding: 7px 10px; font-size: 11px; letter-spacing: .12em; white-space: nowrap; }
        .game-layout { display: flex; align-items: stretch; gap: 28px; margin-top: 4px; }
        .game-page { display: flex; flex-direction: column; flex: 1; min-height: 0; position: relative; }
        .status-strip { display: flex; align-items: center; justify-content: flex-end; gap: 18px; width: 100%; padding-right: 80px; box-sizing: border-box; }
        .board-panel, .game-controls { background: var(--panel); border: 1px solid var(--line); box-shadow: 8px 8px 0 #080f0b; }
        .board-panel { padding: clamp(12px, 2vw, 22px); min-width: 0; flex: 1; }
        .board-heading { display: grid; grid-template-columns: 16px 24px minmax(0, 1fr) 80px; width: 100%; margin-bottom: 4px; color: var(--green); font-size: 12px; letter-spacing: .12em; }
        .board-players { grid-column: 3; justify-self: end; }
        .game-controls { display: flex; flex-direction: column; gap: 14px; width: 274px; flex-shrink: 0; padding: 22px; }
        .status-text { color: var(--green); font-size: 11px; line-height: 1.4; letter-spacing: .16em; }
        .history-heading { display: flex; justify-content: space-between; gap: 8px; color: var(--green); font-size: 12px; letter-spacing: .1em; }
        .move-history-panel { flex: 1; min-height: 180px; overflow-y: auto; border: 1px solid var(--line); background: #101b14; padding: 14px; }
        .move-history { overflow-wrap: anywhere; line-height: 1.8; font-size: 13px; }
        .move-history-entry { display: block; }
        .move-history-entry.current-move { background: #e7cb7d; color: #0c1510; padding: 0 4px; margin: 0 -4px; font-weight: 700; }
        .terminal-button { width: 100%; border: 1px solid var(--green); border-radius: 0; background: transparent; color: var(--green); font-family: inherit; font-weight: 700; letter-spacing: .08em; box-shadow: none; }
        .terminal-button:hover { background: #294733; }
        .terminal-button:focus-visible { outline: 2px solid #f3d68a; outline-offset: 3px; }
        .new-game-button, .board-actions .terminal-button { background: var(--green); color: #0c1510; }
        .new-game-button:hover, .board-actions .terminal-button:hover { background: #cefbd1; }
        .chess-layout { display: grid; grid-template-columns: 16px 24px minmax(0, 1fr) 80px; grid-template-rows: auto 24px; width: 100%; }
        .board-actions { grid-column: 4; grid-row: 1; align-self: end; display: grid; grid-template-columns: repeat(2, 32px); grid-template-rows: repeat(2, 32px); gap: 8px; padding-left: 8px; }
        .board-actions .terminal-button { width: 32px; height: 32px; min-height: 32px; padding: 0; font-size: 20px; line-height: 1; }
        .board-actions .terminal-button:disabled { opacity: .4; }
        .eval-bar { grid-column: 1; grid-row: 1; width: 16px; height: 100%; border: 2px solid #89b993; background: #17251c; display: flex; flex-direction: column; justify-content: flex-end; box-sizing: border-box; }
        .eval-white { width: 100%; background: #d7e8d6; }
        .rank-labels { grid-column: 2; grid-row: 1; display: grid; grid-template-rows: repeat(8, 1fr); }
        .file-labels { grid-column: 3; display: grid; grid-template-columns: repeat(8, 1fr); }
        .axis-label { display: flex; align-items: center; justify-content: center; }
        .chess-board { display: grid; grid-template-columns: repeat(8, 1fr); width: 100%; border: 2px solid #89b993; }
        .chess-square { aspect-ratio: 1; position: relative; cursor: pointer; }
        .chess-square.light { background: #b5c6ad; }
        .chess-square.dark { background: #506953; }
        .chess-square:hover { box-shadow: inset 0 0 0 3px #d0eac2; }
        .chess-square.selected { outline: 4px solid #e7cb7d; outline-offset: -4px; z-index: 1; }
        .chess-square.last-move { box-shadow: inset 0 0 0 4px #e7cb7d; }
        .chess-piece { position: absolute; inset: 5%; width: 90%; height: 90%; pointer-events: none; }
        .promotion-card { background: var(--panel); border: 1px solid var(--green); border-radius: 0; color: var(--green); padding: 24px; font-family: inherit; }
        .promotion-actions { flex-wrap: wrap; margin-top: 12px; }
        .promotion-actions .terminal-button { width: auto; }
        .footer-note { margin-top: 28px; border-top: 1px solid var(--line); padding-top: 16px; user-select: text; cursor: copy; }
        .game-page + .footer-note { margin-top: 20px; }
        .app-shell > main:not(.game-page) { display: flex; flex: 1; }
        .landing { display: flex; flex: 1; flex-direction: column; justify-content: center; gap: 20px; max-width: 440px; width: 100%; margin: auto; }
        .player-row { position: relative; }
        .landing .q-field.elo-select { position: absolute; top: 0; left: calc(100% + 32px); width: 150px; }
        .landing .q-field { width: 100%; color: var(--green); }
        .landing .q-field__label, .landing .q-field__native, .landing .q-field__marginal { color: var(--green) !important; }
        .landing .q-field--outlined .q-field__control:before { border-color: var(--line); }
        .player-options { background: var(--panel); color: var(--green); }
        .landing-title { color: var(--green); font-size: 24px; }
        @media (min-width: 761px) {
            .app-shell { height: 100dvh; display: flex; flex-direction: column; }
            .game-layout { flex: 1; min-height: 0; }
            .board-panel { display: grid; grid-template-rows: auto auto minmax(0, 1fr); min-height: 0; }
            .status-strip, .board-heading { width: min(100%, calc(100dvh - 158px), 740px); justify-self: center; }
            .chess-layout { width: min(100%, calc(100dvh - 158px), 740px); height: max-content; place-self: center; min-width: 0; grid-template-rows: auto 24px; }
            .move-history-panel { min-height: 0; }
        }
        @media (max-width: 760px) {
            .app-header { align-items: start; }
            .status-strip { flex-wrap: wrap; }
            .game-layout { flex-direction: column; }
            .game-controls { width: 100%; }
            .move-history-panel { max-height: 230px; }
            .landing .q-field.elo-select { position: static; width: 100%; margin-top: 20px; }
        }
    ''')
    with ui.element('div').classes('app-shell'):
        with ui.element('header').classes('app-header'):
            with ui.element('div'):
                ui.label('LOCAL CHESS TERMINAL / V.01').classes('app-kicker')
                ui.label('CHESS WITH JEV').classes('app-title')
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
                         on_change=lambda changed: storage.__setitem__('game', game_snapshot(changed)))
        view.fen_label = footer
        footer.set_text(view.position.board.fen())
        footer.visible = True
        content.clear()
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
                    view.render_controls()
                    ui.button('MAIN MENU', on_click=lambda: (view.pause_random(), view.controller.close(), show_landing(True)), color=None).classes('terminal-button')
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
    ui.run(native=True, title='ChessWithJev', window_size=(900, 643), reconnect_timeout=60,
           storage_secret=os.environ.get('CHESSWITHJEV_STORAGE_SECRET', 'chesswithjev-local-state'))


if __name__ in {'__main__', '__mp_main__'}:
    main()
