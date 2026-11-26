---
name: review-my-score
description: Coach the user while THEY write the Beneish M-Score, Piotroski F-Score, or Altman Z-Score code, and review what they wrote. Use when the user is working on files in src/scores/, asks for help with a score formula, or runs /review-my-score. Never write the formula code for them.
---

# Review my score code (coach, don't write)

CLAUDE.md rule: the user writes the three score formulas. This skill keeps it that way.

## When they're starting a score
Give them, briefly:
- the formula, written as math
- each input: what it means in plain English, and which XBRL tag(s) and statement it comes from
- the interpretation thresholds (M > -1.78 flags a likely manipulator; F is 0-9; Z: >3 safe, 1.8-3 gray zone, <1.8 distress)
- one worked example with real numbers, so they can test against it
Then stop and let them code.

## When they share code
1. Run it if there's a test or example. Otherwise ask them to write a pytest check with the worked example first.
2. Review in this order: correctness of the math → right inputs and periods (current vs prior year, point-in-time) → edge cases (divide by zero, missing tags, negative equity) → readability.
3. For each problem: say **where** (line), **what** is wrong, and **a hint** toward the fix. Don't paste corrected code. If they're stuck after 2 hints, show a small piece (one line or one ratio), not the whole function.
4. Praise what's right, specifically and briefly.

## Allowed vs not allowed
- OK: explaining Python syntax, pandas methods, writing the test harness, writing data-loading helpers that feed the score.
- Not OK: writing the score function body, or writing any of the ratio calculations for them.
