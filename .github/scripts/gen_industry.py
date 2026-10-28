#!/usr/bin/env python3
"""Generate the industry-experience timeline card for the GitHub profile README.

Usage: python3 gen_industry.py assets/industry.svg
"""

import sys

# palette (from mayukh-d.github.io)
GREEN, CYAN = "#00ff41", "#00e5ff"
TEXT, MUTED, BORDER_HI = "#d8e4dc", "#7d8f85", "#1d4a2f"
CYAN_BORDER = "#123a40"

W = 1020
CARD_X, CARD_W = 64, 930
RAIL_X = 44

# newest first; current roles are green with a pulsing dot, past roles cyan.
# Each bullet is a list of lines; **word** is drawn bold in the accent colour.
ROLES = [
    dict(org="Haizea Analytics", dates="Sep 2026 – Present", current=True,
         role="SATELLITE AI RESEARCH TRAINEE · CANBERRA",
         bullets=[["Deep learning models that map live tree canopy cover across Australia at 10 m",
                   "from four years of quarterly Sentinel-2 imagery, trained on airborne LiDAR."],
                  ["Run as pre-registered, multi-seed experiments where every change has to beat",
                   "the noise floor."]],
         chips=["PyTorch", "Sentinel-2", "LiDAR", "Remote sensing"]),
    dict(org="Eccoi", dates="Jul 2026 – Present", current=True,
         role="TRAINEE ML ARCHITECT AND SYSTEM ENGINEER · CANBERRA",
         bullets=[["Architecting **SAICOP**, Eccoi's Sovereign AI Community of Practice: architectural",
                   "principles, the system context model, and platform assessment and shortlisting."],
                  ["Proving the conceptual architecture end to end against Australian Government",
                   "delivery, security and procurement realities."],
                  ["Exhibited SAICOP at the Inaugural Australian AI Parliamentary Showcase,",
                   "Parliament House, Sep 2026."]],
         chips=["Solution architecture", "System context modelling", "Platform assessment", "Sovereign AI"]),
    dict(org="Accenture", dates="Jan 2022 – Feb 2025", current=False,
         role="ADVANCED APPLICATION ENGINEERING ANALYST · BENGALURU",
         bullets=[["Built **Ingrain**, an AIOps tool that generates predictive ML pipelines for automated IT ticket resolution,",
                   "with explainable AI and live model-performance reporting."],
                  ["Built **Quasar++**, a chatbot for querying internal documents through the ChatGPT API."],
                  ["Production backend and data work: MERN stack services, MLOps pipelines, and a data",
                   "engineering stack of Hadoop, PySpark and Cassandra."]],
         chips=["MERN", "MLOps", "Hadoop", "PySpark", "Cassandra", "Explainable AI", "ChatGPT API"]),
    dict(org="Cognizant", dates="Oct 2021 – Jan 2022", current=False,
         role="PROGRAMMER ANALYST · INDIA",
         bullets=[["Full-stack .NET MVC systems with React front ends and SQL Server, including a Hospital Logistics",
                   "System for COVID-19 operational workflows."]],
         chips=[".NET MVC", "React", "SQL Server"]),
]

SUBTITLE = "4 roles · 3+ years in industry · 2021 → now"
FOOTNOTE = "# the repos here are mostly ML and research; the production backend side lives in the work above."


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rich(line, accent):
    """Escape a line and turn **word** into a bold accent tspan."""
    parts = esc(line).split("**")
    return "".join(f'<tspan fill="{accent}" font-weight="700">{p}</tspan>' if i % 2 else p
                   for i, p in enumerate(parts))


def chips(x, y, items, accent, stroke):
    out = []
    for it in items:
        w = len(it) * 6.35 + 18
        out.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="20" rx="4" fill="#010203" stroke="{stroke}"/>'
                   f'<text class="t" x="{x + w / 2:.0f}" y="{y + 14}" font-size="10.5" fill="{accent}" '
                   f'text-anchor="middle">{esc(it)}</text>')
        x += w + 8
    return "".join(out)


def card(r, y, delay):
    accent = GREEN if r["current"] else CYAN
    stroke = BORDER_HI if r["current"] else CYAN_BORDER
    body = [f'<text class="t" x="84" y="{y + 28}" font-size="18" font-weight="700" fill="{accent}">{esc(r["org"])}</text>',
            f'<text class="t" x="974" y="{y + 28}" font-size="12" fill="{accent}" text-anchor="end">{esc(r["dates"])}</text>',
            f'<text class="t" x="84" y="{y + 48}" font-size="10" fill="{MUTED}" letter-spacing="1.1">{esc(r["role"])}</text>']
    by = y + 76
    for bullet in r["bullets"]:
        body.append(f'<text class="t" x="84" y="{by}" font-size="12" fill="{accent}">&#8250;</text>')
        for line in bullet:
            body.append(f'<text class="t" x="100" y="{by}" font-size="12" fill="{TEXT}">{rich(line, accent)}</text>')
            by += 16
        by += 8
    cy = by - 10
    body.append(chips(84, cy, r["chips"], accent, stroke))
    h = cy + 20 + 18 - y
    return (f'<g class="card" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{CARD_X}" y="{y}" width="{CARD_W}" height="{h}" rx="8" fill="#0a0f0c" stroke="{stroke}"/>'
            f'<rect x="{CARD_X}" y="{y}" width="3" height="{h}" rx="1.5" fill="{accent}"/>'
            + "".join(body) + "</g>"), h


def build():
    cards, dots, y = [], [], 78
    for i, r in enumerate(ROLES):
        svg, h = card(r, y, i * 0.12)
        cards.append(svg)
        dots.append((y + 23, GREEN if r["current"] else CYAN, r["current"]))
        y += h + 16
    H = y + 34
    top, bottom = dots[0][0], dots[-1][0]
    rail_len = bottom - top
    dot_svg = "".join(
        (f'<circle class="ping" cx="{RAIL_X}" cy="{cy}" r="6" fill="none" stroke="{c}" stroke-width="1.5"/>' if cur else "")
        + f'<circle cx="{RAIL_X}" cy="{cy}" r="6" fill="{c}"/>' for cy, c, cur in dots)
    label = "Industry experience: " + "; ".join(
        f'{r["org"]}, {r["role"].split(" · ")[0].title()}, {r["dates"].replace("–", "to")}' for r in ROLES)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(label)}">
<style>.t{{font-family:ui-monospace,'JetBrains Mono','SF Mono',SFMono-Regular,Menlo,Consolas,monospace}}@keyframes rise{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}.card{{animation:rise .5s ease-out both}}@keyframes ping{{0%{{r:6;opacity:.7}}100%{{r:16;opacity:0}}}}.ping{{animation:ping 2.4s ease-out infinite}}@keyframes draw{{from{{stroke-dashoffset:{rail_len}}}to{{stroke-dashoffset:0}}}}.rail{{stroke-dasharray:{rail_len};animation:draw 1.4s ease-out both}}</style>
<defs><linearGradient id="rg" gradientUnits="userSpaceOnUse" x1="{RAIL_X}" y1="{top}" x2="{RAIL_X}" y2="{bottom}"><stop offset="0" stop-color="{GREEN}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient></defs>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="10" fill="#010203" stroke="#10241a"/>
<text class="t" x="26" y="34" font-size="14" fill="{GREEN}">mayukh@github<tspan fill="{BORDER_HI}">:~$</tspan> <tspan fill="{TEXT}">./experience --industry</tspan></text>
<text class="t" x="26" y="56" font-size="11.5" fill="{MUTED}">{esc(SUBTITLE)}</text>
<line class="rail" x1="{RAIL_X}" y1="{top}" x2="{RAIL_X}" y2="{bottom}" stroke="url(#rg)" stroke-width="2"/>
{dot_svg}
{"".join(cards)}
<text class="t" x="26" y="{H - 22}" font-size="11" fill="{MUTED}">{esc(FOOTNOTE)}</text>
</svg>
'''


if __name__ == "__main__":
    open(sys.argv[1], "w").write(build())
