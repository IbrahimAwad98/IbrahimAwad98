#!/usr/bin/env python3
"""
Genererar självhostade SVG-assets till GitHub-profilen.
Kör: python3 generate_assets.py
Skriver till ./assets/
"""
from pathlib import Path

OUT = Path(__file__).parent

C1, C2, C3 = "#7C3AED", "#6366F1", "#22D3EE"
FONT = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'SFMono-Regular', 'Fira Code', Consolas, 'Liberation Mono', monospace"

# ---------------------------------------------------------------- typing.svg
LINES = [
    "Fullstack Development",
    "Backend & Frontend Engineering",
    "Systems Programming in C",
    "Embedded Systems \u00b7 RISC-V",
    "Databases & System Design",
    "Currently Learning Rust",
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
          font-size="22" fill="#22D3EE">{line.replace("&", "&amp;")}</text>
    <rect y="12" width="11" height="22" fill="#7C3AED" x="{X0}">
      <animate attributeName="x" values="{cur_val}" keyTimes="{cur_kt}"
               dur="{CYCLE}s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.24;0.25;0.49;0.5"
               dur="1s" repeatCount="indefinite"/>
    </rect>
  </g>''')

typing = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 44" width="520" height="44" role="img" aria-label="{' / '.join(LINES).replace('&', '&amp;')}">
  <text x="8" y="29" font-family="{MONO}" font-size="22" fill="#7C3AED">&#62;</text>
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
