#!/usr/bin/env python3
"""Rewrites the quote line between the DAILY markers in README.md.

Run by .github/workflows/daily-readme.yml. With --chance p the README only
changes with probability p, so two scheduled runs a day give 0–2 updates.

    python scripts/daily_update.py            # always swap the quote
    python scripts/daily_update.py --chance .6
"""

import argparse
import html
import random
import re
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
BLOCK = re.compile(r"(<!-- DAILY:START[^\n]*-->\n)(.*?)(\n<!-- DAILY:END -->)", re.S)

QUOTES = [  # (quote, author): add your own, one per line
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Simplicity is prerequisite for reliability.", "Edsger W. Dijkstra"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
    ("Any fool can write code that a computer can understand. "
     "Good programmers write code that humans can understand.", "Martin Fowler"),
    ("The best way to predict the future is to invent it.", "Alan Kay"),
    ("Premature optimization is the root of all evil.", "Donald Knuth"),
    ("Programs must be written for people to read, "
     "and only incidentally for machines to execute.", "Harold Abelson"),
    ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ("Fix the cause, not the symptom.", "Steve Maguire"),
    ("Before software can be reusable it first has to be usable.", "Ralph Johnson"),
    ("Truth can only be found in one place: the code.", "Robert C. Martin"),
    ("Experience is the name everyone gives to their mistakes.", "Oscar Wilde"),
    ("Walking on water and developing software from a specification "
     "are easy if both are frozen.", "Edward V. Berard"),
    ("Deleted code is debugged code.", "Jeff Sickel"),
    ("The function of good software is to make the complex appear to be simple.", "Grady Booch"),
    ("Controlling complexity is the essence of computer programming.", "Brian Kernighan"),
    ("Testing leads to failure, and failure leads to understanding.", "Burt Rutan"),
    ("If debugging is the process of removing bugs, "
     "then programming must be the process of putting them in.", "Edsger W. Dijkstra"),
    ("It's not a bug, it's an undocumented feature.", "Anonymous"),
    ("Learning never exhausts the mind.", "Leonardo da Vinci"),
    ("Hardware eventually fails. Software eventually works.", "Michael Hartung"),
    ("Good design adds value faster than it adds cost.", "Thomas C. Gale"),
    ("Optimism is an occupational hazard of programming: feedback is the treatment.", "Kent Beck"),
    ("Clean code always looks like it was written by someone who cares.", "Michael Feathers"),
]


def render(quote, author):
    return (f'<p align="center"><sub>💬 <i>"{html.escape(quote, quote=False)}"</i> '
            f'— {html.escape(author, quote=False)}</sub></p>')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--chance", type=float, default=1.0,
                        help="probability (0-1) that this run changes the README")
    args = parser.parse_args()

    if random.random() >= args.chance:
        print(f"skipped this run (chance {args.chance})")
        return

    text = README.read_text(encoding="utf-8")
    block = BLOCK.search(text)
    if not block:
        raise SystemExit("DAILY:START / DAILY:END markers not found in README.md")

    current = block.group(2)
    fresh = [q for q in QUOTES if render(*q) != current] or QUOTES
    quote, author = random.choice(fresh)
    README.write_text(text[:block.start(2)] + render(quote, author) + text[block.end(2):],
                      encoding="utf-8")
    print(f"quote -> {quote} ({author})")


if __name__ == "__main__":
    main()
