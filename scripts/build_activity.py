"""Renders assets/activity.svg: live stats + an isometric contribution skyline.

Uses GITHUB_TOKEN when present (GitHub Actions); otherwise falls back to public endpoints.
Run: python scripts/build_activity.py
"""
import datetime as dt
import json
import math
import os
import re
import urllib.request
from collections import Counter

from common import CYAN, EDGE, GREEN, MONO, MUTED, PANEL, PINK, SANS, TEXT, VIOLET, AMBER, esc, svg, write

USER = os.environ.get("PROFILE_USER", "Itz-mehanth")
TOKEN = os.environ.get("GITHUB_TOKEN")


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "profile-readme"})
    if TOKEN:
        req.add_header("Authorization", f"bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def contributions():
    """[(date, count, level 0-4)] for the last year."""
    if TOKEN:
        q = {"query": "query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{"
                      "weeks{contributionDays{date contributionCount contributionLevel}}}}}}",
             "variables": {"u": USER}}
        res = json.loads(get("https://api.github.com/graphql", json.dumps(q).encode()))
        lv = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
        weeks = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        return [(dt.date.fromisoformat(d["date"]), d["contributionCount"], lv[d["contributionLevel"]])
                for w in weeks for d in w["contributionDays"]]
    html = get(f"https://github.com/users/{USER}/contributions")
    counts = {m[0]: 0 if m[1] == "No" else int(m[1].replace(",", ""))
              for m in re.findall(r'for="(contribution-day-component-[\d-]+)"[^>]*>(No|[\d,]+) contribution', html)}
    days = []
    for td in re.findall(r"<td[^>]*data-date[^>]*>", html):
        date = re.search(r'data-date="([\d-]+)"', td).group(1)
        cid = re.search(r'id="([^"]+)"', td).group(1)
        level = int(re.search(r'data-level="(\d)"', td).group(1))
        days.append((dt.date.fromisoformat(date), counts.get(cid, 0), level))
    return sorted(days)


def streaks(days):
    run, best = 0, 0
    for _, c, _ in days:
        run = run + 1 if c else 0
        best = max(best, run)
    cur = 0
    seq = days[:-1] if days and days[-1][1] == 0 else days  # today isn't over yet
    for _, c, _ in reversed(seq):
        if not c:
            break
        cur += 1
    return cur, best


def repos():
    out, page = [], 1
    while True:
        batch = json.loads(get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}"))
        out += batch
        if len(batch) < 100:
            return out
        page += 1


LANG_COLORS = {"JavaScript": "#F7DF1E", "TypeScript": "#3178C6", "Python": "#3776AB", "Java": "#E76F00",
               "Dart": "#00B4AB", "C": "#A8B9CC", "C++": "#F34B7D", "C#": "#9B4F96", "HTML": "#E34C26",
               "CSS": "#663399", "Vue": "#41B883", "GDScript": "#478CBF", "Jupyter Notebook": "#DA5B0B"}
FALLBACK = [CYAN, VIOLET, PINK, GREEN, AMBER]

LEVEL_TOP = ["#232C40", "#3B2A82", "#5B4BD6", "#3FA3F0", "#00F7F4"]


def shade(hex_, k):
    h = hex_.lstrip("#")
    return "#" + "".join(f"{int(int(h[i:i + 2], 16) * k):02x}" for i in (0, 2, 4))


def skyline(days, x_left, y_top):
    first = days[0][0] - dt.timedelta(days=(days[0][0].weekday() + 1) % 7)
    a, b, gap = 10.6, 5.1, 0.82
    max_c = max((c for _, c, _ in days), default=1) or 1
    max_h = 92
    ox, oy = x_left + 7 * a, y_top + max_h + b
    cells = []
    for date, c, lvl in days:
        w, d = (date - first).days // 7, (date.weekday() + 1) % 7
        cells.append((w + d, w, d, c, lvl))
    out = []
    for _, w, d, c, lvl in sorted(cells):
        X, Y = ox + (w - d) * a, oy + (w + d) * b
        ga, gb = a * gap, b * gap
        h = 2 + max_h * math.sqrt(c / max_c) if c else 1.2
        top = LEVEL_TOP[lvl if c else 0]
        T = f"{X:.1f},{Y - gb - h:.1f} {X + ga:.1f},{Y - h:.1f} {X:.1f},{Y + gb - h:.1f} {X - ga:.1f},{Y - h:.1f}"
        L = f"{X - ga:.1f},{Y:.1f} {X:.1f},{Y + gb:.1f} {X:.1f},{Y + gb - h:.1f} {X - ga:.1f},{Y - h:.1f}"
        R = f"{X:.1f},{Y + gb:.1f} {X + ga:.1f},{Y:.1f} {X + ga:.1f},{Y - h:.1f} {X:.1f},{Y + gb - h:.1f}"
        out.append(f'<g class="b" style="animation-delay:{.2 + w * .028:.2f}s">'
                   f'<polygon points="{L}" fill="{shade(top, .55)}"/><polygon points="{R}" fill="{shade(top, .38)}"/>'
                   f'<polygon points="{T}" fill="{top}"/></g>')
    # beacon over today's tower
    date, c, _ = days[-1]
    w, d = (date - first).days // 7, (date.weekday() + 1) % 7
    X, Y = ox + (w - d) * a, oy + (w + d) * b - (2 + max_h * math.sqrt(c / max_c) if c else 1.2)
    out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="4" fill="{CYAN}"/>'
               f'<circle class="ping" cx="{X:.1f}" cy="{Y:.1f}" r="4" fill="none" stroke="{CYAN}" stroke-width="1.5"/>'
               f'<text x="{X + 12:.1f}" y="{Y + 4:.1f}" font-family="{MONO}" font-size="11" fill="{CYAN}">today</text>')
    return "".join(out)


def main():
    user = json.loads(get(f"https://api.github.com/users/{USER}"))
    rs = [r for r in repos() if not r["fork"]]
    days = contributions()
    total = sum(c for _, c, _ in days)
    cur, best = streaks(days)
    stars = sum(r["stargazers_count"] for r in rs)
    langs = Counter(r["language"] for r in rs if r["language"])
    top = langs.most_common(6)
    other = sum(langs.values()) - sum(n for _, n in top)

    W, H = 1200, 500
    style = """
    .b{transform-box:fill-box;transform-origin:50% 100%;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both}
    @keyframes grow{from{transform:scaleY(0);opacity:0}}
    .in{animation:in .9s cubic-bezier(.2,.8,.2,1) both}
    @keyframes in{from{opacity:0;transform:translateY(12px)}}
    .bar{transform-box:fill-box;transform-origin:left;animation:bar 1.4s cubic-bezier(.6,0,.2,1) both .5s}
    @keyframes bar{from{transform:scaleX(0)}}
    .ping{animation:ping 2s ease-out infinite;transform-box:fill-box;transform-origin:center}
    @keyframes ping{from{transform:scale(1);opacity:.9}to{transform:scale(3.5);opacity:0}}
    """
    x = 44

    def tile(tx, ty, tw, value, label, col, delay):
        return (f'<g class="in" style="animation-delay:{delay}s"><rect x="{tx}" y="{ty}" width="{tw}" height="78" rx="14" '
                f'fill="#fff" fill-opacity=".03" stroke="{EDGE}"/>'
                f'<text x="{tx + 18}" y="{ty + 42}" font-family="{SANS}" font-size="28" font-weight="750" fill="{col}">{esc(value)}</text>'
                f'<text x="{tx + 18}" y="{ty + 63}" font-family="{MONO}" font-size="11.5" letter-spacing="1" fill="{MUTED}">{esc(label)}</text></g>')

    left = [f'<g class="in"><text x="{x}" y="64" font-family="{MONO}" font-size="12.5" letter-spacing="2" fill="{MUTED}">LAST 12 MONTHS</text>',
            f'<text x="{x - 3}" y="132" font-family="{SANS}" font-size="72" font-weight="800" letter-spacing="-2" fill="url(#num)">{total:,}</text>',
            f'<text x="{x}" y="160" font-family="{SANS}" font-size="18" fill="{TEXT}">contributions on GitHub</text></g>',
            tile(x, 186, 196, f"{cur} days", "CURRENT STREAK", GREEN, .15),
            tile(x + 210, 186, 196, f"{best} days", "LONGEST STREAK", AMBER, .2),
            tile(x, 278, 126, str(user["public_repos"]), "REPOS", CYAN, .25),
            tile(x + 140, 278, 126, str(stars), "STARS", PINK, .3),
            tile(x + 280, 278, 126, str(user["followers"]), "FOLLOWERS", VIOLET, .35)]

    # language bar
    by = 396
    left.append(f'<g class="in" style="animation-delay:.4s"><text x="{x}" y="{by - 12}" font-family="{MONO}" font-size="11.5" '
                f'letter-spacing="1" fill="{MUTED}">WHAT I BUILD IN · BY REPO</text>'
                f'<clipPath id="lb"><rect x="{x}" y="{by}" width="406" height="10" rx="5"/></clipPath><g clip-path="url(#lb)" class="bar">')
    n_all, bx = sum(langs.values()), x
    segs = top + ([("Other", other)] if other else [])
    for k, (name, n) in enumerate(segs):
        col = LANG_COLORS.get(name, FALLBACK[k % len(FALLBACK)]) if name != "Other" else "#3A4254"
        w = 406 * n / n_all
        left.append(f'<rect x="{bx:.1f}" y="{by}" width="{w + .5:.1f}" height="10" fill="{col}"/>')
        segs[k] = (name, n, col)
        bx += w
    left.append("</g>")
    lx, ly = x, by + 34
    for name, n, col in segs:
        label = f"{name} {100 * n / n_all:.0f}%"
        lw = len(label) * 7.2 + 26
        if lx + lw > x + 420:
            lx, ly = x, ly + 22
        left.append(f'<circle cx="{lx + 5}" cy="{ly - 4}" r="4.5" fill="{col}"/>'
                    f'<text x="{lx + 15}" y="{ly}" font-family="{MONO}" font-size="12" fill="{TEXT}" fill-opacity=".8">{esc(label)}</text>')
        lx += lw
    left.append("</g>")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = f"""<defs><linearGradient id="num" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/>
      <stop offset="1" stop-color="{VIOLET}"/></linearGradient>
      <radialGradient id="glo" cx=".72" cy=".55" r=".55"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".16"/>
      <stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient></defs>
    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="{PANEL}" stroke="{EDGE}"/>
    <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="22" fill="url(#glo)"/>
    {"".join(left)}
    {skyline(days, 500, 34)}
    <text x="{W - 28}" y="{H - 22}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}" fill-opacity=".7">one tower per day · updated {stamp}</text>"""
    write("activity.svg", svg(W, H, body, style,
                              f"{total} contributions in the last year, current streak {cur} days, longest {best} days"))


if __name__ == "__main__":
    main()
