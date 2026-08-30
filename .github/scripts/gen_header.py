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
CW = 9.0           # forced char width (via textLength)
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
.blink{{animation:bl 1.06s steps(1) infinite;}}
@keyframes bl{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}""")

    # ---- terminal chrome ----------------------------------------------
    body.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="{BG}" stroke="{BORDER}"/>')
    body.append(f'<path d="M1 11a10 10 0 0 1 10-10h{W-22}a10 10 0 0 1 10 10v{TOP-11}H1z" fill="{BG_SOFT}"/>')
    body.append(f'<line x1="1" y1="{TOP}" x2="{W-1}" y2="{TOP}" stroke="{BORDER}"/>')
    for i, c in enumerate((RED, MUTED, GREEN_DIM)):
        body.append(f'<circle cx="{22+18*i}" cy="{TOP/2}" r="5" fill="{c}" opacity="0.85"/>')
    body.append(f'<text class="t" x="{W/2}" y="{TOP/2+4.5}" text-anchor="middle" '
                f'font-size="12" fill="{MUTED}">mayukh@github: ~/profile</text>')

    # ---- attention motif (right side) ---------------------------------
    body.append(attention())

    # ---- terminal lines -----------------------------------------------
    y = Y0
    for idx, ((kind, segs), sc) in enumerate(zip(LINES, sched)):
        if kind == "gap":
            y += LH * 0.55
            continue
        start, dur, n = sc
        full = n * CW
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
            f"@keyframes x{idx}{{0%,{s0}%{{transform:translateX(0px)}}{s1}%,99.9%{{transform:translateX({full}px)}}"
            f"100%{{transform:translateX(0px)}}}}"
            f"@keyframes o{idx}{{0%,{max(s0-0.01,0)}%{{opacity:0}}{s0}%,99.9%{{opacity:1}}100%{{opacity:0}}}}"
            f"@keyframes k{idx}{{0%,{max(s0-0.01,0)}%{{opacity:0}}{s0}%,{max(c_off-0.01,s0)}%{{opacity:1}}"
            f"{c_off}%,100%{{opacity:0}}}}"
            f".m{idx}{{animation:w{idx} {T}s steps({n}) infinite}}"
            f".c{idx}{{animation:x{idx} {T}s steps({n}) infinite,k{idx} {T}s steps(1) infinite}}"
            f".l{idx}{{animation:o{idx} {T}s steps(1) infinite}}"
        )
        body.append(f'<mask id="m{idx}"><rect class="m{idx}" x="{X0}" y="{y-FS}" '
                    f'height="{FS*1.5}" width="0" fill="#fff"/></mask>')

        # textLength goes on each tspan, not on the parent <text>: Safari and
        # Firefox do not reliably apply a parent textLength across child tspans,
        # which left the line wider than n*CW and the cursor short of its end.
        def tspan(txt, col):
            return (f'<tspan fill="{col}" textLength="{len(txt)*CW}" '
                    f'lengthAdjust="spacingAndGlyphs">{esc(txt)}</tspan>')

        parts = []
        if kind == "cmd":
            parts.append(tspan(PROMPT, GREEN))
            parts.append(tspan(PS1, GREEN_DIM))
        for txt, col in segs:
            parts.append(tspan(txt, col))

        body.append(f'<text class="t l{idx}" x="{X0}" y="{y}" '
                    f'mask="url(#m{idx})">{"".join(parts)}</text>')
        # walking cursor: the group handles position + handoff, the rect blinks
        body.append(f'<g class="c{idx}"><rect class="blink" x="{X0}" y="{y-FS+2.5}" width="{CW}" '
                    f'height="{FS}" fill="{GREEN}" opacity="0.75"/></g>')
        y += LH

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}" role="img" '
           f'aria-label="Terminal: Mayukh Das, System Architect Intern at Eccoi, '
           f'Master of Computing at ANU, ex-Accenture.">'
           f'<style>{"".join(css)}</style>{"".join(body)}</svg>')
    return svg


def attention():
    """Causal self-attention over a token row.

    The query sweeps left to right; at step j it attends to every key i <= j,
    so its fan of edges lights up and the pulse runs back along them. Edges to
    tokens ahead of the query never fire, which is the causal mask.
    """
    N = 7
    X0_A, SP = 634.0, 56.0
    Y = 270.0
    STEP = 0.9                      # seconds per query position
    T = N * STEP
    xs = [X0_A + i * SP for i in range(N)]

    def pct(x):
        return round(100.0 * x / T, 3)

    css, out = [], ['<g opacity="0.9">']
    css.append(f"@keyframes pulse{{from{{stroke-dashoffset:100}}to{{stroke-dashoffset:0}}}}"
               f".pulse{{animation:pulse {STEP*0.85:.2f}s linear infinite}}")

    # every causal edge, drawn faintly: the attention pattern at rest
    for j in range(N):
        for i in range(j):
            x1, x2 = xs[i], xs[j]
            h = 26.0 * (j - i)
            d = f"M{x1} {Y}Q{(x1+x2)/2:.1f} {Y-h:.1f} {x2} {Y}"
            out.append(f'<path d="{d}" fill="none" stroke="{BORDER_HI}" '
                       f'stroke-width="1" opacity="0.35"/>')

    # the same edges again, lit only while their query is active
    for j in range(1, N):
        s0, s1 = pct(j * STEP), pct((j + 1) * STEP)
        css.append(
            f"@keyframes q{j}{{0%,{max(s0-0.4,0)}%{{opacity:0}}{s0}%,{max(s1-0.4,s0)}%{{opacity:1}}"
            f"{s1}%,100%{{opacity:0}}}}"
            f".q{j}{{animation:q{j} {T}s linear infinite}}")
        out.append(f'<g class="q{j}">')
        for i in range(j):
            x1, x2 = xs[i], xs[j]
            h = 26.0 * (j - i)
            # drawn from the query back to the key, so the pulse runs the way
            # attention reads: query gathers from what came before it
            d = f"M{x2} {Y}Q{(x1+x2)/2:.1f} {Y-h:.1f} {x1} {Y}"
            out.append(f'<path d="{d}" fill="none" stroke="{CYAN}" stroke-width="1.3" '
                       f'opacity="0.4"/>')
            # pathLength normalises the curve to 100 units, so the travelling
            # dash is always exactly one pulse on the path whatever its real length
            out.append(f'<path class="pulse" d="{d}" pathLength="100" fill="none" '
                       f'stroke="{CYAN}" stroke-width="2" stroke-linecap="round" '
                       f'stroke-dasharray="14 86" style="animation-delay:{-0.06*i:.2f}s"/>')
        out.append("</g>")

    # tokens; the active query brightens and swells
    for j in range(N):
        s0, s1 = pct(j * STEP), pct((j + 1) * STEP)
        css.append(
            f"@keyframes t{j}{{0%,{max(s0-0.4,0)}%{{r:3;fill:{GREEN_DIM}}}"
            f"{s0}%,{max(s1-0.4,s0)}%{{r:5.2;fill:{CYAN}}}{s1}%,100%{{r:3;fill:{GREEN_DIM}}}}}"
            f".t{j}{{animation:t{j} {T}s steps(1) infinite}}")
        out.append(f'<circle class="t{j}" cx="{xs[j]}" cy="{Y}" r="3" fill="{GREEN_DIM}"/>')

    out.append(f'<text x="{xs[0]}" y="{Y+28}" font-size="10.5" fill="{MUTED}" opacity="0.65" '
               f'font-family="ui-monospace,Menlo,Consolas,monospace">causal self-attention</text>')
    out.append("</g>")
    return f'<style>{"".join(css)}</style>' + "".join(out)


if __name__ == "__main__":
    import sys
    open(sys.argv[1], "w").write(build())
    print("wrote", sys.argv[1])
