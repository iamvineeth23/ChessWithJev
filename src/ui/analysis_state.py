import math

import chess
import chess.engine


def encode_score(score: chess.engine.Score) -> list:
    if score == chess.engine.MateGiven:
        return ['mate_given', 0]
    return ['cp', score.score()] if score.score() is not None else ['mate', score.mate()]


def decode_score(value) -> chess.engine.Score:
    kind, number = value
    if type(number) is not int:
        raise ValueError('Invalid score')
    if kind == 'cp':
        return chess.engine.Cp(number)
    if kind == 'mate':
        return chess.engine.Mate(number)
    if kind == 'mate_given' and number == 0:
        return chess.engine.MateGiven
    raise ValueError('Invalid score')


def analysis_snapshot(view) -> dict:
    board = view.position.board
    replay = board.root()
    root = replay.fen()
    positions = []
    for ply in range(len(board.move_stack) + 1):
        if ply:
            replay.push(board.move_stack[ply - 1])
        key = (root, tuple(replay.move_stack))
        claim = view.position.claimed_draw if ply == len(board.move_stack) else None
        entry = {'expectation': view.evaluation_cache.get((*key, str(claim)))}
        if key in view.move_analysis_cache:
            alternatives, score, loss = view.move_analysis_cache[key]
            entry['analysis'] = {
                'alternatives': [[san, encode_score(value)] for san, value in alternatives],
                'score': encode_score(score), 'loss': loss,
            }
        positions.append(entry)
    # Bump the version when analysis settings (depth 18, MultiPV 5) or score format change.
    return {'version': 1, 'root_fen': root, 'moves': [move.uci() for move in board.move_stack],
            'claimed_draw': str(view.position.claimed_draw), 'positions': positions}


def restore_analysis(view, snapshot) -> None:
    board = view.position.board
    if (not isinstance(snapshot, dict) or snapshot.get('version') != 1
            or snapshot.get('root_fen') != board.root().fen()
            or snapshot.get('moves') != [move.uci() for move in board.move_stack]
            or snapshot.get('claimed_draw') != str(view.position.claimed_draw)):
        return
    positions = snapshot.get('positions')
    if not isinstance(positions, list) or len(positions) != len(board.move_stack) + 1:
        return
    replay = board.root()
    for ply, entry in enumerate(positions):
        if ply:
            replay.push(board.move_stack[ply - 1])
        if not isinstance(entry, dict):
            continue
        key = (board.root().fen(), tuple(replay.move_stack))
        expectation = entry.get('expectation')
        if type(expectation) in (int, float) and 0 <= expectation <= 1:
            claim = view.position.claimed_draw if ply == len(board.move_stack) else None
            view.evaluation_cache[(*key, str(claim))] = expectation
        if not ply or 'analysis' not in entry:
            continue
        try:
            analysis = entry['analysis']
            alternatives = []
            previous = replay.copy(stack=True)
            previous.pop()
            for san, value in analysis['alternatives']:
                if not isinstance(san, str):
                    raise ValueError('Invalid alternative')
                previous.parse_san(san)
                alternatives.append((san, decode_score(value)))
            score = decode_score(analysis['score'])
            loss = analysis['loss']
            if loss is not None and (type(loss) not in (int, float) or not math.isfinite(loss) or loss < 0):
                raise ValueError('Invalid loss')
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        view.move_analysis_cache[key] = (alternatives, score, loss)
