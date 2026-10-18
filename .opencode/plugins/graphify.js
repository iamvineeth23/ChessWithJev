// graphify OpenCode plugin (OpenCode V2 plugin API)
// Injects a knowledge graph reminder before the first bash tool call when the
// graph exists.
//
// IMPORTANT: keep the reminder string free of backticks and $(...) constructs.
// The hook prepends `echo "<reminder>" && <cmd>` to the user's bash command;
// backticks inside the double-quoted echo trigger bash command substitution,
// which both corrupts tool output and silently executes the very graphify
// command we are only suggesting. Plain words render fine in opencode's TUI.
//
// V2 requires a *default* export: `export default Plugin.define({ id, setup })`.
// A V1 named export ("export const GraphifyPlugin = ...") silently fails to
// load with "Plugin must export a default definition" (err_a9eb3dc5 family).
import { existsSync } from "fs";
import { join } from "path";
import { Plugin } from "@opencode/plugin";

export default Plugin.define({
  id: "graphify",
  async setup(ctx) {
    // V1 plugins received `{ directory }`; V2 exposes it on the context.
    const directory = ctx.location.directory;
    let reminded = false;

    // V1 hook "tool.execute.before" maps to ctx.tool.hook("execute.before", ...).
    await ctx.tool.hook("execute.before", (event) => {
      if (reminded) return;
      if (!existsSync(join(directory, "graphify-out", "graph.json"))) return;

      if (event.tool === "bash") {
        // ';' not '&&' — Windows PowerShell 5.1 rejects '&&' as a statement
        // separator, breaking the first bash command of the session (#1646).
        event.input.command =
          'echo "[graphify] knowledge graph at graphify-out/. For focused questions, run graphify query with your question (scoped subgraph, usually much smaller than GRAPH_REPORT.md) instead of grepping raw files. Read GRAPH_REPORT.md only for broad architecture context." ; ' +
          event.input.command;
        reminded = true;
      }
    });
  },
});
