MOVE_LOG_SCRIPT = '''
        <script>
            let moveLog;
            let moveLogObserver;
            const watchMoveLog = () => {
                const log = document.querySelector('.move-history-panel');
                if (!log || log === moveLog) return;
                moveLogObserver?.disconnect();
                moveLog = log;
                moveLogObserver = new MutationObserver(() => { log.scrollTop = log.scrollHeight; });
                moveLogObserver.observe(log, {childList: true, characterData: true, subtree: true});
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
        .app-header { display: flex; align-items: end; justify-content: space-between; gap: 20px; border-bottom: 1px solid var(--line); padding-bottom: 2px; }
        .app-kicker, .panel-kicker, .panel-meta, .axis-label, .footer-note { color: var(--muted); font-size: 11px; letter-spacing: .16em; }
        .app-title { color: var(--green); font-size: clamp(28px, 4vw, 46px); font-weight: 700; line-height: 1.1; letter-spacing: -.06em; text-shadow: 0 0 24px #72e98940; }
        .header-mark { border: 1px solid var(--line); color: var(--green); padding: 7px 10px; font-size: 11px; letter-spacing: .12em; white-space: nowrap; }
        .main-menu-action { margin-left: 75px; }
        .header-actions { display: flex; gap: 12px; margin-left: auto; }
        .main-menu-action .terminal-button, .header-actions .terminal-button { width: auto; min-height: 30px; padding: 4px 10px; }
        .game-layout { display: flex; align-items: stretch; gap: 28px; margin-top: 4px; }
        .game-page { display: flex; flex-direction: column; flex: 1; min-height: 0; position: relative; }
        .status-strip { display: flex; align-items: center; justify-content: flex-end; gap: 18px; width: 100%; padding-right: 80px; box-sizing: border-box; }
        .board-panel, .game-controls { background: var(--panel); border: 1px solid var(--line); box-shadow: 8px 8px 0 #080f0b; }
        .board-panel { padding: clamp(12px, 2vw, 22px); min-width: 0; flex: 1; }
        .board-heading { display: grid; grid-template-columns: 16px 24px minmax(0, 1fr) 80px; width: 100%; margin-bottom: 4px; color: var(--green); font-size: 12px; letter-spacing: .12em; }
        .board-players { grid-column: 3; justify-self: end; }
        .game-controls { display: flex; flex-direction: column; gap: 14px; width: 274px; flex-shrink: 0; padding: 22px; }
        .status-text { color: var(--green); font-size: 11px; line-height: 1.4; letter-spacing: .16em; }
        .history-heading { display: flex; justify-content: space-between; gap: 8px; color: var(--green); font-size: 12px; letter-spacing: .1em; }
        .move-history-panel { flex: 1; min-height: 180px; overflow-y: auto; border: 1px solid var(--line); background: #101b14; padding: 14px; }
        .move-history { overflow-wrap: anywhere; line-height: 1.8; font-size: 13px; }
        .move-history-entry { display: block; }
        .move-history-entry.current-move { background: #e7cb7d; color: #0c1510; padding: 0 4px; margin: 0 -4px; font-weight: 700; }
        .terminal-button { width: 100%; border: 1px solid var(--green); border-radius: 0; background: transparent; color: var(--green); font-family: inherit; font-weight: 700; letter-spacing: .08em; box-shadow: none; }
        .terminal-button:hover { background: #294733; }
        .terminal-button:focus-visible { outline: 2px solid #f3d68a; outline-offset: 3px; }
        .new-game-button, .board-actions .terminal-button { background: var(--green); color: #0c1510; }
        .new-game-button:hover, .board-actions .terminal-button:hover { background: #cefbd1; }
        .chess-layout { display: grid; grid-template-columns: 16px 24px minmax(0, 1fr) 80px; grid-template-rows: auto 24px; width: 100%; }
        .board-actions { grid-column: 4; grid-row: 1; align-self: end; display: grid; grid-template-columns: repeat(2, 32px); grid-template-rows: repeat(4, 32px); gap: 8px; padding-left: 8px; }
        .board-actions .terminal-button { width: 32px; height: 32px; min-height: 32px; padding: 0; font-size: 20px; line-height: 1; }
        .board-actions .analysis-button { grid-column: span 2; width: 72px; }
        .analysis-button .q-btn__content { display: flex; align-items: center; justify-content: center; }
        .analysis-button .q-btn__content > div { display: flex; }
        .analysis-icon { width: 52px; height: 28px; fill: none; stroke: #0c1510; stroke-width: 2.75; stroke-linecap: round; }
        .analysis-icon circle { fill: #0c1510; stroke: none; }
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
        .evaluation-chart .chart-last-point { fill: #e7cb7d; stroke: #101b14; stroke-width: 3; }
        .evaluation-chart .chart-player-label { font: 700 14px 'SFMono-Regular', Consolas, monospace; letter-spacing: .12em; }
        .evaluation-chart .chart-player-white { fill: var(--green); }
        .evaluation-chart .chart-player-black { fill: #d7e8d6; }
        .evaluation-chart .chart-label, .evaluation-chart .chart-axis-title { fill: var(--muted); font: 14px 'SFMono-Regular', Consolas, monospace; letter-spacing: .06em; }
        .evaluation-chart .chart-axis-title { fill: var(--green); font-weight: 700; }
        .board-actions .record-button { grid-column: span 2; width: 72px; border-color: #f3d68a; background: #0c1510; color: #ff4b45; }
        .record-button .q-btn__content::before { content: '●'; display: inline-block; margin-right: 4px; opacity: 0; }
        .record-button.recording .q-btn__content::before { opacity: 1; animation: record-blink 1s steps(1) infinite; }
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
            .board-panel { display: grid; grid-template-rows: auto auto minmax(0, 1fr); min-height: 0; }
            .status-strip, .board-heading { width: min(100%, calc(100dvh - 158px), 740px); justify-self: center; }
            .chess-layout { width: min(100%, calc(100dvh - 158px), 740px); height: max-content; place-self: center; min-width: 0; grid-template-rows: auto 24px; }
            .move-history-panel { min-height: 0; }
        }
        @media (max-width: 760px) {
            .app-header { align-items: start; }
            .status-strip { flex-wrap: wrap; }
            .game-layout { flex-direction: column; }
            .game-controls { width: 100%; }
            .move-history-panel { max-height: 230px; }
            .landing .q-field.elo-select { position: static; width: 100%; margin-top: 20px; }
        }
    '''
