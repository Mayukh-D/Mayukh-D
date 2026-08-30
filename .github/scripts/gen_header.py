#!/usr/bin/env python3
"""Generate an animated terminal-boot SVG for the GitHub profile README."""

import html

# palette (from mayukh-d.github.io)
BG        = "#010203"
BG_SOFT   = "#0a0f0c"
BORDER    = "#10241a"
BORDER_HI = "#1d4a2f"
GREEN     = "#00ff41"
GREEN_DIM = "#00b32e"
CYAN      = "#00e5ff"
RED       = "#ff2b4e"
TEXT      = "#d8e4dc"
MUTED     = "#7d8f85"

FS = 15.0          # font-size
CW = 9.0           # nominal char width, for layout estimates only
MW = 9.7           # mask step width: deliberately >= any real advance
X0 = 26.0          # left padding
TOP = 34.0         # title bar height
Y0 = TOP + 34.0    # first baseline
LH = 27.0          # line height

W, H = 1020, 336

PROMPT = "mayukh@github"
PS1    = ":~$ "

# (kind, segments) ; kind: "cmd" | "out" | "gap"
LINES = [
    ("cmd", [("whoami", TEXT)]),
    ("out", [("Mayukh Das ", TEXT), (":: ", BORDER_HI),
             ("System Architect Intern ", CYAN), ("@ Eccoi", GREEN)]),
    ("out", [("Master of Computing @ ", MUTED), ("ANU", GREEN),
             ("  ·  ex-Accenture, 3+ yrs", MUTED)]),
    ("gap", []),
    ("cmd", [("cat focus.txt", TEXT)]),
    ("out", [("generative models · sovereign AI · HCI · F1 aero", MUTED)]),
    ("gap", []),
    ("cmd", [("./status --now", TEXT)]),
    ("out", [("[ok] ", GREEN), ("building things people can actually understand", TEXT)]),
]


def esc(s):
    return html.escape(s, quote=False)


def build():
    # ---- schedule ------------------------------------------------------
    t = 0.55
    sched = []          # (start, dur, nchars)
    for kind, segs in LINES:
        if kind == "gap":
            sched.append(None)
            t += 0.18
            continue
        text = "".join(s for s, _ in segs)
        n = len(text) + (len(PROMPT) + len(PS1) if kind == "cmd" else 0)
        dur = (0.055 * len(text)) if kind == "cmd" else 0.34
        sched.append((t, dur, n))
        t += dur + (0.30 if kind == "cmd" else 0.16)

    HOLD = 3.6
    T = t + HOLD

    def pct(x):
        return round(100.0 * x / T, 4)

    css, body = [], []

    css.append(f""".t{{font-family:ui-monospace,'JetBrains Mono','SF Mono',SFMono-Regular,Menlo,Consolas,monospace;font-size:{FS}px;}}
@keyframes bl{{0%,49%{{fill:{GREEN}}}50%,100%{{fill:transparent}}}}""")

    # ---- terminal chrome ----------------------------------------------
    body.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="{BG}" stroke="{BORDER}"/>')
    body.append(f'<path d="M1 11a10 10 0 0 1 10-10h{W-22}a10 10 0 0 1 10 10v{TOP-11}H1z" fill="{BG_SOFT}"/>')
    body.append(f'<line x1="1" y1="{TOP}" x2="{W-1}" y2="{TOP}" stroke="{BORDER}"/>')
    for i, c in enumerate((RED, MUTED, GREEN_DIM)):
        body.append(f'<circle cx="{22+18*i}" cy="{TOP/2}" r="5" fill="{c}" opacity="0.85"/>')
    body.append(f'<text class="t" x="{W/2}" y="{TOP/2+4.5}" text-anchor="middle" '
                f'font-size="12" fill="{MUTED}">mayukh@github: ~/profile</text>')

    # ---- feed-forward block (right side) ------------------------------
    body.append(ffn())

    # ---- terminal lines -----------------------------------------------
    y = Y0
    for idx, ((kind, segs), sc) in enumerate(zip(LINES, sched)):
        if kind == "gap":
            y += LH * 0.55
            continue
        start, dur, n = sc
        full = n * MW
        s0, s1 = pct(start), pct(start + dur)
        # the cursor hands off to the next line as soon as that line begins
        nxt = next((s[0] for s in sched[idx + 1:] if s), None)
        c_off = pct(nxt) if nxt is not None else 99.9
        # Once the line has finished typing, open the mask to the full panel width.
        # Safari and Firefox honour textLength inconsistently across tspans, so the
        # laid-out text can be a touch wider than n*CW; without this the tail clips.
        s1b = min(s1 + 0.05, 99.8)
        css.append(
            f"@keyframes w{idx}{{0%,{s0}%{{width:0px}}{s1}%{{width:{full}px}}"
            f"{s1b}%,99.9%{{width:{W}px}}100%{{width:0px}}}}"
            f"@keyframes o{idx}{{0%,{max(s0-0.01,0)}%{{opacity:0}}{s0}%,99.9%{{opacity:1}}100%{{opacity:0}}}}"
            f"@keyframes k{idx}{{0%,{max(s0-0.01,0)}%{{opacity:0}}{s0}%,{max(c_off-0.01,s0)}%{{opacity:1}}"
            f"{c_off}%,100%{{opacity:0}}}}"
            f".m{idx}{{animation:w{idx} {T}s steps({n}) infinite}}"
            f".c{idx}{{animation:bl 1.06s steps(1) infinite,k{idx} {T}s steps(1) infinite}}"
            f".l{idx}{{animation:o{idx} {T}s steps(1) infinite}}"
        )
        body.append(f'<mask id="m{idx}"><rect class="m{idx}" x="{X0}" y="{y-FS}" '
                    f'height="{FS*1.5}" width="0" fill="#fff"/></mask>')

        # No textLength anywhere. Safari scales tspans unpredictably under
        # lengthAdjust, crushing some lines and stretching others. The cursor
        # is a real character at the end of the run instead, so the engine
        # positions it exactly, whatever advance the font actually has.
        def tspan(txt, col):
            return f'<tspan fill="{col}">{esc(txt)}</tspan>'

        parts = []
        if kind == "cmd":
            parts.append(tspan(PROMPT, GREEN))
            parts.append(tspan(PS1, GREEN_DIM))
        for txt, col in segs:
            parts.append(tspan(txt, col))

        parts.append(f'<tspan class="c{idx}">&#9608;</tspan>')
        body.append(f'<text class="t l{idx}" x="{X0}" y="{y}" '
                    f'mask="url(#m{idx})">{"".join(parts)}</text>')
        y += LH

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}" role="img" '
           f'aria-label="Terminal: Mayukh Das, System Architect Intern at Eccoi, '
           f'Master of Computing at ANU, ex-Accenture.">'
           f'<style>{"".join(css)}</style>{"".join(body)}</svg>')
    return svg


def ffn():
    """Transformer feed-forward block: d -> 4d -> d, with the residual bypass.

    A forward pass propagates left to right. Stage k lights every edge from
    layer k to layer k+1 and runs a pulse along it, then the receiving layer
    brightens. The residual arc carries its own pulse the whole way, which is
    the point of it: the signal skips the block entirely.
    """
    CX = [676.0, 812.0, 948.0]
    SIZES = [3, 12, 3]                # literally the 4x expansion: 3 -> 12 -> 3
    SPACING = [44.0, 18.0, 44.0]
    YMID = 186.0
    STAGE = 0.85                      # seconds per layer transition
    T = len(CX) * STAGE               # two transitions plus a beat to reset

    ys = [[YMID + (i - (n - 1) / 2.0) * sp for i in range(n)]
          for n, sp in zip(SIZES, SPACING)]

    def pct(x):
        return round(100.0 * x / T, 3)

    css, out = [], ['<g opacity="0.92">']
    css.append("@keyframes flow{from{stroke-dashoffset:100}to{stroke-dashoffset:0}}"
               f".fl{{animation:flow {STAGE:.2f}s linear infinite}}")

    # resting weights: every connection, drawn faintly
    for k in range(len(CX) - 1):
        for y1 in ys[k]:
            for y2 in ys[k + 1]:
                out.append(f'<line x1="{CX[k]}" y1="{y1:.1f}" x2="{CX[k+1]}" y2="{y2:.1f}" '
                           f'stroke="{BORDER_HI}" stroke-width="0.7" opacity="0.28"/>')

    # residual: around the block, not through it
    rt = YMID - 122
    res = (f"M{CX[0]-30:.0f} {YMID}C{CX[0]-30:.0f} {rt} {CX[2]+30:.0f} {rt} "
           f"{CX[2]+30:.0f} {YMID}")
    out.append(f'<path d="{res}" fill="none" stroke="{BORDER_HI}" stroke-width="1" '
               f'opacity="0.5" stroke-dasharray="4 4"/>')
    out.append(f'<path class="fl" d="{res}" pathLength="100" fill="none" stroke="{GREEN}" '
               f'stroke-width="1.8" stroke-linecap="round" stroke-dasharray="12 88" '
               f'opacity="0.75" style="animation-duration:{T:.2f}s"/>')

    # the forward pass, one stage per transition
    for k in range(len(CX) - 1):
        s0, s1 = pct(k * STAGE), pct((k + 1) * STAGE)
        css.append(
            f"@keyframes s{k}{{0%,{max(s0-0.3,0)}%{{opacity:0}}{s0}%,{max(s1-0.3,s0)}%"
            f"{{opacity:1}}{s1}%,100%{{opacity:0}}}}"
            f".s{k}{{animation:s{k} {T}s linear infinite}}")
        out.append(f'<g class="s{k}">')
        for y1 in ys[k]:
            for y2 in ys[k + 1]:
                seg = f'x1="{CX[k]}" y1="{y1:.1f}" x2="{CX[k+1]}" y2="{y2:.1f}"'
                out.append(f'<line {seg} stroke="{CYAN}" stroke-width="0.9" opacity="0.35"/>')
                out.append(f'<line class="fl" {seg} pathLength="100" stroke="{CYAN}" '
                           f'stroke-width="1.8" stroke-linecap="round" stroke-dasharray="16 84"/>')
        out.append("</g>")

    # units; each layer lights as the pass reaches it
    for k, col in enumerate(ys):
        s0 = pct(max(k * STAGE - 0.12, 0))
        s1 = pct(min((k + 1) * STAGE, T))
        css.append(
            f"@keyframes u{k}{{0%,{max(s0-0.3,0)}%{{r:3;fill:{GREEN_DIM}}}"
            f"{s0}%,{max(s1-0.3,s0)}%{{r:4.6;fill:{CYAN}}}{s1}%,100%{{r:3;fill:{GREEN_DIM}}}}}"
            f".u{k}{{animation:u{k} {T}s steps(1) infinite}}")
        for y in col:
            out.append(f'<circle class="u{k}" cx="{CX[k]}" cy="{y:.1f}" r="3" fill="{GREEN_DIM}"/>')

    out.append(f'<text x="{CX[0]-30:.0f}" y="{max(ys[1])+34:.0f}" font-size="10.5" '
               f'fill="{MUTED}" opacity="0.65" '
               f'font-family="ui-monospace,Menlo,Consolas,monospace">'
               f'feed-forward &#183; d &#8594; 4d &#8594; d</text>')
    out.append("</g>")
    return f'<style>{"".join(css)}</style>' + "".join(out)


if __name__ == "__main__":
    import sys
    open(sys.argv[1], "w").write(build())
    print("wrote", sys.argv[1])
