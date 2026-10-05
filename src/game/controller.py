import chess
import chess.engine
import os
import random
import shutil
import sys
from typesafe_sdk import Choice, TypeSafeClient

from src.game.position import Position


def stockfish_path() -> str | None:
    path = shutil.which('stockfish')
    if path:
        return path
    if sys.platform.startswith('linux') and os.access('/usr/games/stockfish', os.X_OK):
        return '/usr/games/stockfish'
    return None


class GameController:
    def __init__(self, position: Position | None = None) -> None:
        self.position = position if position is not None else Position()
        self.engine: chess.engine.SimpleEngine | None = None
        self.last_jev_prediction: list[tuple[str, str, float, bool]] = []
        self.last_jev_confidence = 0.0

    def stockfish_engine(self) -> chess.engine.SimpleEngine:
        if self.engine is None:
            self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path() or 'stockfish')
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
        move = engine.play(self.position.board, chess.engine.Limit(depth=18)).move
        return self.play(move)

    def play_jev_move(self) -> bool:
        board = self.position.board
        if self.position.outcome():
            return False
        api_key = os.getenv('JEV_API_KEY')
        if not api_key:
            raise RuntimeError('JEV_API_KEY is not set')
        legal_moves = list(board.legal_moves)
        criteria = {move.uci(): board.san(move) for move in legal_moves}
        question = Choice(
            instructions='Choose the best chess move for the player to move for the given FEN state.',
            criteria=criteria,
        )
        with TypeSafeClient(api_key=api_key) as client:
            response = client.system_one(state={'fen': board.fen()}, questions={'move': question})
        answer = response.answers['move']
        selected = chess.Move.from_uci(answer.choice)
        if selected not in legal_moves:
            raise RuntimeError(f'Jev selected an illegal move: {selected.uci()}')
        self.last_jev_prediction = [
            (uci, criteria[uci], probability, uci == answer.choice)
            for uci, probability in sorted(
                ((uci, probability) for uci, probability in answer.probabilities.items() if uci in criteria),
                key=lambda item: item[1], reverse=True,
            )[:5]
        ]
        self.last_jev_confidence = answer.confidence
        return self.play(selected)
