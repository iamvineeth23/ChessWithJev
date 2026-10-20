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


def test_restored_analysis_preserves_jev_predictions_for_redo_continuation():
    # Undo retains moves for Redo, so their predictions must survive a snapshot round trip.
    view = board_view.BoardView(white='jev', black='human')
    view.position.board.push_uci('e2e4')
    view.jev_prediction_cache[(view.position.board.root().fen(), tuple(view.position.board.move_stack))] = (
        [('e2e4', 'e4', .4, True), ('d2d4', 'd4', .3, False)], .72)
    assert view.position.undo()
    assert view.position.redo_stack == [chess.Move.from_uci('e2e4')]

    game = json.loads(json.dumps(board.game_snapshot(view)))
    assert game['analysis']['redo'] == ['e2e4']
    restored = board.saved_game({'game': game})
    assert restored[0].redo_stack == [chess.Move.from_uci('e2e4')]
    restored_view = board_view.BoardView(position=restored[0], white='jev', black='human')
    restore_analysis(restored_view, game['analysis'])
    assert restored_view.jev_prediction_cache == view.jev_prediction_cache
    assert restored_view.position.redo()
    assert restored_view.position.board.move_stack == [chess.Move.from_uci('e2e4')]
    assert restored_view.controller.engine is None


def test_restored_analysis_accepts_snapshots_without_redo_entries():
    # Snapshots from before the redo continuation existed remain valid: they cover the
    # live move stack only and restore exactly like they always did.
    view = board_view.BoardView(white='jev', black='human')
    view.position.board.push_uci('e2e4')
    view.jev_prediction_cache[(view.position.board.root().fen(), tuple(view.position.board.move_stack))] = (
        [('e2e4', 'e4', .4, True)], .72)
    snapshot = copy.deepcopy(analysis_snapshot(view))
    del snapshot['redo']
    view.jev_prediction_cache.clear()
    restore_analysis(view, snapshot)
    assert view.jev_prediction_cache == {(view.position.board.root().fen(), (chess.Move.from_uci('e2e4'),)):
                                        ([('e2e4', 'e4', .4, True)], .72)}


def test_restored_analysis_ignores_snapshot_redo_mismatch():
    # A stored continuation that does not match the retained redo stack must not be applied.
    view = board_view.BoardView(white='jev', black='human')
    view.position.board.push_uci('e2e4')
    view.jev_prediction_cache[(view.position.board.root().fen(), tuple(view.position.board.move_stack))] = (
        [('e2e4', 'e4', .4, True)], .72)
    assert view.position.undo()
    snapshot = copy.deepcopy(analysis_snapshot(view))
    snapshot['redo'] = ['d7d5']
    view.evaluation_cache.clear()
    view.move_analysis_cache.clear()
    view.jev_prediction_cache.clear()
    restore_analysis(view, snapshot)
    assert not view.evaluation_cache and not view.move_analysis_cache and not view.jev_prediction_cache


@pytest.mark.parametrize('undo', [False, True])
def test_best_post_move_evaluation_survives_restore_without_engine_calls(undo):
    from nicegui import ui
    view = board_view.BoardView(white='human', black='human')
    view.position.board.push_san('h4')
    root = view.position.board.root().fen()
    played = (chess.Move.from_uci('h2h4'),)
    best = (chess.Move.from_uci('d2d4'),)
    view.move_analysis_cache[(root, played)] = ([('d4', chess.engine.Cp(999))], chess.engine.Cp(0), 0)
    view.evaluation_cache = {(root, (), 'None'): .5, (root, played, 'None'): .4,
                             (root, best, 'None'): .6}
    if undo:
        view.position.undo()
    game = json.loads(json.dumps(board.game_snapshot(view)))
    position, *_ = board.saved_game({'game': game})
    restored = board_view.BoardView(position=position, white='human', black='human')
    restore_analysis(restored, game['analysis'])
    assert restored.evaluation_cache == view.evaluation_cache
    if undo:
        restored.position.redo()
    restored.evaluation_plot = ui.html('')
    restored.sync_evaluation_plot(restored.position.board)
    assert restored.controller.engine is None
    assert restored.evaluation_plot.content == board.evaluation_chart_svg([0, -20], compact=True, recommended=[0, 20])


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
    assert len(first.evaluation_cache) == 7
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
                                   'prediction', 'probability', 'confidence', 'selected',
                                   'uci', 'legal', 'notation', 'chosen'])
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
    elif damage == 'uci':
        snapshot['positions'][1]['predictions']['moves'] = [['not-a-move', 'e4', 1.0, True]]
    elif damage == 'legal':
        snapshot['positions'][1]['predictions']['moves'] = [['e2e5', 'e4', 1.0, True]]
    elif damage == 'notation':
        snapshot['positions'][1]['predictions']['moves'] = [['e2e4', 'd4', 1.0, True]]
    elif damage == 'chosen':
        snapshot['positions'][1]['predictions']['moves'] = [['e2e4', 'e4', .4, False], ['d2d4', 'd4', .3, True]]
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
    elif damage in {'prediction', 'probability', 'confidence', 'selected',
                    'uci', 'legal', 'notation', 'chosen'}:
        assert not view.jev_prediction_cache
        assert view.evaluation_cache and view.move_analysis_cache
    else:
        assert not view.evaluation_cache and not view.move_analysis_cache
        assert not view.jev_prediction_cache
