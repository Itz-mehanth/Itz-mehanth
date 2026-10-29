"""Renders assets/{dark,light}/activity.svg: live stats + an isometric contribution skyline.

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

from common import MONO, SANS, SERIF, THEMES, esc, measure, svg, write

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


def shade(hex_, k):
    h = hex_.lstrip("#")
    return "#" + "".join(f"{min(255, int(int(h[i:i + 2], 16) * k)):02x}" for i in (0, 2, 4))


def skyline(t, days, x_left, y_top):
    first = days[0][0] - dt.timedelta(days=(days[0][0].weekday() + 1) % 7)
    a, b, gap = 10.6, 5.1, 0.82
    max_c = max((c for _, c, _ in days), default=1) or 1
    max_h = 92
    ox, oy = x_left + 7 * a, y_top + max_h + b
    side_l, side_r = (.72, .55) if t["name"] == "dark" else (.88, .76)
    cells = sorted(((date - first).days // 7 + (date.weekday() + 1) % 7, (date - first).days // 7,
                    (date.weekday() + 1) % 7, c, lvl) for date, c, lvl in days)
    out = []

    def height(c):
        return 2 + max_h * math.sqrt(c / max_c) if c else 1.2

    for _, w, d, c, lvl in cells:
        X, Y = ox + (w - d) * a, oy + (w + d) * b
        ga, gb = a * gap, b * gap
        h = height(c)
        top = t["ramp"][lvl if c else 0]
        T = f"{X:.1f},{Y - gb - h:.1f} {X + ga:.1f},{Y - h:.1f} {X:.1f},{Y + gb - h:.1f} {X - ga:.1f},{Y - h:.1f}"
        L = f"{X - ga:.1f},{Y:.1f} {X:.1f},{Y + gb:.1f} {X:.1f},{Y + gb - h:.1f} {X - ga:.1f},{Y - h:.1f}"
        R = f"{X:.1f},{Y + gb:.1f} {X + ga:.1f},{Y:.1f} {X + ga:.1f},{Y - h:.1f} {X:.1f},{Y + gb - h:.1f}"
        out.append(f'<g class="b" style="animation-delay:{.2 + w * .028:.2f}s">'
                   f'<polygon points="{L}" fill="{shade(top, side_l)}"/><polygon points="{R}" fill="{shade(top, side_r)}"/>'
                   f'<polygon points="{T}" fill="{top}"/></g>')
    _, w, d, c, _ = max(cells, key=lambda x: (x[1], x[2]))
    X, Y = ox + (w - d) * a, oy + (w + d) * b - height(c)
    out.append(f'<path d="M{X:.1f} {Y - 6:.1f}V{Y - 34:.1f}" stroke="{t["muted"]}"/>'
               f'<text x="{X:.1f}" y="{Y - 42:.1f}" text-anchor="middle" font-family="{MONO}" font-size="10.5" '
               f'letter-spacing="1.4" fill="{t["muted"]}">TODAY</text>')
    return "".join(out)


def render(t, user, rs, days):
    total = sum(c for _, c, _ in days)
    cur, best = streaks(days)
    stars = sum(r["stargazers_count"] for r in rs)
    langs = Counter(r["language"] for r in rs if r["language"])
    top = langs.most_common(4)
    n_all = sum(langs.values())

    W, H = 1200, 500
    style = """
    .b{transform-box:fill-box;transform-origin:50% 100%;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both}
    @keyframes grow{from{transform:scaleY(0);opacity:0}}
    .up{animation:up .9s cubic-bezier(.2,.7,.2,1) both}
    @keyframes up{from{opacity:0;transform:translateY(10px)}}
    .bar{transform-box:fill-box;transform-origin:left;animation:bar 1.4s cubic-bezier(.6,0,.2,1) both .5s}
    @keyframes bar{from{transform:scaleX(0)}}
    """
    x = 48

    def lab(lx, ly, text, color=None, anchor="start"):
        return (f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-family="{MONO}" font-size="11" '
                f'letter-spacing="1.6" fill="{color or t["muted"]}">{esc(text.upper())}</text>')

    def stat(sx, sy, value, name, delay):
        return (f'<g class="up" style="animation-delay:{delay}s">'
                f'<text x="{sx}" y="{sy}" font-family="{SERIF}" font-size="40" letter-spacing="-.5" fill="{t["text"]}">{esc(value)}</text>'
                f'{lab(sx, sy + 22, name)}</g>')

    left = [f'<g class="up">{lab(x, 66, "Last twelve months", t["accent"])}',
            f'<text x="{x - 4}" y="152" font-family="{SERIF}" font-size="100" letter-spacing="-2" fill="{t["text"]}">{total:,}</text>',
            f'<text x="{x}" y="182" font-family="{SANS}" font-size="17" fill="{t["muted"]}">contributions on GitHub</text></g>',
            f'<path d="M{x} 212H{x + 400}M{x} 300H{x + 400}M{x + 136} 226V286M{x + 272} 226V286" stroke="{t["edge"]}"/>',
            stat(x, 260, str(cur), "day streak", .1), stat(x + 152, 260, str(best), "best streak", .15),
            stat(x + 288, 260, str(stars), "stars", .2)]
    left.append(f'<g class="up" style="animation-delay:.3s">{lab(x, 336, "What I build in · by repo")}')
    for k, (name, n) in enumerate(top):
        ly = 368 + k * 28
        pct = 100 * n / n_all
        left.append(f'<text x="{x}" y="{ly}" font-family="{SANS}" font-size="15" fill="{t["text"]}">{esc(name)}</text>'
                    f'<rect x="{x + 130}" y="{ly - 9}" width="230" height="6" rx="3" fill="{t["hair"]}"/>'
                    f'<rect class="bar" style="animation-delay:{.5 + k * .1:.1f}s" x="{x + 130}" y="{ly - 9}" '
                    f'width="{230 * n / top[0][1]:.1f}" height="6" rx="3" fill="{t["accent"] if k == 0 else t["muted"]}"/>'
                    f'<text x="{x + 400}" y="{ly}" text-anchor="end" font-family="{MONO}" font-size="12.5" '
                    f'fill="{t["muted"]}">{pct:.0f}%</text>')
    left.append("</g>")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    legend_x = W - 48 - 5 * 16
    legend = "".join(f'<rect x="{legend_x + k * 16}" y="452" width="11" height="11" rx="2" fill="{c}"/>'
                     for k, c in enumerate(t["ramp"]))
    body = f"""<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="20" fill="{t["panel"]}" stroke="{t["edge"]}"/>
    <path d="M488 40V460" stroke="{t["hair"]}"/>
    {"".join(left)}
    {skyline(t, days, 520, 40)}
    {lab(legend_x - 12, 462, "less", anchor="end")}{legend}{lab(W - 48 + 4, 462, "more")}
    {lab(520, 462, f"one tower per day · updated {stamp}")}"""
    write(t, "activity.svg", svg(W, H, body, style,
                                 f"{total} contributions in the last year, current streak {cur} days, longest {best} days"))


def main():
    user = json.loads(get(f"https://api.github.com/users/{USER}"))
    rs = [r for r in repos() if not r["fork"]]
    days = contributions()
    for theme in THEMES.values():
        render(theme, user, rs, days)


if __name__ == "__main__":
    main()
