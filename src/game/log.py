from datetime import date
import json
from pathlib import Path

import chess
import chess.pgn


def export_pgn(board: chess.Board, players: dict[chess.Color, str] | None = None) -> str:
    game = chess.pgn.Game.from_board(board)
    game.headers.update(Event='ChessWithJev', Site='ChessWithJev',
                        Date=date.today().strftime('%Y.%m.%d'), Round='01')
    if players is not None:
        game.headers.update(White=players[chess.WHITE].title(), Black=players[chess.BLACK].title())
    return str(game)


def write_pgn(board: chess.Board, path: Path | None = None, *, players: dict[chess.Color, str] | None = None) -> Path:
    if path is None:
        log_dir = Path(__file__).resolve().parents[2] / 'gamelog' / 'pgn'
        game_id = date.today().isoformat()
        sequence = 1
        while (log_dir / f'{game_id}_{sequence:03d}.pgn').exists():
            sequence += 1
        path = log_dir / f'{game_id}_{sequence:03d}.pgn'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'{export_pgn(board, players)}\n')
    return path


def write_game_log(board: chess.Board, players: dict[chess.Color, str], elos: dict[chess.Color, int], evaluate, save_copy: bool = False, *, mirror_latest: bool = True, jev_confidences: dict[tuple[str, tuple[chess.Move, ...]], float] | None = None,
                   stockfish_top_moves: dict[tuple[str, tuple[chess.Move, ...]], list] | None = None,
                   jev_top_moves: dict[tuple[str, tuple[chess.Move, ...]], list] | None = None) -> Path:
    # jev_confidences maps (root fen, move stack including Jev's move) to the confidence
    # Jev had in that Choice, keyed exactly like BoardView.jev_prediction_cache.
    # stockfish_top_moves maps the same key shape to the serialized top-5 alternatives shown in
    # the Move Analysis tab for that move, keyed like BoardView.move_analysis_cache.
    # jev_top_moves maps the same key shape to Jev's serialized top-5 recommendations,
    # keyed like BoardView.jev_prediction_cache.
    replay = board.root()
    root_fen = replay.fen()
    moves = []
    for ply, move in enumerate(board.move_stack, 1):
        mover = players.get(chess.WHITE if replay.turn else chess.BLACK)
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
        if stockfish_top_moves is not None:
            moves[-1]['stockfish_top_moves'] = stockfish_top_moves.get((root_fen, tuple(replay.move_stack)))
        if mover == 'jev' and jev_confidences is not None:
            confidence = jev_confidences.get((root_fen, tuple(replay.move_stack)))
            moves[-1]['confidence'] = None if confidence is None else float(confidence)
        if mover == 'jev' and jev_top_moves is not None:
            moves[-1]['jev_top_moves'] = jev_top_moves.get((root_fen, tuple(replay.move_stack)))

    outcome = board.outcome(claim_draw=True)
    result = None if outcome is None else ('1/2-1/2' if outcome.winner is None else ('1-0' if outcome.winner else '0-1'))
    log_dir = Path(__file__).resolve().parents[2] / 'gamelog'
    if not save_copy:
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
            'winner': None if outcome is None or outcome.winner is None else ('white' if outcome.winner else 'black'),
            'score': result,
            'termination': outcome.termination.name.lower() if outcome else None,
        },
        'evaluator': {'engine': 'stockfish', 'depth': 18},
        'moves': moves,
    }
    path.write_text(json.dumps(payload, indent=2) + '\n')
    if save_copy and mirror_latest:
        (log_dir.parent / 'latest.json').write_text(json.dumps(payload, indent=2) + '\n')
    return path
