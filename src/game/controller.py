import chess
import chess.engine
import random
import shutil

from src.game.position import Position


class GameController:
    def __init__(self, position: Position | None = None) -> None:
        self.position = position if position is not None else Position()
        self.engine: chess.engine.SimpleEngine | None = None

    def stockfish_engine(self) -> chess.engine.SimpleEngine:
        if self.engine is None:
            self.engine = chess.engine.SimpleEngine.popen_uci(shutil.which('stockfish') or 'stockfish')
        return self.engine

    def close(self) -> None:
        if self.engine is not None:
            self.engine.quit()
            self.engine = None

    def white_expectation(self, board: chess.Board | None = None) -> float:
        board = board if board is not None else self.position.board
        outcome = self.position.outcome() if board is self.position.board else board.outcome()
        if outcome:
            return 0.5 if outcome.winner is None else float(outcome.winner)
        info = self.stockfish_engine().analyse(board, chess.engine.Limit(depth=15))
        return info['score'].white().wdl().expectation()

    def play(self, move: chess.Move) -> bool:
        return self.position.move(move.from_square, move.to_square, move.promotion)

    def play_random_move(self) -> bool:
        board = self.position.board
        if self.position.outcome():
            return False
        return self.play(random.choice(list(board.legal_moves)))

    def play_random_black_move(self) -> bool:
        return self.position.board.turn == chess.BLACK and self.play_random_move()

    def play_stockfish_move(self, elo: int = 1500) -> bool:
        if self.position.outcome():
            return False
        engine = self.stockfish_engine()
        engine.configure({'UCI_LimitStrength': True, 'UCI_Elo': elo})
        move = engine.play(self.position.board, chess.engine.Limit(time=0.1)).move
        return self.play(move)
