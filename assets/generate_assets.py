#!/usr/bin/env python3
"""
Källa till SVG-filerna i denna mapp. Kör `python3 generate_assets.py`
efter ändringar i färger eller texter.
"""
import random
from pathlib import Path

OUT = Path(__file__).parent
OUT.mkdir(exist_ok=True)

C1, C2, C3 = "#1e3a8a", "#9333ea", "#06b6d4"
FONT = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'SFMono-Regular', 'Fira Code', Consolas, 'Liberation Mono', monospace"

# ---------------------------------------------------------------- banner.svg
random.seed(42)
stars = []
for _ in range(55):
    x = round(random.uniform(0, 1000), 1)
    y = round(random.uniform(0, 230), 1)
    r = round(random.uniform(0.6, 1.9), 2)
    dur = round(random.uniform(2.2, 5.0), 2)
    beg = round(random.uniform(0, 5.0), 2)
    op = round(random.uniform(0.25, 0.75), 2)
    stars.append(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ffffff" opacity="0">'
        f'<animate attributeName="opacity" values="0;{op};0" '
        f'dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/></circle>'
    )
stars_svg = "\n    ".join(stars)

banner = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 230" width="1000" height="230" role="img" aria-label="Ibrahim Awad - Fullstack Developer">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{C1}"/>
      <stop offset="50%" stop-color="{C2}"/>
      <stop offset="100%" stop-color="{C3}"/>
    </linearGradient>
    <filter id="soft" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="55"/>
    </filter>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.75"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <rect width="1000" height="230" fill="url(#bg)"/>

  <g filter="url(#soft)" opacity="0.55">
    <ellipse cx="180" cy="60" rx="200" ry="120" fill="{C3}">
      <animate attributeName="cx" values="180;300;180" dur="14s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="820" cy="190" rx="230" ry="130" fill="{C1}">
      <animate attributeName="cx" values="820;690;820" dur="17s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="520" cy="120" rx="170" ry="100" fill="{C2}">
      <animate attributeName="cy" values="120;60;120" dur="11s" repeatCount="indefinite"/>
    </ellipse>
  </g>

  <g>
    {stars_svg}
  </g>

  <text x="500" y="112" text-anchor="middle" font-family="{FONT}"
        font-size="58" font-weight="700" fill="#ffffff" letter-spacing="1.5">Ibrahim Awad</text>

  <rect x="380" y="132" width="240" height="1.5" fill="url(#rule)"/>

  <text x="500" y="166" text-anchor="middle" font-family="{FONT}"
        font-size="17" font-weight="500" fill="#ffffff" opacity="0.92"
        letter-spacing="3.5">FULLSTACK DEVELOPER</text>
  <text x="500" y="192" text-anchor="middle" font-family="{FONT}"
        font-size="13" fill="#ffffff" opacity="0.68"
        letter-spacing="2">SYSTEMS &#183; EMBEDDED &#183; DATABASES</text>
</svg>
'''
(OUT / "banner.svg").write_text(banner, encoding="utf-8")

# ---------------------------------------------------------------- typing.svg
LINES = [
    "Fullstack Development",
    "Backend & Frontend Engineering",
    "Systems Programming in Rust & C",
    "Embedded Systems \u00b7 RISC-V",
    "Databases & System Design",
    "AI-Assisted Development Workflow",
]
PER = 3.0                      # sekunder per rad
CYCLE = PER * len(LINES)
CHAR_W = 13.2                  # ungefärlig teckenbredd vid 22px monospace
X0 = 34                        # textstart efter prompt-tecknet


def kt(t):
    """Sekund -> keyTime (0-1), klampad."""
    return round(min(max(t / CYCLE, 0.0), 1.0), 6)


groups = []
for i, line in enumerate(LINES):
    start = i * PER
    w = len(line) * CHAR_W
    a, a2 = kt(start), kt(start + 0.05)
    b, b2 = kt(start + PER - 0.35), kt(start + PER - 0.15)
    type_end = kt(start + min(1.5, PER * 0.5))

    vis_kt = f"0;{a};{a2};{b};{b2};1"
    vis_val = "0;0;1;1;0;0"

    clip_kt = f"0;{a};{type_end};{b2};1"
    clip_val = f"0;0;{w:.1f};{w:.1f};0"

    cur_kt = clip_kt
    cur_val = f"{X0};{X0};{X0 + w:.1f};{X0 + w:.1f};{X0}"

    groups.append(f'''  <g opacity="0">
    <animate attributeName="opacity" values="{vis_val}" keyTimes="{vis_kt}"
             dur="{CYCLE}s" repeatCount="indefinite" calcMode="discrete"/>
    <clipPath id="clip{i}">
      <rect x="{X0}" y="0" height="44" width="0">
        <animate attributeName="width" values="{clip_val}" keyTimes="{clip_kt}"
                 dur="{CYCLE}s" repeatCount="indefinite"/>
      </rect>
    </clipPath>
    <text x="{X0}" y="29" clip-path="url(#clip{i})" font-family="{MONO}"
          font-size="22" fill="#06b6d4">{line.replace("&", "&amp;")}</text>
    <rect y="12" width="11" height="22" fill="#9333ea" x="{X0}">
      <animate attributeName="x" values="{cur_val}" keyTimes="{cur_kt}"
               dur="{CYCLE}s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.24;0.25;0.49;0.5"
               dur="1s" repeatCount="indefinite"/>
    </rect>
  </g>''')

typing = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 44" width="520" height="44" role="img" aria-label="{' / '.join(LINES).replace('&', '&amp;')}">
  <text x="8" y="29" font-family="{MONO}" font-size="22" fill="#9333ea">&#62;</text>
{chr(10).join(groups)}
</svg>
'''
(OUT / "typing.svg").write_text(typing, encoding="utf-8")

# --------------------------------------------------------------- divider.svg
divider = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 4" width="1000" height="4" role="presentation">
  <defs>
    <linearGradient id="d" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{C1}"/>
      <stop offset="50%" stop-color="{C2}"/>
      <stop offset="100%" stop-color="{C3}"/>
    </linearGradient>
  </defs>
  <rect width="1000" height="4" rx="2" fill="url(#d)"/>
</svg>
'''
(OUT / "divider.svg").write_text(divider, encoding="utf-8")

# ---------------------------------------------------------------- footer.svg
footer = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 120" width="1000" height="120" role="presentation">
  <defs>
    <linearGradient id="f" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{C3}"/>
      <stop offset="50%" stop-color="{C2}"/>
      <stop offset="100%" stop-color="{C1}"/>
    </linearGradient>
  </defs>
  <path fill="url(#f)" d="M0,60 C150,10 350,110 500,60 C650,10 850,110 1000,60 L1000,120 L0,120 Z">
    <animate attributeName="d" dur="12s" repeatCount="indefinite"
      values="M0,60 C150,10 350,110 500,60 C650,10 850,110 1000,60 L1000,120 L0,120 Z;
              M0,60 C150,110 350,10 500,60 C650,110 850,10 1000,60 L1000,120 L0,120 Z;
              M0,60 C150,10 350,110 500,60 C650,10 850,110 1000,60 L1000,120 L0,120 Z"/>
  </path>
</svg>
'''
(OUT / "footer.svg").write_text(footer, encoding="utf-8")

for f in sorted(OUT.iterdir()):
    print(f"{f.name:14} {f.stat().st_size:>6} bytes")
