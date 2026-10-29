"""Shared themes, embedded fonts and helpers for the profile SVG generators."""
import base64
import io
import json
import os
import re
from functools import lru_cache
from html import escape, unescape

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FONT_DIR = os.path.join(ROOT, "scripts", "fonts")

# Fonts are subset to the glyphs each SVG uses and embedded as data URIs,
# so every visitor sees the same typography regardless of what they have installed.
SERIF = "'IS', Georgia, 'Times New Roman', serif"
SANS = "'G', system-ui, -apple-system, 'Segoe UI', sans-serif"
MONO = "'GM', ui-monospace, Menlo, Consolas, monospace"

FACES = {  # (family, style, weight) -> file
    ("IS", "normal", 400): "InstrumentSerif-Regular",
    ("IS", "italic", 400): "InstrumentSerif-Italic",
    ("G", "normal", 400): "Geist-Regular",
    ("G", "normal", 500): "Geist-Medium",
    ("G", "normal", 600): "Geist-SemiBold",
    ("GM", "normal", 400): "GeistMono-Regular",
    ("GM", "normal", 500): "GeistMono-Medium",
}
FAMILY_OF = {SERIF: "IS", SANS: "G", MONO: "GM"}

THEMES = {
    "dark": dict(
        name="dark", panel="#131211", edge="#2A2825", hair="#1F1E1C", text="#EEEAE3", muted="#A29D94",
        dim="#67635C", accent="#F2683C", ok="#9DBF8F",
        ramp=["#22201E", "#4A2C20", "#7E3D24", "#B9522B", "#F2683C"],
    ),
    "light": dict(
        name="light", panel="#FBFAF7", edge="#E2DDD3", hair="#EEEAE2", text="#1B1A18", muted="#6E695F",
        dim="#A8A398", accent="#D2541F", ok="#4F7A45",
        ramp=["#ECE8E0", "#F4CDB8", "#EC9F78", "#E0703F", "#C24A16"],
    ),
}

with open(os.path.join(ROOT, "scripts", "icons.json"), encoding="utf-8") as f:
    ICONS = json.load(f)


def esc(s):
    return escape(str(s), quote=True)


@lru_cache(None)
def _metrics(file):
    font = TTFont(os.path.join(FONT_DIR, file + ".ttf"))
    return font.getBestCmap(), font["hmtx"].metrics, font["head"].unitsPerEm


def measure(text, family=SANS, size=16, weight=400, italic=False, spacing=0):
    """Advance width of text in px (no kerning; close enough for layout)."""
    fam = FAMILY_OF[family]
    style = "italic" if italic else "normal"
    key = (fam, style, weight) if (fam, style, weight) in FACES else (fam, style, 400)
    cmap, hmtx, upm = _metrics(FACES[key])
    units = sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text)
    return units * size / upm + spacing * max(len(text) - 1, 0)


def wrap(text, width, **font):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, **font) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur] if cur else lines


def icon(slug, x, y, size, color):
    s = size / 24
    return (f'<path transform="translate({x:.1f} {y:.1f}) scale({s:.4f})" '
            f'fill="{color}" d="{ICONS[slug]["d"]}"/>')


def _font_css(body):
    chars = set(unescape(re.sub(r"<[^>]+>", "", body))) | {" "}
    text = "".join(sorted(chars))
    css = []
    for (fam, style, weight), file in FACES.items():
        if f"'{fam}'," not in body or (style == "italic" and "italic" not in body):
            continue
        if fam == "G" and weight != 400 and f'font-weight="{weight}"' not in body:
            continue
        if fam == "GM" and weight != 400 and f'font-weight="{weight}"' not in body:
            continue
        font = TTFont(os.path.join(FONT_DIR, file + ".ttf"))
        opts = subset.Options()
        opts.flavor = "woff"
        opts.layout_features = ["kern", "liga", "calt", "tnum"]
        opts.name_IDs = []
        sub = subset.Subsetter(opts)
        sub.populate(text=text)
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff"
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        css.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
                   f"src:url(data:font/woff;base64,{data}) format('woff')}}")
    return "".join(css)


def svg(w, h, body, style="", title=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title><style>{_font_css(body)}{style}</style>{body}</svg>')


def write(theme, rel, content):
    path = os.path.join(ASSETS, theme["name"], rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  {theme['name']}/{rel:<26} {len(content) / 1024:6.1f} KB")
