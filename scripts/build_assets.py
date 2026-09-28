#!/usr/bin/env python3
"""Generates the animated SVGs in ../assets used by the profile README.

Everything is pure SVG with CSS/SMIL animation (no JavaScript, no external
requests), so it renders inside GitHub's <img> sandbox and can't break when a
third-party card service goes down.

Edit the CONTENT block below, then run:

    python scripts/build_assets.py
"""

import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# ── palette ────────────────────────────────────────────────────────────────
BG, PANEL, BAR, BORDER = "#0A0D14", "#0D1117", "#161B22", "#30363D"
TEXT, SUB, MUTED, DIM = "#E6EDF3", "#C9D1D9", "#8B949E", "#484F58"
BLUE, RED, YELLOW, GREEN = "#4285F4", "#EA4335", "#FBBC05", "#34A853"
GOOGLE = [BLUE, RED, YELLOW, GREEN]

MONO = ("ui-monospace,'SF Mono','Cascadia Code','JetBrains Mono',Menlo,"
        "Consolas,'DejaVu Sans Mono',monospace")
SANS = ("'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',"
        "Roboto,Arial,sans-serif")
MONO_ADVANCE = 0.6  # glyph width in em; textLength pins every font to this grid

# ── content ────────────────────────────────────────────────────────────────
NAME = "APURBA DAS"
GREETING = "hi there, i'm"
STATUS = "OPEN TO COLLABS"
AFFILIATION = "BCA · TECHNO MAIN SALT LAKE"
ROLES = [
    "Full-Stack Developer",
    "Mobile Developer",
    "Cloud & AI Enthusiast",
    "Open-Source Contributor",
    "Tech Community Lead",
]

HOST = ("apurba", "tmsl")
NEOFETCH = [
    ("Name", "Apurba Das"),
    ("Role", "Full-Stack & Mobile Developer"),
    ("Study", "BCA @ Techno Main Salt Lake"),
    ("GDG", "On-Campus TMSL · Social Media Head & PR Core"),
    ("QZone", "Joint Head"),
    ("Cloud", "Google Cloud Arcade Co-Facilitator · 2026 Cohort"),
    ("Stack", "React · Flutter · Node · Firebase · AWS · GCP"),
    ("Focus", "engaging UI + robust backend architecture"),
    ("Uptime", "taking ideas from 0 → 1"),
]
OPEN_TO_DIR = "~/open-to-discuss"
OPEN_TO = ["cross-platform-mobile/", "hackathons/", "open-source/"]

FOOTER_TITLE = "Thanks for stopping by"
FOOTER_LINE = "let's build something from 0 → 1"

SOCIALS = [  # (file name, platform, handle) — the link URLs live in README.md
    ("linkedin", "LINKEDIN", "apurbadas2509"),
    ("instagram", "INSTAGRAM", "@___apurbax___"),
    ("github", "GITHUB", "@Apurba2509"),
]

SECTIONS = [  # (file name, title, subtitle) in page order
    ("whoami", "WHOAMI", "the human behind the commits"),
    ("builds", "HACKATHONS & BUILDS", "shipped against the clock"),
    ("community", "OPEN SOURCE & COMMUNITY", "building in public, with people"),
    ("arsenal", "TECH ARSENAL", "tools of the trade"),
    ("stats", "LIVE STATS", "auto-updated every 12 hours"),
    ("achievements", "ACHIEVEMENTS", "badges collected along the way"),
]

# 7-row pixel font for the neofetch monogram
PIXEL_FONT = {
    "A": [".####.", "##..##", "##..##", "######", "##..##", "##..##", "##..##"],
    "D": ["#####.", "##..##", "##..##", "##..##", "##..##", "##..##", "#####."],
}
MONOGRAM = "AD"


# ── helpers ────────────────────────────────────────────────────────────────
def svg(w, h, label, css, defs, body):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
        f'aria-label="{escape(label, {chr(34): "&quot;"})}">'
        f"<title>{escape(label)}</title>"
        f"<style><![CDATA[{''.join(css)}]]></style>"
        f"<defs>{''.join(defs)}</defs>{''.join(body)}</svg>\n"
    )


def tspan(text, fill, bold=False):
    weight = ' font-weight="700"' if bold else ""
    return f'<tspan fill="{fill}"{weight}>{escape(text)}</tspan>'


def mono(x, y, segments, size, anchor=None, attrs=""):
    """One monospace line pinned to an exact width with textLength, so glyph
    cells line up with cursors and curtains whichever fallback font renders."""
    n = sum(len(s[0]) for s in segments)
    anchor_attr = f' text-anchor="{anchor}"' if anchor else ""
    return (
        f'<text class="mono" x="{x:.1f}" y="{y:.1f}" font-size="{size}"'
        f'{anchor_attr} textLength="{n * size * MONO_ADVANCE:.1f}" '
        f'lengthAdjust="spacing" xml:space="preserve"{attrs}>'
        f'{"".join(tspan(*s) for s in segments)}</text>'
    )


def discrete(attr, period, events, fmt):
    """SMIL step animation from [(seconds, value)]; the first event is at 0."""
    key_times = ";".join(f"{t / period:.5f}" for t, _ in events)
    values = ";".join(fmt(v) for _, v in events)
    return (
        f'<animate attributeName="{attr}" dur="{period:.3f}s" '
        f'repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{key_times}" values="{values}"/>'
    )


def border_gradient(gid, seconds):
    stops = "".join(
        f'<stop offset="{i / 3:.3f}" stop-color="{c}"/>' for i, c in enumerate(GOOGLE)
    )
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">{stops}'
        f'<animateTransform attributeName="gradientTransform" type="rotate" '
        f'values="0 .5 .5;360 .5 .5" dur="{seconds}s" repeatCount="indefinite"/>'
        "</linearGradient>"
    )


def shine_gradient(gid, span, sweep_from, sweep_to, seconds, base="#F5F8FF"):
    """A Google-coloured band that sweeps across text every few seconds."""
    stops = [(0, base), (0.30, base), (0.40, BLUE), (0.48, RED),
             (0.56, YELLOW), (0.64, GREEN), (0.74, base), (1, base)]
    stops_xml = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return (
        f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" '
        f'x1="0" y1="0" x2="{span}" y2="0">{stops_xml}'
        f'<animateTransform attributeName="gradientTransform" type="translate" '
        f'values="{sweep_from} 0;{sweep_to} 0;{sweep_to} 0" keyTimes="0;.5;1" '
        f'calcMode="spline" keySplines=".45 0 .55 1;0 0 1 1" '
        f'dur="{seconds}s" repeatCount="indefinite"/></linearGradient>'
    )


class Timeline:
    """Builds per-element @keyframes on one shared loop of `period` seconds."""

    def __init__(self, period):
        self.period = period
        self.css = []
        self.count = 0

    def pct(self, t):
        return f"{min(max(t / self.period * 100, 0), 100):.3f}%"

    def anim(self, stops):
        """stops: [(seconds, 'css props', optional timing-function)]."""
        name = f"k{self.count}"
        self.count += 1
        frames = []
        for stop in stops:
            timing = f";animation-timing-function:{stop[2]}" if len(stop) > 2 else ""
            frames.append(f"{self.pct(stop[0])}{{{stop[1]}{timing}}}")
        self.css.append(f"@keyframes {name}{{{''.join(frames)}}}")
        self.css.append(f".{name}{{animation:{name} {self.period}s linear infinite}}")
        return name

    def show_at(self, t):
        return self.anim([(0, "opacity:0"), (t - 0.01, "opacity:0"),
                          (t, "opacity:1"), (self.period, "opacity:1")])


# ── hero ───────────────────────────────────────────────────────────────────
def build_hero():
    W, H, R, HZ = 1000, 410, 18, 312  # HZ = horizon of the synthwave floor
    rnd = random.Random(2509)
    css = [
        f".mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}",
        "@keyframes tw{0%,100%{opacity:.08}50%{opacity:.9}}",
        ".stars circle{fill:#fff;animation:tw 4s ease-in-out infinite}",
        f"@keyframes hl{{to{{transform:translateY({H - HZ}px)}}}}",
        ".hl{animation:hl 3.4s cubic-bezier(.55,0,.9,.55) infinite}",
        f"@keyframes sweep{{to{{transform:translateY({H + 160}px)}}}}",
        ".sweep{animation:sweep 7s linear infinite}",
        "@keyframes ping{from{transform:scale(1);opacity:.9}"
        "to{transform:scale(3.4);opacity:0}}",
        ".ping{animation:ping 2s ease-out infinite;"
        "transform-box:fill-box;transform-origin:center}",
        "@keyframes blink{50%{opacity:0}}",
        ".blink{animation:blink 1.05s steps(1) infinite}",
        "@keyframes pulse{0%,100%{opacity:.35}50%{opacity:.7}}",
        ".glow{animation:pulse 3.2s ease-in-out infinite}",
        # glitch burst every 4.8s: chromatic copies, a displaced slice, a skew
        "@keyframes gr{0%,85%,95%,100%{opacity:0;transform:translate(0,0)}"
        "86%{opacity:.9;transform:translate(-7px,-2px)}"
        "89%{opacity:.9;transform:translate(6px,2px)}"
        "92%{opacity:.9;transform:translate(-3px,1px)}}",
        "@keyframes gb{0%,85%,95%,100%{opacity:0;transform:translate(0,0)}"
        "86%{opacity:.9;transform:translate(7px,2px)}"
        "89%{opacity:.9;transform:translate(-6px,-2px)}"
        "92%{opacity:.9;transform:translate(3px,-1px)}}",
        "@keyframes gs{0%,85%,94%,100%{opacity:0;transform:translateX(0)}"
        "86%{opacity:1;transform:translateX(18px)}"
        "89%{opacity:1;transform:translateX(-14px)}"
        "92%{opacity:1;transform:translateX(9px)}}",
        "@keyframes gm{0%,85%,94%,100%{transform:none}"
        "87%{transform:skewX(-7deg)}90%{transform:skewX(5deg)}}",
        ".gr{animation:gr 4.8s linear infinite;mix-blend-mode:screen}",
        ".gb{animation:gb 4.8s linear infinite;mix-blend-mode:screen}",
        ".gs{animation:gs 4.8s steps(1) infinite}",
        ".gm{animation:gm 4.8s steps(1) infinite;"
        "transform-box:fill-box;transform-origin:center}",
    ]
    defs = [
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="{R}"/></clipPath>',
        border_gradient("bd", 9),
        shine_gradient("shine", 700, -420, 760, 6.5),
        '<filter id="blur" x="-20%" y="-60%" width="140%" height="220%">'
        '<feGaussianBlur stdDeviation="16"/></filter>',
        '<linearGradient id="fmg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#fff"/>'
        "</linearGradient>",
        f'<mask id="fm"><rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#fmg)"/></mask>',
        '<linearGradient id="hz" x1="0" x2="1">'
        f'<stop offset="0" stop-color="{BLUE}" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#8AB4F8"/>'
        f'<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></linearGradient>',
        f'<radialGradient id="hglow"><stop offset="0" stop-color="{BLUE}" stop-opacity=".45"/>'
        f'<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>',
        '<radialGradient id="vig" cx=".5" cy=".42" r=".75">'
        f'<stop offset=".55" stop-color="{BG}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{BG}" stop-opacity=".9"/></radialGradient>',
        '<linearGradient id="sw" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#8AB4F8" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#8AB4F8" stop-opacity=".07"/>'
        '<stop offset="1" stop-color="#8AB4F8" stop-opacity="0"/></linearGradient>',
        '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="#fff" opacity=".035"/></pattern>',
        '<clipPath id="slices"><rect y="150" width="1000" height="11"/>'
        '<rect y="181" width="1000" height="7"/><rect y="203" width="1000" height="13"/>'
        "</clipPath>",
        f'<text id="nm" class="sans" x="500" y="222" text-anchor="middle" '
        f'font-size="100" font-weight="900" textLength="680" '
        f'lengthAdjust="spacingAndGlyphs">{escape(NAME)}</text>',
    ]
    body = [f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{BG}"/>']

    # drifting aurora orbs in the four Google colours
    orbs = [(170, 80, 300, BLUE, 17, 140, 50), (860, 70, 260, RED, 21, -120, 60),
            (720, 340, 260, YELLOW, 19, -90, -70), (130, 350, 240, GREEN, 23, 110, -60)]
    for i, (cx, cy, r, col, dur, dx, dy) in enumerate(orbs):
        defs.append(
            f'<radialGradient id="orb{i}"><stop offset="0" stop-color="{col}" stop-opacity=".34"/>'
            f'<stop offset=".5" stop-color="{col}" stop-opacity=".1"/>'
            f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>'
        )
        css.append(f"@keyframes orb{i}{{50%{{transform:translate({dx}px,{dy}px) scale(1.15)}}}}")
        css.append(f".orb{i}{{animation:orb{i} {dur}s ease-in-out infinite;"
                   "transform-box:fill-box;transform-origin:center}")
        body.append(f'<circle class="orb{i}" cx="{cx}" cy="{cy}" r="{r}" fill="url(#orb{i})"/>')

    text_zones = [(360, 104, 640, 138), (150, 136, 850, 236), (220, 250, 780, 292)]
    stars = []
    while len(stars) < 48:
        x, y = rnd.uniform(24, W - 24), rnd.uniform(64, HZ - 16)
        if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in text_zones):
            continue  # a star behind a glyph reads as a stray dot
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rnd.choice([.6, .8, 1, 1.2, 1.5])}" '
            f'style="animation-duration:{rnd.uniform(2.2, 5.5):.2f}s;'
            f'animation-delay:{-rnd.uniform(0, 5):.2f}s"/>'
        )
    body.append(f'<g class="stars">{"".join(stars)}</g>')

    # synthwave floor: converging rails + lines rushing toward the viewer
    floor = [f'<line x1="{500 + i * 22}" y1="{HZ}" x2="{500 + i * 140}" y2="{H}"/>'
             for i in range(-14, 15)]
    floor += [f'<line class="hl" x1="0" y1="{HZ}" x2="{W}" y2="{HZ}" '
              f'style="animation-delay:{-i * 3.4 / 7:.3f}s"/>' for i in range(7)]
    body.append(f'<ellipse cx="500" cy="{HZ}" rx="440" ry="54" fill="url(#hglow)"/>')
    body.append(f'<g mask="url(#fm)" stroke="{BLUE}" stroke-opacity=".6">{"".join(floor)}</g>')
    body.append(f'<rect y="{HZ - .75}" width="{W}" height="1.5" fill="url(#hz)"/>')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    body.append(f'<rect class="sweep" y="-160" width="{W}" height="160" fill="url(#sw)"/>')

    # greeting + glitching name
    body.append(mono(500, 128, [("// ", BLUE), (GREETING, MUTED)], 20, anchor="middle"))
    body.append(
        f'<use xlink:href="#nm" class="glow" fill="{BLUE}" filter="url(#blur)"/>'
        f'<use xlink:href="#nm" class="gr" fill="{RED}"/>'
        f'<use xlink:href="#nm" class="gb" fill="#00C2FF"/>'
        '<use xlink:href="#nm" class="gm" fill="url(#shine)"/>'
        '<g clip-path="url(#slices)"><use xlink:href="#nm" class="gs" fill="#fff"/></g>'
    )

    # role rotator: type, hold, backspace, next
    fs, ry = 26, 280
    cw = fs * MONO_ADVANCE
    TYPE, HOLD, DEL, LEAD, GAP = 0.065, 1.8, 0.03, 0.35, 0.3
    t, schedule = 0.0, []
    for role in ROLES:
        n = len(role)
        events = [(t, 0)] + [(t + LEAD + k * TYPE, k) for k in range(1, n + 1)]
        typed = t + LEAD + n * TYPE
        events += [(typed + HOLD + (n - k) * DEL, k) for k in range(n - 1, -1, -1)]
        gone = typed + HOLD + n * DEL + 0.12
        events.append((gone, None))
        schedule.append(events)
        t = gone + GAP
    period = t

    caret_events = []
    for i, (role, events) in enumerate(zip(ROLES, schedule)):
        x0 = 500 - ((2 + len(role)) * cw + 0.6 * cw) / 2
        clip_events = events if events[0][0] == 0 else [(0, None)] + events
        width = discrete("width", period, clip_events,
                         lambda k: "0" if k is None else f"{(2 + k) * cw + 2:.1f}")
        defs.append(f'<clipPath id="rc{i}"><rect x="{x0 - 2:.1f}" y="{ry - fs}" '
                    f'height="{fs + 12}" width="0">{width}</rect></clipPath>')
        body.append(f'<g clip-path="url(#rc{i})">'
                    f'{mono(x0, ry, [("❯ ", GREEN, True), (role, TEXT)], fs)}</g>')
        caret_events += [(et, None if k is None else x0 + (2 + k) * cw + 2) for et, k in events]
    caret_x = discrete("x", period, caret_events,
                       lambda x: "-100" if x is None else f"{x:.1f}")
    body.append(f'<rect class="blink" x="-100" y="{ry - fs + 5}" width="{cw * .55:.1f}" '
                f'height="{fs + 2}" fill="{BLUE}">{caret_x}</rect>')

    # HUD: status, affiliation, corner brackets
    body.append(f'<circle cx="72" cy="41" r="4.5" fill="{GREEN}"/>'
                f'<circle class="ping" cx="72" cy="41" r="4.5" fill="none" '
                f'stroke="{GREEN}" stroke-width="1.5"/>')
    body.append(f'<text class="mono" x="88" y="46" font-size="13" letter-spacing="2.5" '
                f'fill="{MUTED}">{escape(STATUS)}</text>')
    body.append(f'<text class="mono" x="{W - 64}" y="46" font-size="13" letter-spacing="2.5" '
                f'text-anchor="end" fill="{MUTED}">{escape(AFFILIATION)}</text>')
    corners = [(f"M24 52V24H52", BLUE), (f"M{W - 52} 24H{W - 24}V52", RED),
               (f"M{W - 24} {H - 52}V{H - 24}H{W - 52}", YELLOW), (f"M52 {H - 24}H24V{H - 52}", GREEN)]
    body += [f'<path d="{d}" fill="none" stroke="{c}" stroke-width="2.5" '
             f'stroke-linecap="round" opacity=".9"/>' for d, c in corners]

    body.append(f'<rect width="{W}" height="{H}" fill="url(#scan)"/></g>')
    body.append(f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{R}" '
                f'fill="none" stroke="url(#bd)" stroke-width="1.5" opacity=".75"/>')

    label = f"{NAME.title()}: " + ", ".join(ROLES)
    return svg(W, H, label, css, defs, body)


# ── terminal (neofetch) ────────────────────────────────────────────────────
def build_terminal():
    W, FS, LH, PX, TOP = 1000, 16, 25, 28, 40
    CW = FS * MONO_ADVANCE
    T = 18.0
    tl = Timeline(T)

    def Y(line):
        return TOP + 34 + line * LH

    H = round(Y(17) + 26)
    PROMPT = [("~", BLUE, True), (" ❯ ", GREEN, True)]
    prompt_w = sum(len(s[0]) for s in PROMPT) * CW

    css = [
        f".mono{{font-family:{MONO}}}",
        "@keyframes blink{50%{opacity:0}}",
        ".blink{animation:blink 1.05s steps(1) infinite}",
        ".px rect{transform-box:fill-box;transform-origin:center}",
    ]
    defs = [
        '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="#fff" opacity=".022"/></pattern>',
        '<radialGradient id="tg" cx=".88" cy="0" r=".7">'
        f'<stop offset="0" stop-color="{BLUE}" stop-opacity=".10"/>'
        f'<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="rule" x1="0" x2="1">'
        + "".join(f'<stop offset="{i / 3:.3f}" stop-color="{c}"/>' for i, c in enumerate(GOOGLE))
        + "</linearGradient>",
    ]
    body = []
    content = []

    def command(line, cmd, t_prompt, t_type, per_char, t_done):
        """Prompt appears, command is typed behind a sliding curtain, cursor rides along."""
        y = Y(line)
        n = sum(len(s[0]) for s in cmd)
        x = PX + prompt_w
        dist = n * CW
        t_end = t_type + n * per_char
        content.append(f'<g class="{tl.show_at(t_prompt)}">{mono(PX, y, PROMPT, FS)}</g>')
        content.append(mono(x, y, cmd, FS))
        curtain = tl.anim([(0, "transform:translateX(0)"),
                           (t_type, "transform:translateX(0)", f"steps({n},end)"),
                           (t_end, f"transform:translateX({dist:.1f}px)"),
                           (T, f"transform:translateX({dist:.1f}px)")])
        content.append(f'<rect class="{curtain}" x="{x - 1:.1f}" y="{y - LH + 7}" '
                       f'width="{dist + 2:.1f}" height="{LH}" fill="{PANEL}"/>')
        at = lambda d: f"transform:translateX({d:.1f}px)"
        cursor = tl.anim([(0, "opacity:0;" + at(0)), (t_prompt - .01, "opacity:0;" + at(0)),
                          (t_prompt, "opacity:1;" + at(0)),
                          (t_type, "opacity:1;" + at(0), f"steps({n},end)"),
                          (t_end, "opacity:1;" + at(dist)), (t_done - .01, "opacity:1;" + at(dist)),
                          (t_done, "opacity:0;" + at(dist)), (T, "opacity:0;" + at(dist))])
        content.append(f'<rect class="{cursor}" x="{x:.1f}" y="{y - FS + 2}" '
                       f'width="{CW:.1f}" height="{FS + 3}" fill="{SUB}"/>')

    # window chrome
    body.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" '
                f'fill="{PANEL}" stroke="{BORDER}"/>')
    body.append(f'<path d="M.5 14.5A14 14 0 0 1 14.5 .5H{W - 14.5}A14 14 0 0 1 {W - .5} 14.5'
                f'V{TOP}H.5Z" fill="{BAR}"/>')
    body.append(f'<rect y="{TOP - 1}" width="{W}" height="1.5" fill="url(#rule)" opacity=".7"/>')
    body += [f'<circle cx="{22 + i * 20}" cy="20" r="6" fill="{c}"/>'
             for i, c in enumerate([RED, YELLOW, GREEN])]
    body.append(f'<text class="mono" x="{W / 2}" y="25" font-size="13" text-anchor="middle" '
                f'fill="{MUTED}">{HOST[0]}@{HOST[1]}: ~ — zsh — 100×30</text>')

    # 1) neofetch
    t_out = 2.0
    command(0, [("neofetch", TEXT, True)], 0.4, 1.0, 0.085, t_out)

    # pixel monogram, popping in as a diagonal wave
    pitch, size = 22, 19
    cols = []
    for ch in MONOGRAM:
        rows = PIXEL_FONT[ch]
        if cols:
            cols.append(None)  # 1-column gap between letters
        cols += [[row[c] for row in rows] for c in range(len(rows[0]))]
    art_w, art_h = len(cols) * pitch - (pitch - size), 7 * pitch - (pitch - size)
    art_x = PX + 12
    art_y = (Y(1) - FS + Y(12) + 24) / 2 - art_h / 2
    info_x = art_x + art_w + 48

    defs.append(
        f'<linearGradient id="pxg" gradientUnits="userSpaceOnUse" spreadMethod="repeat" '
        f'x1="{art_x}" y1="{art_y:.1f}" x2="{art_x + 320}" y2="{art_y + 320:.1f}">'
        + "".join(f'<stop offset="{o}" stop-color="{c}"/>'
                  for o, c in zip([0, .25, .5, .75, 1], GOOGLE + [BLUE]))
        + '<animateTransform attributeName="gradientTransform" type="translate" '
          'values="0 0;320 320" dur="6s" repeatCount="indefinite"/></linearGradient>'
    )
    shadows, pixels = [], []
    for c, col in enumerate(cols):
        if col is None:
            continue
        for r, cell in enumerate(col):
            if cell != "#":
                continue
            t = t_out + 0.05 + (r + c) * 0.035
            pop = tl.anim([(0, "opacity:0;transform:scale(.2)"), (t - .01, "opacity:0;transform:scale(.2)"),
                           (t, "opacity:1;transform:scale(.2)", "cubic-bezier(.3,1.7,.5,1)"),
                           (t + .4, "opacity:1;transform:scale(1)"), (T, "opacity:1;transform:scale(1)")])
            x, y = art_x + c * pitch, art_y + r * pitch
            shadows.append(f'<rect class="{pop}" x="{x + 5}" y="{y + 5:.1f}" '
                           f'width="{size}" height="{size}" rx="3"/>')
            pixels.append(f'<rect class="{pop}" x="{x}" y="{y:.1f}" width="{size}" height="{size}" rx="3"/>')
    content.append(f'<g class="px" fill="#1A2440">{"".join(shadows)}</g>')
    content.append(f'<g class="px" fill="url(#pxg)">{"".join(pixels)}</g>')

    # info column
    header = [(HOST[0], BLUE, True), ("@", TEXT), (HOST[1], BLUE, True)]
    info_lines = [header, [("-" * len(HOST[0] + "@" + HOST[1]), MUTED)]]
    label_w = max(len(k) for k, _ in NEOFETCH) + 2
    for i, (key, value) in enumerate(NEOFETCH):
        info_lines.append([((key + ":").ljust(label_w), GOOGLE[i % 4], True), (value, TEXT)])
    for j, segs in enumerate(info_lines):
        n = sum(len(s[0]) for s in segs)
        assert info_x + n * CW < W - 20, f"neofetch line too long: {segs}"
        content.append(f'<g class="{tl.show_at(t_out + j * 0.07)}">{mono(info_x, Y(1 + j), segs, FS)}</g>')

    # colour blocks
    palette = [[DIM, RED, GREEN, YELLOW, BLUE, "#A371F7", "#39C5CF", SUB],
               [MUTED, "#FF7B72", "#56D364", "#E3B341", "#8AB4F8", "#D2A8FF", "#56D4DD", "#FFFFFF"]]
    for r, row in enumerate(palette):
        for c, col in enumerate(row):
            cls = tl.show_at(t_out + 0.9 + (r * 8 + c) * 0.035)
            content.append(f'<rect class="{cls}" x="{info_x + c * 30:.1f}" y="{Y(12) - 12 + r * 18}" '
                           f'width="30" height="18" fill="{col}"/>')

    # 2) ls ~/open-to-discuss
    t_out2 = 5.9
    command(15, [("ls", TEXT, True), (" " + OPEN_TO_DIR, SUB)], 3.9, 4.4, 0.06, t_out2)
    listing = []
    for d in OPEN_TO:
        listing += [(d, BLUE, True), ("   ", TEXT)]
    content.append(f'<g class="{tl.show_at(t_out2)}">{mono(PX, Y(16), listing[:-1], FS)}</g>')

    # 3) idle prompt with a blinking block cursor
    t_idle = 6.2
    content.append(f'<g class="{tl.show_at(t_idle)}">{mono(PX, Y(17), PROMPT, FS)}'
                   f'<rect class="blink" x="{PX + prompt_w:.1f}" y="{Y(17) - FS + 2}" '
                   f'width="{CW:.1f}" height="{FS + 3}" fill="{SUB}"/></g>')

    fade = tl.anim([(0, "opacity:1"), (T - 1.0, "opacity:1"), (T - 0.35, "opacity:0"), (T, "opacity:0")])
    body.append(f'<g class="{fade}">{"".join(content)}</g>')
    body.append(f'<rect y="{TOP}" width="{W}" height="{H - TOP - 14}" fill="url(#tg)"/>')
    body.append(f'<rect y="{TOP}" width="{W}" height="{H - TOP - 14}" fill="url(#scan)"/>')

    label = "Terminal running neofetch: " + "; ".join(f"{k}: {v}" for k, v in NEOFETCH)
    return svg(W, H, label, css + tl.css, defs, body)


# ── divider ────────────────────────────────────────────────────────────────
def build_divider():
    W, H = 1000, 28
    cy = H / 2
    gap = 58  # clear space around the dots
    css = [
        f"@keyframes run{{from{{transform:translateX(0)}}to{{transform:translateX({W + 260}px)}}}}",
        ".run{animation:run 3.6s cubic-bezier(.6,0,.4,1) infinite}",
        "@keyframes hop{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px)}}",
    ]
    css += [f".d{i}{{animation:hop 1.4s ease-in-out {i * 0.14:.2f}s infinite}}" for i in range(4)]
    defs = [
        '<linearGradient id="base" x1="0" x2="1">'
        f'<stop offset="0" stop-color="{BORDER}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{BORDER}"/>'
        f'<stop offset="1" stop-color="{BORDER}" stop-opacity="0"/></linearGradient>',
        '<linearGradient id="pulse" x1="0" x2="1">'
        f'<stop offset="0" stop-color="{BLUE}" stop-opacity="0"/>'
        + "".join(f'<stop offset="{.2 + i * .2:.1f}" stop-color="{c}"/>' for i, c in enumerate(GOOGLE))
        + f'<stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient>',
        f'<clipPath id="rails"><rect width="{W / 2 - gap}" height="{H}"/>'
        f'<rect x="{W / 2 + gap}" width="{W / 2 - gap}" height="{H}"/></clipPath>',
    ]
    body = [
        f'<g clip-path="url(#rails)"><rect y="{cy - .5}" width="{W}" height="1" fill="url(#base)"/>'
        f'<rect class="run" x="-260" y="{cy - 1}" width="260" height="2" rx="1" fill="url(#pulse)"/></g>'
    ]
    body += [f'<circle class="d{i}" cx="{W / 2 - 24 + i * 16}" cy="{cy}" r="4.5" fill="{c}"/>'
             for i, c in enumerate(GOOGLE)]
    return svg(W, H, "section divider", css, defs, body)


# ── footer ─────────────────────────────────────────────────────────────────
def build_footer():
    W, H, R = 1000, 200, 18

    def wave(base, amp, period):
        pts = " ".join(f"{x},{base + amp * math.sin(2 * math.pi * x / period):.1f}"
                       for x in range(0, 2 * W + 1, 10))
        return f"M0,{H} L{pts} L{2 * W},{H}Z"

    def slide(period, seconds, rightward=False):
        values = f"{-period} 0;0 0" if rightward else f"0 0;{-period} 0"
        return (f'<animateTransform attributeName="transform" type="translate" '
                f'values="{values}" dur="{seconds}s" repeatCount="indefinite"/>')

    css = [f".mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}"]
    defs = [
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="{R}"/></clipPath>',
        border_gradient("bd", 9),
        shine_gradient("shine", 700, -420, 760, 6.5),
        '<linearGradient id="gw" x1="0" x2="1">'
        + "".join(f'<stop offset="{i / 3:.3f}" stop-color="{c}"/>' for i, c in enumerate(GOOGLE))
        + "</linearGradient>",
        f'<clipPath id="front"><path d="{wave(172, 7, 250)}">{slide(250, 6)}</path></clipPath>',
        f'<radialGradient id="top" cx=".5" cy="0" r=".8">'
        f'<stop offset="0" stop-color="{BLUE}" stop-opacity=".16"/>'
        f'<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>',
    ]
    body = [
        f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{BG}"/>',
        f'<rect width="{W}" height="{H}" fill="url(#top)"/>',
        f'<path d="{wave(150, 12, 500)}" fill="{BLUE}" opacity=".16">{slide(500, 12)}</path>',
        f'<path d="{wave(160, 9, 400)}" fill="#8AB4F8" opacity=".1">{slide(400, 9, rightward=True)}</path>',
        f'<rect width="{W}" height="{H}" fill="url(#gw)" opacity=".42" clip-path="url(#front)"/>',
        f'<text class="sans" x="500" y="84" text-anchor="middle" font-size="34" '
        f'font-weight="800" fill="url(#shine)">{escape(FOOTER_TITLE)}</text>',
        mono(500, 120, [("// ", BLUE), (FOOTER_LINE, MUTED)], 16, anchor="middle"),
        "</g>",
        f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{R}" '
        f'fill="none" stroke="url(#bd)" stroke-width="1.5" opacity=".75"/>',
    ]
    return svg(W, H, f"{FOOTER_TITLE}: {FOOTER_LINE}", css, defs, body)


# ── social link buttons ────────────────────────────────────────────────────
# Brand glyphs on a 24×24 grid, drawn on an app-icon style tile.
ICONS = {
    "linkedin": (
        "#0A66C2",
        '<path fill="#fff" d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 '
        "1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 "
        "4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 1 1 0-4.125 2.062 2.062 0 0 1 0 4.125zM7.119 "
        '20.452H3.555V9h3.564v11.452z"/>',
    ),
    "instagram": (
        "url(#ig)",
        '<rect x="3" y="3" width="18" height="18" rx="5.2" fill="none" stroke="#fff" stroke-width="2"/>'
        '<circle cx="12" cy="12" r="4.2" fill="none" stroke="#fff" stroke-width="2"/>'
        '<circle cx="17.2" cy="6.8" r="1.25" fill="#fff"/>',
    ),
    "github": (
        "#F0F6FC",
        '<path fill="#0D1117" d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258'
        ".82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 "
        "17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495"
        ".998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135"
        "-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 "
        ".405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 "
        "4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825"
        '.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>',
    ),
}


def build_social(index, name, platform, handle):
    W, H, R = 236, 64, 16
    tile, glyph = ICONS[name]
    css = [
        f".mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}",
        f"@keyframes shine{{0%{{transform:translateX(0)}}30%,100%{{transform:translateX({W + 160}px)}}}}",
        f".shine{{animation:shine 6s ease-in-out {index * 0.35:.2f}s infinite}}",
    ]
    defs = [
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="{R}"/></clipPath>',
        '<linearGradient id="ig" x1="0" y1="1" x2="1" y2="0">'
        '<stop offset="0" stop-color="#FEDA75"/><stop offset=".3" stop-color="#FA7E1E"/>'
        '<stop offset=".6" stop-color="#D62976"/><stop offset="1" stop-color="#4F5BD5"/></linearGradient>',
        '<linearGradient id="edge" x1="0" x2="1">'
        + "".join(f'<stop offset="{i / 3:.3f}" stop-color="{c}" stop-opacity=".7"/>'
                  for i, c in enumerate(GOOGLE))
        + "</linearGradient>",
        '<linearGradient id="gloss" x1="0" x2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff" stop-opacity=".09"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
    ]
    body = [
        f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{PANEL}"/>',
        f'<rect class="shine" x="-150" width="110" height="{H}" fill="url(#gloss)" '
        f'transform="skewX(-20)"/></g>',
        f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{R - .5}" fill="none" '
        f'stroke="{BORDER}" stroke-width="1.5"/>',
        f'<rect x="{R}" y="{H - 1.5}" width="{W - 2 * R}" height="1.5" fill="url(#edge)"/>',
        f'<rect x="12" y="12" width="40" height="40" rx="11" fill="{tile}"/>',
        f'<g transform="translate(20 20) scale(1)">{glyph}</g>',
        f'<text class="mono" x="66" y="28" font-size="10.5" letter-spacing="2" fill="{MUTED}">{platform}</text>',
        f'<text class="sans" x="66" y="47" font-size="16" font-weight="600" fill="{TEXT}">{escape(handle)}</text>',
        f'<path d="M{W - 33} {H / 2 + 5}l10-10m-7 0h7v7" fill="none" stroke="{MUTED}" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    ]
    return svg(W, H, f"{platform.title()}: {handle}", css, defs, body)


# ── section headers ────────────────────────────────────────────────────────
def build_section(number, title, subtitle):
    W, H, R = 1000, 88, 14
    total = len(SECTIONS)
    css = [
        f".mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}",
        "@keyframes live{0%,100%{opacity:1}50%{opacity:.35}}",
        ".live{animation:live 1.6s ease-in-out infinite}",
        f"@keyframes edge{{from{{transform:translateX(0)}}to{{transform:translateX({W + 300}px)}}}}",
        ".edge{animation:edge 5s cubic-bezier(.6,0,.4,1) infinite}",
    ]
    defs = [
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="{R}"/></clipPath>',
        # same shimmer as the hero name, staggered so headers don't flash in sync
        shine_gradient("shine", 520, -300, 700, 6.5 + number * 0.4),
        '<radialGradient id="glow" cx="0" cy=".5" r=".55">'
        f'<stop offset="0" stop-color="{BLUE}" stop-opacity=".16"/>'
        f'<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="sweep" x1="0" x2="1">'
        f'<stop offset="0" stop-color="{BLUE}" stop-opacity="0"/>'
        + "".join(f'<stop offset="{.2 + i * .2:.1f}" stop-color="{c}"/>' for i, c in enumerate(GOOGLE))
        + f'<stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient>',
    ]
    body = [
        f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{BG}"/>',
        f'<rect width="{W}" height="{H}" fill="url(#glow)"/>',
    ]
    # Google-coloured spine on the left edge
    body += [f'<rect y="{i * H / 4:.1f}" width="5" height="{H / 4:.1f}" fill="{c}"/>'
             for i, c in enumerate(GOOGLE)]
    body.append(f'<rect class="edge" x="-300" y="{H - 2}" width="300" height="2" fill="url(#sweep)"/></g>')
    body.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{R}" fill="none" stroke="#1F2633"/>')

    # index chip, title, subtitle
    body.append(f'<rect x="32" y="22" width="42" height="26" rx="7" fill="{BLUE}" fill-opacity=".1" '
                f'stroke="{BLUE}" stroke-opacity=".55"/>')
    body.append(f'<text class="mono" x="53" y="40" font-size="14" font-weight="700" text-anchor="middle" '
                f'fill="{BLUE}">{number:02d}</text>')
    body.append(f'<text class="sans" x="92" y="45" font-size="27" font-weight="800" letter-spacing="2.5" '
                f'fill="url(#shine)">{escape(title)}</text>')
    body.append(mono(92, 69, [("// ", BLUE), (subtitle, MUTED)], 13))

    # progress through the page: one segment per section
    seg_w, gap = 22, 6
    x0 = W - 32 - total * seg_w - (total - 1) * gap
    for i in range(total):
        fill = GOOGLE[i % 4] if i < number else "#1F2633"
        live = ' class="live"' if i == number - 1 else ""
        body.append(f'<rect{live} x="{x0 + i * (seg_w + gap)}" y="30" width="{seg_w}" height="5" rx="2.5" fill="{fill}"/>')
    body.append(f'<text class="mono" x="{W - 32}" y="62" font-size="11" letter-spacing="2" text-anchor="end" '
                f'fill="{MUTED}">SECTION {number:02d}/{total:02d}</text>')

    return svg(W, H, f"{number:02d} · {title.title()}: {subtitle}", css, defs, body)


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    for name, build in [("hero", build_hero), ("terminal", build_terminal),
                        ("divider", build_divider), ("footer", build_footer)]:
        out = ASSETS / f"{name}.svg"
        out.write_text(build(), encoding="utf-8")
        print(f"wrote {out.relative_to(ASSETS.parent)}  ({out.stat().st_size / 1024:.1f} KB)")
    (ASSETS / "social").mkdir(exist_ok=True)
    for index, (name, platform, handle) in enumerate(SOCIALS):
        out = ASSETS / "social" / f"{name}.svg"
        out.write_text(build_social(index, name, platform, handle), encoding="utf-8")
        print(f"wrote {out.relative_to(ASSETS.parent)}  ({out.stat().st_size / 1024:.1f} KB)")
    (ASSETS / "headers").mkdir(exist_ok=True)
    for number, (name, title, subtitle) in enumerate(SECTIONS, 1):
        out = ASSETS / "headers" / f"{name}.svg"
        out.write_text(build_section(number, title, subtitle), encoding="utf-8")
        print(f"wrote {out.relative_to(ASSETS.parent)}  ({out.stat().st_size / 1024:.1f} KB)")
