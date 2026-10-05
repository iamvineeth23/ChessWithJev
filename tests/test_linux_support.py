import os
from pathlib import Path
import shutil
import subprocess
from unittest.mock import MagicMock

import pytest

from src.game import controller
from src.ui import board


@pytest.mark.parametrize('platform,path,executable,expected', [
    ('linux', '/custom/stockfish', True, '/custom/stockfish'),
    ('linux', None, True, '/usr/games/stockfish'),
    ('linux', None, False, None),
    ('darwin', None, True, None),
])
def test_stockfish_discovery(monkeypatch, platform, path, executable, expected):
    monkeypatch.setattr(controller.sys, 'platform', platform)
    monkeypatch.setattr(controller.shutil, 'which', lambda name: path)
    monkeypatch.setattr(controller.os, 'access', lambda name, mode: executable)
    assert controller.stockfish_path() == expected
    if expected:
        launch = MagicMock()
        monkeypatch.setattr(controller.chess.engine.SimpleEngine, 'popen_uci', launch)
        game = controller.GameController()
        assert game.stockfish_engine() is launch.return_value
        game.stockfish_engine()
        launch.assert_called_once_with(expected)


def test_linux_startup_uses_shared_discovery(monkeypatch):
    monkeypatch.setattr(controller.sys, 'platform', 'linux')
    monkeypatch.setattr(controller.shutil, 'which', lambda name: None)
    monkeypatch.setattr(controller.os, 'access', lambda name, mode: True)
    schedule = MagicMock()
    monkeypatch.setattr(board.BoardView, 'schedule_update', schedule)
    board.build_page({'game': {'white': 'human', 'black': 'random',
                              'position': controller.Position().snapshot()}})
    schedule.assert_called_once()


def test_linux_native_startup_skips_macos_hook(monkeypatch):
    monkeypatch.setattr(board.sys, 'platform', 'linux')
    monkeypatch.setattr(board.sys, 'argv', ['chess'])
    monkeypatch.setattr(board.app.native, 'start_args', {})
    run = MagicMock()
    monkeypatch.setattr(board.ui, 'run', run)
    board.main()
    assert 'func' not in board.app.native.start_args
    assert run.call_args.kwargs['native'] is True


@pytest.mark.parametrize('platform', ['Linux', 'Darwin'])
def test_setup_platform_dependencies(tmp_path, platform):
    repo = tmp_path / 'repo'
    (repo / 'scripts').mkdir(parents=True)
    shutil.copyfile(Path(__file__).resolve().parents[1] / 'scripts/setup.sh', repo / 'scripts/setup.sh')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    log = tmp_path / 'commands'
    for name, body in {
        'uname': f'echo {platform}',
        'apt': 'echo "apt $*" >> "$SETUP_LOG"',
        'sudo': 'exec "$@"',
        'brew': 'echo "brew $*" >> "$SETUP_LOG"',
        'python3': 'mkdir -p "$3/bin"; cp "$FAKE_PYTHON" "$3/bin/python"',
    }.items():
        executable = bin_dir / name
        executable.write_text('#!/bin/bash\n' + body + '\n')
        executable.chmod(0o755)
    fake_python = tmp_path / 'python'
    fake_python.write_text('#!/bin/bash\necho "python $*" >> "$SETUP_LOG"\n')
    fake_python.chmod(0o755)
    # Only expose shell utilities, so host Stockfish cannot affect the macOS branch.
    for name in ['bash', 'dirname', 'mkdir', 'cp', 'chmod', 'cat']:
        (bin_dir / name).symlink_to(shutil.which(name))
    subprocess.run(['/bin/bash', str(repo / 'scripts/setup.sh')], check=True,
                   env={**os.environ, 'PATH': str(bin_dir), 'SETUP_LOG': str(log),
                        'FAKE_PYTHON': str(fake_python)})
    commands = log.read_text()
    assert 'nicegui[native]' in commands
    assert (repo / '.venv/bin/chess').stat().st_mode & 0o111
    if platform == 'Linux':
        assert 'apt update\n' in commands
        assert 'apt install -y stockfish python3-venv' in commands
        assert 'pywebview[qt]' in commands
        assert 'brew' not in commands
    else:
        assert 'brew install stockfish\n' in commands
        assert 'apt ' not in commands
        assert 'pywebview[qt]' not in commands
