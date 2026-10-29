"""Shared palette, fonts and helpers for the profile SVG generators."""
import json
import os
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Inter, Arial, sans-serif"
MONO = "'JetBrains Mono', 'Cascadia Code', 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
MONO_W = 0.6  # advance width of one monospace glyph, in em

BG = "#07090F"
PANEL = "#0B0E17"
EDGE = "#1C2333"
TEXT = "#E6EDF3"
MUTED = "#8B95A7"
DIM = "#4B5466"
CYAN = "#00F7F4"
VIOLET = "#8B5CF6"
PINK = "#FF4D9D"
GREEN = "#3DDC84"
AMBER = "#FFB547"

with open(os.path.join(ROOT, "scripts", "icons.json"), encoding="utf-8") as f:
    ICONS = json.load(f)


def esc(s):
    return escape(str(s), quote=True)


def mono_width(text, size):
    return len(text) * size * MONO_W


def icon_color(slug):
    """Brand colour, lifted to light grey when it would vanish on a dark panel."""
    h = ICONS[slug]["hex"].lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return TEXT if lum < 0.18 else "#" + h


def icon(slug, x, y, size, color=None):
    s = size / 24
    return (f'<path transform="translate({x:.1f} {y:.1f}) scale({s:.4f})" '
            f'fill="{color or icon_color(slug)}" d="{ICONS[slug]["d"]}"/>')


def svg(w, h, body, style="", title=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title><style>{style}</style>{body}</svg>')


def write(rel, content):
    path = os.path.join(ASSETS, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  {rel:<28} {len(content) / 1024:6.1f} KB")
