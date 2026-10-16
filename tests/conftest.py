from unittest.mock import MagicMock

import chess
import chess.engine
import pytest


@pytest.fixture(autouse=True)
def mock_stockfish(monkeypatch: pytest.MonkeyPatch) -> None:
    # UI tests must not launch real engines and leave their background threads alive.
    def launch(*args, **kwargs):
        engine = MagicMock(spec=chess.engine.SimpleEngine)

        def analyse(board, limit, *, multipv=None, root_moves=None):
            moves = list(board.legal_moves) if root_moves is None else list(root_moves)
            infos = [{'pv': [move], 'score': chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE)}
                     for move in moves[:multipv or 1]]
            return infos if multipv is not None else infos[0]

        engine.analyse.side_effect = analyse
        engine.play.side_effect = lambda board, limit: chess.engine.PlayResult(next(iter(board.legal_moves)), None)
        return engine

    monkeypatch.setattr(chess.engine.SimpleEngine, 'popen_uci', launch)
