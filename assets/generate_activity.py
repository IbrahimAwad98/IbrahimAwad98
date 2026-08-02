#!/usr/bin/env python3
"""
Genererar assets/activity.svg — en linjegraf över bidrag per dag,
självhostad ersättare för github-readme-activity-graph.

Data hämtas via GitHubs GraphQL-API (contributionsCollection).
OBS: det inbyggda GITHUB_TOKEN i Actions saknar ofta behörighet för
den queryn. Skapa i så fall en classic PAT med scope `read:user`,
lägg den som repo-secret PAT och skicka in den som GH_GRAPHQL_TOKEN.

Körning:
    GH_GRAPHQL_TOKEN=ghp_xxx python3 generate_activity.py
Testkörning utan nätverk:
    python3 generate_activity.py --demo
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

USER = os.environ.get("STATS_USER", "IbrahimAwad98")
TOKEN = os.environ.get("GH_GRAPHQL_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
OUT = Path(__file__).parent / "activity.svg"
DAYS = 31

BG, PANEL, FG, MUTED = "#0D1117", "#161B22", "#C9D1D9", "#8B949E"
ACCENT, ACCENT2, BORDER = "#9333EA", "#06B6D4", "#21262D"
FONT = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"

QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch():
    to = datetime.now(timezone.utc)
    frm = to - timedelta(days=DAYS - 1)
    body = json.dumps({
        "query": QUERY,
        "variables": {
            "login": USER,
            "from": frm.strftime("%Y-%m-%dT00:00:00Z"),
            "to": to.strftime("%Y-%m-%dT23:59:59Z"),
        },
    }).encode()

    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-activity-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)

    if "errors" in payload:
        raise RuntimeError(payload["errors"][0].get("message", "GraphQL-fel"))

    weeks = (payload["data"]["user"]["contributionsCollection"]
             ["contributionCalendar"]["weeks"])
    days = [d for w in weeks for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    return [(d["date"], d["contributionCount"]) for d in days][-DAYS:]


def demo():
    import random
    random.seed(3)
    base = datetime(2026, 7, 3, tzinfo=timezone.utc)
    out = []
    for i in range(DAYS):
        d = base + timedelta(days=i)
        n = max(0, int(random.gauss(4, 3)))
        if d.weekday() >= 5:
            n = max(0, n - 2)
        out.append((d.strftime("%Y-%m-%d"), n))
    return out


def build(series):
    W, H = 880, 260
    L, R, T, B = 52, 24, 46, 42          # marginaler
    PW, PH = W - L - R, H - T - B

    counts = [c for _, c in series]
    peak = max(counts) or 1
    # runda upp y-max till närmaste jämna tal för snyggare gridlinjer
    ymax = peak if peak % 2 == 0 else peak + 1
    n = len(series)
    step = PW / (n - 1) if n > 1 else PW

    def px(i):
        return L + i * step

    def py(v):
        return T + PH - (v / ymax) * PH

    # gridlinjer + y-etiketter
    grid = []
    ticks = 4
    for t in range(ticks + 1):
        v = ymax * t / ticks
        y = py(v)
        grid.append(
            f'<line x1="{L}" y1="{y:.1f}" x2="{L + PW}" y2="{y:.1f}" '
            f'stroke="{BORDER}" stroke-width="1"/>'
            f'<text x="{L - 10}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-family="{FONT}" font-size="10" fill="{MUTED}">{v:.0f}</text>'
        )

    pts = [(px(i), py(c)) for i, (_, c) in enumerate(series)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = (f"{L},{T + PH} " + line + f" {L + PW},{T + PH}")

    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{BG}" '
        f'stroke="{ACCENT2}" stroke-width="2"/>'
        for x, y in pts
    )

    # x-etiketter var 5:e dag
    xlab = []
    for i, (date, _) in enumerate(series):
        if i % 5 == 0 or i == n - 1:
            day = date[8:10].lstrip("0")
            xlab.append(
                f'<text x="{px(i):.1f}" y="{T + PH + 20}" text-anchor="middle" '
                f'font-family="{FONT}" font-size="10" fill="{MUTED}">{day}</text>'
            )

    total = sum(counts)
    first, last = series[0][0], series[-1][0]
    nl = "\n  "
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Bidrag per dag för {USER} mellan {first} och {last}. Totalt {total} bidrag, som mest {peak} på en dag.">
  <defs>
    <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="{ACCENT2}" stop-opacity="0.02"/>
    </linearGradient>
    <linearGradient id="stroke" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{ACCENT}"/>
      <stop offset="100%" stop-color="{ACCENT2}"/>
    </linearGradient>
  </defs>

  <rect width="{W}" height="{H}" rx="10" fill="{PANEL}" stroke="{BORDER}"/>
  <rect x="0" y="0" width="{W}" height="3" rx="1.5" fill="url(#stroke)"/>

  <text x="{L - 10}" y="26" font-family="{FONT}" font-size="13"
        font-weight="600" fill="{FG}">Contributions — last {DAYS} days</text>
  <text x="{W - R}" y="26" text-anchor="end" font-family="{FONT}"
        font-size="11" fill="{MUTED}">{total} total &#183; peak {peak}</text>

  {nl.join(grid)}

  <polygon points="{area}" fill="url(#fill)"/>
  <polyline points="{line}" fill="none" stroke="url(#stroke)"
            stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
  {dots}

  {nl.join(xlab)}
</svg>
'''


if __name__ == "__main__":
    if "--demo" in sys.argv:
        series = demo()
        print("Demoläge — inga API-anrop.")
    else:
        if not TOKEN:
            print("Ingen token satt (GH_GRAPHQL_TOKEN eller GITHUB_TOKEN).",
                  file=sys.stderr)
            sys.exit(1)
        print(f"Hämtar bidrag för {USER} ...")
        try:
            series = fetch()
        except (urllib.error.HTTPError, RuntimeError) as e:
            print(f"Misslyckades: {e}\n"
                  f"Tips: GITHUB_TOKEN saknar ofta behörighet för "
                  f"contributionsCollection. Skapa en PAT med scope "
                  f"read:user och skicka in som GH_GRAPHQL_TOKEN.",
                  file=sys.stderr)
            sys.exit(1)
        print(f"  {len(series)} dagar, {sum(c for _, c in series)} bidrag")

    OUT.write_text(build(series), encoding="utf-8")
    print(f"Skrev {OUT} ({OUT.stat().st_size} bytes)")
