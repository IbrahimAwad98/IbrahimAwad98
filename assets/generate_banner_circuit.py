#!/usr/bin/env python3
"""
Genererar assets/banner.svg — mörkt stjärnfält med kretskortsspår längs
kanterna och namnet i mitten.

Allt ritas procedurellt: spåren genereras av algoritmen nedan, inga
externa bilder eller logotyper. Kör om skriptet för ny slumpad layout
(ändra SEED).

Körning:
    python3 generate_banner_circuit.py
"""
import random
from pathlib import Path

OUT = Path(__file__).parent / "banner.svg"

NAME = "Ibrahim Awad"
ROLE = "FULLSTACK DEVELOPER"
SUB = "SYSTEMS  \u00b7  EMBEDDED  \u00b7  DATABASES"

SEED = 21
W, H = 1000, 200                # 5:1

DEEP = "#050B29"                # djup marinblå
MID = "#0B1445"
TRACE = "#C77A20"               # kopparorange, som på riktiga kretskort
TRACE_HI = "#E8A54B"
GLOW1 = "#9333EA"
GLOW2 = "#06B6D4"
STAR = "#FFFFFF"
PALE = "#C0E4E4"
FONT = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"

random.seed(SEED)


def traces(x0, x1, mirror=False):
    """Bygger kretskortsspår i en vertikal remsa mellan x0 och x1.

    Varje spår går från kanten inåt i 45-graderssteg — samma
    designregel som riktiga PCB-layouter använder — och avslutas
    med en via (genomkontakt) eller ett lödöga.
    """
    paths, pads = [], []
    for _ in range(22):
        y = random.uniform(6, H - 6)
        x = x0 if not mirror else x1
        d = [f"M {x:.1f} {y:.1f}"]
        cur_x, cur_y = x, y
        steps = random.randint(2, 5)
        for _ in range(steps):
            run = random.uniform(14, 46)
            direction = 1 if not mirror else -1
            if random.random() < 0.45:
                # diagonal 45 grader, sedan rakt
                dy = random.choice([-1, 1]) * min(run, 26)
                cur_x += direction * abs(dy)
                cur_y += dy
                cur_y = max(4, min(H - 4, cur_y))
                d.append(f"L {cur_x:.1f} {cur_y:.1f}")
            else:
                cur_x += direction * run
                d.append(f"L {cur_x:.1f} {cur_y:.1f}")
            cur_x = max(x0, min(x1, cur_x))
            if (not mirror and cur_x >= x1) or (mirror and cur_x <= x0):
                break

        op = round(random.uniform(0.6, 1.0), 2)
        wdt = round(random.choice([1.2, 1.5, 1.9]), 1)
        col = TRACE_HI if random.random() < 0.35 else TRACE
        paths.append(
            f'<path d="{" ".join(d)}" fill="none" stroke="{col}" '
            f'stroke-width="{wdt}" opacity="{op}" stroke-linejoin="round"/>'
        )

        # via i änden: ring med hål
        r = random.choice([2.4, 3.0, 3.6])
        pads.append(
            f'<circle cx="{cur_x:.1f}" cy="{cur_y:.1f}" r="{r}" fill="none" '
            f'stroke="{col}" stroke-width="1.1" opacity="{op}"/>'
            f'<circle cx="{cur_x:.1f}" cy="{cur_y:.1f}" r="{r * 0.35:.1f}" '
            f'fill="{DEEP}"/>'
        )
    return "\n    ".join(paths + pads)


# stjärnfält i två lager
def stars(count, rmin, rmax, opmax, twinkle):
    out = []
    for _ in range(count):
        x = round(random.uniform(0, W), 1)
        y = round(random.uniform(0, H), 1)
        r = round(random.uniform(rmin, rmax), 2)
        op = round(random.uniform(opmax * 0.35, opmax), 2)
        if twinkle:
            dur = round(random.uniform(2.5, 6.0), 2)
            beg = round(random.uniform(0, 6.0), 2)
            out.append(
                f'<circle cx="{x}" cy="{y}" r="{r}" fill="{STAR}" opacity="{op}">'
                f'<animate attributeName="opacity" values="{op};{op * 0.15:.2f};{op}" '
                f'dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/></circle>'
            )
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{STAR}" opacity="{op}"/>')
    return "\n    ".join(out)


far = stars(140, 0.35, 0.85, 0.45, False)
near = stars(45, 0.7, 1.4, 0.8, True)
left = traces(0, 250)
right = traces(750, W, mirror=True)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{NAME} — {ROLE}">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0.25" y2="1">
      <stop offset="0%" stop-color="{DEEP}"/>
      <stop offset="50%" stop-color="{MID}"/>
      <stop offset="100%" stop-color="{DEEP}"/>
    </linearGradient>
    <filter id="neb" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="52"/>
    </filter>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{GLOW1}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{GLOW2}" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="{GLOW1}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="{PALE}"/>
    </linearGradient>
    <radialGradient id="center" cx="0.5" cy="0.5" r="0.30">
      <stop offset="0%" stop-color="{DEEP}" stop-opacity="0.92"/>
      <stop offset="100%" stop-color="{DEEP}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="{W}" height="{H}" fill="url(#sky)"/>

  <g filter="url(#neb)" opacity="0.42">
    <ellipse cx="230" cy="40" rx="180" ry="88" fill="{GLOW1}">
      <animate attributeName="cx" values="230;300;230" dur="21s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="780" cy="170" rx="200" ry="95" fill="{GLOW2}">
      <animate attributeName="cx" values="780;710;780" dur="25s" repeatCount="indefinite"/>
    </ellipse>
  </g>

  <g>
    {far}
  </g>

  <g>
    {left}
  </g>
  <g>
    {right}
  </g>

  <g>
    {near}
  </g>

  <rect width="{W}" height="{H}" fill="url(#center)"/>

  <text x="{W // 2}" y="96" text-anchor="middle" font-family="{FONT}"
        font-size="52" font-weight="700" fill="url(#name)"
        letter-spacing="2">{NAME}</text>

  <rect x="{W // 2 - 130}" y="115" width="260" height="1.4" fill="url(#rule)"/>

  <text x="{W // 2}" y="145" text-anchor="middle" font-family="{FONT}"
        font-size="14" font-weight="600" fill="{STAR}" opacity="0.93"
        letter-spacing="6">{ROLE}</text>
  <text x="{W // 2}" y="168" text-anchor="middle" font-family="{FONT}"
        font-size="10.5" fill="{PALE}" opacity="0.62"
        letter-spacing="2.5">{SUB}</text>
</svg>
'''

OUT.write_text(svg, encoding="utf-8")
print(f"Skrev {OUT} ({OUT.stat().st_size} bytes)")
