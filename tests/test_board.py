import runpy
from base64 import b64decode
import chess
import chess.engine
import pytest
from src.game.position import Position
from src.game.controller import GameController
from src.ui.board import BoardView, lock_window_aspect_ratio, move_history, piece_image, square_color, square_name
from src.ui import board
from unittest.mock import MagicMock, patch


def test_board_colors() -> None:
    colors = [[square_color(row, column) for column in range(8)] for row in range(8)]
    assert all(colors[row][column] != colors[row][column + 1] for row in range(8) for column in range(7))
    assert all(colors[row][column] != colors[row + 1][column] for row in range(7) for column in range(8))
    assert colors[0][0] == colors[7][7] == 'light'
    assert colors[7][0] == 'dark'  # a1


@pytest.mark.parametrize('debug', [False, True])
def test_board_opens_native_window(debug: bool) -> None:
    with patch.object(board.sys, 'argv', ['chess', '-d'] if debug else ['chess']), patch.object(board.ui, 'add_body_html') as add_body_html, patch.object(board.ui, 'add_css'), patch.object(board.ui, 'element', return_value=MagicMock()), patch.object(board.ui, 'label') as label, patch.object(board.ui, 'image') as image, patch.object(board.ui, 'dialog', return_value=MagicMock()), patch.object(board.ui, 'card', return_value=MagicMock()), patch.object(board.ui, 'row', return_value=MagicMock()), patch.object(board.ui, 'button', return_value=MagicMock()) as button, patch.object(board.ui, 'select', return_value=MagicMock()) as select, patch.object(board.ui, 'run') as run:
        runpy.run_path(board.__file__, run_name='__mp_main__')
    assert add_body_html.call_count == 1 + debug
    assert 'new MutationObserver' in add_body_html.call_args_list[0].args[0]
    if debug:
        assert 'window.innerWidth' in add_body_html.call_args_list[1].args[0]
        assert "addEventListener('resize', updateSize)" in add_body_html.call_args_list[1].args[0]
    run.assert_called_once_with(native=True, title='ChessWithJev', window_size=(900, 643))
    labels = [call.args[0] for call in label.call_args_list]
    assert labels == ['LOCAL CHESS TERMINAL / V.01', 'CHESS WITH JEV', '● SYSTEM ONLINE', 'CHESS WITH JEV  /  LOCAL SESSION', 'SELECT PLAYERS']
    assert [call.kwargs['label'] for call in select.call_args_list] == ['White', 'Black']
    assert all(call.args[0] == ['human', 'random', 'stockfish'] for call in select.call_args_list)
    assert image.call_count == 0
    assert [call.args[0] for call in button.call_args_list] == ['START GAME']


def test_native_window_keeps_its_starting_aspect_ratio() -> None:
    window = MagicMock()
    with patch('webview.windows', [window]), patch('PyObjCTools.AppHelper.callAfter', side_effect=lambda callback: callback()):
        lock_window_aspect_ratio()
    window.events.shown.wait.assert_called_once_with()
    window.native.setContentMinSize_.assert_called_once_with((800, 600))
    window.native.setContentSize_.assert_called_once_with((900, 643))
    window.native.setContentAspectRatio_.assert_called_once_with((900, 643))


def test_piece_images_are_distinct_svgs() -> None:
    images = [piece_image(chess.Piece(piece_type, color))
              for color in chess.COLORS for piece_type in chess.PIECE_TYPES]
    assert len(set(images)) == 12
    assert all(b'<svg ' in b64decode(image.split(',', 1)[1]) for image in images)


def test_square_coordinates() -> None:
    assert square_name(0, 0) == 'a8'
    assert square_name(0, 7) == 'h8'
    assert square_name(7, 0) == 'a1'
    assert square_name(7, 7) == 'h1'


def test_starting_pieces() -> None:
    position = Position()
    expected = ['rnbqkbnr', 'pppppppp', '........', '........',
                '........', '........', 'PPPPPPPP', 'RNBQKBNR']
    actual = [''.join((position.board.piece_at(chess.parse_square(square_name(row, column))).symbol()
                       if position.board.piece_at(chess.parse_square(square_name(row, column))) else '.')
                      for column in range(8)) for row in range(8)]
    assert actual == expected


def test_programmatic_position_updates_refresh_board() -> None:
    view = BoardView()
    with patch.object(view, 'sync') as refresh:
        view.set_fen('8/8/8/8/8/8/8/K6k w - - 0 1')
        assert view.position.board.piece_at(chess.A1) == chess.Piece.from_symbol('K')
        refresh.assert_called_once_with()
        replacement = chess.Board.empty()
        replacement.set_piece_at(chess.E4, chess.Piece.from_symbol('q'))
        view.set_board(replacement)
        assert view.position.board.piece_at(chess.E4) == chess.Piece.from_symbol('q')
        assert refresh.call_count == 2


def test_render_uses_current_position() -> None:
    view = BoardView()
    view.position.set_fen('8/8/8/8/8/8/8/K6k w - - 0 1')
    with patch.object(board.ui, 'element', return_value=MagicMock()), patch.object(board.ui, 'image') as image:
        view.render()
    assert image.call_count == 2


def test_clicks_move_only_legal_pieces() -> None:
    view = BoardView()
    with patch.object(view, 'sync'), patch('src.game.controller.random.choice', side_effect=lambda moves: next(move for move in moves if move.uci() == 'e7e5')):
        view.click_square(chess.E7)  # black cannot move first
        assert view.selected is None
        view.click_square(chess.E2)
        assert view.selected == chess.E2
        view.click_square(chess.E5)  # illegal pawn move
        assert view.position.board.fen() == chess.Board().fen()
        view.click_square(chess.E2)
        view.click_square(chess.E4)
        assert view.position.board.piece_at(chess.E4) == chess.Piece.from_symbol('P')
        assert view.position.board.turn == chess.WHITE
        assert [move.uci() for move in view.position.board.move_stack] == ['e2e4', 'e7e5']
        view.click_square(chess.E7)
        assert view.selected is None
        assert view.position.board.piece_at(chess.E5) == chess.Piece.from_symbol('p')


def test_controller_accepts_moves_from_any_caller() -> None:
    controller = GameController()
    assert not controller.play(chess.Move.from_uci('e2e5'))
    assert controller.position.board.fen() == chess.STARTING_FEN
    assert controller.play(chess.Move.from_uci('e2e4'))
    assert controller.play(chess.Move.from_uci('e7e5'))
    assert [move.uci() for move in controller.position.board.move_stack] == ['e2e4', 'e7e5']


def test_random_black_move_uses_legal_moves_and_stops_at_game_end() -> None:
    controller = GameController()
    assert not controller.play_random_black_move()
    assert controller.play(chess.Move.from_uci('f2f3'))
    with patch('src.game.controller.random.choice', side_effect=lambda moves: next(move for move in moves if move.uci() == 'e7e5')):
        assert controller.play_random_black_move()
    assert controller.play(chess.Move.from_uci('g2g4'))
    with patch('src.game.controller.random.choice', side_effect=lambda moves: next(move for move in moves if move.uci() == 'd8h4')):
        assert controller.play_random_black_move()
    assert controller.position.status() == 'Checkmate — Black wins'
    assert not controller.play_random_black_move()


def test_human_cannot_move_black_and_mate_ends_before_reply() -> None:
    view = BoardView()
    view.set_fen('7k/8/5KQ1/8/8/8/8/8 w - - 0 1')
    with patch('src.game.controller.random.choice') as choose:
        view.click_square(chess.G6)
        view.click_square(chess.G7)
    assert view.position.status() == 'Checkmate — White wins'
    choose.assert_not_called()
    assert len(view.position.board.move_stack) == 1
    view.set_fen('7k/8/8/8/8/8/8/K7 b - - 0 1')
    view.click_square(chess.H8)
    assert view.selected is None


def test_programmatic_move_refreshes_board_view() -> None:
    view = BoardView()
    view.render_controls()
    assert view.play_move(chess.Move.from_uci('e2e4'))
    assert view.history_label.text == '1. e4'
    assert view.status_label.text == 'Black to move'


def test_promotion_and_external_position_reset() -> None:
    view = BoardView()
    view.promotion_dialog = MagicMock()
    with patch.object(view, 'sync'):
        view.set_fen('7k/P7/8/8/8/8/8/K7 w - - 0 1')
        view.click_square(chess.A7)
        view.click_square(chess.A8)
        assert view.pending_promotion == (chess.A7, chess.A8)
        assert view.position.board.piece_at(chess.A7) == chess.Piece.from_symbol('P')
        view.choose_promotion(chess.KNIGHT)
        assert view.position.board.piece_at(chess.A8) == chess.Piece.from_symbol('N')
        view.click_square(chess.H8)
        view.set_fen(chess.STARTING_FEN)
        assert view.selected is None


def test_all_promotion_choices_are_legal() -> None:
    for piece_type in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
        position = Position()
        position.set_fen('7k/P7/8/8/8/8/8/K7 w - - 0 1')
        assert not position.move(chess.A7, chess.A8)
        assert position.move(chess.A7, chess.A8, promotion=piece_type)
        assert position.board.piece_at(chess.A8) == chess.Piece(piece_type, chess.WHITE)


def test_move_updates_only_changed_squares() -> None:
    view = BoardView()
    elements = [MagicMock() for _ in chess.SQUARES]
    view.squares = dict(zip(chess.SQUARES, elements))
    view.shown_pieces = {square: view.position.board.piece_at(square) for square in chess.SQUARES}
    with patch('src.game.controller.random.choice', side_effect=lambda moves: next(move for move in moves if move.uci() == 'e7e5')):
        view.click_square(chess.E2)
        assert not any(element.clear.called for element in elements)
        view.click_square(chess.E4)
    changed = {square for square, element in view.squares.items() if element.clear.called}
    assert changed == {chess.E2, chess.E4, chess.E7, chess.E5}


def test_only_legal_moves_are_printed(capsys) -> None:
    position = Position()
    assert not position.move(chess.E2, chess.E5)
    assert capsys.readouterr().out == ''
    assert position.move(chess.E2, chess.E4)
    assert position.move(chess.E7, chess.E5)
    assert capsys.readouterr().out == 'e4\ne5\n'


def test_castling_and_en_passant_update_all_affected_squares() -> None:
    view = BoardView()
    view.squares = {square: MagicMock() for square in chess.SQUARES}
    view.shown_pieces = {square: view.position.board.piece_at(square) for square in chess.SQUARES}
    view.promotion_dialog = MagicMock()
    view.set_fen('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1')
    for element in view.squares.values():
        element.reset_mock()
    with patch.object(view.controller, 'play_random_move'):
        view.click_square(chess.E1)
        view.click_square(chess.G1)
    assert view.position.board.piece_at(chess.F1) == chess.Piece.from_symbol('R')
    assert view.position.board.piece_at(chess.G1) == chess.Piece.from_symbol('K')
    assert {square for square, element in view.squares.items() if element.clear.called} == {chess.E1, chess.F1, chess.G1, chess.H1}
    view.set_fen('7k/8/8/3pP3/8/8/8/K7 w - d6 0 1')
    for element in view.squares.values():
        element.reset_mock()
    with patch.object(view.controller, 'play_random_move'):
        view.click_square(chess.E5)
        view.click_square(chess.D6)
    assert view.position.board.piece_at(chess.D5) is None
    assert view.position.board.piece_at(chess.D6) == chess.Piece.from_symbol('P')
    assert {square for square, element in view.squares.items() if element.clear.called} == {chess.E5, chess.D5, chess.D6}


def test_check_checkmate_stalemate_and_draw_status() -> None:
    position = Position()
    position.set_fen('7k/6Q1/6K1/8/8/8/8/8 b - - 0 1')
    assert position.status() == 'Checkmate — White wins'
    assert not position.move(chess.H8, chess.H7)
    position.set_fen('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')
    assert position.status() == 'Stalemate — draw'
    position.set_fen('7k/8/6K1/8/8/8/8/8 w - - 0 1')
    assert position.status() == 'Draw — insufficient material'
    position.set_fen('7k/8/8/8/8/8/7R/K7 b - - 0 1')
    assert position.status() == 'Black to move — check'


def test_claimable_and_automatic_draws() -> None:
    position = Position()
    position.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 100 1')
    assert position.claim_draw()
    assert position.status() == 'Draw — 50-move rule'
    assert not position.move(chess.G2, chess.G3)
    position.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 150 1')
    assert position.status() == 'Draw — 75-move rule'
    assert not position.claim_draw()


def test_threefold_claim_and_fivefold_automatic_draw(capsys) -> None:
    position = Position()
    cycle = [(chess.G1, chess.F3), (chess.G8, chess.F6),
             (chess.F3, chess.G1), (chess.F6, chess.G8)]
    for _ in range(2):
        for source, target in cycle:
            assert position.move(source, target)
    assert position.claim_draw()
    assert position.status() == 'Draw — threefold repetition'
    position.set_fen(chess.STARTING_FEN)
    for _ in range(4):
        for source, target in cycle:
            assert position.move(source, target)
    assert position.status() == 'Draw — fivefold repetition'
    assert not position.move(chess.E2, chess.E4)
    capsys.readouterr()


def test_real_nicegui_promotion_draw_and_status_controls() -> None:
    def click(element) -> None:
        listener = next(iter(element._event_listeners.values()))
        element.client.handle_event({'id': element.id, 'listener_id': listener.id, 'args': []})

    view = BoardView()
    view.render()
    view.render_controls()
    assert len(view.squares) == 64
    assert view.status_label.text == 'White to move'
    assert not view.claim_button.visible
    assert not view.undo_button.enabled
    assert not view.redo_button.enabled
    click(view.squares[chess.E2])
    click(view.squares[chess.E4])
    assert view.undo_button.enabled
    click(view.undo_button)
    assert view.history_label.text == 'No moves yet'
    assert view.redo_button.enabled
    click(view.redo_button)
    assert view.history_label.text.startswith('1. e4\n1... ')

    view.set_fen('7k/P7/8/8/8/8/8/K7 w - - 0 1')
    click(view.squares[chess.A7])
    click(view.squares[chess.A8])
    assert view.promotion_dialog.value
    assert view.position.board.piece_at(chess.A7) == chess.Piece.from_symbol('P')
    knight_button = next(element for element in view.promotion_dialog.descendants()
                         if element._props.get('label') == 'Knight')
    click(knight_button)
    assert not view.promotion_dialog.value
    assert view.position.board.piece_at(chess.A8) == chess.Piece.from_symbol('N')
    assert view.status_label.text == 'Draw — insufficient material'

    view.set_fen('7k/8/8/8/8/8/6R1/K7 w - - 100 1')
    assert view.claim_button.visible
    click(view.claim_button)
    assert view.status_label.text == 'Draw — 50-move rule'
    assert not view.claim_button.visible
    click(view.squares[chess.G2])
    assert view.selected is None

    view.set_fen('7k/8/8/8/8/8/7R/K7 b - - 0 1')
    assert view.status_label.text == 'Black to move — check'
    view.set_fen('7k/6Q1/6K1/8/8/8/8/8 b - - 0 1')
    assert view.status_label.text == 'Checkmate — White wins'


def test_move_history_and_new_game() -> None:
    view = BoardView()
    view.render_controls()
    view.position.move(chess.E2, chess.E4)
    view.position.move(chess.C7, chess.C5)
    view.sync()
    assert view.history_label.text == '1. e4\n1... c5'
    assert view.status_label.text == 'White to move'
    view.new_game()
    assert view.position.board.fen() == chess.STARTING_FEN
    assert view.history_label.text == 'No moves yet'


def test_move_history_preserves_move_numbers_from_custom_position() -> None:
    position = Position()
    position.set_fen('7k/8/8/8/8/8/6R1/K7 b - - 0 12')
    position.move(chess.H8, chess.H7)
    assert move_history(position.board) == '12... Kh7'


def test_undo_redo_updates_board_history_and_status() -> None:
    view = BoardView()
    view.render_controls()
    assert view.position.move(chess.E2, chess.E4)
    assert view.position.move(chess.E7, chess.E5)
    view.sync()
    view.undo()
    assert view.history_label.text == 'No moves yet'
    assert view.status_label.text == 'White to move'
    assert view.position.board.piece_at(chess.E5) is None
    view.redo()
    assert view.history_label.text == '1. e4\n1... e5'
    assert view.position.board.piece_at(chess.E5) == chess.Piece.from_symbol('p')
    view.undo()
    assert view.position.move(chess.E2, chess.E4)
    assert view.position.move(chess.C7, chess.C5)
    view.sync()
    view.redo()
    assert view.history_label.text == '1. e4\n1... c5'
    view.new_game()
    assert not view.position.redo_stack
    assert view.history_label.text == 'No moves yet'


def test_undo_reopens_finished_game() -> None:
    position = Position()
    for source, target in [(chess.F2, chess.F3), (chess.E7, chess.E5),
                           (chess.G2, chess.G4), (chess.D8, chess.H4)]:
        assert position.move(source, target)
    assert position.status() == 'Checkmate — Black wins'
    assert position.undo()
    assert position.status() == 'Black to move'
    assert position.redo()
    assert position.status() == 'Checkmate — Black wins'


def test_player_combinations_and_random_opening() -> None:
    human = BoardView(white='human', black='human')
    with patch.object(human, 'sync'):
        assert human.play_human_move(chess.Move.from_uci('e2e4'))
        assert human.play_human_move(chess.Move.from_uci('e7e5'))
    assert len(human.position.board.move_stack) == 2

    mixed = BoardView(white='random', black='human')
    with patch.object(mixed, 'sync'), patch('src.game.controller.random.choice', side_effect=lambda moves: next(move for move in moves if move.uci() == ('e2e4' if any(move.uci() == 'e2e4' for move in moves) else 'g1f3'))):
        mixed.new_game()
        assert [move.uci() for move in mixed.position.board.move_stack] == ['e2e4']
        mixed.undo()  # keep the required random opening
        assert len(mixed.position.board.move_stack) == 1
        assert mixed.play_human_move(chess.Move.from_uci('e7e5'))
        assert [move.uci() for move in mixed.position.board.move_stack] == ['e2e4', 'e7e5', 'g1f3']
        mixed.undo()
        assert [move.uci() for move in mixed.position.board.move_stack] == ['e2e4']


def test_stockfish_plays_for_either_color_and_stops_at_game_end() -> None:
    engine = MagicMock()
    engine.play.return_value.move = chess.Move.from_uci('e7e5')
    with patch('src.game.controller.chess.engine.SimpleEngine.popen_uci', return_value=engine) as open_engine:
        view = BoardView(white='human', black='stockfish')
        with patch.object(view, 'sync'):
            assert view.play_human_move(chess.Move.from_uci('e2e4'))
        assert [move.uci() for move in view.position.board.move_stack] == ['e2e4', 'e7e5']
        assert open_engine.call_count == 1
        view.set_fen('7k/6Q1/6K1/8/8/8/8/8 b - - 0 1')
        assert not view.controller.play_stockfish_move()
        assert open_engine.call_count == 1

        engine.play.return_value.move = chess.Move.from_uci('e2e4')
        opening = BoardView(white='stockfish', black='human')
        with patch.object(opening, 'sync'):
            opening.new_game()
        assert [move.uci() for move in opening.position.board.move_stack] == ['e2e4']
        opening.undo()
        assert len(opening.position.board.move_stack) == 1


def test_stockfish_and_random_can_play_each_other() -> None:
    view = BoardView(white='stockfish', black='random')
    view.render_controls()
    with patch.object(view.controller, 'play_stockfish_move', side_effect=lambda: view.controller.play(chess.Move.from_uci('e2e4'))), patch.object(view.controller, 'play_random_move', side_effect=lambda: view.controller.play(chess.Move.from_uci('e7e5'))):
        view.toggle_random()
        view.random_step()
        view.random_step()
    assert [move.uci() for move in view.position.board.move_stack] == ['e2e4', 'e7e5']
    view.new_game()
    assert not view.random_timer.active


def test_evaluation_bar_tracks_position_and_reuses_unchanged_score() -> None:
    view = BoardView(white='human', black='human')
    with patch.object(view.controller, 'white_expectation', side_effect=[0.5, 0.8, 0.2]) as evaluate:
        view.render_evaluation()
        assert view.eval_fill._style['height'] == '50.0%'
        view.sync()
        assert evaluate.call_count == 1
        view.play_move(chess.Move.from_uci('e2e4'))
        assert view.eval_fill._style['height'] == '80.0%'
        view.undo()
        assert view.eval_fill._style['height'] == '20.0%'
    assert view.eval_bar._props['aria-valuenow'] == '20'


def test_stockfish_evaluation_handles_scores_and_finished_games() -> None:
    controller = GameController()
    engine = MagicMock()
    engine.analyse.return_value = {'score': chess.engine.PovScore(chess.engine.Cp(200), chess.WHITE)}
    with patch('src.game.controller.chess.engine.SimpleEngine.popen_uci', return_value=engine):
        assert controller.white_expectation() > 0.5
        controller.position.set_fen('7k/6Q1/6K1/8/8/8/8/8 b - - 0 1')
        assert controller.white_expectation() == 1.0
        controller.position.set_fen('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')
        assert controller.white_expectation() == 0.5
        controller.close()
    engine.quit.assert_called_once_with()


def test_random_vs_random_starts_pauses_and_resets() -> None:
    view = BoardView(white='random', black='random')
    view.render_controls()
    assert not view.random_timer.active
    view.toggle_random()
    assert view.random_timer.active
    view.random_step()
    assert len(view.position.board.move_stack) == 1
    view.toggle_random()
    assert not view.random_timer.active
    view.new_game()
    assert not view.random_timer.active
    assert view.position.board.fen() == chess.STARTING_FEN


def test_landing_starts_game_and_returns_to_setup() -> None:
    from nicegui import ui

    with patch.object(ui, 'run'):
        board.main()
    client = ui.context.client

    def click(element) -> None:
        listener = next(iter(element._event_listeners.values()))
        client.handle_event({'id': element.id, 'listener_id': listener.id, 'args': []})

    selects = [element for element in client.elements.values() if type(element).__name__ == 'Select'][-2:]
    assert [select._props['label'] for select in selects] == ['White', 'Black']
    selects[0].value = 'human'
    selects[1].value = 'human'
    start = max((element for element in client.elements.values() if element._props.get('label') == 'START GAME'), key=lambda element: element.id)
    click(start)
    assert any(element.text == 'WHITE / HUMAN  ·  BLACK / HUMAN' for element in client.elements.values() if hasattr(element, 'text'))
    status_strip = max((element for element in client.elements.values() if 'status-strip' in element._classes), key=lambda element: element.id)
    board_panel = max((element for element in client.elements.values() if 'board-panel' in element._classes), key=lambda element: element.id)
    controls = max((element for element in client.elements.values() if 'game-controls' in element._classes), key=lambda element: element.id)
    assert {element.text for element in status_strip.descendants() if hasattr(element, 'text')} == {'SYSTEM STATUS', 'White to move'}
    assert status_strip in board_panel.descendants()
    assert not any(element.text == 'SYSTEM STATUS' for element in controls.descendants() if hasattr(element, 'text'))
    back = max((element for element in client.elements.values() if element._props.get('label') == 'MAIN MENU'), key=lambda element: element.id)
    click(back)
    assert max((element for element in client.elements.values() if element._props.get('label') == 'START GAME'), key=lambda element: element.id).id != start.id
