import chess

from src.game.position import Position


class GameController:
    def __init__(self, position: Position | None = None) -> None:
        self.position = position if position is not None else Position()

    def play(self, move: chess.Move) -> bool:
        return self.position.move(move.from_square, move.to_square, move.promotion)
