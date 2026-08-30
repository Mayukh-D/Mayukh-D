#!/usr/bin/env python3
"""Render assets/langs.svg: language mix across my public repos, in the portfolio palette.

Reads live data from the GitHub GraphQL API. Run locally with `gh` authenticated,
or in Actions with GITHUB_TOKEN. Refreshed weekly by .github/workflows/langs.yml
so the panel never depends on a third-party card service staying up.
"""

import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request

USER = "Mayukh-D"
TOP_N = 7

BG, BG_SOFT = "#010203", "#0a0f0c"
BORDER, BORDER_HI = "#10241a", "#1d4a2f"
GREEN, CYAN, MUTED, TEXT = "#00ff41", "#00e5ff", "#7d8f85", "#d8e4dc"

QUERY = """{ user(login: "%s") { repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
  totalCount nodes { languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
    edges { size node { name } } } } } } }""" % USER


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

    repos = data["data"]["user"]["repositories"]
    totals = {}
    for node in repos["nodes"]:
        for e in node["languages"]["edges"]:
            totals[e["node"]["name"]] = totals.get(e["node"]["name"], 0) + e["size"]
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    return ranked, repos["totalCount"]


def ramp(i, n):
    """Interpolate green -> cyan across the segments, dimming the tail."""
    t = i / max(n - 1, 1)
    g = tuple(int(GREEN[k:k + 2], 16) for k in (1, 3, 5))
    c = tuple(int(CYAN[k:k + 2], 16) for k in (1, 3, 5))
    dim = 1.0 - 0.45 * t
    rgb = [int((g[j] + (c[j] - g[j]) * t) * dim) for j in range(3)]
    return "#%02x%02x%02x" % tuple(rgb)


def build(ranked, repo_count):
    top = ranked[:TOP_N]
    rest = sum(s for _, s in ranked[TOP_N:])
    if rest:
        top.append(("Other", rest))
    total = sum(s for _, s in top) or 1

    W, PAD = 1020, 26
    BAR_W = W - 2 * PAD
    bar_y, bar_h = 74, 24
    rows = (len(top) + 3) // 4
    H = bar_y + bar_h + 26 + rows * 24 + 14

    css = [
        ".t{font-family:ui-monospace,'JetBrains Mono','SF Mono',SFMono-Regular,Menlo,Consolas,"
        "monospace}"
        "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
        "@keyframes shim{from{transform:translateX(-200px)}to{transform:translateX(%dpx)}}"
        "@keyframes rise{from{opacity:0}to{opacity:1}}"
        ".seg{animation:grow .85s cubic-bezier(.22,1,.36,1) both}"
        ".lg{animation:rise .5s ease-out both}"
        ".shim{animation:shim 3.8s linear infinite}" % BAR_W
    ]
    body = [
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<text class="t" x="{PAD}" y="34" font-size="14" fill="{GREEN}">'
        f'mayukh@github<tspan fill="{BORDER_HI}">:~$</tspan> '
        f'<tspan fill="{TEXT}">git ls-lang --all</tspan></text>',
        f'<text class="t" x="{PAD}" y="56" font-size="11.5" fill="{MUTED}">'
        f'{repo_count} public repos &#183; by bytes of source &#183; '
        f'updated {dt.date.today().isoformat()}</text>',
        f'<clipPath id="clip"><rect x="{PAD}" y="{bar_y}" width="{BAR_W}" height="{bar_h}" rx="4"/></clipPath>',
        f'<g clip-path="url(#clip)">',
        f'<rect x="{PAD}" y="{bar_y}" width="{BAR_W}" height="{bar_h}" fill="{BG_SOFT}"/>',
    ]

    x = float(PAD)
    legend = []
    for i, (name, size) in enumerate(top):
        w = BAR_W * size / total
        col = MUTED if name == "Other" else ramp(i, len(top))
        body.append(
            f'<rect class="seg" x="{x:.2f}" y="{bar_y}" width="{max(w-2,1):.2f}" height="{bar_h}" '
            f'fill="{col}" style="transform-origin:{x:.2f}px 0;animation-delay:{0.08*i:.2f}s"/>')
        x += w
        pct = 100.0 * size / total
        legend.append((name, pct, col, i))

    body.append(f'<rect class="shim" x="{PAD}" y="{bar_y}" width="200" height="{bar_h}" '
                f'fill="#fff" opacity="0.07"/>')
    body.append("</g>")

    col_w = BAR_W / 4
    for name, pct, col, i in legend:
        cx = PAD + (i % 4) * col_w
        cy = bar_y + bar_h + 40 + (i // 4) * 24
        body.append(
            f'<g class="lg" style="animation-delay:{0.5+0.06*i:.2f}s">'
            f'<rect x="{cx}" y="{cy-9}" width="9" height="9" rx="2" fill="{col}"/>'
            f'<text class="t" x="{cx+16}" y="{cy}" font-size="12" fill="{TEXT}">{name}</text>'
            f'<text class="t" x="{cx+col_w-24}" y="{cy}" font-size="12" fill="{MUTED}" '
            f'text-anchor="end">{pct:.1f}%</text></g>')

    label = ", ".join(f"{n} {p:.0f}%" for n, p, _, _ in legend)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
            f'height="{H}" role="img" aria-label="Language mix: {label}">'
            f'<style>{"".join(css)}</style>{"".join(body)}</svg>')


if __name__ == "__main__":
    ranked, count = fetch()
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/langs.svg"
    with open(out, "w") as f:
        f.write(build(ranked, count))
    print(f"wrote {out}: {len(ranked)} languages across {count} repos")
