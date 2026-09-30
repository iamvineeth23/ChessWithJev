import json
from pathlib import Path


def latest_game_evaluations(path: Path | None = None) -> list[float]:
    """Return each logged position as a balance percentage: Black -100 to White +100."""
    path = path or Path(__file__).resolve().parents[2] / 'gamelog' / 'latest.json'
    try:
        moves = json.loads(path.read_text())['moves']
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return []
    return [200 * value - 100 for move in moves
            if isinstance(value := move.get('evaluation', {}).get('wdl_expectation_white'), (int, float)) and 0 <= value <= 1]


def latest_game_players(path: Path | None = None) -> str:
    path = path or Path(__file__).resolve().parents[2] / 'gamelog' / 'latest.json'
    try:
        players = json.loads(path.read_text())['players']
        return ' | '.join(
            f'{color.title()}: {player["type"].title()}'
            f'{f" [{player["elo"]}]" if player["type"] == "stockfish" and player.get("elo") is not None else ""}'
            for color in ('white', 'black') if (player := players[color]))
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return ''


def evaluation_chart_svg(evaluations: list[float], *, compact: bool = False) -> str:
    width, height, left, right, top, bottom = (380, 190, 64, 14, 18, 40) if compact else (1080, 580, 100, 40, 40, 72)
    plot_width, plot_height = width - left - right, height - top - bottom
    def x(index: int) -> float:
        return left + plot_width * index / max(len(evaluations) - 1, 1)

    def y(value: float) -> float:
        return top + plot_height * (100 - value) / 200

    points = ' '.join(f'{x(index):.1f},{y(value):.1f}' for index, value in enumerate(evaluations))
    horizontal_grid = ''.join(
        f'<line x1="{left}" y1="{y(value):.1f}" x2="{width - right}" y2="{y(value):.1f}" class="chart-grid"/>'
        f'<text x="{left - 14}" y="{y(value) + 5:.1f}" text-anchor="end" class="chart-label">{("0%" if compact else "0% EVEN") if value == 0 else f"{value:+.0f}%"}</text>'
        for value in (100, 50, 0, -50, -100))
    ticks = sorted({0, len(evaluations) - 1, *(round((len(evaluations) - 1) * step / 4) for step in range(1, 4))})
    vertical_grid = ''.join(
        f'<line x1="{x(index):.1f}" y1="{top}" x2="{x(index):.1f}" y2="{height - bottom}" class="chart-grid chart-grid-vertical"/>'
        f'<text x="{x(index):.1f}" y="{height - (24 if compact else 46)}" text-anchor="middle" class="chart-label">{index if compact else index + 1}</text>'
        for index in ticks)
    return f'''<svg class="evaluation-chart" viewBox="0 0 {width} {height}" role="img" aria-label="Game evaluation by move step, with zero percent balanced">
        <rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height / 2}" class="chart-zone chart-zone-white"/>
        <rect x="{left}" y="{top + plot_height / 2}" width="{plot_width}" height="{plot_height / 2}" class="chart-zone chart-zone-black"/>
        {horizontal_grid}
        {vertical_grid}
        <line x1="{left}" y1="{y(0):.1f}" x2="{width - right}" y2="{y(0):.1f}" class="chart-balance"/>
        <polyline points="{points}" class="chart-line"/>
        <circle cx="{x(len(evaluations) - 1):.1f}" cy="{y(evaluations[-1]):.1f}" r="7" class="chart-last-point"/>
        <text x="{width - right - 12}" y="{top + (14 if compact else 28)}" text-anchor="end" class="chart-player-label chart-player-white">WHITE</text>
        <text x="{width - right - 12}" y="{y(0) + (18 if compact else 32):.1f}" text-anchor="end" class="chart-player-label chart-player-black">BLACK</text>
        <text x="{width / 2}" y="{height - (6 if compact else 22)}" text-anchor="middle" class="chart-axis-title">MOVE STEP</text>
    </svg>'''
