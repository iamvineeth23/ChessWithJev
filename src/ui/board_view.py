from base64 import b64encode
from collections.abc import Callable
from functools import lru_cache

import chess
import chess.svg
from nicegui import run, ui

from src.game.controller import GameController
from src.game.log import write_game_log
from src.game.position import Position
from src.ui.analysis import evaluation_chart_svg, latest_game_evaluations, latest_game_players


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




class BoardView:
    def __init__(self, position: Position | None = None, white: str = 'human', black: str = 'random', white_elo: int = 1500, black_elo: int = 1500, on_change: Callable[['BoardView'], None] | None = None, recording: bool = False) -> None:
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
        self.move_analysis_panel = None
        self.analysis_position = None
        self.analysis_busy = False
        self.analysis_engine_label = None
        self.closed = False
        self.history_labels = []
        self.eval_fill = None
        self.eval_bar = None
        self.eval_position = None
        self.evaluation_plot = None
        self.evaluation_cache = {}
        self.move_analysis_cache = {}
        self.claim_button = None
        self.undo_button = None
        self.redo_button = None
        self.history_back_button = None
        self.history_forward_button = None
        self.record_button = None
        self.recording = recording
        self.game_logged = self.position.outcome() is not None
        self.has_played_move = bool(self.position.board.move_stack)
        self.preview_index: int | None = None
        self.preview_board: chess.Board | None = None
        self.squares = {}
        self.shown_pieces: dict[chess.Square, chess.Piece | None] = {}
        self.shown_board: chess.Board | None = None

    def movement_origins(self, board: chess.Board) -> dict[chess.Square, chess.Square]:
        previous = self.shown_board
        if previous is None or board.root().fen() != previous.root().fen():
            return {}
        count = len(previous.move_stack)
        if board.move_stack[:count] != previous.move_stack or len(board.move_stack) <= count:
            return {}
        replay = previous.copy(stack=True)
        origins = {square: square for square in replay.piece_map()}
        for move in board.move_stack[count:]:
            source = origins.pop(move.from_square)
            if replay.is_en_passant(move):
                origins.pop(move.to_square - 8 if replay.turn else move.to_square + 8, None)
            if replay.is_castling(move):
                rank = chess.square_rank(move.from_square)
                kingside = replay.is_kingside_castling(move)
                rook_from = chess.square(7 if kingside else 0, rank)
                rook_to = chess.square(5 if kingside else 3, rank)
                origins[rook_to] = origins.pop(rook_from)
            origins[move.to_square] = source
            replay.push(move)
        return {target: source for target, source in origins.items() if target != source}

    def set_fen(self, fen: str) -> None:
        self.position.set_fen(fen)
        self.evaluation_cache.clear()
        self.move_analysis_cache.clear()
        self.preview_index = self.preview_board = None
        self.selected = None
        self.pending_promotion = None
        self.has_played_move = False
        self.game_logged = False
        if self.promotion_dialog:
            self.promotion_dialog.close()
        self.sync()

    def set_board(self, board: chess.Board) -> None:
        self.position.set_board(board)
        self.evaluation_cache.clear()
        self.move_analysis_cache.clear()
        self.preview_index = self.preview_board = None
        self.selected = None
        self.pending_promotion = None
        self.has_played_move = False
        self.game_logged = False
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
            self.has_played_move = True
            self.preview_index = self.preview_board = None
            self.selected = None
            self.sync()
        return played

    def play_human_move(self, move: chess.Move) -> bool:
        if self.preview_board is not None or self.players[self.position.board.turn] != 'human' or not self.controller.play(move):
            return False
        self.selected = None
        self.has_played_move = True
        self.resume_history_scroll()
        if self.analysis_engine_label is None or not self.analysis_engine_label.client.has_socket_connection:
            self.automatic_step()
        self.sync()
        return True

    def automatic_step(self) -> None:
        player = self.players[self.position.board.turn]
        if player == 'random':
            self.has_played_move |= self.controller.play_random_move()
        elif player == 'stockfish':
            self.has_played_move |= self.controller.play_stockfish_move(self.stockfish_elos[self.position.board.turn])

    def random_step(self) -> None:
        if self.analysis_engine_label is not None and self.analysis_engine_label.client.has_socket_connection:
            if not self.analysis_busy:
                self.schedule_update(self.automatic_turn)
            return
        if self.preview_board is None and not self.position.outcome() and self.players[self.position.board.turn] != 'human':
            self.automatic_step()
            self.sync()
        if self.position.outcome() and self.random_timer:
            self.random_timer.active = False
            self.random_button.set_text('START')

    async def automatic_turn(self) -> None:
        if (self.closed or self.analysis_busy or self.preview_board is not None or self.position.outcome()
                or self.players[self.position.board.turn] == 'human'):
            return
        await self.analyse_position(advance=True)

    async def analyse_position(self, *, advance: bool = False) -> None:
        if self.closed:
            self.analysis_busy = False
            self.set_analysis_indicator(False)
            return
        self.analysis_busy = True
        try:
            if advance:
                self.automatic_step()
            self.set_analysis_indicator(True)
            self.sync()
            await ui.run_javascript('return await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve(true))));', timeout=10)
            while True:
                if self.closed:
                    return
                source = self.preview_board or self.position.board
                board = source.copy(stack=True)
                cache = self.evaluation_cache.copy()
                claimed_draw = self.position.claimed_draw if source is self.position.board else None

                def analyse():
                    replay = board.root()
                    positions = [replay.copy(stack=True)]
                    for move in board.move_stack:
                        replay.push(move)
                        positions.append(replay.copy(stack=True))
                    for position in positions:
                        if self.closed:
                            return cache, None
                        claim = claimed_draw if position.move_stack == board.move_stack else None
                        key = (position.root().fen(), tuple(position.move_stack), str(claim))
                        if key not in cache:
                            cache[key] = (0.5 if claim is not None else self.controller.white_expectation(position))
                    return cache, self.cached_move_analysis(board) if board.move_stack else None

                analysed = await run.io_bound(analyse)
                if self.closed or analysed is None:
                    self.pause_random()
                    return
                cache, result = analysed
                if (source is not (self.preview_board or self.position.board) or source.fen() != board.fen()
                        or (source is self.position.board and claimed_draw != self.position.claimed_draw)):
                    continue
                self.evaluation_cache.update(cache)
                self.sync_analysis(source, result, refresh=False)
                self.set_analysis_indicator(False)
                break
            await ui.run_javascript('return await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve(true))));', timeout=10)
            if self.has_played_move and self.position.outcome() and not self.game_logged:
                finished = self.position.board
                await run.io_bound(write_game_log, finished.copy(stack=True), self.players.copy(),
                                   self.stockfish_elos.copy(), self.controller.white_expectation, self.recording)
                if self.position.board is finished:
                    self.game_logged = True
            if self.position.outcome():
                self.pause_random()
        except Exception:
            self.pause_random()
            if not self.closed:
                raise
        finally:
            self.analysis_busy = False
            self.set_analysis_indicator(False)
        if (not self.closed and self.preview_board is None and not self.position.outcome()
                and 'human' in self.players.values() and self.players[self.position.board.turn] != 'human'
                and self.analysis_engine_label is not None and self.analysis_engine_label.client.has_socket_connection):
            self.schedule_update(self.automatic_turn)

    def schedule_update(self, callback: Callable) -> None:
        # Event handlers can clear their own panel; keep timers in the persistent heading.
        with self.analysis_engine_label.parent_slot:
            ui.timer(0, callback, once=True)

    def set_analysis_indicator(self, active: bool) -> None:
        if self.analysis_engine_label is not None:
            self.analysis_engine_label.classes(add='analyzing' if active else None,
                                               remove=None if active else 'analyzing')
            self.analysis_engine_label.props(f'aria-busy="{str(active).lower()}"')

    def close(self) -> None:
        self.closed = True
        self.pause_random()
        self.controller.close()

    def toggle_random(self) -> None:
        if self.position.outcome():
            return
        if self.preview_board is not None:
            self.select_history(len(self.position.board.move_stack))
        self.random_timer.active = not self.random_timer.active
        if self.random_timer.active:
            self.resume_history_scroll()
        self.random_button.set_text('PAUSE' if self.random_timer.active else 'START')

    def pause_random(self) -> None:
        if self.random_timer:
            self.random_timer.active = False
            self.random_button.set_text('START')

    def resume_history_scroll(self) -> None:
        if self.history_panel:
            generation = int(self.history_panel._props.get('data-scroll-resume', 0)) + 1
            self.history_panel.props(f'data-scroll-resume={generation}')

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

    def toggle_recording(self) -> None:
        self.recording = not self.recording
        self.record_button.classes(add='recording' if self.recording else None,
                                   remove=None if self.recording else 'recording')
        self.record_button.props(f'aria-pressed="{str(self.recording).lower()}"')

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
        self.select_history(target)

    def select_history(self, target: int) -> None:
        count = len(self.position.board.move_stack)
        index = count if self.preview_index is None else self.preview_index
        target = max(0, min(count, target))
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

    def cached_move_analysis(self, board: chess.Board):
        key = (board.root().fen(), tuple(board.move_stack))
        if key not in self.move_analysis_cache:
            self.move_analysis_cache[key] = self.controller.move_analysis(board)
        return self.move_analysis_cache[key]

    def cached_white_expectation(self, board: chess.Board, *, refresh: bool = False) -> float:
        key = (board.root().fen(), tuple(board.move_stack),
               str(self.position.claimed_draw) if board is self.position.board else str(None))
        if refresh or key not in self.evaluation_cache:
            self.evaluation_cache[key] = self.controller.white_expectation(board)
        return self.evaluation_cache[key]

    def sync_evaluation_plot(self, board: chess.Board) -> None:
        replay = board.root()
        evaluations = [200 * self.cached_white_expectation(board if not board.move_stack else replay) - 100]
        for move in board.move_stack:
            replay.push(move)
            evaluated = board if len(replay.move_stack) == len(board.move_stack) else replay
            evaluations.append(200 * self.cached_white_expectation(evaluated) - 100)
        self.evaluation_plot.set_content(evaluation_chart_svg(evaluations, compact=True))

    def sync_analysis(self, board: chess.Board, result=None, *, refresh: bool = True) -> None:
        if self.eval_fill:
            position = (board.fen(), self.position.claimed_draw if self.preview_board is None else None)
            if position != self.eval_position:
                percent = 100 * self.cached_white_expectation(board, refresh=refresh)
                self.eval_fill.style(f'height: {percent:.1f}%')
                self.eval_bar.props(f'aria-valuenow="{percent:.0f}" aria-valuetext="White expected score {percent:.0f} percent"')
                self.eval_position = position
        if self.evaluation_plot:
            self.sync_evaluation_plot(board)
        if self.move_analysis_panel and board.fen() != self.analysis_position:
            self.render_move_analysis(board, result)
            self.analysis_position = board.fen()

    def sync(self) -> None:
        board = self.preview_board or self.position.board
        if not self.analysis_busy:
            position = (board.fen(), self.position.claimed_draw if self.preview_board is None else None)
            cache_key = (board.root().fen(), tuple(board.move_stack), str(position[1]))
            needs_analysis = ((bool(board.move_stack) and (board.root().fen(), tuple(board.move_stack)) not in self.move_analysis_cache)
                              or ((self.eval_fill is not None or self.evaluation_plot is not None)
                                  and cache_key not in self.evaluation_cache))
            if (self.analysis_engine_label is not None
                    and self.analysis_engine_label.client.has_socket_connection
                    and needs_analysis):
                self.analysis_busy = True
                self.set_analysis_indicator(True)
                self.schedule_update(self.analyse_position)
            else:
                self.sync_analysis(board, refresh=False)
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
            self.random_button.set_enabled(not bool(self.position.outcome()))
        current_index = len(self.position.board.move_stack) if self.preview_index is None else self.preview_index
        current_move = self.position.board.move_stack[current_index - 1] if current_index else None
        origins = self.movement_origins(board)
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
                    image = ui.image(piece_image(piece)).classes('chess-piece').props(f'alt="{"white" if piece.color else "black"} {chess.piece_name(piece.piece_type)}"')
                    if square in origins:
                        source = origins[square]
                        direction = -1 if self.black_at_bottom else 1
                        x = direction * (chess.square_file(source) - chess.square_file(square)) * 100 / .9
                        y = direction * (chess.square_rank(square) - chess.square_rank(source)) * 100 / .9
                        image.classes('chess-piece-moving').style(f'--piece-x: {x}%; --piece-y: {y}%')
            self.shown_pieces[square] = piece
        self.shown_board = board.copy(stack=True)
        if self.on_change:
            self.on_change(self)
        if not self.analysis_busy and self.has_played_move and self.position.outcome() and not self.game_logged:
            write_game_log(self.position.board, self.players, self.stockfish_elos, self.controller.white_expectation, self.recording)
            self.game_logged = True

    def render(self) -> None:
        self.squares.clear()
        self.shown_pieces.clear()
        board = self.preview_board or self.position.board
        self.shown_board = board.copy(stack=True)
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
            self.record_button = ui.button('REC', on_click=self.toggle_recording, color=None).classes(f'terminal-button record-button{" recording" if self.recording else ""}').props(f'aria-label="Record game log" aria-pressed="{str(self.recording).lower()}"')
            self.undo_button = ui.button('↶', on_click=self.undo, color=None).classes('terminal-button').props('aria-label="Undo move" title="Undo move"')
            self.redo_button = ui.button('↷', on_click=self.redo, color=None).classes('terminal-button').props('aria-label="Redo move" title="Redo move"')
            self.history_back_button = ui.button('←', on_click=lambda: self.step_history(-1), color=None).classes('terminal-button').props('aria-label="Previous move in history" title="Previous move in history"')
            self.history_forward_button = ui.button('→', on_click=lambda: self.step_history(1), color=None).classes('terminal-button').props('aria-label="Next move in history" title="Next move in history"')
            with ui.button('', on_click=self.show_analysis, color=None).classes('terminal-button analysis-button').props('aria-label="Analysis"'):
                ui.html('''<svg class="analysis-icon" viewBox="0 0 56 28" aria-hidden="true"><path d="M8 19 15 10M21 10l7 8M34 18l9-11"/><circle cx="5" cy="22" r="2.5"/><circle cx="18" cy="6" r="2.8"/><circle cx="31" cy="21" r="2.5"/><circle cx="47" cy="5" r="2.8"/></svg>''')
            self.undo_button.set_enabled(bool(self.position.board.move_stack))
            self.redo_button.set_enabled(bool(self.position.redo_stack))
            self.history_back_button.set_enabled(bool(self.position.board.move_stack))
            self.history_forward_button.set_enabled(False)

    def show_analysis(self) -> None:
        evaluations = latest_game_evaluations()
        if not evaluations:
            ui.notify('Run a game. Last game log not available', type='warning')
            return
        with ui.dialog() as dialog, ui.card().classes('analysis-card'):
            with ui.row().classes('analysis-heading'):
                with ui.column().classes('analysis-title'):
                    ui.label('Game Evaluation · last game').classes('panel-kicker')
                    ui.label(latest_game_players()).classes('analysis-meta')
                ui.button('CLOSE', on_click=dialog.close, color=None).classes('terminal-button analysis-close')
            ui.html(evaluation_chart_svg(evaluations)).classes('analysis-chart')
        dialog.open()

    def render_evaluation(self) -> None:
        with ui.element('div').classes('eval-bar').props('role="meter" aria-label="Position evaluation" aria-valuemin="0" aria-valuemax="100"') as self.eval_bar:
            self.eval_fill = ui.element('div').classes('eval-white')
        self.sync()

    def render_status(self) -> None:
        ui.label('SYSTEM STATUS').classes('panel-kicker')
        self.status_label = ui.label(self.position.status()).classes('status-text').props('role="status" aria-live="polite"')

    def render_controls(self, header_actions=None) -> None:
        if self.status_label is None:
            self.render_status()
        with ui.element('div').classes('move-analysis-heading'):
            ui.label('Move Analysis')
            self.analysis_engine_label = ui.label('STOCKFISH').classes('analysis-engine').props('aria-busy="false"')
        self.move_analysis_panel = ui.element('div').classes('move-analysis-panel')
        if not self.analysis_busy:
            self.render_move_analysis(self.preview_board or self.position.board)
            self.analysis_position = (self.preview_board or self.position.board).fen()
        with ui.tabs().classes('evaluation-plot-heading evaluation-tabs').props('dense no-caps align=left') as tabs:
            evaluation_tab = ui.tab('Evaluation Plot')
            predictions_tab = ui.tab('Jev Predictions')
        with ui.element('div').classes('move-placeholder-panel'):
            with ui.tab_panels(tabs, value=evaluation_tab).classes('evaluation-panels').props('keep-alive'):
                with ui.tab_panel(evaluation_tab).classes('evaluation-tab-panel').props('aria-label="Live evaluation plot"'):
                    self.evaluation_plot = ui.html('').classes('live-evaluation-chart')
                with ui.tab_panel(predictions_tab).classes('evaluation-tab-panel'):
                    pass
        if not self.analysis_busy:
            self.sync_evaluation_plot(self.preview_board or self.position.board)
        with ui.element('div').classes('history-heading'):
            ui.label('Move Log')
        with ui.element('div').classes('move-history-panel'):
            self.history_panel = ui.element('div').classes('move-history')
        self.render_history()
        with header_actions or ui.element('div'):
            ui.button('NEW GAME', on_click=self.new_game, color=None).classes('terminal-button new-game-button')
            if all(player != 'human' for player in self.players.values()):
                self.random_timer = ui.timer(0.6, self.automatic_turn, active=False)
                self.random_button = ui.button('START', on_click=self.toggle_random, color=None).classes('terminal-button')
            elif header_actions is not None:
                ui.button('START', color=None).classes('terminal-button').style('visibility: hidden').props('aria-hidden="true" tabindex=-1').disable()
        self.claim_button = ui.button('CLAIM DRAW', on_click=self.claim_draw).classes('terminal-button claim-button')
        self.claim_button.visible = not self.position.outcome() and self.position.board.can_claim_draw()
        with ui.dialog().props('persistent') as self.promotion_dialog, ui.card().classes('promotion-card'):
            ui.label('CHOOSE PROMOTION').classes('panel-kicker')
            with ui.row().classes('promotion-actions'):
                for piece_type in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
                    ui.button(chess.piece_name(piece_type).title(), on_click=lambda _, piece_type=piece_type: self.choose_promotion(piece_type)).classes('terminal-button')

    def render_move_analysis(self, board: chess.Board, result=None) -> None:
        self.move_analysis_panel.clear()
        if not board.move_stack:
            return
        previous_position = board.copy(stack=True)
        played = previous_position.pop()
        played_san = previous_position.san(played)
        prefix = f'{previous_position.fullmove_number}.' if previous_position.turn else f'{previous_position.fullmove_number}...'
        alternatives, played_score, loss = result if result is not None else self.cached_move_analysis(board)

        def evaluation_text(score: chess.engine.Score) -> str:
            cp = score.score()
            if cp is not None and abs(cp) < 10:
                return 'Equal'
            side = 'White' if score > chess.engine.Cp(0) else 'Black'
            return f'{side} +{abs(cp) / 100:.2f}' if cp is not None else f'{side} #{abs(score.mate())}'

        with self.move_analysis_panel:
            ui.label(f'Position before {prefix} {played_san}').classes('move-analysis-context')
            with ui.element('div').classes('played-move-card'):
                with ui.element('div').classes('move-analysis-detail'):
                    ui.label(f'Played by {chess.COLOR_NAMES[previous_position.turn]} ({self.players[previous_position.turn].title()})').classes('move-analysis-context')
                    ui.label(played_san).classes('played-move-name')
                with ui.element('div').classes('move-analysis-detail'):
                    ui.label('Eval after move')
                    ui.label(evaluation_text(played_score))
                with ui.element('div').classes('move-analysis-detail'):
                    ui.label('Eval loss')
                    ui.label(f'{loss:.2f} pawns' if loss is not None else 'N/A (mate score)').classes('played-move-name')
            ui.label('Best alternatives').classes('move-analysis-context')
            with ui.element('div').classes('move-alternatives'):
                for rank, (move, score) in enumerate(alternatives, 1):
                    with ui.element('div').classes('move-alternative' + (' played-alternative' if move == played_san else '')):
                        ui.label(f'{rank}.').classes('move-analysis-context')
                        ui.label(move)
                        expectation = score.wdl(ply=previous_position.ply()).expectation()
                        if not previous_position.turn:
                            expectation = 1 - expectation
                        with ui.element('div').classes('move-alternative-bar').props('title="Mover expected score"'):
                            ui.element('div').classes('move-alternative-fill').style(f'width: {expectation * 100:.1f}%')
                        ui.label(evaluation_text(score))

    def render_history(self) -> None:
        self.history_panel.clear()
        self.history_labels = []
        current_index = len(self.position.board.move_stack) if self.preview_index is None else self.preview_index
        with self.history_panel:
            lines = move_history_lines(self.position.board)
            if not lines:
                self.history_labels.append(ui.label('No moves yet').classes('move-history-entry'))
            for index, line in enumerate(lines, 1):
                label = ui.button(line, on_click=lambda _, index=index: self.select_history(index), color=None).props('no-caps unelevated').classes('move-history-entry')
                label.style(f'grid-column: {2 if "..." in line.split()[0] else 1}')
                if index == current_index:
                    label.classes('current-move').props('aria-current="step"')
                self.history_labels.append(label)
