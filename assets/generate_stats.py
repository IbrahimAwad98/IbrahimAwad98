#!/usr/bin/env python3
"""
Genererar assets/stats.svg (mest använda språk) från GitHub-API:t.

Körs automatiskt av .github/workflows/stats.yml en gång per dygn.
Manuell körning:
    GITHUB_TOKEN=ghp_xxx python3 generate_stats.py
Testkörning utan nätverk (visar hur kortet ser ut):
    python3 generate_stats.py --demo
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

USER = os.environ.get("STATS_USER", "IbrahimAwad98")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = Path(__file__).parent / "stats.svg"

BG, FG, MUTED = "#0B1020", "#C9D1D9", "#8B949E"
ACCENT, ACCENT2, BORDER = "#7C3AED", "#22D3EE", "#21262D"
FONT = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"

# Palett efter rang (störst språk först), inte per språk
PALETTE = ["#4AD5ED", "#A68CF8", "#ED6FB5", "#F6BD36", "#50D49A", "#6AA7F8"]


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-stats-generator",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    repos, page = [], 1
    while True:
        batch = api(f"/user/repos?per_page=100&page={page}&affiliation=owner")  # /user/ = inkl. privata (kräver PAT)
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    langs = {}
    for r in repos:
        if r["fork"] or r["archived"]:
            continue
        try:
            for lang, byts in api(f"/repos/{USER}/{r['name']}/languages").items():
                langs[lang] = langs.get(lang, 0) + byts
        except Exception as e:              # ett trasigt repo får inte fälla hela körningen
            print(f"  hoppar över {r['name']}: {e}", file=sys.stderr)

    return {"langs": dict(sorted(langs.items(), key=lambda kv: -kv[1])[:6])}


DEMO = {
    "langs": {"Java": 420000, "C": 310000, "TypeScript": 180000,
              "Rust": 95000, "Python": 60000, "CSS": 40000},
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(d):
    W, H = 880, 165
    total = sum(d["langs"].values()) or 1

    # --- språkfördelning: stapel + legend i tre kolumner ---
    X, BW = 30, 820
    bar, legend, off = [], [], 0.0
    for i, (lang, byts) in enumerate(d["langs"].items()):
        frac = byts / total
        w = frac * BW
        color = PALETTE[i % len(PALETTE)]
        bar.append(f'<rect x="{X + off:.1f}" y="70" width="{max(w, 1):.1f}" '
                   f'height="14" fill="{color}"/>')
        off += w

        col, row = i % 3, i // 3
        lx, ly = X + col * 275, 118 + row * 26
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>'
            f'<text x="{lx + 18}" y="{ly}" font-family="{FONT}" font-size="13" '
            f'fill="{FG}">{esc(lang)}</text>'
            f'<text x="{lx + 18 + len(lang) * 7.6:.0f}" y="{ly}" font-family="{FONT}" '
            f'font-size="13" fill="{MUTED}">{frac * 100:.1f}%</text>'
        )

    nl = "\n  "
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Mest använda språk för {USER}: {', '.join(d['langs'])}">
  <defs>
    <clipPath id="rounded"><rect x="{X}" y="70" width="{BW}" height="14" rx="7"/></clipPath>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{ACCENT}"/><stop offset="100%" stop-color="{ACCENT2}"/>
    </linearGradient>
  </defs>

  <rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="{BORDER}"/>
  <rect x="0" y="0" width="{W}" height="3" rx="1.5" fill="url(#accent)"/>

  <text x="30" y="40" font-family="{FONT}" font-size="15" font-weight="600"
        fill="{FG}" letter-spacing="0.4">{esc(USER)}</text>
  <line x1="30" y1="52" x2="{W - 30}" y2="52" stroke="{BORDER}"/>

  <text x="{X}" y="60" font-family="{FONT}" font-size="11" fill="{MUTED}"
        letter-spacing="0.6">MOST USED LANGUAGES</text>
  <g clip-path="url(#rounded)">
  {nl.join(bar)}
  </g>
  {nl.join(legend)}
</svg>
'''


if __name__ == "__main__":
    if "--demo" in sys.argv:
        data = DEMO
        print("Demoläge — ingen API-anrop.")
    else:
        print(f"Hämtar statistik för {USER} ...")
        data = collect()
        print(f"  {len(data['langs'])} språk")

    OUT.write_text(build(data), encoding="utf-8")
    print(f"Skrev {OUT} ({OUT.stat().st_size} bytes)")
