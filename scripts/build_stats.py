#!/usr/bin/env python3
"""Renders the live GitHub stats card (stats.svg) and the reach strip
(counters.svg: LinkedIn/Instagram counts from REACH + live GitHub followers
and profile views).

Runs in the profile-assets workflow with the built-in GITHUB_TOKEN and is
published to the `output` branch next to the snake, so the card never depends
on a shared third-party instance staying up. Standard library only.

    GITHUB_TOKEN=... python scripts/build_stats.py --user Apurba2509 --out dist/stats.svg

Preview the layout locally (clearly marked as sample data):

    python scripts/build_stats.py --sample --out preview/stats.svg
"""

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request
from collections import Counter
from datetime import date, timedelta
from xml.sax.saxutils import escape

from build_assets import (BG, BLUE, BORDER, GOOGLE, ICONS, IG_GRADIENT, MONO, MUTED, PANEL,
                          REACH, SANS, SUB, TEXT, YELLOW, border_gradient, mono, svg)

GRID = "#1C2230"  # hairline, one step off the card surface
EYE = (f'<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" fill="none" '
       f'stroke="{SUB}" stroke-width="2.2"/><circle cx="12" cy="12" r="3.2" fill="{SUB}"/>')

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    pullRequests { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# ── data ───────────────────────────────────────────────────────────────────
def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-stats-card"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            if payload.get("errors") or not payload.get("data", {}).get("user"):
                raise RuntimeError(payload.get("errors") or f"user {login!r} not found")
            return payload["data"]["user"]
        except Exception as err:
            if attempt == 2:
                raise
            print(f"GitHub API error, retrying: {err}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))


def fetch_profile_views(login):
    """komarev only exposes its counter inside the badge image (reading it counts
    as one view). Returns None rather than failing the whole run."""
    request = urllib.request.Request(f"https://komarev.com/ghpvc/?username={login}",
                                     headers={"User-Agent": "profile-stats-card"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            numbers = re.findall(r">([\d,]+)</text>", response.read().decode())
        return int(numbers[-1].replace(",", "")) if numbers else None
    except Exception as err:
        print(f"profile views unavailable: {err}", file=sys.stderr)
        return None


def summarize(user):
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = sorted((d for w in calendar["weeks"] for d in w["contributionDays"]),
                  key=lambda d: d["date"])
    counts = [d["contributionCount"] for d in days]

    # today may not have a contribution yet, so a live streak can end yesterday
    current, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0:
        i -= 1
    while i >= 0 and counts[i] > 0:
        current, i = current + 1, i - 1
    best = run = 0
    for c in counts:
        run = run + 1 if c else 0
        best = max(best, run)

    weeks = [(w["contributionDays"][0]["date"], sum(d["contributionCount"] for d in w["contributionDays"]))
             for w in calendar["weeks"] if w["contributionDays"]][-52:]

    languages = Counter()
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            languages[edge["node"]["name"]] += edge["size"]
    total = sum(languages.values()) or 1

    return {
        "contributions": calendar["totalContributions"],
        "current_streak": current,
        "best_streak": best,
        "commits": user["contributionsCollection"]["totalCommitContributions"],
        "pull_requests": user["pullRequests"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "views": None,
        "stars": sum(r["stargazerCount"] for r in user["repositories"]["nodes"]),
        "weeks": weeks,
        "languages": [(name, size / total) for name, size in languages.most_common(6)],
        "sample": False,
    }


def sample_stats():
    rnd = random.Random(7)
    start = date.today() - timedelta(weeks=52)
    weeks = [((start + timedelta(weeks=i)).isoformat(),
              max(0, int(rnd.gauss(9 + 8 * (i / 52), 7)))) for i in range(52)]
    return {
        "contributions": sum(c for _, c in weeks), "current_streak": 6, "best_streak": 19,
        "commits": 402, "pull_requests": 37, "stars": 24, "followers": 42, "views": 1234,
        "weeks": weeks,
        "languages": [("JavaScript", .36), ("Kotlin", .19), ("Dart", .14),
                      ("HTML", .12), ("CSS", .09), ("Python", .05)],
        "sample": True,
    }


# ── render ─────────────────────────────────────────────────────────────────
def compact(n):
    return f"{n / 1000:.1f}K".replace(".0K", "K") if n >= 10_000 else f"{n:,}"


def nice_ceiling(value):
    """Smallest 1/2/4/5/6/8 × 10^k at or above value, for clean axis ticks."""
    step = 1
    while True:
        for m in (1, 2, 4, 5, 6, 8):
            if m * step >= value:
                return m * step
        step *= 10


def column(x, base, w, h, r=4):
    """Bar with a rounded data-end and a square foot on the baseline."""
    r = min(r, w / 2, h)
    return (f"M{x:.1f},{base}V{base - h + r:.1f}A{r:.1f},{r:.1f} 0 0 1 {x + r:.1f},{base - h:.1f}"
            f"H{x + w - r:.1f}A{r:.1f},{r:.1f} 0 0 1 {x + w:.1f},{base - h + r:.1f}V{base}Z")


def row_bar(x, y, w, h, r=4):
    r = min(r, h / 2, w)
    return (f"M{x:.1f},{y:.1f}H{x + w - r:.1f}A{r:.1f},{r:.1f} 0 0 1 {x + w:.1f},{y + r:.1f}"
            f"V{y + h - r:.1f}A{r:.1f},{r:.1f} 0 0 1 {x + w - r:.1f},{y + h:.1f}H{x:.1f}Z")


def render(stats, login):
    W, H, R, PAD = 1000, 362, 18, 40
    css = [
        f".mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}",
        "@keyframes rise{from{opacity:0;transform:translateY(8px)}}",
        "@keyframes up{from{transform:scaleY(0)}}",
        "@keyframes out{from{transform:scaleX(0)}}",
        ".tile{animation:rise .6s ease-out both}",
        ".col{transform-box:fill-box;transform-origin:50% 100%;"
        "animation:up .7s cubic-bezier(.2,.8,.2,1) both}",
        ".lang{transform-box:fill-box;transform-origin:0 50%;"
        "animation:out .9s cubic-bezier(.2,.8,.2,1) both}",
    ]
    defs = [f'<clipPath id="card"><rect width="{W}" height="{H}" rx="{R}"/></clipPath>',
            border_gradient("bd", 9)]
    body = [f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{BG}"/>']

    # header
    body.append(f'<text class="mono" x="{PAD}" y="46" font-size="13" letter-spacing="2.5" '
                f'fill="{MUTED}"><tspan fill="{BLUE}">// </tspan>GITHUB TELEMETRY</text>')
    note = ("sample data · preview only" if stats["sample"]
            else f"@{login} · updated {date.today():%d %b %Y}")
    body.append(f'<text class="mono" x="{W - PAD}" y="46" font-size="12" text-anchor="end" '
                f'fill="{YELLOW if stats["sample"] else MUTED}">{escape(note)}</text>')

    # KPI row
    tiles = [
        ("Contributions", "past year", compact(stats["contributions"]), ""),
        ("Current streak", "consecutive days", str(stats["current_streak"]), " days"),
        ("Longest streak", "past year", str(stats["best_streak"]), " days"),
        ("Commits", "past year", compact(stats["commits"]), ""),
        ("Pull requests", "all time", compact(stats["pull_requests"]), ""),
        ("Stars earned", "public repos", compact(stats["stars"]), ""),
    ]
    tile_w = (W - 2 * PAD) / len(tiles)
    for i, (label, period, value, unit) in enumerate(tiles):
        x = PAD + i * tile_w + (0 if i == 0 else 18)
        if i:
            body.append(f'<rect x="{PAD + i * tile_w:.1f}" y="76" width="1" height="76" fill="{GRID}"/>')
        unit_span = f'<tspan font-size="15" font-weight="400" fill="{MUTED}">{unit}</tspan>' if unit else ""
        body.append(
            f'<g class="tile" style="animation-delay:{i * 70}ms">'
            f'<rect x="{x:.1f}" y="76" width="18" height="3" rx="1.5" fill="{GOOGLE[i % 4]}"/>'
            f'<text class="sans" x="{x:.1f}" y="118" font-size="32" font-weight="600" '
            f'fill="{TEXT}">{value}{unit_span}</text>'
            f'<text class="sans" x="{x:.1f}" y="138" font-size="13" fill="{SUB}">{label}</text>'
            f'<text class="mono" x="{x:.1f}" y="153" font-size="11" fill="{MUTED}">{period}</text></g>'
        )

    # contributions per week: one series, one hue, clean ticks
    x0, x1, base, plot_h = PAD + 30, 612, 318, 96
    weeks = stats["weeks"]
    top = nice_ceiling(max((c for _, c in weeks), default=0) or 10)
    body.append(f'<text class="sans" x="{PAD}" y="196" font-size="13" fill="{SUB}">Contributions'
                f'<tspan fill="{MUTED}"> · per week, last {len(weeks)} weeks</tspan></text>')
    for tick in (0, top // 2, top) if top % 2 == 0 else (0, top):
        y = base - plot_h * tick / top
        body.append(f'<rect x="{x0}" y="{y - .5:.1f}" width="{x1 - x0}" height="1" '
                    f'fill="{BORDER if tick == 0 else GRID}"/>')
        body.append(f'<text class="mono" x="{x0 - 8}" y="{y + 4:.1f}" font-size="10" '
                    f'text-anchor="end" fill="{MUTED}">{tick:,}</text>')
    slot = (x1 - x0) / max(len(weeks), 1)
    bar_w = min(24, slot * 0.62)
    peak = max(range(len(weeks)), key=lambda i: weeks[i][1], default=None)
    last_label_x, last_month = -99, None
    for i, (start, count) in enumerate(weeks):
        cx = x0 + slot * i + slot / 2
        if count:
            h = max(2, plot_h * count / top)
            body.append(f'<path class="col" style="animation-delay:{300 + i * 14}ms" '
                        f'd="{column(cx - bar_w / 2, base, bar_w, h)}" fill="{BLUE}"/>')
        month = date.fromisoformat(start).strftime("%b")
        if month != last_month and cx - last_label_x > 34:
            body.append(f'<text class="mono" x="{cx:.1f}" y="{base + 18}" font-size="10" '
                        f'text-anchor="middle" fill="{MUTED}">{month}</text>')
            last_label_x = cx
        last_month = month
    if peak is not None and weeks[peak][1]:
        cx = x0 + slot * peak + slot / 2
        y = base - max(2, plot_h * weeks[peak][1] / top) - 7
        anchor = "end" if cx > x1 - 40 else "middle"
        body.append(f'<text class="mono tile" style="animation-delay:1.1s" x="{cx:.1f}" y="{y:.1f}" '
                    f'font-size="11" text-anchor="{anchor}" fill="{TEXT}">peak {weeks[peak][1]:,}</text>')

    # top languages: sorted bars, one hue, value at the tip
    lx, bar_x, bar_max = 664, 760, 150
    body.append(f'<text class="sans" x="{lx}" y="196" font-size="13" fill="{SUB}">Top languages'
                f'<tspan fill="{MUTED}"> · share of code</tspan></text>')
    langs = stats["languages"]
    biggest = max((s for _, s in langs), default=1) or 1
    for i, (name, share) in enumerate(langs):
        y = 222 + i * 20
        shown = name if len(name) <= 13 else name[:12] + "…"
        body.append(f'<text class="sans" x="{lx}" y="{y + 9}" font-size="12.5" fill="{TEXT}">{escape(shown)}</text>')
        w = max(3, bar_max * share / biggest)
        body.append(f'<path class="lang" style="animation-delay:{500 + i * 90}ms" '
                    f'd="{row_bar(bar_x, y, w, 10)}" fill="{BLUE}"/>')
        body.append(f'<text class="mono tile" style="animation-delay:{900 + i * 90}ms" x="{bar_x + w + 8:.1f}" '
                    f'y="{y + 9}" font-size="11" fill="{SUB}">{share * 100:.1f}%</text>')
    if not langs:
        body.append(f'<text class="mono" x="{lx}" y="232" font-size="12" fill="{MUTED}">no public code yet</text>')

    body.append("</g>")
    body.append(f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{R}" '
                f'fill="none" stroke="url(#bd)" stroke-width="1.5" opacity=".75"/>')

    label = (f"GitHub stats for @{login}: {stats['contributions']:,} contributions in the past year, "
             f"current streak {stats['current_streak']} days, longest streak {stats['best_streak']} days, "
             f"{stats['commits']:,} commits in the past year, {stats['pull_requests']:,} pull requests, "
             f"{stats['stars']:,} stars. Top languages: "
             + (", ".join(f"{n} {s * 100:.1f}%" for n, s in langs) or "none"))
    return svg(W, H, label, css, defs, body)


def render_counters(stats, login):
    """Reach strip: hand-typed LinkedIn/Instagram counts (REACH in build_assets.py)
    followed by live GitHub followers and profile views."""
    H, PAD, TILE = 44, 16, 20
    groups = {}
    for platform, number, label in REACH:
        groups.setdefault(platform, []).append((number, label))
    groups["github"] = [(f"{stats['followers']:,}", "followers")]
    if stats.get("views") is not None:
        groups["views"] = [(f"{stats['views']:,}", "profile views")]
    names = {"linkedin": "LinkedIn: ", "instagram": "Instagram: ", "github": "GitHub: ", "views": ""}

    y = H / 2 + 5
    parts, x = [], PAD
    for g, (platform, items) in enumerate(groups.items()):
        if g:
            parts.append(f'<rect x="{x + 11:.1f}" y="13" width="1" height="{H - 26}" fill="{BORDER}"/>')
            x += 23
        tile, glyph = ("#1F2633", EYE) if platform == "views" else ICONS.get(platform, ("#1F2633", ""))
        parts.append(f'<rect x="{x:.1f}" y="{(H - TILE) / 2}" width="{TILE}" height="{TILE}" rx="5.5" fill="{tile}"/>'
                     f'<g transform="translate({x + 4:.1f} {(H - TILE) / 2 + 4}) scale(.5)">{glyph}</g>')
        x += TILE + 9
        for i, (number, label) in enumerate(items):
            if i:
                parts.append(mono(x, y, [("·", MUTED)], 12))
                x += 1 * 12 * 0.6 + 8
            parts.append(mono(x, y, [(number, TEXT, True)], 14))
            x += len(number) * 14 * 0.6 + 6
            parts.append(mono(x, y, [(label, MUTED)], 12))
            x += len(label) * 12 * 0.6 + 6
    W = round(x - 6 + PAD)
    body = [f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{H / 2 - .75}" '
            f'fill="{PANEL}" stroke="{BORDER}" stroke-width="1.5"/>'] + parts
    label = " · ".join(names.get(p, p.title() + ": ") + ", ".join(f"{n} {l}" for n, l in items)
                       for p, items in groups.items())
    return svg(W, H, label, [f".mono{{font-family:{MONO}}}"], [IG_GRADIENT], body)

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "Apurba2509"))
    parser.add_argument("--out", default="dist/stats.svg")
    parser.add_argument("--sample", action="store_true", help="render with made-up data")
    args = parser.parse_args()

    if args.sample:
        stats = sample_stats()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("GITHUB_TOKEN is not set (use --sample for a local preview)")
        stats = summarize(fetch(args.user, token))
        stats["views"] = fetch_profile_views(args.user)

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(stats, args.user))
    counters = os.path.join(os.path.dirname(out), "counters.svg")
    with open(counters, "w", encoding="utf-8") as f:
        f.write(render_counters(stats, args.user))
    print(f"wrote {args.out} and {counters}")


if __name__ == "__main__":
    main()
