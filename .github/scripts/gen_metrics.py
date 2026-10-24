#!/usr/bin/env python3
"""Render assets/metrics.svg: a panel of career and GitHub numbers, in the portfolio palette.

The career numbers are facts that only change when I do something, so they live here as
constants. The two GitHub numbers are read live from the GraphQL API, and the citations
from the Scholar numbers the portfolio site keeps (assets/scholar.json there). Run locally with `gh`
authenticated, or in Actions with GITHUB_TOKEN; refreshed weekly by .github/workflows/langs.yml.
"""

import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request

USER = "Mayukh-D"
SCHOLAR = "https://raw.githubusercontent.com/Mayukh-D/mayukh-d.github.io/main/assets/scholar.json"

# (value, label, detail). Update by hand when one of these changes.
CAREER = [
    ("3+", "years in industry", "Accenture · Cognizant"),
    ("5", "roles held", "2 current: Eccoi · Haizea"),
    ("3", "internships", "Ashok Leyland and two more"),
    ("1", "course taught", "HCI at the ANU"),
    ("3", "peer-reviewed papers", "1 as first author"),
]

BG, BG_SOFT = "#010203", "#0a0f0c"
BORDER, BORDER_HI = "#10241a", "#1d4a2f"
GREEN, CYAN, MUTED, TEXT = "#00ff41", "#00e5ff", "#7d8f85", "#d8e4dc"

QUERY = """{ user(login: "%s") {
  repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) { totalCount }
  contributionsCollection { contributionCalendar { totalContributions } } } }""" % USER


def fetch():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": QUERY}).encode(),
            headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    else:  # local fallback
        out = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}"],
                             capture_output=True, text=True, check=True).stdout
        data = json.loads(out)
    user = data["data"]["user"]
    return (user["repositories"]["totalCount"],
            user["contributionsCollection"]["contributionCalendar"]["totalContributions"])


def scholar():
    """The citations tile, from the site's Scholar numbers; the last known ones if unreachable."""
    try:
        with urllib.request.urlopen(SCHOLAR, timeout=30) as r:
            s = json.load(r)
        when = dt.date.fromisoformat(s["as_of"]).strftime("%b %Y")
        return (str(s["citations"]), "citations", f"h-index {s['h_index']} · Scholar, {when}")
    except Exception:
        return ("58", "citations", "h-index 3 · Scholar, Oct 2026")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace("·", "&#183;")


def render(repos, contributions):
    tiles = CAREER + [scholar()] + [
        (str(repos), "public projects", "built and kept in the open"),
        (str(contributions), "contributions", "in the last 12 months"),
    ]
    cols, tw, th, gap, x0, y0 = 4, 233, 82, 12, 26, 74
    rows = (len(tiles) + cols - 1) // cols
    width, height = 1020, y0 + rows * th + (rows - 1) * gap + 24
    today = dt.date.today().isoformat()
    label = "Metrics: " + ", ".join(f"{v} {l}" for v, l, _ in tiles)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="{esc(label)}">',
        "<style>.t{font-family:ui-monospace,'JetBrains Mono','SF Mono',SFMono-Regular,Menlo,Consolas,monospace}"
        "@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
        ".tile{animation:rise .5s ease-out both}</style>",
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<text class="t" x="26" y="34" font-size="14" fill="{GREEN}">mayukh@github<tspan fill="{BORDER_HI}">:~$</tspan> '
        f'<tspan fill="{TEXT}">./metrics --all</tspan></text>',
        f'<text class="t" x="26" y="56" font-size="11.5" fill="{MUTED}">career by hand &#183; Scholar and GitHub numbers live &#183; updated {today}</text>',
    ]
    for i, (value, name, detail) in enumerate(tiles):
        x = x0 + (i % cols) * (tw + gap)
        y = y0 + (i // cols) * (th + gap)
        colour = CYAN if i >= len(CAREER) else GREEN
        out.append(
            f'<g class="tile" style="animation-delay:{i * 0.06:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="8" fill="{BG_SOFT}" stroke="{BORDER_HI}"/>'
            f'<text class="t" x="{x + 16}" y="{y + 38}" font-size="28" font-weight="700" fill="{colour}">{esc(value)}</text>'
            f'<text class="t" x="{x + tw - 16}" y="{y + 30}" font-size="12" fill="{TEXT}" text-anchor="end">{esc(name)}</text>'
            f'<text class="t" x="{x + 16}" y="{y + 64}" font-size="10.5" fill="{MUTED}">{esc(detail)}</text>'
            "</g>"
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "assets/metrics.svg"
    svg = render(*fetch())
    with open(target, "w") as f:
        f.write(svg)
    print(f"wrote {target}")
