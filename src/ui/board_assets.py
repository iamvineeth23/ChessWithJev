MOVE_LOG_SCRIPT = '''
        <script>
            let moveLog;
            let moveLogObserver;
            let followLatest = true;
            let historyScrollTop = 0;
            const watchMoveLog = () => {
                const log = document.querySelector('.move-history-panel');
                if (!log || log === moveLog) return;
                moveLogObserver?.disconnect();
                moveLog = log;
                followLatest = true;
                historyScrollTop = 0;
                const history = log.querySelector('.move-history');
                history?.addEventListener('scroll', () => {
                    if (history.scrollTop < historyScrollTop) followLatest = false;
                    historyScrollTop = history.scrollTop;
                });
                moveLogObserver = new MutationObserver((changes) => {
                    if (changes.some(change => change.attributeName === 'data-scroll-resume')) followLatest = true;
                    const history = log.querySelector('.move-history');
                    if (history) {
                        history.scrollTop = followLatest ? history.scrollHeight : historyScrollTop;
                        historyScrollTop = history.scrollTop;
                    }
                });
                moveLogObserver.observe(log, {childList: true, characterData: true, subtree: true, attributes: true, attributeFilter: ['data-scroll-resume']});
            };
            const attachMoveLog = new MutationObserver(watchMoveLog);
            attachMoveLog.observe(document.body, {childList: true, subtree: true});
            watchMoveLog();
        </script>
    '''


DEBUG_VIEWPORT_HTML = '''
            <div id="viewport-size" style="position:fixed;right:8px;bottom:8px;z-index:1000;
                padding:4px 7px;background:#17251c;color:#a8f0b0;border:1px solid #425c48;
                font:11px monospace;pointer-events:none" aria-label="Viewport size"></div>
            <script>
                const size = document.getElementById('viewport-size');
                function updateSize() { size.textContent = `${window.innerWidth} × ${window.innerHeight}`; }
                window.addEventListener('resize', updateSize);
                updateSize();
            </script>
        '''


BOARD_CSS = '''
        :root { --green: #a8f0b0; --muted: #779780; --line: #425c48; --panel: #17251c; }
        body { background: #0c1510; color: #d7e8d6; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; }
        .nicegui-content { padding: 0; }
        .app-shell { width: min(1120px, 100%); min-height: 100dvh; margin: 0 auto; padding: clamp(20px, 4vw, 44px); padding-top: 5px; box-sizing: border-box; }
        .app-header { display: grid; grid-template-columns: minmax(0, 1fr) 274px; align-items: end; gap: 28px; border-bottom: 1px solid var(--line); padding-bottom: 2px; }
        .header-save-action { display: flex; justify-content: flex-end; }
        .header-save-action .save-game-button { width: auto; min-height: 30px; padding: 4px 10px; }
        .header-left { display: flex; align-items: end; justify-content: space-between; gap: 20px; }
        .app-kicker, .panel-kicker, .panel-meta, .axis-label, .footer-note { color: var(--muted); font-size: 11px; letter-spacing: .16em; }
        .app-title { color: var(--green); font-size: clamp(28px, 4vw, 46px); font-weight: 700; line-height: 1.1; letter-spacing: -.06em; text-shadow: 0 0 24px #72e98940; }
        .main-menu-action { display: flex; gap: 10px; }
        .main-menu-action .terminal-button { width: auto; min-height: 30px; padding: 4px 10px; }
        .game-layout { display: flex; align-items: stretch; gap: 28px; margin-top: 4px; }
        .game-page { display: flex; flex-direction: column; flex: 1; min-height: 0; position: relative; }
        .status-strip { display: flex; align-items: center; justify-content: flex-end; gap: 18px; width: 100%; padding-right: 80px; box-sizing: border-box; }
        .board-panel, .game-controls { background: var(--panel); border: 1px solid var(--line); box-shadow: 8px 8px 0 #080f0b; }
        .board-panel { padding: clamp(12px, 2vw, 22px); min-width: 0; flex: 1; }
        .board-heading { display: grid; grid-template-columns: 16px 24px minmax(0, 1fr) 80px; width: 100%; margin-bottom: 4px; color: var(--green); font-size: 12px; letter-spacing: .12em; }
        .board-players { grid-column: 3; justify-self: end; }
        .game-controls { display: flex; flex-direction: column; gap: 14px; width: 274px; flex-shrink: 0; padding: 22px; }
        .status-text { color: var(--green); font-size: 11px; line-height: 1.4; letter-spacing: .16em; }
        .move-analysis-heading, .history-heading, .evaluation-plot-heading { display: flex; justify-content: space-between; gap: 8px; color: var(--green); font-size: 12px; letter-spacing: .1em; }
        .history-heading { margin-top: -10px; }
        .terminal-button.export-pgn-button { width: auto; min-width: 0; min-height: 0; padding: 2px 5px; border: 1px solid var(--green); font-size: 9px; font-weight: 400; line-height: 1; }
        .terminal-button.export-pgn-button:hover { background: transparent; text-decoration: underline; }
        .move-placeholder-panel { flex: 1; min-height: 40px; border: 1px solid var(--line); background: #101b14; }
        .evaluation-tabs { height: 18px; min-height: 18px; flex-shrink: 0; }
        .evaluation-tabs .q-tab { min-height: 18px; padding: 0 12px; }
        .evaluation-tabs .q-tab__indicator { display: none; }
        .evaluation-tabs .q-tab--active::before, .evaluation-tabs .q-tab--active::after { content: ''; position: absolute; inset: 0; clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 100%, 0 100%); pointer-events: none; }
        .evaluation-tabs .q-tab--active:last-child::before, .evaluation-tabs .q-tab--active:last-child::after { clip-path: polygon(12px 0, 100% 0, 100% 100%, 0 100%); }
        .evaluation-tabs .q-tab--active::before { background: var(--line); }
        .evaluation-tabs .q-tab--active::after { inset: 2px 3px 0 2px; background: #101b14; }
        .evaluation-tabs .q-tab__content { z-index: 1; }
        .evaluation-tabs .q-tab__label { font-size: 12px; line-height: 18px; letter-spacing: .1em; }
        .evaluation-panels, .evaluation-tab-panel { width: 100%; height: 100%; padding: 0; background: transparent; color: inherit; }
        .evaluation-plot-panel { position: relative; }
        .evaluation-expand { position: absolute; top: 2px; right: 4px; width: 20px; height: 20px; min-height: 20px; color: var(--muted); z-index: 2; }
        .evaluation-expand .q-icon { font-size: 16px; }
        .evaluation-fullscreen { position: relative; width: 100vw; height: 100vh; padding: 24px; background: #101b14; }
        .evaluation-fullscreen .evaluation-expand { top: 8px; right: 8px; }
        .live-evaluation-chart { width: 100%; height: 100%; }
        .live-evaluation-chart .evaluation-chart { height: 100%; border: 0; }
        .jev-predictions { display: grid; align-content: start; gap: 7px; width: 100%; height: 100%; padding: 8px; color: #d7e8d6; font-size: 11px; }
        .jev-prediction-card, .jev-confidence-card { padding: 8px 10px; border: 1px solid #284636; border-radius: 8px; background: rgba(12, 28, 20, .45); }
        .jev-prediction-heading, .jev-confidence-heading, .jev-confidence-title { display: flex; align-items: center; }
        .jev-prediction-heading { gap: 5px; margin-bottom: 5px; color: var(--green); font-size: 13px; }
        .jev-info { display: grid; place-items: center; width: 15px; height: 15px; border: 1px solid var(--muted); border-radius: 50%; color: var(--muted); font-size: 9px; }
        .jev-prediction-row { display: grid; grid-template-columns: 50px minmax(50px, 1fr) 38px; align-items: center; gap: 7px; min-height: 22px; padding: 2px 5px; border-radius: 5px; }
        .jev-prediction-row.selected { color: #ffe28a; background: rgba(165, 132, 35, .28); }
        .jev-prediction-track, .jev-confidence-track { overflow: hidden; height: 8px; border-radius: 5px; background: #1b392a; }
        .jev-prediction-fill, .jev-confidence-fill { height: 100%; border-radius: inherit; background: var(--green); }
        .jev-prediction-row.selected .jev-prediction-fill, .jev-confidence-fill { background: #ffe28a; }
        .jev-prediction-rating { text-align: right; font-variant-numeric: tabular-nums; }
        .jev-confidence-card { padding-block: 9px; }
        .jev-confidence-heading { justify-content: space-between; gap: 8px; margin-bottom: 8px; }
        .jev-confidence-title { gap: 5px; color: var(--muted); }
        .jev-confidence-value { display: flex; gap: 5px; white-space: nowrap; }
        .jev-confidence-percent { color: #ffe28a; }
        .jev-confidence-track { height: 9px; }
        .move-analysis-panel, .move-history-panel { flex: 1; min-height: 180px; border: 1px solid var(--line); background: #101b14; padding: 14px; }
        .move-analysis-table { width: 100%; border-collapse: collapse; color: #d7e8d6; font-size: 13px; line-height: 1.8; }
        .move-analysis-table th { color: var(--muted); font-size: 11px; letter-spacing: .12em; text-align: left; }
        .move-analysis-table th:last-child, .move-analysis-table td:last-child { text-align: right; }
        .analysis-engine { position: relative; padding: 0 6px; border-radius: 12px; background: #22372a; color: var(--muted); letter-spacing: 0; }
        .analysis-engine::before { content: ''; position: absolute; left: -12px; top: 50%; transform: translateY(-50%); width: 6px; height: 6px; border-radius: 50%; background: var(--green); opacity: 0; }
        .analysis-engine.analyzing::before { opacity: 1; animation: record-blink 1s steps(1, end) infinite; }
        body:has(.game-page .analysis-engine.analyzing),
        body:has(.game-page .analysis-engine.analyzing) * { cursor: wait !important; }
        @media (prefers-reduced-motion: reduce) { .analysis-engine.analyzing::before { animation: none; } }
        .move-analysis-panel { flex: 0 0 auto; min-height: 0; height: 209px; box-sizing: border-box; overflow-y: auto; font-size: 13px; line-height: 1.25; }
        .move-analysis-context, .move-analysis-note { color: var(--muted); }
        .played-move-card { margin: 4px 0; padding: 4px 8px; border-radius: 6px; background: #22372a; }
        .played-move-name, .played-alternative { color: #f1d585; font-weight: 700; }
        .move-analysis-detail { display: flex; justify-content: space-between; gap: 8px; }
        .move-alternative { display: grid; grid-template-columns: 18px 48px minmax(0, 1fr) 96px; gap: 6px; align-items: center; }
        .move-alternative > :last-child { text-align: right; white-space: nowrap; }
        .move-alternative-bar { height: 5px; border-radius: 3px; background: #22372a; overflow: hidden; }
        .move-alternative-fill { height: 100%; background: var(--green); }
        .played-alternative .move-alternative-fill { background: #f1d585; }
        .move-analysis-note { margin-top: 4px; font-size: 11px; line-height: 1.4; }
        .move-history-panel { flex: 0 0 auto; min-height: 0; height: calc(4 * (13px * 1.8 + 4px) + 3 * 2px + 30px); box-sizing: border-box; overflow: hidden; }
        .move-history { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 2px 6px; max-height: calc(4 * (13px * 1.8 + 4px) + 3 * 2px); overflow-y: auto; overflow-wrap: anywhere; line-height: 1.8; font-size: 13px; }
        .move-history-entry { display: block; padding: 2px 8px; border-radius: 6px; background: #22372a; color: #d7e8d6; }
        .q-btn.move-history-entry { min-height: 0; font: inherit; letter-spacing: 0; text-align: left; }
        .move-history-entry .q-btn__content { justify-content: flex-start; }
        .move-history-entry:focus-visible { outline: 2px solid var(--green); outline-offset: -2px; }
        .move-history-entry:only-child:not([style]) { grid-column: 1 / -1; }
        .move-history-entry.current-move { background: #f1d585; color: #172116; font-weight: 700; }
        .terminal-button { width: 100%; border: 1px solid var(--green); border-radius: 0; background: transparent; color: var(--green); font-family: inherit; font-weight: 700; letter-spacing: .08em; box-shadow: none; }
        .terminal-button:hover { background: #294733; }
        .terminal-button:focus-visible { outline: 2px solid #f3d68a; outline-offset: 3px; }
        .new-game-button, .board-actions .terminal-button { background: var(--green); color: #0c1510; }
        .new-game-button:hover, .board-actions .terminal-button:hover { background: #cefbd1; }
        .chess-layout { display: grid; grid-template-columns: 16px 24px minmax(0, 1fr) 80px; grid-template-rows: auto 24px; width: 100%; }
        .board-actions { grid-column: 4; grid-row: 1; align-self: end; display: grid; grid-template-columns: repeat(2, 32px); grid-template-rows: repeat(4, 32px); gap: 8px; padding-left: 8px; }
        .board-actions .terminal-button { width: 32px; height: 32px; min-height: 32px; padding: 0; font-size: 20px; line-height: 1; }
        .analysis-card { box-sizing: border-box; background: var(--panel); border: 1px solid var(--green); border-radius: 0; color: var(--green); padding: 28px; font-family: inherit; }
        .q-dialog__inner--minimized > .analysis-card { width: calc(100vw - 128px) !important; max-width: none !important; }
        .analysis-heading { width: 100%; align-items: center; justify-content: space-between; margin-top: -22px; margin-bottom: 0; }
        .analysis-title { gap: 3px; }
        .analysis-meta { color: var(--muted); font-size: 12px; }
        .analysis-close { width: auto; padding: 5px 9px; font-size: 11px; }
        .analysis-chart { width: 100%; }
        .evaluation-chart { display: block; width: 100%; height: auto; background: #101b14; border: 1px solid var(--line); }
        .evaluation-chart .chart-zone-white { fill: #a8f0b0; opacity: .035; }
        .evaluation-chart .chart-zone-black { fill: #080f0b; opacity: .35; }
        .evaluation-chart .chart-grid { stroke: var(--line); stroke-width: 1; opacity: .75; }
        .evaluation-chart .chart-grid-vertical { opacity: .38; }
        .evaluation-chart .chart-balance { stroke: #e7cb7d; stroke-width: 1.5; stroke-dasharray: 5 4; }
        .evaluation-chart .chart-line { fill: none; stroke: var(--green); stroke-width: 4; stroke-linejoin: round; stroke-linecap: round; filter: drop-shadow(0 0 4px #72e98970); }
        .evaluation-chart .chart-recommended { fill: none; stroke: #e7cb7d; stroke-width: 1.5; stroke-dasharray: 5 4; stroke-linejoin: round; }
        .evaluation-chart .chart-last-point { fill: #e7cb7d; stroke: #101b14; stroke-width: 3; }
        .evaluation-chart .chart-player-label { font: 700 14px 'SFMono-Regular', Consolas, monospace; letter-spacing: .12em; }
        .evaluation-chart .chart-player-white { fill: var(--green); }
        .evaluation-chart .chart-player-black { fill: #d7e8d6; }
        .evaluation-chart .chart-label, .evaluation-chart .chart-axis-title { fill: var(--muted); font: 14px 'SFMono-Regular', Consolas, monospace; letter-spacing: .06em; }
        .evaluation-chart .chart-axis-title { fill: var(--green); font-weight: 700; }
        .live-evaluation-chart .evaluation-chart .chart-label { font-size: 9px; letter-spacing: 0; }
        .live-evaluation-chart .evaluation-chart .chart-player-label,
        .live-evaluation-chart .evaluation-chart .chart-axis-title { font-size: 9px; font-weight: 400; letter-spacing: .08em; fill: var(--muted); }
        .live-evaluation-chart .chart-line { stroke-width: 1.5; filter: none; }
        .live-evaluation-chart .chart-last-point { r: 2.5px; stroke-width: 1; }
        .live-evaluation-chart .chart-grid { stroke-width: .6; opacity: .45; }
        .live-evaluation-chart .chart-grid-vertical { opacity: .22; }
        .live-evaluation-chart .chart-balance { stroke-width: .8; stroke-dasharray: 3 4; opacity: .65; }
        @keyframes record-blink { 50% { opacity: 0; } }
        .board-actions .terminal-button:disabled { opacity: .4; }
        .eval-bar { grid-column: 1; grid-row: 1; width: 16px; height: 100%; border: 2px solid #89b993; background: #17251c; display: flex; flex-direction: column; justify-content: flex-end; box-sizing: border-box; }
        .eval-white { width: 100%; background: #d7e8d6; }
        .rank-labels { grid-column: 2; grid-row: 1; display: grid; grid-template-rows: repeat(8, 1fr); }
        .file-labels { grid-column: 3; display: grid; grid-template-columns: repeat(8, 1fr); }
        .axis-label { display: flex; align-items: center; justify-content: center; }
        .chess-board { display: grid; grid-template-columns: repeat(8, 1fr); width: 100%; border: 2px solid #89b993; }
        .chess-square { aspect-ratio: 1; position: relative; cursor: pointer; }
        .chess-square.light { background: #b5c6ad; }
        .chess-square.dark { background: #506953; }
        .chess-square:hover { box-shadow: inset 0 0 0 3px #d0eac2; }
        .chess-square.selected { outline: 4px solid #e7cb7d; outline-offset: -4px; z-index: 1; }
        .chess-square.last-move { box-shadow: inset 0 0 0 4px #e7cb7d; }
        .chess-piece { position: absolute; inset: 5%; width: 90%; height: 90%; pointer-events: none; }
        .chess-piece-moving { animation: piece-slide 550ms cubic-bezier(.4, 0, .2, 1); z-index: 2; }
        @keyframes piece-slide {
            from { transform: translate(var(--piece-x), var(--piece-y)); }
            to { transform: translate(0, 0); }
        }
        @media (prefers-reduced-motion: reduce) {
            .chess-piece-moving { animation: none; }
        }
        .promotion-card { background: var(--panel); border: 1px solid var(--green); border-radius: 0; color: var(--green); padding: 24px; font-family: inherit; }
        .promotion-actions { flex-wrap: wrap; margin-top: 12px; }
        .promotion-actions .terminal-button { width: auto; }
        .footer-note { margin-top: 28px; border-top: 1px solid var(--line); padding-top: 16px; user-select: text; cursor: copy; }
        .game-page + .footer-note { margin-top: 20px; transform: translateY(22px); }
        .app-shell > main:not(.game-page) { display: flex; flex: 1; }
        .landing { display: flex; flex: 1; flex-direction: column; justify-content: center; gap: 20px; max-width: 440px; width: 100%; margin: auto; }
        .player-row { position: relative; }
        .landing .q-field.elo-select { position: absolute; top: 0; left: calc(100% + 32px); width: 150px; }
        .landing .q-field { width: 100%; color: var(--green); }
        .landing .q-field__label, .landing .q-field__native, .landing .q-field__marginal { color: var(--green) !important; }
        .landing .q-field--outlined .q-field__control:before { border-color: var(--line); }
        .player-options { background: var(--panel); color: var(--green); }
        .landing-title { color: var(--green); font-size: 24px; }
        @media (min-width: 761px) {
            .app-shell { height: 100dvh; display: flex; flex-direction: column; }
            .game-layout { flex: 1; min-height: 0; }
            .game-controls { position: relative; margin-bottom: -38px; background: transparent; border-color: transparent; box-shadow: none; }
            .game-controls::before { content: ''; position: absolute; inset: -1px -1px -1px -98.5px; z-index: -1; background: var(--panel); border: 1px solid var(--line); box-shadow: 8px 8px 0 #080f0b; }
            .board-panel { position: relative; display: grid; grid-template-rows: auto auto minmax(0, 1fr); min-height: 0; margin-bottom: -38px; padding-bottom: calc(clamp(12px, 2vw, 22px) + 43px); background: transparent; border-color: transparent; box-shadow: none; }
            .board-panel::before { content: ''; position: absolute; inset: -1px 78.5px -1px -1px; z-index: -1; background: var(--panel); border: 1px solid var(--line); box-shadow: 8px 8px 0 #080f0b; }
            .status-strip, .board-heading { width: min(100%, calc(100dvh - 158px), 740px); justify-self: center; }
            .chess-layout { position: relative; width: min(100%, calc(100dvh - 158px), 740px); height: max-content; place-self: center; min-width: 0; grid-template-rows: auto 24px; }
            .board-actions { position: absolute; grid-column: 3 / 4; left: 50%; transform: translateX(-50%); bottom: -39px; display: flex; width: max-content; padding: 0; }
            .move-analysis-heading, .history-heading { margin-left: -97.5px; position: relative; top: 10px; }
            .evaluation-plot-heading { margin-left: -97.5px; margin-top: -28px; position: relative; top: 10px; }
            .move-analysis-heading, .move-analysis-panel { transform: translateY(-14px); }
            .move-analysis-panel, .move-history-panel { flex: 0 1 50%; min-height: 0; margin-left: -97.5px; }
            .move-analysis-panel { flex: 0 0 auto; }
            .move-history-panel { flex: 0 0 auto; }
            .move-placeholder-panel { margin-left: -97.5px; }
        }
        @media (max-width: 760px) {
            .app-header { grid-template-columns: minmax(0, 1fr) auto; align-items: start; gap: 20px; }
            .header-left { align-items: start; flex-direction: column; }
            .status-strip { flex-wrap: wrap; }
            .game-layout { flex-direction: column; }
            .game-controls { width: 100%; }
            .move-analysis-panel, .move-history-panel { max-height: 230px; }
            .landing .q-field.elo-select { position: static; width: 100%; margin-top: 20px; }
        }
    '''
