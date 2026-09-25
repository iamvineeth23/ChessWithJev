import chess


class Position:
    def __init__(self) -> None:
        self.board = chess.Board()
        self.claimed_draw: chess.Outcome | None = None

    def set_fen(self, fen: str) -> None:
        self.board.set_fen(fen)
        self.claimed_draw = None

    def set_board(self, board: chess.Board) -> None:
        self.board = board.copy()
        self.claimed_draw = None

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

    def move(self, source: chess.Square, target: chess.Square, promotion: chess.PieceType | None = None) -> bool:
        if self.outcome():
            return False
        move = chess.Move(source, target, promotion=promotion)
        if move not in self.board.legal_moves:
            return False
        notation = self.board.san(move)
        self.board.push(move)
        print(notation, flush=True)
        return True
