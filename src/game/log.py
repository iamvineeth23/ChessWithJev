from datetime import date
import json
from pathlib import Path

import chess


def write_game_log(board: chess.Board, players: dict[chess.Color, str], elos: dict[chess.Color, int], evaluate, recording: bool = False) -> Path:
    replay = board.root()
    moves = []
    for ply, move in enumerate(board.move_stack, 1):
        moves.append({
            'ply': ply,
            'move_number': replay.fullmove_number,
            'color': 'white' if replay.turn else 'black',
            'fen_before': replay.fen(),
            'legal_moves': [replay.san(legal_move) for legal_move in replay.legal_moves],
            'move': replay.san(move),
            'fen_after': '',
            'evaluation': {'wdl_expectation_white': None},
        })
        replay.push(move)
        moves[-1]['fen_after'] = replay.fen()
        moves[-1]['evaluation']['wdl_expectation_white'] = evaluate(replay)

    outcome = board.outcome(claim_draw=True)
    assert outcome is not None
    result = '1/2-1/2' if outcome.winner is None else ('1-0' if outcome.winner else '0-1')
    log_dir = Path(__file__).resolve().parents[2] / 'gamelog'
    if not recording:
        path = log_dir / 'latest.json'
    else:
        log_dir /= 'rec'
        game_id = date.today().isoformat()
        sequence = 1
        while (log_dir / f'{game_id}_{sequence:03d}.json').exists():
            sequence += 1
        path = log_dir / f'{game_id}_{sequence:03d}.json'
    log_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        'game_id': path.stem,
        'players': {
            color: {'type': players[value], 'elo': elos[value] if players[value] == 'stockfish' else None, 'model': None}
            for color, value in (('white', chess.WHITE), ('black', chess.BLACK))
        },
        'result': {
            'winner': None if outcome.winner is None else ('white' if outcome.winner else 'black'),
            'score': result,
            'termination': outcome.termination.name.lower(),
        },
        'evaluator': {'engine': 'stockfish', 'depth': 15},
        'moves': moves,
    }
    path.write_text(json.dumps(payload, indent=2) + '\n')
    return path
