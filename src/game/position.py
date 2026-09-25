import chess


class Position:
    def __init__(self) -> None:
        self.board = chess.Board()

    def set_fen(self, fen: str) -> None:
        self.board.set_fen(fen)

    def set_board(self, board: chess.Board) -> None:
        self.board = board.copy()

    def move(self, source: chess.Square, target: chess.Square) -> bool:
        piece = self.board.piece_at(source)
        promotion = chess.QUEEN if piece and piece.piece_type == chess.PAWN and chess.square_rank(target) in (0, 7) else None
        move = chess.Move(source, target, promotion=promotion)
        if move not in self.board.legal_moves:
            return False
        notation = self.board.san(move)
        self.board.push(move)
        print(notation, flush=True)
        return True
