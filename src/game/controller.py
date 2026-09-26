import chess
import random

from src.game.position import Position


class GameController:
    def __init__(self, position: Position | None = None) -> None:
        self.position = position if position is not None else Position()

    def play(self, move: chess.Move) -> bool:
        return self.position.move(move.from_square, move.to_square, move.promotion)

    def play_random_black_move(self) -> bool:
        board = self.position.board
        if board.turn != chess.BLACK or self.position.outcome():
            return False
        return self.play(random.choice(list(board.legal_moves)))
