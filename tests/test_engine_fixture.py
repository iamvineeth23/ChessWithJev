import chess
import chess.engine

from src.game.controller import GameController


def test_default_engine_supports_analysis_play_and_close() -> None:
    controller = GameController()
    other = GameController()
    engine = controller.stockfish_engine()
    assert controller.stockfish_engine() is engine
    assert other.stockfish_engine() is not engine
    assert controller.white_expectation() == 0.5
    assert len(controller.top_moves()) == 5
    previous = controller.position.board.copy()
    assert controller.play_stockfish_move()
    assert controller.position.board.peek() in previous.legal_moves
    alternatives, score, loss = controller.move_analysis(controller.position.board)
    assert alternatives and score == chess.engine.Cp(0) and loss == 0
    # Exercise analysis of a played move outside the default top five.
    position = chess.Board()
    position.push_san('a3')
    assert controller.move_analysis(position)[1:] == (chess.engine.Cp(0), 0)
    controller.close()
    engine.quit.assert_called_once_with()
    assert controller.engine is None
    other.close()
