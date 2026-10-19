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


# Palett för aktivitetskortet (GitHub Dark). Streak-kortet behåller sina färger.
C_BG, C_CARD, C_BORDER = "#0D1117", "#161B22", "#30363D"
C_FG, C_MUTED, C_DIM = "#E6EDF3", "#8B949E", "#6E7681"
C_PURPLE, C_CYAN = "#A855F7", "#00D9FF"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def nice_step(peak, ticks=4):
    """Avrundar y-steget till 1/2/2.5/5 × 10^k så etiketterna blir läsbara."""
    import math
    raw = max(peak, 1) / ticks
    mag = 10 ** math.floor(math.log10(raw))
    for f in (1, 2, 2.5, 5, 10):
        if f * mag >= raw:
            step = f * mag
            return int(step) if step >= 1 else step
    return mag * 10


def smooth_path(pts):
    """Monoton kubisk interpolation (Fritsch–Carlson).

    Ger en mjuk kurva som aldrig över-/underskjuter datapunkterna:
    nollor stannar på noll och toppar träffar exakt sitt värde.
    """
    import math
    n = len(pts)
    if n < 2:
        return ""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    dx = [xs[i + 1] - xs[i] for i in range(n - 1)]
    m = [(ys[i + 1] - ys[i]) / dx[i] for i in range(n - 1)]
    t = [0.0] * n
    t[0], t[-1] = m[0], m[-1]
    for i in range(1, n - 1):
        t[i] = 0.0 if m[i - 1] * m[i] <= 0 else (m[i - 1] + m[i]) / 2
    for i in range(n - 1):
        if m[i] == 0:
            t[i] = t[i + 1] = 0.0
            continue
        a, b = t[i] / m[i], t[i + 1] / m[i]
        s = a * a + b * b
        if s > 9:
            tau = 3 / math.sqrt(s)
            t[i], t[i + 1] = tau * a * m[i], tau * b * m[i]
    d = [f"M{xs[0]:.1f},{ys[0]:.1f}"]
    for i in range(n - 1):
        h = dx[i] / 3
        d.append(f"C{xs[i] + h:.1f},{ys[i] + t[i] * h:.1f} "
                 f"{xs[i + 1] - h:.1f},{ys[i + 1] - t[i + 1] * h:.1f} "
                 f"{xs[i + 1]:.1f},{ys[i + 1]:.1f}")
    return " ".join(d)


def build(series):
    W, H = 880, 320
    L, R, T, B = 60, 28, 92, 46          # marginaler runt plottytan
    PW, PH = W - L - R, H - T - B

    counts = [c for _, c in series]
    peak = max(counts)
    step = nice_step(peak)
    ticks = max(1, -(-peak // step)) if step >= 1 else 4
    ymax = step * ticks
    if peak >= ymax:                      # lite luft ovanför toppen
        ymax += step
        ticks += 1
    n = len(series)
    stepx = PW / (n - 1) if n > 1 else PW

    def px(i):
        return L + i * stepx

    def py(v):
        return T + PH - (v / ymax) * PH

    nl = "\n  "

    # Horisontella gridlinjer + y-etiketter
    grid = []
    for k in range(ticks + 1):
        v = step * k
        y = py(v)
        grid.append(
            f'<line x1="{L}" y1="{y:.1f}" x2="{L + PW}" y2="{y:.1f}" '
            f'stroke="#FFFFFF" stroke-opacity="{0.10 if k == 0 else 0.05}" stroke-width="1"/>'
            f'<text x="{L - 12}" y="{y + 3.5:.1f}" text-anchor="end" '
            f'font-family="{FONT}" font-size="10.5" fill="{C_DIM}">{v:g}</text>'
        )

    pts = [(px(i), py(c)) for i, (_, c) in enumerate(series)]
    line = smooth_path(pts)
    area = f"{line} L{L + PW:.1f},{T + PH:.1f} L{L:.1f},{T + PH:.1f} Z"

    # X-etiketter: varje månadsskifte vid långa intervall, dagsnummer vid korta
    xlab = []
    if n > 60:
        for i, (date, _) in enumerate(series):
            if date[8:10] == "01":
                x = px(i)
                xlab.append(
                    f'<line x1="{x:.1f}" y1="{T + PH}" x2="{x:.1f}" y2="{T + PH + 5}" '
                    f'stroke="#FFFFFF" stroke-opacity="0.12"/>'
                    f'<text x="{x:.1f}" y="{T + PH + 22}" text-anchor="middle" '
                    f'font-family="{FONT}" font-size="10.5" fill="{C_MUTED}">'
                    f'{MONTHS[int(date[5:7]) - 1]}</text>'
                )
    else:
        for i, (date, _) in enumerate(series):
            if i % 5 == 0 or i == n - 1:
                xlab.append(
                    f'<text x="{px(i):.1f}" y="{T + PH + 22}" text-anchor="middle" '
                    f'font-family="{FONT}" font-size="10.5" fill="{C_MUTED}">'
                    f'{date[8:10].lstrip("0")}</text>'
                )

    # Toppmarkering
    pi = counts.index(peak)
    pxk, pyk = pts[pi]
    lx = min(max(pxk, L + 14), L + PW - 14)
    peak_mark = (
        f'<circle cx="{pxk:.1f}" cy="{pyk:.1f}" r="7" fill="{C_CYAN}" fill-opacity="0.18"/>'
        f'<circle cx="{pxk:.1f}" cy="{pyk:.1f}" r="3.2" fill="{C_BG}" stroke="{C_CYAN}" stroke-width="2"/>'
        f'<text x="{lx:.1f}" y="{pyk - 12:.1f}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="10.5" font-weight="600" fill="{C_FG}">{peak}</text>'
    )

    total = sum(counts)
    first, last = series[0][0], series[-1][0]
    heading = ("Last 12 Months" if n > 300 else
               f"Last {n // 30} Months" if n > 60 else
               f"Last {n} Days")

    # Statistikrutor uppe till höger
    def pill(x, label, value):
        w = 112
        return (
            f'<rect x="{x}" y="22" width="{w}" height="46" rx="10" fill="{C_CARD}" stroke="{C_BORDER}"/>'
            f'<text x="{x + 14}" y="39" font-family="{FONT}" font-size="9.5" letter-spacing="1" '
            f'fill="{C_DIM}">{label}</text>'
            f'<text x="{x + 14}" y="59" font-family="{FONT}" font-size="17" font-weight="700" '
            f'fill="url(#stroke)">{value:,}</text>'
        )

    pills = pill(W - R - 112, "PEAK / DAY", peak) + pill(W - R - 112 - 10 - 112, "TOTAL", total)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Daily GitHub contributions for {USER} from {first} to {last}: {total} total, peak {peak} in one day.">
  <defs>
    <linearGradient id="stroke" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{C_PURPLE}"/>
      <stop offset="100%" stop-color="{C_CYAN}"/>
    </linearGradient>
    <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{C_PURPLE}" stop-opacity="0.45"/>
      <stop offset="60%" stop-color="{C_CYAN}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{C_CYAN}" stop-opacity="0.03"/>
    </linearGradient>
    <filter id="glow" x="-5%" y="-20%" width="110%" height="140%">
      <feGaussianBlur stdDeviation="3"/>
    </filter>
    <clipPath id="plot"><rect x="{L}" y="{T - 20}" width="{PW}" height="{PH + 20}"/></clipPath>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>
    <path id="ln" d="{line}"/>
  </defs>

  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="{C_BG}" stroke="{C_BORDER}"/>
  <rect x="0" y="0" width="{W}" height="3" fill="url(#stroke)" clip-path="url(#card)"/>

  <text x="{L - 12}" y="40" font-family="{FONT}" font-size="16" font-weight="600" fill="{C_FG}">Contributions &#8212; {heading}</text>
  <text x="{L - 12}" y="60" font-family="{FONT}" font-size="11.5" fill="{C_MUTED}">Daily GitHub activity</text>
  {pills}

  {nl.join(grid)}

  <g clip-path="url(#plot)" fill="none" stroke="url(#stroke)" stroke-linejoin="round" stroke-linecap="round">
    <path d="{area}" fill="url(#fill)" stroke="none"/>
    <use href="#ln" stroke-width="5" stroke-opacity="0.35" filter="url(#glow)"/>
    <use href="#ln" stroke-width="1.8"/>
  </g>
  {peak_mark}

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
