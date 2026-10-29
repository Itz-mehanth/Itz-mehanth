"""Generates every static SVG in assets/. Run: python scripts/build.py"""
import math
import random
import textwrap

from common import (AMBER, BG, CYAN, DIM, EDGE, GREEN, MONO, MUTED, PANEL, PINK, SANS, TEXT,
                    VIOLET, esc, icon, icon_color, mono_width, svg, write)

PROFILE = "https://github.com/Itz-mehanth"


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


def wireframe(cx, cy, r, verts, edges, angles, frames, dur, stroke, dot_r):
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
        return 0.12 + 0.88 * ((z + 1) / 2) ** 1.6

    anim = f'dur="{dur}s" repeatCount="indefinite"'
    out = []
    for i, j in edges:
        d = ";".join(f"M{p[i][0]:.1f} {p[i][1]:.1f}L{p[j][0]:.1f} {p[j][1]:.1f}" for p in proj)
        o = ";".join(f"{depth((p[i][2] + p[j][2]) / 2):.2f}" for p in proj)
        out.append(f'<path stroke="{stroke}" stroke-width="1.6" stroke-linecap="round">'
                   f'<animate attributeName="d" values="{d}" {anim}/>'
                   f'<animate attributeName="stroke-opacity" values="{o}" {anim}/></path>')
    for i in range(len(verts)):
        xs = ";".join(f"{p[i][0]:.1f}" for p in proj)
        ys = ";".join(f"{p[i][1]:.1f}" for p in proj)
        o = ";".join(f"{depth(p[i][2]):.2f}" for p in proj)
        out.append(f'<circle r="{dot_r}" fill="#fff">'
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


def typing_track(n, start, t_type, t_hold, t_del, cw):
    """(time, revealed-width) pairs: type n chars, hold, delete them."""
    pts = [(start + t_type * k / n, k * cw) for k in range(n + 1)]
    end = start + t_type + t_hold
    pts += [(end + t_del * k / n, (n - k) * cw) for k in range(1, n + 1)]
    return pts


# ---------------------------------------------------------------- hero

def hero():
    W, H = 1200, 440
    rnd = random.Random(7)
    style = """
    .blob{animation:drift 16s ease-in-out infinite alternate}
    .b2{animation-duration:21s;animation-delay:-7s}
    .b3{animation-duration:26s;animation-delay:-13s}
    @keyframes drift{from{transform:translate(0,0)}to{transform:translate(-70px,45px)}}
    .star{animation:tw 4s ease-in-out infinite}
    @keyframes tw{0%,100%{opacity:.1}50%{opacity:.85}}
    .caret{animation:blink 1s steps(1) infinite}
    @keyframes blink{50%{opacity:0}}
    .ping{animation:ping 2s ease-out infinite;transform-box:fill-box;transform-origin:center}
    @keyframes ping{from{transform:scale(1);opacity:.8}to{transform:scale(3.2);opacity:0}}
    .rise{animation:rise 1s cubic-bezier(.2,.8,.2,1) both}
    @keyframes rise{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:none}}
    .float{animation:float 7s ease-in-out infinite}
    @keyframes float{0%,100%{transform:translateY(-8px)}50%{transform:translateY(8px)}}
    .shadow{animation:shadow 7s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
    @keyframes shadow{0%,100%{transform:scale(.85);opacity:.55}50%{transform:scale(1.05);opacity:.9}}
    """
    defs = f"""<defs>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="28"/></clipPath>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0A0D18"/><stop offset="1" stop-color="{BG}"/></linearGradient>
    <linearGradient id="ng" x1="0" y1="0" x2="620" y2="0" gradientUnits="userSpaceOnUse" spreadMethod="reflect">
      <stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="0 0;1240 0" dur="9s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="wire" x1="760" y1="60" x2="1100" y2="380" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>
    <radialGradient id="floor"><stop offset="0" stop-color="{CYAN}" stop-opacity=".45"/>
      <stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
    <radialGradient id="fade" cx=".3" cy=".4" r=".8"><stop offset="0" stop-color="#fff" stop-opacity=".9"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <mask id="gridmask"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
    <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
      <circle cx="1" cy="1" r="1" fill="#fff" fill-opacity=".09"/></pattern>
    <filter id="blur" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="55"/></filter>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>"""

    b = [f'<g clip-path="url(#frame)"><rect width="{W}" height="{H}" fill="url(#bg)"/>',
         f'<circle class="blob" cx="960" cy="110" r="150" fill="{CYAN}" opacity=".16" filter="url(#blur)"/>',
         f'<circle class="blob b2" cx="1080" cy="400" r="170" fill="{VIOLET}" opacity=".22" filter="url(#blur)"/>',
         f'<circle class="blob b3" cx="180" cy="470" r="160" fill="{PINK}" opacity=".10" filter="url(#blur)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gridmask)"/>']
    for _ in range(46):
        b.append(f'<circle class="star" cx="{rnd.uniform(20, W - 20):.0f}" cy="{rnd.uniform(15, H - 15):.0f}" '
                 f'r="{rnd.choice((.7, 1, 1.3)):.1f}" fill="#fff" '
                 f'style="animation-delay:-{rnd.uniform(0, 4):.1f}s;animation-duration:{rnd.uniform(3, 6):.1f}s"/>')

    # the spinning object
    cx, cy = 935, 205
    b.append(f'<ellipse class="shadow" cx="{cx}" cy="388" rx="170" ry="20" fill="url(#floor)"/>')
    b.append('<g class="float">')
    for rx, ry, ang, col, dur, rev in ((235, 58, -16, CYAN, 9, False), (205, 74, 22, PINK, 13, True)):
        path = f"M{cx - rx} {cy}a{rx} {ry} 0 1 {0 if rev else 1} {2 * rx} 0a{rx} {ry} 0 1 {0 if rev else 1} {-2 * rx} 0"
        b.append(f'<g transform="rotate({ang} {cx} {cy})"><path d="{path}" fill="none" stroke="{col}" '
                 f'stroke-opacity=".22" stroke-dasharray="2 7"/>'
                 f'<circle r="4" fill="{col}" filter="url(#glow)"><animateMotion dur="{dur}s" '
                 f'repeatCount="indefinite" path="{path}"/></circle></g>')
    b.append('<g filter="url(#glow)" fill="none">')
    b.append(wireframe(cx, cy, 150, ICO_V, ICO_E, lambda t: (0.42, t, 0.22), 90, 26, "url(#wire)", 3.2))
    b.append(wireframe(cx, cy, 62, OCT_V, OCT_E, lambda t: (2 * t, -t, -0.3), 90, 26, PINK, 2.4))
    b.append('</g></g>')

    # copy
    x0 = 72
    b.append(f'<text class="rise" style="animation-delay:.1s" x="{x0}" y="112" font-family="{MONO}" '
             f'font-size="17" fill="{CYAN}">// hello, world — I&#8217;m</text>')
    b.append(f'<text class="rise" style="animation-delay:.25s" x="{x0 - 5}" y="216" font-family="{SANS}" '
             f'font-size="104" font-weight="800" letter-spacing="-3" fill="url(#ng)">Mehanth T</text>')

    size, cw = 28, mono_width("x", 28)
    phrases = ["3D worlds for the browser", "AI agents that do the work",
               "AR you can walk around in", "HTML speak 23 Indian languages"]
    colors = [CYAN, VIOLET, GREEN, AMBER]
    px = x0 + 7 * cw
    total, slot = 18.0, 1 / len(phrases)
    caret = [(0, px)]
    line = [f'<g class="rise" style="animation-delay:.4s" font-family="{MONO}" font-size="{size}">',
            f'<text x="{x0}" y="282" fill="{MUTED}" textLength="{6 * cw:.1f}">I make</text>']
    for i, (p, c) in enumerate(zip(phrases, colors)):
        track = typing_track(len(p), i * slot + 0.01, 0.075, 0.115, 0.03, cw)
        clip = [(0, 0)] + track
        caret += [(t, px + w) for t, w in track]
        line.append(f'<clipPath id="t{i}"><rect x="{px}" y="250" height="44" width="0">'
                    f'{discrete("width", clip, total)}</rect></clipPath>')
        line.append(f'<text clip-path="url(#t{i})" x="{px}" y="282" fill="{c}" font-weight="600" '
                    f'textLength="{len(p) * cw:.1f}">{esc(p)}</text>')
    line.append(f'<rect class="caret" y="258" width="3" height="30" fill="{TEXT}" x="{px}">'
                f'{discrete("x", caret, total)}</rect></g>')
    b += line

    b.append(f'<text class="rise" style="animation-delay:.55s" x="{x0}" y="336" font-family="{SANS}" '
             f'font-size="19" fill="{MUTED}">Building scalable apps, automations &amp; intelligent systems '
             f'—</text><text class="rise" style="animation-delay:.6s" x="{x0}" y="362" font-family="{SANS}" '
             f'font-size="19" fill="{MUTED}">real-world problems, solved with code.</text>')

    cx_ = x0
    chips = [("Chennai, India", GREEN, True), ("3D · XR · AI · full-stack", None, False),
             ("60+ public repos", None, False)]
    g = ['<g class="rise" style="animation-delay:.75s">']
    for label, dot, ping in chips:
        w = mono_width(label, 14) + (50 if dot else 30)
        g.append(f'<rect x="{cx_}" y="386" width="{w:.0f}" height="32" rx="16" fill="#fff" '
                 f'fill-opacity=".04" stroke="{EDGE}"/>')
        tx = cx_ + 15
        if dot:
            g.append(f'<circle class="ping" cx="{tx + 6}" cy="402" r="4" fill="{dot}"/>'
                     f'<circle cx="{tx + 6}" cy="402" r="4" fill="{dot}"/>')
            tx += 20
        g.append(f'<text x="{tx}" y="407" font-family="{MONO}" font-size="14" fill="{TEXT}">{esc(label)}</text>')
        cx_ += w + 10
    g.append('</g>')
    b += g

    b.append(f'<text x="{W - 28}" y="{H - 18}" text-anchor="end" font-family="{MONO}" font-size="11" '
             f'fill="{DIM}">yes, this is still a README · hand-written SVG, zero gifs</text>')
    b.append(f'</g><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="28" fill="none" stroke="{EDGE}"/>')
    write("hero.svg", svg(W, H, defs + "".join(b), style, "Mehanth T — I make 3D worlds, AI agents and AR apps"))


# ---------------------------------------------------------------- section headers

SECTIONS = [
    ("about", "01", "About me", "~/whoami", CYAN),
    ("work", "02", "Things I&#8217;ve built", "8 picks from 60+ repos", VIOLET),
    ("stack", "03", "Toolbox", "daily drivers", PINK),
    ("activity", "04", "Activity", "rebuilt every night by a GitHub Action", GREEN),
    ("connect", "05", "Let&#8217;s build something", "inbox is open", AMBER),
]


def headers():
    W, H = 1200, 110
    style = """
    .draw{stroke-dasharray:1200;animation:draw 1.6s cubic-bezier(.6,0,.2,1) both .2s}
    @keyframes draw{from{stroke-dashoffset:1200}to{stroke-dashoffset:0}}
    .in{animation:in .8s ease-out both}
    @keyframes in{from{opacity:0;transform:translateX(-14px)}to{opacity:1;transform:none}}
    """
    for theme, fg, muted in (("dark", TEXT, MUTED), ("light", "#0D1117", "#57606A")):
        for key, num, title, aside, acc in SECTIONS:
            path = f"M0 92H{W}"
            body = f"""<defs><linearGradient id="l" x1="0" x2="1">
              <stop offset="0" stop-color="{acc}"/><stop offset=".55" stop-color="{acc}" stop-opacity=".25"/>
              <stop offset="1" stop-color="{acc}" stop-opacity="0"/></linearGradient></defs>
            <g class="in"><text x="2" y="66" font-family="{MONO}" font-size="18" font-weight="600" fill="{acc}">/{num}</text>
            <text x="58" y="68" font-family="{SANS}" font-size="38" font-weight="750" letter-spacing="-.5" fill="{fg}">{title}</text>
            <text x="{W - 2}" y="66" text-anchor="end" font-family="{MONO}" font-size="14" fill="{muted}">{aside}</text></g>
            <path class="draw" d="{path}" stroke="url(#l)" stroke-width="2"/>
            <circle r="3.5" fill="{acc}"><animateMotion dur="5s" repeatCount="indefinite" path="{path}"
              keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines=".6 0 .4 1"/>
              <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.75;1" dur="5s" repeatCount="indefinite"/></circle>"""
            write(f"headers/{key}-{theme}.svg", svg(W, H, body, style, title.replace("&#8217;", "'")))


# ---------------------------------------------------------------- terminal

def terminal():
    W = 1200
    size, lh, cw = 19, 34, mono_width("x", 19)
    x0, y0 = 40, 104
    prompt = [("mehanth", GREEN), ("@", MUTED), ("chennai", CYAN), (" ~ ", VIOLET), ("$ ", MUTED)]
    plen = sum(len(t) for t, _ in prompt)
    script = [
        ("cmd", "whoami"),
        ("out", [("Mehanth T", TEXT), ("  ·  computer science engineer  ·  Chennai, India", MUTED)]),
        ("cmd", "cat focus.md"),
        ("out", [("▸ ", CYAN), ("3D + XR on the web     ", TEXT), ("three.js · react-three-fiber · webxr", MUTED)]),
        ("out", [("▸ ", VIOLET), ("AI agents & automation ", TEXT), ("python · whisper · transformers · multi-agent", MUTED)]),
        ("out", [("▸ ", PINK), ("full-stack products    ", TEXT), ("react · vue · node · flask · flutter", MUTED)]),
        ("out", [("▸ ", AMBER), ("games                  ", TEXT), ("godot · unity · android · webgl", MUTED)]),
        ("cmd", "echo $MOTTO"),
        ("out", [('"real-world problems, solved with code."', GREEN)]),
        ("cmd", ""),
    ]
    H = y0 + lh * len(script) + 10
    total = 15.0
    style = f"""
    text{{white-space:pre}}
    .caret{{animation:blink 1s steps(1) infinite}}
    @keyframes blink{{50%{{opacity:0}}}}
    .loop{{animation:loop {total}s linear infinite}}
    @keyframes loop{{0%,95%{{opacity:1}}98.5%,100%{{opacity:0}}}}
    """

    def spans(parts):
        return "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for t, c in parts)

    t = 0.03
    rows, kf = [], []
    for n, (kind, val) in enumerate(script):
        y = y0 + n * lh
        cls = f"r{n}"
        kf.append(f".{cls}{{opacity:0;animation:{cls} {total}s linear infinite}}"
                  f"@keyframes {cls}{{0%,{t * 100:.2f}%{{opacity:0}}{t * 100 + .01:.2f}%,100%{{opacity:1}}}}")
        if kind == "out":
            rows.append(f'<text class="{cls}" x="{x0 + 2 * cw:.1f}" y="{y}">{spans(val)}</text>')
            t += 0.012
            continue
        px = x0 + plen * cw
        rows.append(f'<g class="{cls}"><text x="{x0}" y="{y}">{spans(prompt)}</text>')
        if val:
            n_ch = len(val)
            t_type = 0.012 * n_ch / 2 + 0.02
            start = t + 0.035
            track = [(0, 0), (start, 0)] + [(start + t_type * k / n_ch, k * cw) for k in range(1, n_ch + 1)]
            rows.append(f'<clipPath id="c{n}"><rect x="{px:.1f}" y="{y - 24}" height="34" width="0">'
                        f'{discrete("width", track, total)}</rect></clipPath>'
                        f'<text clip-path="url(#c{n})" x="{px:.1f}" y="{y}" fill="{TEXT}" '
                        f'textLength="{n_ch * cw:.1f}">{esc(val)}</text>')
            end = start + t_type + 0.025
            car = [(0, px), (start, px)] + [(start + t_type * k / n_ch, px + k * cw) for k in range(1, n_ch + 1)]
            rows.append(f'<rect y="{y - 17}" width="{cw * .9:.1f}" height="22" fill="{CYAN}" x="{px:.1f}">'
                        f'{discrete("x", car, total)}'
                        f'{discrete("opacity", [(0, 0), (t, 1), (end, 0)], total, "{:.0f}")}</rect>')
            t = end
        else:
            rows.append(f'<rect class="caret" x="{px:.1f}" y="{y - 17}" width="{cw * .9:.1f}" height="22" fill="{CYAN}"/>')
        rows.append("</g>")

    body = f"""<defs><linearGradient id="bar" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#161B28"/><stop offset="1" stop-color="#11151F"/></linearGradient>
      <radialGradient id="glo" cx="1" cy="0" r="1"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".18"/>
      <stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient></defs>
    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="{PANEL}" stroke="{EDGE}"/>
    <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="url(#glo)"/>
    <path d="M1 46V19A18 18 0 0 1 19 1H{W - 19}A18 18 0 0 1 {W - 1} 19V46Z" fill="url(#bar)"/>
    <path d="M1 46H{W - 1}" stroke="{EDGE}"/>
    <circle cx="28" cy="24" r="7" fill="#FF5F57"/><circle cx="52" cy="24" r="7" fill="#FEBC2E"/><circle cx="76" cy="24" r="7" fill="#28C840"/>
    <text x="{W / 2}" y="29" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">mehanth@chennai — zsh — 120×32</text>
    <g class="loop" font-family="{MONO}" font-size="{size}" xml:space="preserve">{"".join(rows)}</g>"""
    write("terminal.svg", svg(W, H, body, style + "".join(kf), "Terminal: whoami — Mehanth T, Chennai. Focus: 3D/XR, AI agents, full-stack, games."))


# ---------------------------------------------------------------- project cards

PROJECTS = [
    dict(slug="bharat-html", repo="Tamil-HTML-CSS", title="Bharat HTML", kind="language tooling",
         icon="typescript", accent="#FF9933",
         desc="Write HTML and CSS in 23 Indian languages. Learning to code shouldn't require learning English first.",
         tags=["TypeScript", "transpiler", "i18n"], stars=9),
    dict(slug="gh9b", repo="GH9B", title="GH9-B", kind="webxr · survival horror", icon="threedotjs",
         accent="#FF3B5C",
         desc="Survive a haunted hostel, in the browser or in VR. Physics, dynamic lighting and a steady supply of dread.",
         tags=["React Three Fiber", "WebXR", "physics"]),
    dict(slug="crown", repo="CrownOfSovereigns", title="Crown of Sovereigns", kind="3D strategy game",
         icon="godotengine", accent="#FFC14D", live=True,
         desc="A tile-laying strategy board game in full 3D. Place tiles, build cities and outwit your rivals.",
         tags=["Godot 4.4", "GDScript", "web export"]),
    dict(slug="aura", repo="Aura-AI-Agent", title="Aura", kind="voice AI agent", icon="huggingface",
         accent=CYAN,
         desc="A voice-activated assistant that runs your machine. Whisper for ears, Transformers for a brain, Python for hands.",
         tags=["Python", "Whisper", "Transformers"]),
    dict(slug="4kwallpaper", repo="4kwallpaper.ai", title="4kwallpaper.ai", kind="multi-agent system",
         icon="python", accent=PINK,
         desc="An autonomous Instagram studio: a team of agents that creates, publishes and runs the community end to end.",
         tags=["Python", "multi-agent", "automation"]),
    dict(slug="ardrive", repo="ARDrive", title="ARDrive", kind="augmented reality", icon="webgl",
         accent=GREEN, live=True,
         desc="Your Google Drive in augmented reality. Browse and arrange files as objects floating in the room around you.",
         tags=["WebXR", "Drive API", "3D UI"]),
    dict(slug="retempla", repo="Retempla", title="Retempla", kind="document automation", icon="nodedotjs",
         accent="#6E8BFF",
         desc="Upload a raw .docx, pick a template and get a perfectly styled document back in seconds. API-first.",
         tags=["full-stack", "docx engine", "REST API"]),
    dict(slug="r3f-nav", repo="NPM-Package---R3F-Nav-Controls", title="r3f-nav-controls", kind="npm package",
         icon="react", accent=VIOLET,
         desc="Drop-in joystick, keyboard and pointer controls for React Three Fiber scenes. FPS, exploration, mobile.",
         tags=["React", "R3F", "TypeScript"]),
]


def card(i, p):
    W, H = 600, 270
    acc = p["accent"]
    style = f"""
    .shine{{animation:shine 8s ease-in-out infinite {i * .7:.1f}s}}
    @keyframes shine{{0%{{transform:translateX(-260px)}}22%,100%{{transform:translateX(900px)}}}}
    .glow{{animation:glow 5s ease-in-out infinite {i * .4:.1f}s;transform-box:fill-box;transform-origin:center}}
    @keyframes glow{{0%,100%{{opacity:.35;transform:scale(1)}}50%{{opacity:.6;transform:scale(1.15)}}}}
    .in{{animation:in .9s cubic-bezier(.2,.8,.2,1) both {.1 + (i % 2) * .15:.2f}s}}
    @keyframes in{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
    """
    lines = textwrap.wrap(p["desc"], 56)
    desc = "".join(f'<tspan x="34" dy="{0 if k == 0 else 25}">{esc(l)}</tspan>' for k, l in enumerate(lines))
    tags, tx = [], 34
    for t in p["tags"]:
        w = mono_width(t, 12.5) + 22
        tags.append(f'<rect x="{tx:.0f}" y="222" width="{w:.0f}" height="26" rx="7" fill="{acc}" fill-opacity=".09" '
                    f'stroke="{acc}" stroke-opacity=".25"/><text x="{tx + 11:.0f}" y="239.5" font-family="{MONO}" '
                    f'font-size="12.5" fill="{TEXT}" fill-opacity=".85">{esc(t)}</text>')
        tx += w + 8
    meta = []
    if p.get("live"):
        meta.append((f'<circle cx="0" cy="-4" r="4" fill="{GREEN}"><animate attributeName="opacity" '
                     f'values="1;.3;1" dur="1.6s" repeatCount="indefinite"/></circle>', "live demo", GREEN))
    if p.get("stars"):
        meta.append(("", f"★ {p['stars']}", AMBER))
    m, mx = [], W - 34
    for dot, label, col in reversed(meta):
        tw = mono_width(label, 13)
        m.append(f'<text x="{mx}" y="44" text-anchor="end" font-family="{MONO}" font-size="13" fill="{col}">{esc(label)}</text>')
        mx -= tw
        if dot:
            m.append(f'<g transform="translate({mx - 12:.0f} 44)">{dot}</g>')
            mx -= 16
        mx -= 18
    body = f"""<defs>
    <clipPath id="cl"><rect width="{W}" height="{H}" rx="20"/></clipPath>
    <linearGradient id="bd" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{acc}"/><stop offset=".35" stop-color="{acc}" stop-opacity=".08"/>
      <stop offset=".65" stop-color="{acc}" stop-opacity=".08"/><stop offset="1" stop-color="{acc}" stop-opacity=".9"/>
      <animateTransform attributeName="gradientTransform" type="rotate" values="0 .5 .5;360 .5 .5" dur="7s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".5" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <filter id="bl" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="40"/></filter>
    </defs>
    <g clip-path="url(#cl)"><rect width="{W}" height="{H}" fill="{PANEL}"/>
    <circle class="glow" cx="{W - 40}" cy="30" r="90" fill="{acc}" filter="url(#bl)"/>
    <text x="{W - 26}" y="{H - 30}" text-anchor="end" font-family="{SANS}" font-size="150" font-weight="900"
      fill="none" stroke="{acc}" stroke-opacity=".13" stroke-width="1.5">{i + 1:02d}</text>
    <rect class="shine" x="0" y="-40" width="160" height="{H + 80}" fill="url(#sh)" transform="skewX(-18)"/></g>
    <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="19" fill="none" stroke="url(#bd)" stroke-width="1.6"/>
    <g class="in">
    <rect x="34" y="30" width="54" height="54" rx="14" fill="{acc}" fill-opacity=".1" stroke="{acc}" stroke-opacity=".3"/>
    {icon(p["icon"], 47, 43, 28)}
    <text x="106" y="52" font-family="{MONO}" font-size="12.5" letter-spacing="1.6" fill="{acc}">{esc(p["kind"].upper())}</text>
    <text x="105" y="83" font-family="{SANS}" font-size="28" font-weight="750" letter-spacing="-.4" fill="{TEXT}">{esc(p["title"])}</text>
    {"".join(m)}
    <text y="132" font-family="{SANS}" font-size="16.5" fill="{MUTED}">{desc}</text>
    {"".join(tags)}
    <text x="{W - 34}" y="240" text-anchor="end" font-family="{MONO}" font-size="13" fill="{acc}">view repo ↗</text>
    </g>"""
    write(f"cards/{p['slug']}.svg", svg(W, H, body, style, f"{p['title']} — {p['desc']}"))


# ---------------------------------------------------------------- tech marquee

ROWS = [
    ["python", "typescript", "javascript", "openjdk", "cplusplus", "dart", "react", "threedotjs",
     "vuedotjs", "nextdotjs", "nodedotjs", "tailwindcss", "flask", "webgl"],
    ["tensorflow", "pytorch", "opencv", "huggingface", "flutter", "android", "godotengine", "unity",
     "blender", "mongodb", "postgresql", "firebase", "apachekafka", "apachespark", "docker", "git", "figma", "vercel"],
]
NAMES = {"openjdk": "Java", "cplusplus": "C++", "threedotjs": "Three.js", "vuedotjs": "Vue", "nextdotjs": "Next.js",
         "nodedotjs": "Node.js", "tailwindcss": "Tailwind", "webgl": "WebGL", "huggingface": "Hugging Face",
         "godotengine": "Godot", "mongodb": "MongoDB", "postgresql": "PostgreSQL", "apachekafka": "Kafka",
         "apachespark": "Spark", "opencv": "OpenCV", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
         "typescript": "TypeScript", "javascript": "JavaScript"}


def stack():
    W, H = 1200, 214
    rows, kf = [], []
    for r, slugs in enumerate(ROWS):
        y = 34 + r * 84
        pills, x = [], 0
        for s in slugs:
            name = NAMES.get(s, s.capitalize())
            w = mono_width(name, 15) + 66
            col = icon_color(s)
            pills.append(f'<g transform="translate({x:.0f} {y})"><rect width="{w:.0f}" height="58" rx="16" '
                         f'fill="#fff" fill-opacity=".03" stroke="{EDGE}"/>'
                         f'<rect x="12" y="13" width="32" height="32" rx="9" fill="{col}" fill-opacity=".12"/>'
                         f'{icon(s, 18, 19, 20, col)}<text x="54" y="34.5" font-family="{MONO}" font-size="15" '
                         f'fill="{TEXT}">{esc(name)}</text></g>')
            x += w + 14
        span = x
        dur = span / 38
        a, bnd = (0, -span) if r == 0 else (-span, 0)
        kf.append(f".m{r}{{animation:m{r} {dur:.1f}s linear infinite}}"
                  f"@keyframes m{r}{{from{{transform:translateX({a:.0f}px)}}to{{transform:translateX({bnd:.0f}px)}}}}")
        group = "".join(pills)
        rows.append(f'<g class="m{r}">{group}<g transform="translate({span:.0f} 0)">{group}</g></g>')
    body = f"""<defs><linearGradient id="f" x1="0" x2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".08" stop-color="#fff"/>
      <stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <mask id="m"><rect width="{W}" height="{H}" fill="url(#f)"/></mask>
      <clipPath id="c"><rect width="{W}" height="{H}" rx="20"/></clipPath></defs>
    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="20" fill="{PANEL}" stroke="{EDGE}"/>
    <g clip-path="url(#c)"><g mask="url(#m)">{"".join(rows)}</g></g>"""
    write("stack.svg", svg(W, H, body, "".join(kf), "Tech: " + ", ".join(NAMES.get(s, s) for row in ROWS for s in row)))


# ---------------------------------------------------------------- links + footer

LINKS = [
    ("portfolio", "mehanth.vercel.app", CYAN),
    ("linkedin", "in/mehanth", "#4C9AFF"),
    ("email", "mehanth362@gmail.com", PINK),
    ("instagram", "@itz_mehanth", AMBER),
]


def links():
    W, H = 290, 84
    for i, (label, value, acc) in enumerate(LINKS):
        fs = 15 if len(value) < 19 else 13.5
        body = f"""<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{acc}" stop-opacity=".16"/>
          <stop offset="1" stop-color="{acc}" stop-opacity="0"/></linearGradient></defs>
        <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{PANEL}" stroke="{EDGE}"/>
        <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="url(#g)"/>
        <rect x="0" y="20" width="3" height="44" rx="1.5" fill="{acc}"/>
        <text x="22" y="34" font-family="{MONO}" font-size="12" letter-spacing="1.5" fill="{acc}">{label.upper()}</text>
        <text x="22" y="60" font-family="{MONO}" font-size="{fs}" fill="{TEXT}">{esc(value)}</text>
        <text x="{W - 20}" y="34" text-anchor="end" font-family="{SANS}" font-size="18" fill="{acc}">↗
          <animate attributeName="opacity" values=".4;1;.4" dur="2.4s" begin="{i * .6:.1f}s" repeatCount="indefinite"/></text>"""
        write(f"links/{label}.svg", svg(W, H, body, "", f"{label}: {value}"))


def footer():
    W, H = 1200, 200

    def wave(amp, period, y):
        pts = [f"{x} {y + amp * math.sin(2 * math.pi * x / period):.1f}" for x in range(0, 3 * W + 1, 10)]
        return "M" + "L".join(pts)

    waves, kf = [], []
    for k, (amp, period, y, col, dur) in enumerate(((10, 300, 150, CYAN, 12), (14, 400, 158, VIOLET, 17),
                                                     (8, 240, 166, PINK, 9))):
        kf.append(f".w{k}{{animation:w{k} {dur}s linear infinite}}"
                  f"@keyframes w{k}{{to{{transform:translateX(-{period * (W // period + 1)}px)}}}}")
        waves.append(f'<path class="w{k}" d="{wave(amp, period, y)}" fill="none" stroke="{col}" '
                     f'stroke-opacity=".5" stroke-width="1.6"/>')
    body = f"""<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="22"/></clipPath>
      <linearGradient id="f" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <mask id="m"><rect width="{W}" height="{H}" fill="url(#f)"/></mask></defs>
    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="{PANEL}" stroke="{EDGE}"/>
    <g clip-path="url(#c)"><g mask="url(#m)">{"".join(waves)}</g></g>
    <text x="{W / 2}" y="76" text-anchor="middle" font-family="{SANS}" font-size="30" font-weight="750"
      letter-spacing="-.4" fill="{TEXT}">Thanks for scrolling this far.</text>
    <text x="{W / 2}" y="108" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{MUTED}">every pixel above is hand-written SVG, generated by Python and refreshed by GitHub Actions</text>"""
    write("footer.svg", svg(W, H, body, "".join(kf), "Thanks for scrolling this far."))


if __name__ == "__main__":
    print("building assets/")
    hero()
    headers()
    terminal()
    for i, p in enumerate(PROJECTS):
        card(i, p)
    stack()
    links()
    footer()
