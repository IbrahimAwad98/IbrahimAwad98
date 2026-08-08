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
DAYS = int(os.environ.get("ACTIVITY_DAYS", "365"))   # 31, 90, 180 eller 365

BG, FG, MUTED = "#0B1020", "#C9D1D9", "#8B949E"
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
    end = datetime(2026, 8, 2, tzinfo=timezone.utc)
    base = end - timedelta(days=DAYS - 1)
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

    # Punktmarkörer bara när de får plats — vid långa intervall blir de gyttrig
    dots = ""
    if n <= 60:
        dots = "".join(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{BG}" '
            f'stroke="{ACCENT2}" stroke-width="2"/>'
            for x, y in pts
        )

    # x-etiketter: månadsnamn vid långa intervall, dagsnummer vid korta
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    xlab = []
    if n > 60:
        seen = set()
        for i, (date, _) in enumerate(series):
            month = date[:7]
            if month not in seen:
                seen.add(month)
                if i > 6 and i < n - 6:       # undvik krock med kanterna
                    xlab.append(
                        f'<text x="{px(i):.1f}" y="{T + PH + 20}" '
                        f'text-anchor="middle" font-family="{FONT}" '
                        f'font-size="10" fill="{MUTED}">'
                        f'{MONTHS[int(date[5:7]) - 1]}</text>'
                    )
    else:
        for i, (date, _) in enumerate(series):
            if i % 5 == 0 or i == n - 1:
                xlab.append(
                    f'<text x="{px(i):.1f}" y="{T + PH + 20}" text-anchor="middle" '
                    f'font-family="{FONT}" font-size="10" '
                    f'fill="{MUTED}">{date[8:10].lstrip("0")}</text>'
                )

    total = sum(counts)
    first, last = series[0][0], series[-1][0]
    heading = ("last 12 months" if n > 300 else
               f"last {n // 30} months" if n > 60 else
               f"last {n} days")
    lw = 1.6 if n > 60 else 2.5
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

  <rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="{BORDER}"/>
  <rect x="0" y="0" width="{W}" height="3" rx="1.5" fill="url(#stroke)"/>

  <text x="{L - 10}" y="26" font-family="{FONT}" font-size="13"
        font-weight="600" fill="{FG}">Contributions — {heading}</text>
  <text x="{W - R}" y="26" text-anchor="end" font-family="{FONT}"
        font-size="11" fill="{MUTED}">{total} total &#183; peak {peak}</text>

  {nl.join(grid)}

  <polygon points="{area}" fill="url(#fill)"/>
  <polyline points="{line}" fill="none" stroke="url(#stroke)"
            stroke-width="{lw}" stroke-linejoin="round" stroke-linecap="round"/>
  {dots}

  {nl.join(xlab)}
</svg>
'''



STREAK_OUT = Path(__file__).parent / "streak.svg"


def streaks(series):
    """Räknar strecken ur samma dagsdata som grafen använder.

    Dagens datum bryter inte ett streck förrän dygnet är slut — samma
    konvention som GitHub själva använder, annars skulle strecket se
    brutet ut varje morgon.
    """
    days = [(d, c) for d, c in series]
    total = sum(c for _, c in days)

    # Längsta strecket någonstans i perioden
    longest = run = 0
    longest_range = ("", "")
    run_start = ""
    for date, count in days:
        if count > 0:
            if run == 0:
                run_start = date
            run += 1
            if run > longest:
                longest = run
                longest_range = (run_start, date)
        else:
            run = 0

    # Nuvarande streck, räknat bakifrån
    current = 0
    current_range = ("", "")
    for i in range(len(days) - 1, -1, -1):
        date, count = days[i]
        if count > 0:
            current += 1
            current_range = (date, current_range[1] or date)
        elif i == len(days) - 1:
            continue          # dagens nolla bryter inte strecket ännu
        else:
            break
    if current:
        current_range = (days[len(days) - current][0], days[-1][0])

    return {
        "total": total,
        "current": current,
        "current_range": current_range,
        "longest": longest,
        "longest_range": longest_range,
        "first": days[0][0],
        "last": days[-1][0],
    }


def short_date(iso):
    """2026-07-14 -> 14 Jul"""
    if not iso:
        return ""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    try:
        y, m, d = iso.split("-")
        return f"{int(d)} {months[int(m) - 1]}"
    except (ValueError, IndexError):
        return iso


def build_streak(st):
    W, H = 880, 190
    third = W / 3
    r = 46
    cx, cy = W / 2, 96

    def block(x, value, label, sub):
        return (
            f'<text x="{x:.0f}" y="86" text-anchor="middle" font-family="{FONT}" '
            f'font-size="34" font-weight="700" fill="{FG}">{value}</text>'
            f'<text x="{x:.0f}" y="112" text-anchor="middle" font-family="{FONT}" '
            f'font-size="12" fill="{MUTED}" letter-spacing="0.5">{label}</text>'
            f'<text x="{x:.0f}" y="134" text-anchor="middle" font-family="{FONT}" '
            f'font-size="10.5" fill="{MUTED}" opacity="0.75">{sub}</text>'
        )

    cur_sub = (f"{short_date(st['current_range'][0])} – "
               f"{short_date(st['current_range'][1])}") if st["current"] else "no active streak"
    long_sub = (f"{short_date(st['longest_range'][0])} – "
                f"{short_date(st['longest_range'][1])}") if st["longest"] else ""

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Contribution streaks: {st['total']} contributions in the last 12 months, current streak {st['current']} days, longest streak {st['longest']} days">
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{ACCENT}"/>
      <stop offset="100%" stop-color="{ACCENT2}"/>
    </linearGradient>
  </defs>

  <rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="{BORDER}"/>
  <rect x="0" y="0" width="{W}" height="3" rx="1.5" fill="url(#edge)"/>

  <line x1="{third:.0f}" y1="42" x2="{third:.0f}" y2="150" stroke="{BORDER}"/>
  <line x1="{2 * third:.0f}" y1="42" x2="{2 * third:.0f}" y2="150" stroke="{BORDER}"/>

  {block(third / 2, st["total"], "TOTAL CONTRIBUTIONS", f"{short_date(st['first'])} – {short_date(st['last'])}")}

  <circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r}" fill="none" stroke="{BORDER}" stroke-width="3"/>
  <circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r}" fill="none" stroke="{ACCENT}" stroke-width="3"
          stroke-linecap="round" stroke-dasharray="{2 * 3.14159 * r:.0f}"
          stroke-dashoffset="{2 * 3.14159 * r * (1 - min(st['current'] / 14, 1)):.0f}"
          transform="rotate(-90 {cx:.0f} {cy:.0f})"/>
  <text x="{cx:.0f}" y="{cy + 10:.0f}" text-anchor="middle" font-family="{FONT}"
        font-size="30" font-weight="700" fill="{FG}">{st['current']}</text>
  <text x="{cx:.0f}" y="162" text-anchor="middle" font-family="{FONT}"
        font-size="12" fill="{ACCENT2}" letter-spacing="0.5">CURRENT STREAK</text>
  <text x="{cx:.0f}" y="{cy + 62:.0f}" text-anchor="middle" font-family="{FONT}"
        font-size="10.5" fill="{MUTED}" opacity="0">{cur_sub}</text>

  {block(2.5 * third, st["longest"], "LONGEST STREAK", long_sub)}
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

    st = streaks(series)
    STREAK_OUT.write_text(build_streak(st), encoding="utf-8")
    print(f"Skrev {STREAK_OUT} — total {st['total']}, "
          f"current {st['current']}, longest {st['longest']}")
