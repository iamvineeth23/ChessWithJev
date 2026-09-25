from base64 import b64encode
from functools import lru_cache

import chess
import chess.svg
from nicegui import ui

from src.game.position import Position


def square_color(row: int, column: int) -> str:
    return 'light' if (row + column) % 2 == 0 else 'dark'


def square_name(row: int, column: int) -> str:
    return f'{chr(ord("a") + column)}{8 - row}'


@lru_cache(maxsize=12)
def piece_image(piece: chess.Piece) -> str:
    svg = chess.svg.piece(piece).encode()
    return f'data:image/svg+xml;base64,{b64encode(svg).decode()}'


def move_history(board: chess.Board) -> str:
    replay = board.root()
    lines = []
    for move in board.move_stack:
        prefix = f'{replay.fullmove_number}.' if replay.turn else f'{replay.fullmove_number}...'
        lines.append(f'{prefix} {replay.san(move)}')
        replay.push(move)
    return '\n'.join(lines) or 'No moves yet'


class BoardView:
    def __init__(self, position: Position | None = None) -> None:
        self.position = position or Position()
        self.selected: chess.Square | None = None
        self.pending_promotion: tuple[chess.Square, chess.Square] | None = None
        self.promotion_dialog = None
        self.status_label = None
        self.history_label = None
        self.claim_button = None
        self.squares = {}
        self.shown_pieces: dict[chess.Square, chess.Piece | None] = {}

    def set_fen(self, fen: str) -> None:
        self.position.set_fen(fen)
        self.selected = None
        self.pending_promotion = None
        if self.promotion_dialog:
            self.promotion_dialog.close()
        self.sync()

    def set_board(self, board: chess.Board) -> None:
        self.position.set_board(board)
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
        self.position.move(source, target, promotion=piece_type)
        self.selected = None
        self.sync()

    def claim_draw(self) -> None:
        if self.position.claim_draw():
            self.selected = None
            self.sync()

    def new_game(self) -> None:
        self.set_board(chess.Board())

    def click_square(self, square: chess.Square) -> None:
        if self.position.outcome() or self.pending_promotion:
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
                self.position.move(self.selected, square)
                self.selected = None
        self.sync()

    def sync(self) -> None:
        if self.status_label:
            self.status_label.set_text(self.position.status())
        if self.history_label:
            self.history_label.set_text(move_history(self.position.board))
        if self.claim_button:
            self.claim_button.visible = not self.position.outcome() and self.position.board.can_claim_draw()
        for square, element in self.squares.items():
            element.classes(add='selected' if square == self.selected else None,
                            remove='selected' if square != self.selected else None)
            piece = self.position.board.piece_at(square)
            if piece == self.shown_pieces[square]:
                continue
            element.clear()
            if piece:
                with element:
                    ui.image(piece_image(piece)).classes('chess-piece').props(f'alt="{"white" if piece.color else "black"} {chess.piece_name(piece.piece_type)}"')
            self.shown_pieces[square] = piece

    def render(self) -> None:
        self.squares.clear()
        self.shown_pieces.clear()
        with ui.element('div').classes('chess-board').props('aria-label="Chess board"'):
            for row in range(8):
                for column in range(8):
                    square = chess.parse_square(square_name(row, column))
                    element = ui.element('div').classes(f'chess-square {square_color(row, column)}').props(f'aria-label="{square_name(row, column)}"').on('click', lambda _, square=square: self.click_square(square))
                    self.squares[square] = element
                    if square == self.selected:
                        element.classes('selected')
                    with element:
                        piece = self.position.board.piece_at(square)
                        if piece:
                            ui.image(piece_image(piece)).classes('chess-piece').props(f'alt="{"white" if piece.color else "black"} {chess.piece_name(piece.piece_type)}"')
                        self.shown_pieces[square] = piece

    def render_controls(self) -> None:
        with ui.element('div').classes('history-heading'):
            ui.label('Move History')
            self.status_label = ui.label(self.position.status()).props('role="status" aria-live="polite"')
        with ui.element('div').classes('move-history-panel'):
            self.history_label = ui.label(move_history(self.position.board)).classes('move-history')
        ui.button('New Game', on_click=self.new_game).classes('new-game-button')
        self.claim_button = ui.button('Claim draw', on_click=self.claim_draw)
        self.claim_button.visible = not self.position.outcome() and self.position.board.can_claim_draw()
        with ui.dialog().props('persistent') as self.promotion_dialog, ui.card():
            ui.label('Choose promotion')
            with ui.row():
                for piece_type in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
                    ui.button(chess.piece_name(piece_type).title(), on_click=lambda _, piece_type=piece_type: self.choose_promotion(piece_type))


def main() -> None:
    ui.add_css('''
        .game-layout { display: flex; align-items: flex-start; gap: 24px; }
        .game-controls { display: flex; flex-direction: column; justify-content: flex-end; gap: 12px; width: 260px; height: min(calc(100vw - 340px), calc(90dvh - 20px), 640px); flex-shrink: 0; }
        .history-heading { display: flex; justify-content: space-between; gap: 8px; }
        .move-history-panel { height: 190px; overflow-y: auto; border: 1px solid #bbb; padding: 8px; }
        .move-history { white-space: pre-line; overflow-wrap: anywhere; }
        .new-game-button { width: 100%; }
        .chess-layout { display: grid; grid-template-columns: 20px auto; grid-template-rows: auto 20px; width: max-content; }
        .rank-labels { display: grid; grid-template-rows: repeat(8, 1fr); }
        .file-labels { grid-column: 2; display: grid; grid-template-columns: repeat(8, 1fr); }
        .axis-label { display: flex; align-items: center; justify-content: center; font-size: 14px; line-height: 1; }
        .chess-board { display: grid; grid-template-columns: repeat(8, 1fr); width: min(calc(100vw - 340px), calc(90dvh - 20px), 640px); }
        .chess-square { aspect-ratio: 1; position: relative; }
        .chess-square.light { background: #f0d9b5; }
        .chess-square.dark { background: #b58863; }
        .chess-square.selected { outline: 4px solid #3b82f6; outline-offset: -4px; z-index: 1; }
        .chess-piece { position: absolute; inset: 5%; width: 90%; height: 90%; pointer-events: none; }
    ''')
    view = BoardView()
    with ui.element('div').classes('game-layout'):
        with ui.element('div').classes('chess-layout'):
            with ui.element('div').classes('rank-labels'):
                for rank in range(8, 0, -1):
                    ui.label(str(rank)).classes('axis-label')
            view.render()
            with ui.element('div').classes('file-labels'):
                for file in 'abcdefgh':
                    ui.label(file).classes('axis-label')
        with ui.element('div').classes('game-controls'):
            view.render_controls()
    ui.run(native=True, title='ChessWithJev')


if __name__ in {'__main__', '__mp_main__'}:
    main()
