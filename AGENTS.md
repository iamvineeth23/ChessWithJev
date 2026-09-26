# Project

A simple Chess app to play against Jev. 
Integration of Stockfish to evaluate or compare with Jev.

## Instructions

- Scope & access is only for this repository.
- Update `README.md` with information that helps user in interacting or using the application. Design decisions don't belong here.
- **DO NOT** update `README.md` with every single change. Update only functional information that end user needs. 
- **DO NOT** assume before making any changes. **ALWAYS** ask the user until common-understanding is reached before making major changes.
- Write tests for all relevant features.
- When GUI updates are requested, keep scope precise to requested change. If any other changes occur as a consequence of one action, inform the user and avoid regressions.

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
