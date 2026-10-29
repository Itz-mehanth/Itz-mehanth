"""Generates every static SVG in assets/{dark,light}/. Run: python scripts/build.py"""
import math
import os

from common import MONO, ROOT, SANS, SERIF, THEMES, esc, icon, measure, svg, wrap, write

# ---------------------------------------------------------------- 3D wireframes

PHI = (1 + 5 ** 0.5) / 2
ICO_V = [(x, y, z) for a in (-1, 1) for b in (-PHI, PHI)
         for (x, y, z) in ((0, a, b), (a, b, 0), (b, 0, a))]
ICO_E = [(i, j) for i in range(12) for j in range(i + 1, 12)
         if abs(sum((p - q) ** 2 for p, q in zip(ICO_V[i], ICO_V[j])) - 4) < 1e-6]
ICO_V = [tuple(c / math.sqrt(1 + PHI ** 2) for c in v) for v in ICO_V]

OCT_V = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
OCT_E = [(i, j) for i in range(6) for j in range(i + 1, 6) if j != i + 1 or i % 2]


def rot(p, ax, ay, az):
    x, y, z = p
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    x, y = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
    return x, y, z


def wireframe(cx, cy, r, verts, edges, angles, frames, dur, stroke, width, dot, dot_r):
    """Pre-computes a spinning, perspective-projected wireframe as SMIL keyframes."""
    f = 3.6
    proj = []
    for k in range(frames + 1):
        t = 2 * math.pi * k / frames
        pts = []
        for v in verts:
            x, y, z = rot(v, *angles(t))
            s = f / (f - z)
            pts.append((cx + r * x * s, cy - r * y * s, z))
        proj.append(pts)

    def depth(z):
        return 0.14 + 0.86 * ((z + 1) / 2) ** 1.4

    anim = f'dur="{dur}s" repeatCount="indefinite"'
    out = []
    for i, j in edges:
        d = ";".join(f"M{p[i][0]:.1f} {p[i][1]:.1f}L{p[j][0]:.1f} {p[j][1]:.1f}" for p in proj)
        o = ";".join(f"{depth((p[i][2] + p[j][2]) / 2):.2f}" for p in proj)
        out.append(f'<path stroke="{stroke}" stroke-width="{width}" stroke-linecap="round">'
                   f'<animate attributeName="d" values="{d}" {anim}/>'
                   f'<animate attributeName="stroke-opacity" values="{o}" {anim}/></path>')
    for i in range(len(verts)):
        xs = ";".join(f"{p[i][0]:.1f}" for p in proj)
        ys = ";".join(f"{p[i][1]:.1f}" for p in proj)
        o = ";".join(f"{depth(p[i][2]):.2f}" for p in proj)
        out.append(f'<circle r="{dot_r}" fill="{dot}">'
                   f'<animate attributeName="cx" values="{xs}" {anim}/>'
                   f'<animate attributeName="cy" values="{ys}" {anim}/>'
                   f'<animate attributeName="opacity" values="{o}" {anim}/></circle>')
    return "".join(out)


def discrete(attr, pts, dur, fmt="{:.1f}"):
    """A stepped SMIL animation through (time-fraction, value) pairs."""
    kt = ";".join(f"{t:.4f}" for t, _ in pts)
    vals = ";".join(fmt.format(v) for _, v in pts)
    return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{dur}s" '
            f'repeatCount="indefinite" keyTimes="{kt}" values="{vals}"/>')


FADE_UP = """
.up{animation:up 1s cubic-bezier(.2,.7,.2,1) both}
@keyframes up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
"""


def label(x, y, text, color, size=11.5, anchor="start", spacing=1.6):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{MONO}" font-size="{size}" '
            f'letter-spacing="{spacing}" fill="{color}">{esc(text.upper())}</text>')


# ---------------------------------------------------------------- hero

PHRASES = ["agentic AI systems", "real-time data pipelines", "3D worlds for the web", "tools developers install"]


def hero(t):
    W, H = 1200, 460
    x0 = 64
    cycle = 16
    style = FADE_UP + """
    .ok{animation:ok 2.4s ease-in-out infinite}
    @keyframes ok{50%{opacity:.25}}
    .draw{stroke-dasharray:600;animation:draw 2s cubic-bezier(.6,0,.2,1) both .3s}
    @keyframes draw{from{stroke-dashoffset:600}to{stroke-dashoffset:0}}
    """
    n = len(PHRASES)
    for i in range(n):
        a = 100 * i / n
        style += (f".p{i}{{opacity:0;animation:p{i} {cycle}s infinite}}"
                  f"@keyframes p{i}{{0%,{a:.1f}%{{opacity:0;transform:translateY(34px);"
                  f"animation-timing-function:cubic-bezier(.2,.7,.2,1)}}"
                  f"{a + 4:.1f}%,{a + 21:.1f}%{{opacity:1;transform:none;animation-timing-function:cubic-bezier(.6,0,.8,.3)}}"
                  f"{a + 24.5:.1f}%,100%{{opacity:0;transform:translateY(-34px)}}}}")

    b = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="20" fill="{t["panel"]}" stroke="{t["edge"]}"/>']

    # technical-drawing plate for the figure
    fx, fy, fw, fh = 716, 36, 448, 388
    cx, cy = fx + fw / 2, fy + fh / 2 - 6
    plate = [f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="none" stroke="{t["hair"]}"/>']
    for gx in range(fx + 32, fx + fw, 32):
        plate.append(f'<path d="M{gx} {fy}V{fy + fh}" stroke="{t["hair"]}"/>')
    for gy in range(fy + 32, fy + fh, 32):
        plate.append(f'<path d="M{fx} {gy}H{fx + fw}" stroke="{t["hair"]}"/>')
    plate.append(f'<path d="M{cx} {fy}V{fy + fh}M{fx} {cy}H{fx + fw}" stroke="{t["edge"]}" stroke-dasharray="3 5"/>')
    for (px, py, dx, dy) in ((fx, fy, 1, 1), (fx + fw, fy, -1, 1), (fx, fy + fh, 1, -1), (fx + fw, fy + fh, -1, -1)):
        plate.append(f'<path d="M{px} {py + 14 * dy}V{py}H{px + 14 * dx}" fill="none" stroke="{t["muted"]}" stroke-width="1.2"/>')
    plate.append(label(fx + 16, fy + 26, "fig. 01 — icosahedron", t["dim"], 10.5))
    plate.append(label(fx + fw - 16, fy + fh - 16, "26 s / rev", t["dim"], 10.5, "end"))
    b += plate
    b.append('<g fill="none">')
    b.append(wireframe(cx, cy, 140, ICO_V, ICO_E, lambda a: (0.42, a, 0.22), 90, 26, t["text"], 1.3, t["text"], 2.6))
    b.append(wireframe(cx, cy, 56, OCT_V, OCT_E, lambda a: (2 * a, -a, -0.3), 90, 26, t["accent"], 1.6, t["accent"], 2.4))
    b.append("</g>")

    # copy
    b.append(f'<g class="up"><rect x="{x0}" y="66" width="8" height="8" fill="{t["accent"]}"/>'
             f'{label(x0 + 20, 74, "Mehanth T  —  Software engineer  —  Chennai", t["muted"], 12, spacing=2)}</g>')
    b.append(f'<text class="up" style="animation-delay:.1s" x="{x0 - 3}" y="180" font-family="{SERIF}" '
             f'font-size="88" letter-spacing="-1.5" fill="{t["text"]}">I build</text>')
    widest = max(measure(p, SERIF, 88, italic=True, spacing=-1.5) for p in PHRASES)
    size = min(88, 88 * 600 / widest)
    b.append(f'<clipPath id="line"><rect x="{x0 - 10}" y="{200}" width="660" height="{size + 20:.0f}"/></clipPath>'
             f'<g clip-path="url(#line)" font-family="{SERIF}" font-style="italic" font-size="{size:.1f}" '
             f'letter-spacing="-1.5" fill="{t["accent"]}">')
    for i, p in enumerate(PHRASES):
        b.append(f'<text class="p{i}" x="{x0 - 3}" y="{200 + size * .8:.0f}">{esc(p)}</text>')
    b.append("</g>")
    b.append(f'<path class="draw" d="M{x0} 306H{x0 + 560}" stroke="{t["edge"]}"/>')
    b.append(f'<g class="up" style="animation-delay:.3s" font-family="{SANS}" font-size="18" fill="{t["muted"]}">'
             f'<text x="{x0}" y="344">CS undergrad at SSN College of Engineering. Most recently,</text>'
             f'<text x="{x0}" y="370">building agentic AI as a software engineering intern at Visa.</text></g>')

    items = [("ex-Visa SWE intern", False), ("4× hackathon winner", False), ("mehanth.com", False)]
    g, x = [f'<g class="up" style="animation-delay:.45s">'], x0
    for text, live in items:
        if live:
            g.append(f'<circle class="ok" cx="{x + 4}" cy="{406}" r="4" fill="{t["ok"]}"/>')
            x += 16
        g.append(label(x, 410, text, t["text"], 11.5))
        x += measure(text.upper(), MONO, 11.5, spacing=1.6) + 22
        g.append(f'<path d="M{x - 11:.0f} 398V414" stroke="{t["edge"]}"/>')
    g.pop()
    g.append("</g>")
    b += g
    write(t, "hero.svg", svg(W, H, "".join(b), style,
                             "Mehanth T — software engineer building agentic AI, data pipelines, 3D for the web and developer tools"))


# ---------------------------------------------------------------- highlights + experience

HIGHLIGHTS = [
    ("Visa", "SWE intern · agentic AI"),
    ("4×", "hackathon wins in 2026"),
    ("5k+", "VS Code extension downloads"),
    ("Top 1%", "NPTEL · C++"),
]


def highlights(t):
    W, H = 1200, 150
    col = W / len(HIGHLIGHTS)
    b = [f'<path d="M0 .5H{W}M0 {H - .5}H{W}" stroke="{t["edge"]}"/>']
    for k, (value, text) in enumerate(HIGHLIGHTS):
        x = k * col + (8 if k == 0 else 32)
        if k:
            b.append(f'<path d="M{k * col:.0f} 28V{H - 28}" stroke="{t["edge"]}"/>')
        b.append(f'<g class="up" style="animation-delay:{k * .08:.2f}s">'
                 f'<text x="{x:.0f}" y="84" font-family="{SERIF}" font-size="60" letter-spacing="-1.2" '
                 f'fill="{t["accent"] if k == 0 else t["text"]}">{esc(value)}</text>'
                 f'{label(x + 2, 114, text, t["muted"], 11)}</g>')
    write(t, "highlights.svg", svg(W, H, "".join(b), FADE_UP, " · ".join(f"{v} {s}" for v, s in HIGHLIGHTS)))


EXPERIENCE = [
    dict(when="May – Jul 2026", org="Visa Inc.  —  Bangalore", role="Software Engineering Intern", points=[
        "Built an agentic AI system for automated dispute-case resolution, reducing reliance on human analysts in decision-making workflows.",
        "Designed a future-ready API architecture to fix flaws in existing service internals: orchestration, state, validation and downstream processing.",
        "Implemented queue-based task processing, persistent state, human-in-the-loop validation and structured auditing.",
        "Proposed future architecture directions for the platform and was recognised by engineers for the improvements identified.",
    ], tags=["Python", "LangGraph", "PostgreSQL", "pgvector"]),
]


def experience(t):
    W = 1200
    rx, rw = 300, 852
    b, y, dots = [], 60, []
    for k, e in enumerate(EXPERIENCE):
        top = y
        g = [f'<g class="up" style="animation-delay:{k * .15:.2f}s">',
             label(48, y + 8, e["when"], t["muted"], 11.5),
             label(rx, y + 8, e["org"], t["accent"], 11.5),
             f'<text x="{rx - 2}" y="{y + 54}" font-family="{SERIF}" font-size="40" letter-spacing="-.6" '
             f'fill="{t["text"]}">{esc(e["role"])}</text>']
        y += 92
        for pt in e["points"]:
            lines = wrap(pt, rw - 26, family=SANS, size=16.5)
            g.append(f'<text x="{rx}" y="{y}" font-family="{SANS}" font-size="16.5" fill="{t["accent"]}">—</text>')
            g += [f'<text x="{rx + 26}" y="{y + i * 25}" font-family="{SANS}" font-size="16.5" '
                  f'fill="{t["muted"]}">{esc(l)}</text>' for i, l in enumerate(lines)]
            y += 25 * len(lines) + 9
        g.append(f'<text x="{rx}" y="{y + 16}" font-family="{MONO}" font-size="12.5" fill="{t["dim"]}">'
                 f'{esc("  /  ".join(e["tags"]))}</text></g>')
        y += 76
        dots.append(top)
        b += g
    H = y - 20
    rail = 252
    b.insert(0, f'<path d="M{rail} {dots[0] + 4}V{H - 40}" stroke="{t["edge"]}"/>')
    for k, dy in enumerate(dots):
        fill = t["accent"] if k == 0 else t["panel"]
        b.insert(1, f'<circle cx="{rail}" cy="{dy + 4}" r="5.5" fill="{fill}" stroke="{t["accent"] if k == 0 else t["muted"]}" stroke-width="1.5"/>')
    b.insert(0, f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="20" fill="{t["panel"]}" stroke="{t["edge"]}"/>')
    write(t, "experience.svg", svg(W, H, "".join(b), FADE_UP,
                                   "Experience: " + "; ".join(f"{e['role']} at {e['org'].split('  ')[0]} ({e['when']})" for e in EXPERIENCE)))


# ---------------------------------------------------------------- section headers

SECTIONS = [
    ("experience", "01", "Experience", "industry"),
    ("work", "02", "Selected work", "projects & products"),
    ("about", "03", "About", "~/whoami"),
    ("stack", "04", "Toolbox", "what I reach for"),
    ("activity", "05", "Activity", "rebuilt nightly by GitHub Actions"),
    ("connect", "06", "Say hello", "inbox is open"),
]


def headers(t):
    W, H = 1200, 100
    style = FADE_UP + """
    .draw{stroke-dasharray:1200;animation:draw 1.8s cubic-bezier(.6,0,.2,1) both .15s}
    @keyframes draw{from{stroke-dashoffset:1200}to{stroke-dashoffset:0}}
    """
    for key, num, title, aside in SECTIONS:
        tw = measure(title, SERIF, 50, spacing=-.8)
        body = (f'<g class="up">{label(2, 70, num, t["accent"], 13, spacing=1)}'
                f'<text x="44" y="74" font-family="{SERIF}" font-size="50" letter-spacing="-.8" fill="{t["text"]}">{esc(title)}</text>'
                f'{label(W - 2, 70, aside, t["muted"], 11.5, "end")}</g>'
                f'<path class="draw" d="M0 92H{W}" stroke="{t["edge"]}"/>'
                f'<path class="draw" d="M0 92H{44 + tw:.0f}" stroke="{t["accent"]}" stroke-width="1.5"/>')
        write(t, f"headers/{key}.svg", svg(W, H, body, style, f"{num} {title}"))


# ---------------------------------------------------------------- terminal

def terminal(t):
    W = 1200
    size, lh = 17, 32
    cw = measure("x", MONO, size)
    x0, y0 = 40, 100
    prompt = [("mehanth", t["accent"]), ("@chennai", t["muted"]), (" ~ $ ", t["dim"])]
    plen = sum(len(s) for s, _ in prompt)
    script = [
        ("cmd", "whoami"),
        ("out", [("Mehanth T", t["text"]), ("  ·  B.Tech CSE, SSN College of Engineering ’27  ·  Chennai", t["muted"])]),
        ("cmd", "cat focus.md"),
        ("out", [("— ", t["accent"]), ("agentic AI          ", t["text"]), ("langgraph, pgvector, multi-agent systems", t["muted"])]),
        ("out", [("— ", t["accent"]), ("backend & data      ", t["text"]), ("fastapi, spring boot, kafka, spark", t["muted"])]),
        ("out", [("— ", t["accent"]), ("3D & XR             ", t["text"]), ("three.js, webxr, blender", t["muted"])]),
        ("cmd", "cat achievements.txt"),
        ("out", [("— ", t["accent"]), ("4× hackathon winner, 2026", t["text"]), ("  ·  Best Performance at TechathonX", t["muted"])]),
        ("out", [("— ", t["accent"]), ("NPTEL top 1% in C++", t["text"]), ("  ·  top 5% in competitive programming", t["muted"])]),
        ("out", [("— ", t["accent"]), ("Lead, AR/VR & Game Dev Club", t["text"]), ("  ·  SSN College of Engineering", t["muted"])]),
        ("cmd", "echo $MOTTO"),
        ("out", [("real-world problems, solved with code.", t["text"])]),
        ("cmd", ""),
    ]
    H = y0 + lh * len(script) + 6
    total = 15.0
    style = f"""
    text{{white-space:pre}}
    .caret{{animation:blink 1.1s steps(1) infinite}}
    @keyframes blink{{50%{{opacity:0}}}}
    .loop{{animation:loop {total}s linear infinite}}
    @keyframes loop{{0%,95%{{opacity:1}}98.5%,100%{{opacity:0}}}}
    """

    def spans(parts):
        return "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in parts)

    tt = 0.03
    rows, kf = [], []
    for n, (kind, val) in enumerate(script):
        y = y0 + n * lh
        cls = f"r{n}"
        kf.append(f".{cls}{{opacity:0;animation:{cls} {total}s linear infinite}}"
                  f"@keyframes {cls}{{0%,{tt * 100:.2f}%{{opacity:0}}{tt * 100 + .01:.2f}%,100%{{opacity:1}}}}")
        if kind == "out":
            rows.append(f'<text class="{cls}" x="{x0 + 2 * cw:.1f}" y="{y}">{spans(val)}</text>')
            tt += 0.012
            continue
        px = x0 + plen * cw
        rows.append(f'<g class="{cls}"><text x="{x0}" y="{y}">{spans(prompt)}</text>')
        if val:
            n_ch = len(val)
            t_type = 0.006 * n_ch + 0.02
            start = tt + 0.035
            track = [(0, 0), (start, 0)] + [(start + t_type * k / n_ch, k * cw) for k in range(1, n_ch + 1)]
            rows.append(f'<clipPath id="c{n}"><rect x="{px:.1f}" y="{y - 22}" height="32" width="0">'
                        f'{discrete("width", track, total)}</rect></clipPath>'
                        f'<text clip-path="url(#c{n})" x="{px:.1f}" y="{y}" fill="{t["text"]}">{esc(val)}</text>')
            end = start + t_type + 0.025
            car = [(0, px), (start, px)] + [(start + t_type * k / n_ch, px + k * cw) for k in range(1, n_ch + 1)]
            rows.append(f'<rect y="{y - 15}" width="{cw:.1f}" height="20" fill="{t["accent"]}" x="{px:.1f}">'
                        f'{discrete("x", car, total)}'
                        f'{discrete("opacity", [(0, 0), (tt, 1), (end, 0)], total, "{:.0f}")}</rect>')
            tt = end
        else:
            rows.append(f'<rect class="caret" x="{px:.1f}" y="{y - 15}" width="{cw:.1f}" height="20" fill="{t["accent"]}"/>')
        rows.append("</g>")

    body = f"""<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{t["panel"]}" stroke="{t["edge"]}"/>
    <path d="M1 44H{W - 1}" stroke="{t["edge"]}"/>
    <circle cx="26" cy="22" r="5.5" fill="none" stroke="{t["dim"]}"/><circle cx="46" cy="22" r="5.5" fill="none" stroke="{t["dim"]}"/>
    <circle cx="66" cy="22" r="5.5" fill="none" stroke="{t["dim"]}"/>
    <text x="{W / 2}" y="26.5" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{t["dim"]}">mehanth@chennai — zsh</text>
    <g class="loop" font-family="{MONO}" font-size="{size}">{"".join(rows)}</g>"""
    write(t, "terminal.svg", svg(W, H, body, style + "".join(kf),
                                 "Terminal: whoami — Mehanth T, Chennai. Focus: 3D/XR, AI agents, full-stack, games."))


# ---------------------------------------------------------------- project cards

PROJECTS = [
    dict(slug="herbal-garden", title="Virtual Herbal Garden", kind="webxr · agentic AI", icon="threedotjs",
         href="https://vrroom.netlify.app", cta="Live", metric="100+ concurrent users",
         desc="A collaborative WebXR garden with 10 specialised AI agents, real weather and soil data, and geo-referenced crop simulation.",
         tags=["WebXR", "WebRTC", "WebSockets", "Node.js"]),
    dict(slug="stock-pipeline", title="Real-Time Stock Pipeline", kind="distributed systems", icon="apachekafka",
         href="https://github.com/Itz-mehanth/LiveStock", cta="Repo", metric="streaming + ML",
         desc="Kafka into Spark Streaming into PostgreSQL, with Spark MLlib retraining, a Flask API and a live Angular dashboard.",
         tags=["Kafka", "PySpark", "PostgreSQL", "Docker"]),
    dict(slug="vscode", title="VS Code Extensions", kind="developer products", icon="typescript",
         href="https://marketplace.visualstudio.com/publishers/Mehanth", cta="Marketplace", metric="5k+ downloads",
         desc="Bharat HTML/CSS lets you code in 23 Indian languages; HDR/EXR 360 Viewer renders HDR images on the GPU.",
         tags=["TypeScript", "VS Code API", "WebGL"]),
    dict(slug="retempla", title="ReTempla", kind="automation SaaS", icon="fastapi",
         href="https://github.com/Itz-mehanth/Retempla", cta="Repo", metric="API-first",
         desc="Generates and emails formatted DOCX certificates to hundreds of recipients per session, with API keys and analytics.",
         tags=["React", "FastAPI", "Firebase", "MongoDB"]),
    dict(slug="medplant", title="MedPlant", kind="on-device ML", icon="tensorflow",
         href="https://github.com/Itz-mehanth/MedPlant", cta="Repo", metric="90%+ accuracy",
         desc="Identifies medicinal plants fully offline, with edge inference on a Raspberry Pi and a multilingual Flutter app.",
         tags=["TensorFlow", "Flutter", "Flask", "Raspberry Pi"]),
    dict(slug="gh9b", title="GH9-B", kind="webxr · survival horror", icon="react",
         href="https://github.com/Itz-mehanth/GH9B", cta="Repo", metric="playable in VR",
         desc="Survive a haunted hostel, in the browser or in VR. Physics, dynamic lighting and a steady supply of dread.",
         tags=["React Three Fiber", "WebXR", "physics"]),
]


def card(t, i, p):
    W, H = 600, 290
    style = FADE_UP + """
    .ok{animation:ok 2.4s ease-in-out infinite}
    @keyframes ok{50%{opacity:.25}}
    """
    lines = wrap(p["desc"], W - 72, family=SANS, size=16.5)
    assert len(lines) <= 3, f"{p['slug']}: description wraps to {len(lines)} lines"
    desc = "".join(f'<text x="34" y="{170 + k * 25}">{esc(l)}</text>' for k, l in enumerate(lines))
    link = f"{p['cta']} ↗"
    meta = [f'<text x="{W - 34}" y="257" text-anchor="end" font-family="{SANS}" font-size="15" font-weight="500" '
            f'fill="{t["accent"]}">{esc(link)}</text>']
    if p["cta"] == "Live":
        mx = W - 34 - measure(link, SANS, 15, 500) - 12
        meta.append(f'<circle class="ok" cx="{mx:.0f}" cy="252" r="3.5" fill="{t["ok"]}"/>')
    metric = (f'<text x="{W - 34}" y="50" text-anchor="end" font-family="{MONO}" font-size="11.5" letter-spacing="1.6" '
              f'fill="{t["text"]}">{esc(p["metric"].upper())}</text>')
    body = f"""<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{t["panel"]}" stroke="{t["edge"]}"/>
    <g class="up" style="animation-delay:{.05 + (i % 2) * .1:.2f}s">
    {label(34, 50, f"{i + 1:02d}", t["accent"], 12, spacing=1)}
    {label(66, 50, p["kind"], t["muted"], 11.5)}
    {metric}
    <path d="M34 72H{W - 34}" stroke="{t["hair"]}"/>
    <text x="32" y="128" font-family="{SERIF}" font-size="46" letter-spacing="-.8" fill="{t["text"]}">{esc(p["title"])}</text>
    {icon(p["icon"], W - 56, 100, 22, t["dim"])}
    <g font-family="{SANS}" font-size="16.5" fill="{t["muted"]}">{desc}</g>
    <path d="M34 228H{W - 34}" stroke="{t["hair"]}"/>
    <text x="34" y="257" font-family="{MONO}" font-size="12.5" fill="{t["muted"]}">{esc("  /  ".join(p["tags"]))}</text>
    {"".join(meta)}
    </g>"""
    write(t, f"cards/{p['slug']}.svg", svg(W, H, body, style, f"{p['title']} — {p['desc']}"))


# ---------------------------------------------------------------- tech marquee

ROWS = [
    ["python", "openjdk", "cplusplus", "typescript", "javascript", "springboot", "fastapi", "flask",
     "nodedotjs", "postgresql", "mysql", "mongodb"],
    ["langgraph", "tensorflow", "opencv", "apachekafka", "apachespark", "docker", "react", "nextdotjs",
     "flutter", "threedotjs", "blender", "git", "firebase"],
]
NAMES = {"springboot": "Spring Boot", "fastapi": "FastAPI", "langgraph": "LangGraph", "mysql": "MySQL", "openjdk": "Java","cplusplus": "C++", "threedotjs": "Three.js", "vuedotjs": "Vue", "nextdotjs": "Next.js",
         "nodedotjs": "Node.js", "tailwindcss": "Tailwind", "webgl": "WebGL", "huggingface": "Hugging Face",
         "godotengine": "Godot", "mongodb": "MongoDB", "postgresql": "PostgreSQL", "apachekafka": "Kafka",
         "apachespark": "Spark", "opencv": "OpenCV", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
         "typescript": "TypeScript", "javascript": "JavaScript"}


def stack(t):
    W, H = 1200, 176
    rows, kf = [], []
    for r, slugs in enumerate(ROWS):
        y = 30 + r * 66
        items, x = [], 0
        for s in slugs:
            name = NAMES.get(s, s.capitalize())
            w = measure(name, SANS, 16, 500) + 66
            items.append(f'<g transform="translate({x:.0f} {y})"><rect x=".5" y=".5" width="{w:.0f}" height="50" rx="25" '
                         f'fill="none" stroke="{t["edge"]}"/>{icon(s, 20, 15, 20, t["text"])}'
                         f'<text x="50" y="31" font-family="{SANS}" font-size="16" font-weight="500" '
                         f'fill="{t["text"]}">{esc(name)}</text></g>')
            x += w + 12
        span = x
        a, z = (0, -span) if r == 0 else (-span, 0)
        kf.append(f".m{r}{{animation:m{r} {span / 30:.1f}s linear infinite}}"
                  f"@keyframes m{r}{{from{{transform:translateX({a:.0f}px)}}to{{transform:translateX({z:.0f}px)}}}}")
        group = "".join(items)
        rows.append(f'<g class="m{r}">{group}<g transform="translate({span:.0f} 0)">{group}</g></g>')
    body = f"""<defs><linearGradient id="f" x1="0" x2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".1" stop-color="#fff"/>
      <stop offset=".9" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <mask id="m"><rect width="{W}" height="{H}" fill="url(#f)"/></mask></defs>
    <g mask="url(#m)">{"".join(rows)}</g>"""
    write(t, "stack.svg", svg(W, H, body, "".join(kf), "Tech: " + ", ".join(NAMES.get(s, s) for row in ROWS for s in row)))


# ---------------------------------------------------------------- links + footer

LINKS = [
    ("portfolio", "mehanth.com"),
    ("linkedin", "in/mehanth"),
    ("email", "mehanth362@gmail.com"),
    ("instagram", "@itz_mehanth"),
]


def links(t):
    W, H = 290, 96
    for key, value in LINKS:
        fs = min(19, 19 * (W - 64) / measure(value, SANS, 19))
        body = f"""<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{t["panel"]}" stroke="{t["edge"]}"/>
        {label(24, 36, key, t["muted"], 11)}
        <text x="{W - 24}" y="37" text-anchor="end" font-family="{SANS}" font-size="17" fill="{t["accent"]}">↗</text>
        <text x="24" y="70" font-family="{SANS}" font-size="{fs:.1f}" fill="{t["text"]}">{esc(value)}</text>"""
        write(t, f"links/{key}.svg", svg(W, H, body, "", f"{key}: {value}"))


def footer(t):
    W, H = 1200, 170
    period = 240

    def wave(amp, y):
        return "M" + "L".join(f"{x} {y + amp * math.sin(2 * math.pi * x / period):.1f}" for x in range(0, 3 * W + 1, 8))

    body = f"""<defs><linearGradient id="f" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <mask id="m"><rect width="{W}" height="{H}" fill="url(#f)"/></mask></defs>
    <path d="M0 1H{W}" stroke="{t["edge"]}"/>
    <text x="{W / 2}" y="78" text-anchor="middle" font-family="{SERIF}" font-style="italic" font-size="44"
      letter-spacing="-.6" fill="{t["text"]}">Thanks for scrolling.</text>
    {label(W / 2, 110, "designed in python · drawn in svg · refreshed nightly", t["muted"], 11, "middle")}
    <g mask="url(#m)"><path class="w" d="{wave(5, 146)}" fill="none" stroke="{t["accent"]}" stroke-opacity=".55" stroke-width="1.2"/></g>"""
    style = f".w{{animation:w 14s linear infinite}}@keyframes w{{to{{transform:translateX(-{period * 5}px)}}}}"
    write(t, "footer.svg", svg(W, H, body, style, "Thanks for scrolling."))


# ---------------------------------------------------------------- README

LINK_HREFS = {"portfolio": "https://mehanth.com", "linkedin": "https://www.linkedin.com/in/mehanth-776892279",
              "email": "mailto:mehanth362@gmail.com", "instagram": "https://instagram.com/itz_mehanth"}
SNAKE = "https://raw.githubusercontent.com/Itz-mehanth/Itz-mehanth/output/github-snake"


def pic(path, alt, width="100%"):
    return (f'<picture><source media="(prefers-color-scheme: light)" srcset="assets/light/{path}"/>'
            f'<img src="assets/dark/{path}" width="{width}" alt="{esc(alt)}"/></picture>')


def readme():
    def header(key):
        num, title = next((n, ti) for k, n, ti, _ in SECTIONS if k == key)
        return pic(f"headers/{key}.svg", f"{num} {title}")

    exp = "; ".join(f"{e['role']}, {e['org'].split('  ')[0]} ({e['when']}): " + " ".join(e["points"])
                    for e in EXPERIENCE)
    parts = [
        "<!--\n  Every image on this page is an animated SVG with embedded fonts, in a dark and a light version.\n"
        "  Generated by scripts/build.py (this README too). Edit the data there, then run:  python scripts/build.py\n"
        "  assets/*/activity.svg is rebuilt nightly by .github/workflows/activity.yml\n-->\n",
        f'<a href="https://mehanth.com">{pic("hero.svg", "Mehanth T, software engineer. I build agentic AI systems, real-time data pipelines, 3D worlds for the web and tools developers install.")}</a>',
        "", pic("highlights.svg", " · ".join(f"{v} {s}" for v, s in HIGHLIGHTS)),
        "", "<br/><br/>", "", header("experience"), "", pic("experience.svg", exp),
        "", "<br/><br/>", "", header("work"), "", '<p align="center">',
        *[f'  <a href="{p["href"]}">{pic(f"cards/{p["slug"]}.svg", f"{p["title"]}: {p["desc"]}", "49%")}</a>'
          for p in PROJECTS],
        "</p>", "", "<br/>", "", header("about"), "",
        pic("terminal.svg", "B.Tech CSE at SSN College of Engineering, class of 2027. Focus: agentic AI, backend and data, 3D and XR. "
                            "4x hackathon winner in 2026, NPTEL top 1% in C++, Lead of the AR/VR and Game Dev Club at SSN."),
        "", "<br/><br/>", "", header("stack"), "",
        pic("stack.svg", ", ".join(NAMES.get(s, s.capitalize()) for row in ROWS for s in row)),
        "", "<br/>", "", header("activity"), "",
        pic("activity.svg", "Contribution stats and a 3D skyline of the last year of commits"), "",
        f'<picture><source media="(prefers-color-scheme: light)" srcset="{SNAKE}.svg"/>'
        f'<img src="{SNAKE}-dark.svg" width="100%" alt="A snake eating my contribution graph"/></picture>',
        "", "<br/><br/>", "", header("connect"), "", '<p align="center">',
        *[f'  <a href="{LINK_HREFS[k]}">{pic(f"links/{k}.svg", f"{k}: {v}", "24%")}</a>' for k, v in LINKS],
        "</p>", "", "<br/>", "", pic("footer.svg", "Thanks for scrolling."), "",
    ]
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts))
    print("  README.md")


if __name__ == "__main__":
    readme()
    for theme in THEMES.values():
        print(f"building assets/{theme['name']}/")
        hero(theme)
        highlights(theme)
        experience(theme)
        headers(theme)
        terminal(theme)
        for i, p in enumerate(PROJECTS):
            card(theme, i, p)
        stack(theme)
        links(theme)
        footer(theme)
