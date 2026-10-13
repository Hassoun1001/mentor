"""Strategy lab — trading plans proposed, tested harshly, paper-traded, promoted.

The owner asked for a system that "acts like a professional trader:
learns, designs patterns and plans". A professional's real edge is not a
pattern; it is the discipline of not believing a pattern until it has
earned it. This package is that discipline, written down:

- ``spec`` — what a plan is: entry, stop, target, time stop, sizing,
  timeframe, and a plain-language reason it might work.
- ``rules`` / ``library`` — the candidate ideas, each a small
  parameterised rule family with a deliberately small grid.
- ``simulator`` — one position at a time, bar by bar, full costs; the same
  code runs history and the live paper book.
- ``gate`` + ``deflation`` — walk-forward selection, a held-out period
  touched once, and a bar that rises with every trial ever run.
- ``live`` — paper-trading verdicts: promote, demote, retire.

The system never places a real trade. Most ideas are expected to fail
here, and a lab that says so is working.
"""
