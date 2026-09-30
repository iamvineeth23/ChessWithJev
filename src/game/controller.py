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

    def analysis_engine(self) -> chess.engine.SimpleEngine:
        engine = self.stockfish_engine()
        engine.configure({'UCI_LimitStrength': False, 'Skill Level': 20})
        return engine

    def white_expectation(self, board: chess.Board | None = None) -> float:
        board = board if board is not None else self.position.board
        outcome = self.position.outcome() if board is self.position.board else board.outcome()
        if outcome:
            return 0.5 if outcome.winner is None else float(outcome.winner)
        info = self.analysis_engine().analyse(board, chess.engine.Limit(depth=18))
        return info['score'].white().wdl().expectation()

    def top_moves(self, board: chess.Board | None = None) -> list[tuple[str, str]]:
        board = board if board is not None else self.position.board
        if board.outcome():
            return []
        return [(board.san(info['pv'][0]), str(info['score'].white()))
                for info in self.analysis_engine().analyse(board, chess.engine.Limit(depth=18), multipv=5)
                if info.get('pv')]

    def move_analysis(self, board: chess.Board) -> tuple[list[tuple[str, chess.engine.Score]], chess.engine.Score, float | None]:
        previous = board.copy(stack=True)
        played = previous.pop()
        engine = self.analysis_engine()
        options = [info for info in engine.analyse(previous, chess.engine.Limit(depth=18), multipv=5)
                   if info.get('pv')]
        played_info = next((info for info in options if info['pv'][0] == played), None)
        if played_info is None:
            played_info = engine.analyse(previous, chess.engine.Limit(depth=18), root_moves=[played])
        played_score = played_info['score'].white()
        alternatives = [(previous.san(info['pv'][0]), info['score'].white()) for info in options]
        best_cp = options[0]['score'].pov(previous.turn).score() if options else None
        played_cp = played_info['score'].pov(previous.turn).score()
        loss = max(0, best_cp - played_cp) / 100 if best_cp is not None and played_cp is not None else None
        return alternatives, played_score, loss

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
