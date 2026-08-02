#!/usr/bin/env python3
"""
Genererar assets/stats.svg från GitHub-API:t.

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

# Officiella GitHub-språkfärger för de vanligaste språken
LANG_COLORS = {
    "Rust": "#dea584", "C": "#555555", "C++": "#f34b7d", "C#": "#178600",
    "Java": "#b07219", "Python": "#3572A5", "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#563d7c",
    "Assembly": "#6E4C13", "Shell": "#89e051", "Makefile": "#427819",
    "Go": "#00ADD8", "Kotlin": "#A97BFF", "Swift": "#F05138",
    "Ruby": "#701516", "PHP": "#4F5D95", "Dart": "#00B4AB",
}
FALLBACK = "#6e7681"


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
    user = api(f"/users/{USER}")
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}&type=owner")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)

    langs = {}
    for r in own:
        if r["archived"]:
            continue
        try:
            for lang, byts in api(f"/repos/{USER}/{r['name']}/languages").items():
                langs[lang] = langs.get(lang, 0) + byts
        except Exception as e:              # ett trasigt repo får inte fälla hela körningen
            print(f"  hoppar över {r['name']}: {e}", file=sys.stderr)

    return {
        "repos": len(own),
        "stars": stars,
        "followers": user["followers"],
        "langs": dict(sorted(langs.items(), key=lambda kv: -kv[1])[:6]),
    }


DEMO = {
    "repos": 28, "stars": 3, "followers": 14,
    "langs": {"Java": 420000, "C": 310000, "TypeScript": 180000,
              "Rust": 95000, "Python": 60000, "CSS": 40000},
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(d):
    W, H = 880, 210
    total = sum(d["langs"].values()) or 1

    # --- vänsterpanel: nyckeltal ---
    metrics = [("Repositories", d["repos"]), ("Total Stars", d["stars"]),
               ("Followers", d["followers"])]
    left = []
    for i, (label, val) in enumerate(metrics):
        y = 78 + i * 42
        left.append(
            f'<text x="46" y="{y}" font-family="{FONT}" font-size="26" font-weight="700" '
            f'fill="{ACCENT2}">{val}</text>'
            f'<text x="46" y="{y + 17}" font-family="{FONT}" font-size="11" '
            f'fill="{MUTED}" letter-spacing="0.6">{label.upper()}</text>'
        )

    # --- högerpanel: språkfördelning ---
    X, BW = 300, 520
    bar, legend, off = [], [], 0.0
    for i, (lang, byts) in enumerate(d["langs"].items()):
        frac = byts / total
        w = frac * BW
        color = LANG_COLORS.get(lang, FALLBACK)
        bar.append(f'<rect x="{X + off:.1f}" y="70" width="{max(w, 1):.1f}" '
                   f'height="14" fill="{color}"/>')
        off += w

        col, row = i % 2, i // 2
        lx, ly = X + col * 265, 118 + row * 26
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>'
            f'<text x="{lx + 18}" y="{ly}" font-family="{FONT}" font-size="13" '
            f'fill="{FG}">{esc(lang)}</text>'
            f'<text x="{lx + 18 + len(lang) * 7.6:.0f}" y="{ly}" font-family="{FONT}" '
            f'font-size="13" fill="{MUTED}">{frac * 100:.1f}%</text>'
        )

    nl = "\n  "
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub-statistik för {USER}: {d['repos']} repositories, {d['stars']} stjärnor, {d['followers']} följare">
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

  {nl.join(left)}

  <line x1="265" y1="66" x2="265" y2="180" stroke="{BORDER}"/>

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
        print(f"  {data['repos']} repon, {data['stars']} stjärnor, "
              f"{data['followers']} följare, {len(data['langs'])} språk")

    OUT.write_text(build(data), encoding="utf-8")
    print(f"Skrev {OUT} ({OUT.stat().st_size} bytes)")
