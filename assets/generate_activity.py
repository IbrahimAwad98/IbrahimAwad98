#!/usr/bin/env python3
"""
Genererar assets/activity.svg — en linjegraf som jämför bidrag per dag
för föregående och innevarande kalenderår (t.ex. 2025 vs 2026), samt
assets/streak.svg ur samma dagsdata.

Data hämtas via GitHubs GraphQL-API (contributionsCollection), ett anrop
per kalenderår (API:et tillåter max ett års spann per anrop).
OBS: det inbyggda GITHUB_TOKEN i Actions saknar ofta behörighet för
den queryn. Skapa i så fall en classic PAT med scope `read:user`,
lägg den som repo-secret PAT och skicka in den som GH_GRAPHQL_TOKEN.

Körning:
    GH_GRAPHQL_TOKEN=ghp_xxx python3 generate_activity.py
Testkörning utan nätverk:
    python3 generate_activity.py --demo
"""
import json
import math
import os
import sys
import urllib.request
import urllib.error
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

USER = os.environ.get("STATS_USER", "IbrahimAwad98")
TOKEN = os.environ.get("GH_GRAPHQL_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
OUT = Path(__file__).parent / "activity.svg"
DAYS = int(os.environ.get("ACTIVITY_DAYS", "365"))   # fönster för streak-kortet

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


def fetch_year(year, today):
    """[(iso-datum, antal)] för ett kalenderår, aldrig bortom dagens datum.

    Framtida dagar utelämnas helt i stället för att bli nollor — annars
    skulle kurvan för innevarande år få en falsk platt svans.
    """
    end = min(date(year, 12, 31), today)
    body = json.dumps({
        "query": QUERY,
        "variables": {
            "login": USER,
            "from": f"{year}-01-01T00:00:00Z",
            "to": f"{end.isoformat()}T23:59:59Z",
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
    return sorted(
        (d["date"], d["contributionCount"])
        for w in weeks for d in w["contributionDays"]
        if d["date"][:4] == str(year) and d["date"] <= end.isoformat()
    )


def demo(years, today):
    import random
    random.seed(3)
    out = {}
    for y in years:
        end = min(date(y, 12, 31), today)
        d, series = date(y, 1, 1), []
        while d <= end:
            n = max(0, int(random.gauss(4, 3)))
            if d.weekday() >= 5:
                n = max(0, n - 2)
            series.append((d.isoformat(), n))
            d += timedelta(days=1)
        out[y] = series
    return out


# Palett för aktivitetskortet (GitHub Dark). Streak-kortet behåller sina färger.
C_BG, C_CARD, C_BORDER = "#080D1B", "#0F1629", "#2A3350"
C_FG, C_MUTED, C_DIM = "#E6EDF3", "#8B949E", "#6E7681"
C_PURPLE, C_CYAN = "#A855F7", "#00D9FF"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SLOTS = 366   # x-axeln indexeras via skottåret 2024 så 29 feb får en egen plats


def slot(iso):
    """Dag-i-året (0–365) oberoende av år, så 15 mar 2025 och 2026 får samma x."""
    _, m, d = (int(s) for s in iso.split("-"))
    return date(2024, m, d).timetuple().tm_yday - 1


def nice_step(peak, ticks=4):
    """Avrundar y-steget till 1/2/2.5/5 × 10^k så etiketterna blir läsbara."""
    raw = max(peak, 1) / ticks
    mag = 10 ** math.floor(math.log10(raw))
    for f in (1, 2, 2.5, 5, 10):
        if f * mag >= raw:
            step = f * mag
            return int(step) if step >= 1 else step
    return mag * 10


def build(data):
    """data: {år: [(iso-datum, antal)]} — två år, färgas lila resp. cyan."""
    W, H = 880, 360
    L, R, T, B = 56, 28, 92, 86          # marginaler runt plottytan
    PW, PH = W - L - R, H - T - B
    years = sorted(data)
    colors = dict(zip(years, (C_PURPLE, C_CYAN)))

    peak = max((c for s in data.values() for _, c in s), default=0)
    step = nice_step(peak)
    ticks = max(1, -(-peak // step)) if step >= 1 else 4
    ymax = step * ticks
    if peak >= ymax:                      # lite luft ovanför toppen
        ymax += step
        ticks += 1

    def px(i):
        return L + i * PW / (SLOTS - 1)

    def py(v):
        return T + PH - (v / ymax) * PH

    nl = "\n  "

    def waves(x0, y0, color, flip):
        k = -1 if flip else 1
        return "".join(
            f'<path d="M{x0},{y0 - i * 10} c{60 * k},-18 {110 * k},-18 {170 * k},-2 '
            f's{110 * k},18 {170 * k},-6" fill="none" stroke="{color}" '
            f'stroke-width="1" stroke-opacity="{0.18 - i * 0.04:.2f}"/>'
            for i in range(4)
        )

    # Horisontella gridlinjer + y-etiketter
    grid = []
    for k in range(ticks + 1):
        v = step * k
        y = py(v)
        grid.append(
            f'<line x1="{L}" y1="{y:.1f}" x2="{L + PW}" y2="{y:.1f}" '
            f'stroke="#FFFFFF" stroke-opacity="{0.10 if k == 0 else 0.05}"/>'
            f'<text x="{L - 12}" y="{y + 3.5:.1f}" text-anchor="end" '
            f'font-family="{FONT}" font-size="10.5" fill="{C_DIM}">{v:g}</text>'
        )

    # Vertikala gridlinjer + månadsetiketter vid varje månadsskifte
    xlab = []
    for m in range(12):
        x = px(slot(f"2024-{m + 1:02d}-01"))
        xlab.append(
            f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{T + PH + 5}" '
            f'stroke="#FFFFFF" stroke-opacity="0.05"/>'
            f'<text x="{x:.1f}" y="{T + PH + 22}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="10.5" fill="{C_MUTED}">{MONTHS[m]}</text>'
        )

    # En polyline per år — rådata, ingen utjämning. Serien slutar vid sista
    # registrerade dagen så framtiden lämnas tom.
    series_svg = []
    for y in years:
        pts = [(px(slot(d)), py(c)) for d, c in data[y]]
        if not pts:
            continue
        line = "M" + " L".join(f"{x:.1f},{yy:.1f}" for x, yy in pts)
        area = f"{line} L{pts[-1][0]:.1f},{T + PH:.1f} L{pts[0][0]:.1f},{T + PH:.1f} Z"
        series_svg.append(
            f'<g clip-path="url(#plot)" fill="none" stroke="{colors[y]}" '
            f'stroke-linejoin="round" stroke-linecap="round">'
            f'<path d="{area}" fill="url(#fill{y})" stroke="none"/>'
            f'<path d="{line}" stroke-width="4" stroke-opacity="0.35" filter="url(#glow)"/>'
            f'<path d="{line}" stroke-width="1.4"/></g>'
        )

    # Centrerad legend under grafen: "2025 (617 contributions)"
    totals = {y: sum(c for _, c in data[y]) for y in years}
    labels = {y: f"{y} ({totals[y]:,} contributions)" for y in years}
    SW, GAP, PAD, CW = 26, 8, 36, 6.2     # swatch, mellanrum, avstånd, ~px/tecken
    widths = [SW + GAP + len(labels[y]) * CW for y in years]
    x = W / 2 - (sum(widths) + PAD * (len(years) - 1)) / 2
    ly = H - 24
    legend = []
    for y, w in zip(years, widths):
        legend.append(
            f'<line x1="{x:.1f}" y1="{ly}" x2="{x + SW:.1f}" y2="{ly}" stroke="{colors[y]}" '
            f'stroke-width="2.5" stroke-linecap="round"/>'
            f'<text x="{x + SW + GAP:.1f}" y="{ly + 3.8}" font-family="{FONT}" font-size="11.5" '
            f'fill="{C_MUTED}"><tspan font-weight="600" fill="{colors[y]}">{y}</tspan> '
            f'({totals[y]:,} contributions)</text>'
        )
        x += w + PAD

    title = " vs ".join(f'<tspan fill="{colors[y]}">{y}</tspan>' for y in years)
    aria = ", ".join(f"{y}: {totals[y]} contributions" for y in years)
    fills = "".join(
        f'<linearGradient id="fill{y}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{colors[y]}" stop-opacity="0.32"/>'
        f'<stop offset="100%" stop-color="{colors[y]}" stop-opacity="0.02"/></linearGradient>'
        for y in years
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Daily GitHub contributions for {USER}, {aria}; peak {peak} in one day.">
  <defs>
    <linearGradient id="stroke" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{C_PURPLE}"/>
      <stop offset="100%" stop-color="{C_CYAN}"/>
    </linearGradient>
    {fills}
    <filter id="glow" x="-5%" y="-20%" width="110%" height="140%">
      <feGaussianBlur stdDeviation="3"/>
    </filter>
    <clipPath id="plot"><rect x="{L}" y="{T - 20}" width="{PW}" height="{PH + 20}"/></clipPath>
    <radialGradient id="glowL" cx="0" cy="0.5" r="0.55">
      <stop offset="0%" stop-color="{C_PURPLE}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{C_PURPLE}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowR" cx="1" cy="0.5" r="0.55">
      <stop offset="0%" stop-color="{C_CYAN}" stop-opacity="0.14"/>
      <stop offset="100%" stop-color="{C_CYAN}" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>

  <rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="18" fill="{C_BG}" stroke="url(#stroke)" stroke-width="1.5"/>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="url(#glowL)"/>
    <rect width="{W}" height="{H}" fill="url(#glowR)"/>
    <rect x="0" y="0" width="{W}" height="3" fill="url(#stroke)"/>
    {waves(-20, H - 22, C_PURPLE, False)}
    {waves(W + 20, H - 22, C_CYAN, True)}
  </g>

  <text x="{L - 12}" y="40" font-family="{FONT}" font-size="16" font-weight="600" fill="{C_FG}">Contributions &#8212; {title}</text>
  <text x="{L - 12}" y="60" font-family="{FONT}" font-size="11.5" fill="{C_MUTED}">Daily GitHub activity, Jan&#8211;Dec</text>

  {nl.join(grid)}
  {nl.join(xlab)}

  {nl.join(series_svg)}

  {nl.join(legend)}
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
    W, H = 880, 220
    third = W / 3
    cx, cy, r = W / 2, 98, 52
    S_BG, S_FG, S_MUTED, S_DIM = "#080D1B", "#F0F6FC", "#8B949E", "#6E7681"

    def rng(a, b, year=False):
        if not (a and b):
            return ""
        ya, yb = (f" {a[:4]}", f" {b[:4]}") if year else ("", "")
        return f"{short_date(a)}{ya} &#8211; {short_date(b)}{yb}"

    def block(x, value, label, sub):
        return (
            f'<text x="{x:.0f}" y="108" text-anchor="middle" font-family="{FONT}" '
            f'font-size="42" font-weight="800" fill="{S_FG}">{value:,}</text>'
            f'<text x="{x:.0f}" y="134" text-anchor="middle" font-family="{FONT}" '
            f'font-size="11" letter-spacing="1.5" fill="{S_MUTED}">{label}</text>'
            f'<text x="{x:.0f}" y="154" text-anchor="middle" font-family="{FONT}" '
            f'font-size="10.5" fill="{S_DIM}">{sub}</text>'
        )

    # Dekorativa vågor i nedre hörnen (klipps av kortet)
    def waves(x0, y0, color, flip):
        k = -1 if flip else 1
        out = []
        for i in range(4):
            dy = i * 10
            out.append(
                f'<path d="M{x0},{y0 - dy} c{60 * k},-18 {110 * k},-18 {170 * k},-2 '
                f's{110 * k},18 {170 * k},-6" fill="none" stroke="{color}" '
                f'stroke-width="1" stroke-opacity="{0.22 - i * 0.045:.2f}"/>'
            )
        return "".join(out)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Contribution streaks: {st['total']} contributions in the last 12 months, current streak {st['current']} days, longest streak {st['longest']} days">
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{C_PURPLE}"/>
      <stop offset="100%" stop-color="{C_CYAN}"/>
    </linearGradient>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{C_PURPLE}"/>
      <stop offset="100%" stop-color="{C_CYAN}"/>
    </linearGradient>
    <linearGradient id="sep" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.14"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="glowL" cx="0" cy="0.5" r="0.55">
      <stop offset="0%" stop-color="{C_PURPLE}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{C_PURPLE}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowR" cx="1" cy="0.5" r="0.55">
      <stop offset="0%" stop-color="{C_CYAN}" stop-opacity="0.14"/>
      <stop offset="100%" stop-color="{C_CYAN}" stop-opacity="0"/>
    </radialGradient>
    <filter id="soft" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="6"/>
    </filter>
    <clipPath id="card"><rect x="0" y="0" width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>

  <rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="16" fill="{S_BG}" stroke="url(#edge)" stroke-width="1.5"/>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="url(#glowL)"/>
    <rect width="{W}" height="{H}" fill="url(#glowR)"/>
    <rect x="0" y="0" width="{W}" height="3" fill="url(#edge)"/>
    {waves(-20, H - 22, C_PURPLE, False)}
    {waves(W + 20, H - 22, C_CYAN, True)}
  </g>

  <line x1="{third:.0f}" y1="40" x2="{third:.0f}" y2="{H - 40}" stroke="url(#sep)"/>
  <line x1="{2 * third:.0f}" y1="40" x2="{2 * third:.0f}" y2="{H - 40}" stroke="url(#sep)"/>

  {block(third / 2, st["total"], "TOTAL CONTRIBUTIONS", rng(st["first"], st["last"], year=True))}

  <circle cx="{cx:.0f}" cy="{cy}" r="{r}" fill="none" stroke="url(#ring)" stroke-width="7" stroke-opacity="0.55" filter="url(#soft)"/>
  <circle cx="{cx:.0f}" cy="{cy}" r="{r}" fill="none" stroke="url(#ring)" stroke-width="4"/>
  <text x="{cx:.0f}" y="{cy + 13}" text-anchor="middle" font-family="{FONT}"
        font-size="38" font-weight="800" fill="{S_FG}">{st['current']}</text>
  <text x="{cx:.0f}" y="{cy + r + 32}" text-anchor="middle" font-family="{FONT}"
        font-size="11" letter-spacing="1.5" font-weight="600" fill="url(#edge)">CURRENT STREAK</text>

  {block(2.5 * third, st["longest"], "LONGEST STREAK", rng(*st["longest_range"]))}
</svg>
'''



if __name__ == "__main__":
    today = datetime.now(timezone.utc).date()
    years = [today.year - 1, today.year]

    if "--demo" in sys.argv:
        data = demo(years, today)
        print("Demoläge — inga API-anrop.")
    else:
        if not TOKEN:
            print("Ingen token satt (GH_GRAPHQL_TOKEN eller GITHUB_TOKEN).",
                  file=sys.stderr)
            sys.exit(1)
        print(f"Hämtar bidrag för {USER} ({years[0]} + {years[1]}) ...")
        try:
            data = {y: fetch_year(y, today) for y in years}
        except (urllib.error.HTTPError, RuntimeError) as e:
            print(f"Misslyckades: {e}\n"
                  f"Tips: GITHUB_TOKEN saknar ofta behörighet för "
                  f"contributionsCollection. Skapa en PAT med scope "
                  f"read:user och skicka in som GH_GRAPHQL_TOKEN.",
                  file=sys.stderr)
            sys.exit(1)
        for y in years:
            print(f"  {y}: {len(data[y])} dagar, {sum(c for _, c in data[y])} bidrag")

    OUT.write_text(build(data), encoding="utf-8")
    print(f"Skrev {OUT} ({OUT.stat().st_size} bytes)")

    # Streak-kortet använder de senaste DAYS dagarna ur samma data —
    # två kalenderår täcker alltid minst 365 dagar bakåt.
    series = (data[years[0]] + data[years[1]])[-DAYS:]
    st = streaks(series)
    STREAK_OUT.write_text(build_streak(st), encoding="utf-8")
    print(f"Skrev {STREAK_OUT} — total {st['total']}, "
          f"current {st['current']}, longest {st['longest']}")
