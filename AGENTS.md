# Project

A simple Chess app to play against Jev. 
Integration of Stockfish to evaluate or compare with Jev.

## Instructions

- Scope & access is only for this repository.
- Update `README.md` with information that helps user in interacting or using the application. Design decisions don't belong here.
- **DO NOT** update `README.md` with every single change. Update only functional information that end user needs. 
- **DO NOT** assume before making any changes. **ALWAYS** ask the user until common-understanding is reached before making major changes.
- Write tests for all relevant features.
- When GUI updates are request to change X, keep scope only to X. Preserve rest of the GUI state. Validate the change before claiming as done.

## Stack

- Python 3.12+
- NiceGUI
- python-chess
- pytest


## Architecture

- Keep chess and AI logic separate from GUI.
- UI code belongs to `src/ui`
- supporting scripts like setup, etc. belongs to `scripts/`
- tests belong to `tests/`

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
