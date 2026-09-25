import chess


_STARTING_PIECES = chess.Board().piece_map()


def starting_piece(square: str) -> chess.Piece | None:
    return _STARTING_PIECES.get(chess.parse_square(square))
