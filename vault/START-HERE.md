# Start Here

Project memory for the Earnings Quality Scanner. Adapted from the repo-continuity template (github.com/vector233/repo-continuity): the repo files, not chat history, are the source of truth.

## Resume a session (read in this order)
1. `CLAUDE.md` (repo root): rules and phases
2. The latest entry in [[build-log]]: where we stopped and the next step
3. Only the note you need:

| Need | Note |
|---|---|
| What counts as done for a phase | [[requirements]] |
| Why something is built the way it is | [[design-notes]] |
| Known traps and bugs | [[gotchas]] |

## Writeback (end of every session)
- Add a build log entry (template is at the top of [[build-log]])
- New decision → [[design-notes]]. New trap or bug → [[gotchas]]
- Tick finished phases in `CLAUDE.md` and [[requirements]]
