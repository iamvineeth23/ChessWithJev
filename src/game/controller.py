import chess
import chess.engine
import random
import shutil

from src.game.position import Position


class GameController:
    def __init__(self, position: Position | None = None) -> None:
        self.position = position if position is not None else Position()

    def play(self, move: chess.Move) -> bool:
        return self.position.move(move.from_square, move.to_square, move.promotion)

    def play_random_move(self) -> bool:
        board = self.position.board
        if self.position.outcome():
            return False
        return self.play(random.choice(list(board.legal_moves)))

    def play_random_black_move(self) -> bool:
        return self.position.board.turn == chess.BLACK and self.play_random_move()

    def play_stockfish_move(self) -> bool:
        if self.position.outcome():
            return False
        with chess.engine.SimpleEngine.popen_uci(shutil.which('stockfish') or 'stockfish') as engine:
            move = engine.play(self.position.board, chess.engine.Limit(time=0.1)).move
        return self.play(move)
