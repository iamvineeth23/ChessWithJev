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
    # Undo keeps undone moves in position.redo_stack for Redo; snapshot analysis along that
    # retained continuation too, so a page restore does not lose Jev predictions for them.
    continuation = list(board.move_stack) + list(reversed(view.position.redo_stack))
    live = len(board.move_stack)
    positions = []
    for ply in range(len(continuation) + 1):
        if ply:
            replay.push(continuation[ply - 1])
        key = (root, tuple(replay.move_stack))
        claim = view.position.claimed_draw if ply == live else None
        entry = {'expectation': view.evaluation_cache.get((*key, str(claim)))}
        if key in view.move_analysis_cache:
            alternatives, score, loss = view.move_analysis_cache[key]
            entry['analysis'] = {
                'alternatives': [[san, encode_score(value)] for san, value in alternatives],
                'score': encode_score(score), 'loss': loss,
            }
        if key in view.jev_prediction_cache:
            predictions, confidence = view.jev_prediction_cache[key]
            entry['predictions'] = {
                'moves': [[uci, san, probability, selected] for uci, san, probability, selected in predictions],
                'confidence': confidence,
            }
        positions.append(entry)
    # Bump the version when analysis settings (depth 18, MultiPV 5) or score format change. New
    # optional entries (predictions, redo continuation) stay on the same version because old
    # snapshots remain valid.
    return {'version': 1, 'root_fen': root, 'moves': [move.uci() for move in board.move_stack],
            'redo': [move.uci() for move in reversed(view.position.redo_stack)],
            'claimed_draw': str(view.position.claimed_draw), 'positions': positions}


def restore_analysis(view, snapshot) -> None:
    board = view.position.board
    if (not isinstance(snapshot, dict) or snapshot.get('version') != 1
            or snapshot.get('root_fen') != board.root().fen()
            or snapshot.get('moves') != [move.uci() for move in board.move_stack]
            or snapshot.get('claimed_draw') != str(view.position.claimed_draw)):
        return
    positions = snapshot.get('positions')
    if not isinstance(positions, list):
        return
    # Snapshots may also cover the retained redo continuation (Undo then a page restore), so
    # predictions for those moves come back when they are redone; the stored redo must match
    # the redostack that survived the position restore.
    continuation = list(board.move_stack)
    redo = list(reversed(view.position.redo_stack))
    if (len(positions) == len(continuation) + len(redo) + 1
            and snapshot.get('redo') == [move.uci() for move in redo]):
        continuation += redo
    elif len(positions) != len(continuation) + 1:
        return
    replay = board.root()
    for ply, entry in enumerate(positions):
        if ply:
            replay.push(continuation[ply - 1])
        if not isinstance(entry, dict):
            continue
        key = (board.root().fen(), tuple(replay.move_stack))
        expectation = entry.get('expectation')
        if type(expectation) in (int, float) and 0 <= expectation <= 1:
            claim = view.position.claimed_draw if ply == len(board.move_stack) else None
            view.evaluation_cache[(*key, str(claim))] = expectation
        if not ply:
            continue
        if 'analysis' in entry:
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
                alternatives = None
            if alternatives is not None:
                view.move_analysis_cache[key] = (alternatives, score, loss)
        if 'predictions' in entry:
            try:
                moves = entry['predictions']['moves']
                if not isinstance(moves, list) or not moves:
                    raise ValueError('Invalid predictions')
                previous = replay.copy(stack=True)
                previous.pop()
                played_move = replay.move_stack[-1]
                parsed = []
                for uci, san, probability, selected in moves:
                    if (not isinstance(uci, str) or not isinstance(san, str)
                            or type(probability) not in (int, float) or not math.isfinite(probability)
                            or not 0 <= probability <= 1 or type(selected) is not bool):
                        raise ValueError('Invalid prediction')
                    move = chess.Move.from_uci(uci)  # raises ValueError for malformed UCI
                    if move not in previous.legal_moves or previous.san(move) != san:
                        # The UCI must be a legal move and the SAN must describe that same move,
                        # so damaged storage cannot swap in moves Jev did not predict.
                        raise ValueError('Invalid prediction move')
                    if selected and move != played_move:
                        # Only the actually played continuation move may be flagged selected.
                        raise ValueError('Invalid prediction selection')
                    parsed.append((uci, san, float(probability), selected))
                confidence = entry['predictions']['confidence']
                if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
                    raise ValueError('Invalid confidence')
            except (KeyError, TypeError, ValueError, OverflowError):
                parsed = None
            if parsed is not None:
                view.jev_prediction_cache[key] = (parsed, float(confidence))
