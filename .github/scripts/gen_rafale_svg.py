#!/usr/bin/env python3
"""Bake the halftone Rafale into a static SVG for the GitHub README.

A README cannot run JavaScript, so the dot field that the site computes at
runtime has to be emitted as real elements here. The region geometry is
parsed straight out of the canvas renderer so the two cannot drift apart.

Dots are grouped twice over: by tone (which sets fill and radius) and by
vertical band (which staggers a brightness wave across the airframe), so
the whole thing animates with ~100 CSS rules instead of per-dot animation.

rafale_dots.js alongside this script is the geometry source. The portfolio
site (mayukh-d.github.io) inlines the same renderer to draw this on a canvas;
if the airframe changes, both need regenerating.
"""

import math
import os
import re
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rafale_dots.js")

DOT_LO = (0, 118, 150)
DOT_HI = (120, 245, 255)
AIR = "#00ff41"
ACCENT = "#00ff41"
MUTED = "#7d8f85"
MONO = "ui-monospace,'JetBrains Mono','SF Mono',Menlo,Consolas,monospace"

W, H = 1000, 300
MINX, MAXX, MINY, MAXY = -11.7, 8.8, -1.65, 3.45
PITCH = 5.6            # viewBox units between samples
LEVELS = 6
BANDS = 16


PLUME_X0 = -7.72          # nozzle exit
PLUME_LEN = 3.5           # visible plume, metres
PLUME_R0 = 0.46
P_LEVELS, P_BANDS = 8, 16
COOL = (40, 120, 255)     # royal blue at the cool tail
HOT = (150, 215, 255)     # bright blue, not white, at the throat


P_PITCH = PITCH * 0.66
CELL_L0 = 0.95            # first shock cell, metres
CELL_DECAY = 0.80         # each cell is shorter than the one before it


def build_plume(S, ox, oy):
    """Afterburner plume: a tapering jet with shock diamonds.

    Radius pulses along the axis, so the flow pinches and bulges the way a
    real over-expanded nozzle does, and brightness peaks at the pinches.
    That periodic structure is what reads as an afterburner rather than a
    smear of colour.
    """
    # Cell boundaries. Each shock cell is shorter than the last as the jet
    # loses the pressure mismatch driving it, which is why a real plume is
    # never periodic. A cosine here was the tell: it read as a sine wave.
    cells, d = [0.0], 0.0
    for k in range(10):
        d += CELL_L0 * (CELL_DECAY ** k)
        cells.append(d)
        if d > PLUME_LEN:
            break

    def cell_u(dist):
        """Position within the current cell, 0 at one shock crossing to 1 at the next."""
        for k in range(len(cells) - 1):
            if cells[k] <= dist < cells[k + 1]:
                return (dist - cells[k]) / (cells[k + 1] - cells[k])
        return 1.0

    g = P_PITCH / S
    buckets = {}
    y = -PLUME_R0 * 1.9
    row = 0
    while y <= PLUME_R0 * 1.9:
        x = PLUME_X0 - (g / 2 if row % 2 else 0)
        while x >= PLUME_X0 - PLUME_LEN:
            dist = PLUME_X0 - x
            t = dist / PLUME_LEN
            u = cell_u(dist)
            # triangular profile: straight edges meeting at a cusp, so the
            # cells read as diamonds rather than as smooth humps
            tri = 1.0 - abs(2.0 * u - 1.0)
            r = max(PLUME_R0 * (1 - t) ** 0.5 * (0.52 + 0.48 * tri), 0.05)
            a = abs(y)
            if a <= r * 1.75:
                axial = (1 - t) ** 0.80
                # the glow is unburnt fuel re-igniting where the shocks cross,
                # so it spikes narrowly at the cell boundary
                node = math.exp(-((min(u, 1.0 - u)) / 0.14) ** 2)
                glow = 0.52 + 1.05 * node
                if a <= r:
                    v = axial * (1 - (a / r) ** 2) * glow
                else:
                    v = axial * 0.34 * (1 - (a - r) / (r * 0.75)) * glow
                v = max(0.0, min(1.0, v)) ** 0.70
                if v > 0.06:
                    buckets.setdefault(
                        (min(P_LEVELS - 1, int(v * P_LEVELS)),
                         min(P_BANDS - 1, int(t * P_BANDS))), []
                    ).append((ox + x * S, oy - y * S))
            x -= g
        y += g
        row += 1
    return buckets


def load_regions(path):
    """Pull reg(tone, [[x,y],...]) out of the canvas renderer."""
    src = open(path).read()
    out = []
    for m in re.finditer(r"reg\(([\d.]+),\s*(\[.*?\])\);", src, re.S):
        tone = float(m.group(1))
        pts = [(float(a), float(b)) for a, b in
               re.findall(r"\[\s*(-?[\d.]+),\s*(-?[\d.]+)\s*\]", m.group(2))]
        if pts:
            out.append((tone, pts))
    return out


def inside(px, py, poly):
    c = False
    n = len(poly)
    for i in range(n):
        j = (i - 1) % n
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
            c = not c
    return c


def frame():
    spanX, spanY = MAXX - MINX, MAXY - MINY
    S = min(W / spanX, H / spanY) * 0.88
    return (S,
            W / 2 - ((MINX + MAXX) / 2) * S,
            H / 2 + ((MINY + MAXY) / 2) * S - H * 0.05)


def build(regions):
    spanX, spanY = MAXX - MINX, MAXY - MINY
    S, ox, oy = frame()

    g = PITCH / S
    buckets = {}
    y = MINY
    row = 0
    while y <= MAXY:
        x = MINX + (g / 2 if row % 2 else 0)
        while x <= MAXX:
            tone = -1.0
            for t, poly in reversed(regions):
                if inside(x, y, poly):
                    tone = t
                    break
            if tone >= 0:
                lit = 0.80 + 0.34 * ((y - MINY) / spanY)
                v = max(0.10, min(1.0, 0.16 + 0.86 * tone * lit))
                px, py = ox + x * S, oy - y * S
                lvl = min(LEVELS - 1, int(v * LEVELS))
                band = min(BANDS - 1, max(0, int(px / W * BANDS)))
                buckets.setdefault((lvl, band), []).append((px, py))
            x += g
        y += g
        row += 1
    return buckets


def main(out_path):
    regions = load_regions(SRC)
    buckets = build(regions)
    S, ox, oy = frame()
    total = sum(len(v) for v in buckets.values())

    css = [
        "@keyframes wave{0%,62%,100%{opacity:.80}18%{opacity:1}}",
        f"@keyframes drift{{from{{transform:translateX(0)}}to{{transform:translateX(-{W+340}px)}}}}",
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}",
    ]
    for lvl in range(LEVELS):
        f = (lvl + 0.5) / LEVELS
        r = 0.38 + 0.62 * f
        col = tuple(round(DOT_LO[i] + (DOT_HI[i] - DOT_LO[i]) * f) for i in range(3))
        css.append(f".t{lvl}{{fill:rgb{col};fill-opacity:{0.42 + 0.58 * f:.2f}}}")
    for b in range(BANDS):
        css.append(f".b{b}{{animation:wave 5.4s ease-in-out infinite;"
                   f"animation-delay:-{(BANDS - b) * 0.28:.2f}s}}")

    body = [f'<rect width="{W}" height="{H}" fill="#010203"/>']

    # air and cloud lines, drifting aft
    rnd = 99991
    body.append('<g>')
    for i in range(26):
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        yy = (rnd % 10000) / 10000.0 * H
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        ln = 30 + rnd % 190
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        dur = 6 + (rnd % 800) / 100.0
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        op = 0.05 + (rnd % 12) / 100.0
        css.append(f".a{i}{{animation:drift {dur:.2f}s linear infinite;"
                   f"animation-delay:-{(i * 0.9) % dur:.2f}s}}")
        body.append(f'<line class="a{i}" x1="{W+300}" y1="{yy:.0f}" x2="{W+300+ln}" '
                    f'y2="{yy:.0f}" stroke="{AIR}" stroke-width="1" '
                    f'opacity="{op:.2f}" stroke-linecap="round"/>')
    for i in range(5):
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        yy = 20 + rnd % (H - 40)
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        sc = 0.8 + (rnd % 80) / 100.0
        dur = 22 + (rnd % 1200) / 100.0
        css.append(f".w{i}{{animation:drift {dur:.2f}s linear infinite;"
                   f"animation-delay:-{(i * 5.1) % dur:.2f}s}}")
        d = (f"M0 0c{30*sc:.0f} -{14*sc:.0f} {76*sc:.0f} -{18*sc:.0f} {130*sc:.0f} -{6*sc:.0f}"
             f"c{38*sc:.0f} -{15*sc:.0f} {84*sc:.0f} -{10*sc:.0f} {124*sc:.0f} {8*sc:.0f}")
        body.append(f'<path class="w{i}" d="{d}" transform="translate({W+300} {yy})" '
                    f'fill="none" stroke="{AIR}" stroke-width="1.1" opacity="0.10" '
                    f'stroke-linecap="round"/>')
    body.append('</g>')

    # afterburner, behind the airframe
    css.append("@keyframes burn{0%,100%{opacity:.52}45%{opacity:1}}")
    for lvl in range(P_LEVELS):
        f = (lvl + 0.5) / P_LEVELS
        col = tuple(round(COOL[i] + (HOT[i] - COOL[i]) * f) for i in range(3))
        css.append(f".p{lvl}{{fill:rgb{col};fill-opacity:{0.58 + 0.42 * f:.2f}}}")
    for b in range(P_BANDS):
        css.append(f".f{b}{{animation:burn 0.8s ease-in-out infinite;"
                   f"animation-delay:-{b * 0.05:.2f}s}}")
    for (lvl, band), pts in sorted(build_plume(S, ox, oy).items()):
        f = (lvl + 0.5) / P_LEVELS
        rr = (0.52 + 0.48 * f) * P_PITCH * 0.5
        dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.2f}"/>' for x, y in pts)
        body.append(f'<g class="p{lvl} f{band}">{dots}</g>')

    # the airframe
    for (lvl, band), pts in sorted(buckets.items()):
        f = (lvl + 0.5) / LEVELS
        rr = (0.38 + 0.62 * f) * PITCH * 0.50
        dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.2f}"/>'
                       for x, y in pts)
        body.append(f'<g class="t{lvl} b{band}">{dots}</g>')

    # caption
    body.append(f'<text x="34" y="{H-46}" font-family="{MONO}" font-size="15" '
                f'fill="#00e5ff" letter-spacing="1">DASSAULT RAFALE EH</text>')
    body.append(f'<text x="34" y="{H-28}" font-family="{MONO}" font-size="11" '
                f'fill="{MUTED}">No. 17 SQN &#183; GOLDEN ARROWS</text>')
    body.append(f'<text x="34" y="{H-12}" font-family="{MONO}" font-size="11" '
                f'fill="{ACCENT}" opacity="0.55">defence &#183; geopolitics &#183; airpower</text>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}" role="img" '
           f'aria-label="Halftone side elevation of a Dassault Rafale EH of '
           f'No. 17 Squadron, Indian Air Force.">'
           f'<style>{"".join(css)}</style>{"".join(body)}</svg>')
    open(out_path, "w").write(svg)
    print(f"wrote {out_path}: {total} dots, {len(buckets)} groups, "
          f"{len(svg)/1024:.0f} KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "rafale.svg")
