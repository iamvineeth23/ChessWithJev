import chess
import sys


class Position:
    def __init__(self) -> None:
        self.board = chess.Board()
        self.claimed_draw: chess.Outcome | None = None
        self.redo_stack: list[chess.Move] = []

    def set_fen(self, fen: str) -> None:
        self.board.set_fen(fen)
        self.claimed_draw = None
        self.redo_stack.clear()

    def set_board(self, board: chess.Board) -> None:
        self.board = board.copy()
        self.claimed_draw = None
        self.redo_stack.clear()

    def snapshot(self) -> dict[str, object]:
        return {
            'root_fen': self.board.root().fen(),
            'moves': [move.uci() for move in self.board.move_stack],
            'redo': [move.uci() for move in self.redo_stack],
            'claimed_draw': self.claimed_draw is not None,
        }

    def restore(self, snapshot: object) -> bool:
        if not isinstance(snapshot, dict):
            return False
        root_fen = snapshot.get('root_fen')
        moves = snapshot.get('moves')
        redo = snapshot.get('redo')
        if not isinstance(root_fen, str) or not isinstance(moves, list) or not isinstance(redo, list):
            return False
        try:
            board = chess.Board(root_fen)
            for encoded in moves:
                move = chess.Move.from_uci(encoded)
                if move not in board.legal_moves:
                    return False
                board.push(move)
            redo_moves = [chess.Move.from_uci(encoded) for encoded in redo]
            probe = board.copy(stack=True)
            for move in reversed(redo_moves):
                if move not in probe.legal_moves:
                    return False
                probe.push(move)
        except (TypeError, ValueError):
            return False
        self.board = board
        self.redo_stack = redo_moves
        self.claimed_draw = board.outcome(claim_draw=True) if snapshot.get('claimed_draw') else None
        return True

    def undo(self) -> bool:
        if not self.board.move_stack:
            return False
        self.claimed_draw = None
        self.redo_stack.append(self.board.pop())
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        self.board.push(self.redo_stack.pop())
        return True

    def outcome(self) -> chess.Outcome | None:
        return self.claimed_draw or self.board.outcome()

    def claim_draw(self) -> bool:
        if self.outcome() or not self.board.can_claim_draw():
            return False
        self.claimed_draw = self.board.outcome(claim_draw=True)
        return True

    def status(self) -> str:
        outcome = self.outcome()
        if outcome:
            if outcome.termination == chess.Termination.CHECKMATE:
                return f'Checkmate — {"White" if outcome.winner else "Black"} wins'
            if outcome.termination == chess.Termination.STALEMATE:
                return 'Stalemate — draw'
            reasons = {
                chess.Termination.INSUFFICIENT_MATERIAL: 'insufficient material',
                chess.Termination.FIVEFOLD_REPETITION: 'fivefold repetition',
                chess.Termination.SEVENTYFIVE_MOVES: '75-move rule',
                chess.Termination.THREEFOLD_REPETITION: 'threefold repetition',
                chess.Termination.FIFTY_MOVES: '50-move rule',
            }
            return f'Draw — {reasons[outcome.termination]}'
        return f'{"White" if self.board.turn else "Black"} to move' + (' — check' if self.board.is_check() else '')

    def print_legal_moves(self) -> None:
        print([self.board.san(move) for move in self.board.legal_moves], flush=True)

    def move(self, source: chess.Square, target: chess.Square, promotion: chess.PieceType | None = None) -> bool:
        if self.outcome():
            return False
        move = chess.Move(source, target, promotion=promotion)
        if move not in self.board.legal_moves:
            return False
        notation = self.board.san(move)
        self.board.push(move)
        self.redo_stack.clear()
        print(notation, flush=True)
        if '-d' in sys.argv[1:]:
            self.print_legal_moves()
        return True
