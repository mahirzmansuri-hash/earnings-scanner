---
name: end-session
description: Close out a work session on the Earnings Quality Scanner - run the explain-back, update the build log, design notes, gotchas and phase checkboxes, update the linked Obsidian note, then commit. Use when the user says "end session", "wrap up", "let's stop here", or runs /end-session.
---

# End a session

Do these in order. Keep it short.

## 1. Explain-back (skip only if the user already did one this session)
Ask the user 2-3 questions about what we built today, in plain words:
- What does the new code/file do?
- Why did we make the key choice (for example, filed date vs period end)?
- What could go wrong with it?
Let them answer first. Then correct gaps briefly. Don't lecture.

## 2. Repo memory (`vault/`)
- `vault/build-log.md`: add an entry at the bottom using the template at the top of that file (Did / Decisions / Bugs / State / Next). Use today's date (YYYY-MM-DD). Record the user's explain-back gaps under "Next" if any.
- `vault/design-notes.md`: one entry per new decision (what, why, trade-off).
- `vault/gotchas.md`: one entry per new trap (symptom → cause → fix).
- Tick finished items in `vault/requirements.md` and phases in `CLAUDE.md`.

## 3. Obsidian note (linked brain)
Edit only `/Users/mahir/Documents/Obsidian Vault/Mahir's Second Brain/Areas/Earnings Quality Scanner.md`:
- Add one line under "## Progress log": `- YYYY-MM-DD: <what we did>. Next: <next step>.`
- Update phase checkboxes and the `status` frontmatter if they changed.
Never edit other notes in that vault. Never copy vault notes into the repo.

## 4. Commit
- Show the user `git status --short` and a one-line summary of the changes.
- Check that `.env` is not staged (`git diff --cached --name-only | grep -x .env` must print nothing).
- Commit with a short message describing the session, and end the message with the attribution line from the session's instructions. Push only if the user says to.

## 5. Report
In 3-4 lines: what's saved, what's next session's first step, roughly how long it will take.

## Session summary for Mahir (required, last thing in the session)
Give a running summary of EVERYTHING done so far in the project (start to now), not just this session:
- small bullet points, very short sentences, simple words
- grouped by stage; newest session at the bottom
- each bullet = what was done, in plain English (no code), plus a real number where it helps
Also save it to `vault/summary.md` (overwrite with the updated full version).
