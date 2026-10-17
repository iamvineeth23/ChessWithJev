import asyncio
import copy
import json
from unittest.mock import AsyncMock

import chess
import chess.engine
import pytest

from src.ui import board, board_view
from src.ui.analysis_state import analysis_snapshot, decode_score, encode_score, restore_analysis


@pytest.mark.parametrize('score', [chess.engine.Cp(-123), chess.engine.Cp(0),
                                  chess.engine.Mate(3), chess.engine.Mate(-2),
                                  chess.engine.Mate(0), chess.engine.MateGiven])
def test_analysis_score_survives_json_round_trip(score):
    assert decode_score(json.loads(json.dumps(encode_score(score)))) == score


def test_restored_analysis_preserves_claimed_draw_evaluation():
    view = board_view.BoardView(white='human', black='human')
    view.position.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 100 1')
    assert view.position.claim_draw()
    assert view.cached_white_expectation(view.position.board) == 0.5
    game = json.loads(json.dumps(board.game_snapshot(view)))
    restored = board.saved_game({'game': game})
    restored_view = board_view.BoardView(position=restored[0], white='human', black='human')
    restore_analysis(restored_view, game['analysis'])
    assert restored_view.evaluation_cache == view.evaluation_cache
    assert restored_view.cached_white_expectation(restored_view.position.board) == 0.5
    assert restored_view.controller.engine is None


def test_restored_analysis_preserves_jev_predictions():
    view = board_view.BoardView(white='jev', black='human')
    view.position.board.push_uci('e2e4')
    prediction = [('e2e4', 'e4', .4, True), ('d2d4', 'd4', .3, False), ('c2c4', 'c4', .15, False)]
    view.jev_prediction_cache[(view.position.board.root().fen(), tuple(view.position.board.move_stack))] = (prediction, .72)
    game = json.loads(json.dumps(board.game_snapshot(view)))
    restored = board.saved_game({'game': game})
    restored_view = board_view.BoardView(position=restored[0], white='jev', black='human')
    restore_analysis(restored_view, game['analysis'])
    assert restored_view.jev_prediction_cache == view.jev_prediction_cache
    assert restored_view.controller.engine is None


def test_page_restore_reuses_analysis_and_computes_only_missing_entries(monkeypatch):
    callbacks = []
    monkeypatch.setattr(board, 'stockfish_path', lambda: '/mock/stockfish')
    monkeypatch.setattr(board_view.BoardView, 'schedule_update', lambda self, callback: callbacks.append(callback))
    monkeypatch.setattr(board_view.ui, 'run_javascript', AsyncMock())

    async def worker(callback, *args):
        return callback(*args)

    monkeypatch.setattr(board_view.run, 'io_bound', worker)
    original = board_view.BoardView(white='human', black='human')
    for move in ['e2e4', 'e7e5', 'g1f3']:
        original.position.board.push_uci(move)
    storage = {'game': board.game_snapshot(original)}

    def load():
        board.build_page(storage)
        callback = callbacks.pop()
        view = callback.__self__
        asyncio.run(callback())
        return view

    first = load()
    assert first.controller.engine is not None
    assert len(first.evaluation_cache) == 4
    assert len(first.move_analysis_cache) == 3
    # Analysis must be saved after the worker finishes, not just before it starts.
    storage['game'] = json.loads(json.dumps(storage['game']))
    restored = load()
    assert restored.controller.engine is None
    assert restored.evaluation_cache == first.evaluation_cache
    assert restored.move_analysis_cache == first.move_analysis_cache
    assert restored.evaluation_plot.content == first.evaluation_plot.content

    storage['game']['analysis']['positions'][1]['expectation'] = None
    partial = load()
    partial.controller.engine.analyse.assert_called_once()
    assert partial.evaluation_cache == first.evaluation_cache

    del storage['game']['analysis']
    legacy = load()
    assert legacy.controller.engine is not None
    assert legacy.move_analysis_cache == first.move_analysis_cache


@pytest.mark.parametrize('damage', ['version', 'root', 'moves', 'claim', 'positions',
                                   'expectation', 'score', 'alternatives', 'loss',
                                   'prediction', 'probability', 'confidence', 'selected'])
def test_invalid_saved_analysis_is_ignored(damage):
    view = board_view.BoardView(white='human', black='human')
    view.position.board.push_uci('e2e4')
    view.cached_white_expectation(view.position.board)
    view.cached_move_analysis(view.position.board)
    view.jev_prediction_cache[(view.position.board.root().fen(), tuple(view.position.board.move_stack))] = (
        [('e2e4', 'e4', .4, True)], .25)
    snapshot = copy.deepcopy(analysis_snapshot(view))
    if damage == 'version':
        snapshot['version'] = 99
    elif damage == 'root':
        snapshot['root_fen'] = 'different'
    elif damage == 'moves':
        snapshot['moves'] = ['d2d4']
    elif damage == 'claim':
        snapshot['claimed_draw'] = 'different'
    elif damage == 'positions':
        snapshot['positions'] = []
    elif damage == 'expectation':
        snapshot['positions'][1]['expectation'] = float('nan')
    elif damage == 'score':
        snapshot['positions'][1]['analysis']['score'] = ['invalid', 0]
    elif damage == 'alternatives':
        snapshot['positions'][1]['analysis']['alternatives'] = [['invalid', ['cp', 0]]]
    elif damage == 'loss':
        snapshot['positions'][1]['analysis']['loss'] = -1
    elif damage == 'prediction':
        snapshot['positions'][1]['predictions']['moves'] = [[None, 'e4', 1.0, True]]
    elif damage == 'probability':
        snapshot['positions'][1]['predictions']['moves'][0][2] = 2
    elif damage == 'confidence':
        snapshot['positions'][1]['predictions']['confidence'] = -1
    else:
        snapshot['positions'][1]['predictions']['moves'][0][3] = 'yes'
    view.evaluation_cache.clear()
    view.move_analysis_cache.clear()
    view.jev_prediction_cache.clear()
    restore_analysis(view, snapshot)
    if damage in {'score', 'alternatives', 'loss'}:
        assert not view.move_analysis_cache
        assert view.evaluation_cache
        assert view.jev_prediction_cache
    elif damage == 'expectation':
        assert not view.evaluation_cache
        assert view.move_analysis_cache
        assert view.jev_prediction_cache
    elif damage in {'prediction', 'probability', 'confidence', 'selected'}:
        assert not view.jev_prediction_cache
        assert view.evaluation_cache and view.move_analysis_cache
    else:
        assert not view.evaluation_cache and not view.move_analysis_cache
        assert not view.jev_prediction_cache
