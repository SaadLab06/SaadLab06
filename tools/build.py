#!/usr/bin/env python3
"""Builds assets/*.svg for the profile README.  Run: python tools/build.py

GitHub shows README images in a sandbox: no scripts, no web fonts. So display
type (Anton, Kaushan Script, the two faces saadlabri.com uses) is converted to
paths here, and all motion is plain CSS keyframes inside each SVG.
"""
import html
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets')

# Theme tokens, copied from portfolio-v3/src/index.css
BG, PANEL, LINE = '#09090c', '#101015', '#1d1d25'
INK, MUTE, DIM = '#f2f2f4', '#8a8a96', '#55555f'
RED, BLUE = '#f0282d', '#0d99ff'
W = 880          # README column width, so 1 unit is 1 px on desktop
RAIL = 44        # x of the red thread that runs through every panel
X0, X1 = 68, 848  # content left and right edges
SANS = "'Inter Tight',Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

esc = lambda s: html.escape(s, quote=False)
num = lambda v: ('%.1f' % v).rstrip('0').rstrip('.')


class Face:
    def __init__(self, file):
        self.f = TTFont(os.path.join(HERE, 'fonts', file))
        self.gs, self.cmap = self.f.getGlyphSet(), self.f.getBestCmap()
        self.upm, self.hmtx = self.f['head'].unitsPerEm, self.f['hmtx']

    def run(self, s, size, x=0, y=0, track=0):
        """One path per visible glyph, plus the advance width of the string."""
        sc, out, cx = size / self.upm, [], x
        for ch in s:
            gn = self.cmap[ord(ch)]  # KeyError means the font lacks the glyph: change the copy
            pen = SVGPathPen(self.gs, ntos=num)
            self.gs[gn].draw(TransformPen(pen, (sc, 0, 0, -sc, cx, y)))
            if pen.getCommands():
                out.append(pen.getCommands())
            cx += self.hmtx[gn][0] * sc + track
        return out, cx - x - (track if s else 0)

    def width(self, s, size, track=0):
        return self.run(s, size, track=track)[1]


ANTON = Face('anton-latin-400-normal.woff')
SCRIPT = Face('kaushan-script-latin-400-normal.woff')
CAP = 1760 / 2048  # Anton cap height in em


def P(s, size, x, y, fill=INK, anchor='start', face=ANTON, track=0, cls='', delay=None, letters=None):
    """Display text as paths. letters=(start, stagger) draws each glyph in, outline first."""
    w = face.width(s, size, track)
    if anchor == 'end':
        x -= w
    elif anchor == 'middle':
        x -= w / 2
    ds, _ = face.run(s, size, x, y, track)
    if letters:
        t0, step = letters
        return ''.join(
            f'<path class="lt" pathLength="1" fill="{fill}" style="animation-delay:{t0 + i * step:.2f}s" d="{d}"/>'
            for i, d in enumerate(ds))
    st = f' style="animation-delay:{delay}s"' if delay is not None else ''
    c = f' class="{cls}"' if cls else ''
    return f'<path{c}{st} fill="{fill}" d="{"".join(ds)}"/>'


def T(x, y, s, size=13, fill=MUTE, weight=400, anchor='start', cls='', delay=None, extra=''):
    """System-font text."""
    a = f' text-anchor="{anchor}"' if anchor != 'start' else ''
    c = f' class="{cls}"' if cls else ''
    st = f' style="animation-delay:{delay}s"' if delay is not None else ''
    wt = f' font-weight="{weight}"' if weight != 400 else ''
    return f'<text x="{x}" y="{y}" font-size="{size}"{wt} fill="{fill}"{a}{c}{st}{extra}>{esc(s)}</text>'


def typed(x, y, s, start, cps=70, size=13, fill=MUTE, weight=400, anchor='start', extra=''):
    """Text that types itself in, one character at a time."""
    a = f' text-anchor="{anchor}"' if anchor != 'start' else ''
    wt = f' font-weight="{weight}"' if weight != 400 else ''
    spans = ''.join(
        f'<tspan class="c" style="animation-delay:{start + i / cps:.2f}s">{esc(ch)}</tspan>'
        for i, ch in enumerate(s))
    return f'<text xml:space="preserve" x="{x}" y="{y}" font-size="{size}"{wt} fill="{fill}"{a}{extra}>{spans}</text>'


def sel(x, y, w, h, start, dur):
    """A design-tool selection box that flashes around a layer while it is built."""
    hs = ''.join(f'<rect x="{hx - 3.5}" y="{hy - 3.5}" width="7" height="7" fill="#fff" stroke="{BLUE}" stroke-width="1.5"/>'
                 for hx, hy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)))
    label = f'{w:.0f} × {h:.0f}'
    lw = len(label) * 5.6 + 12
    return (f'<g class="sel" style="animation-duration:{dur}s;animation-delay:{start}s">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{BLUE}" stroke-width="1.5"/>{hs}'
            f'<rect x="{x + w / 2 - lw / 2}" y="{y + h + 7}" width="{lw}" height="16" rx="3" fill="{BLUE}"/>'
            f'<text x="{x + w / 2}" y="{y + h + 18.5}" text-anchor="middle" font-size="10" font-weight="600" fill="#fff">{label}</text></g>')


def agent(i, name, color, pts, total):
    """A named cursor that travels between layers. pts = [(seconds, x, y), ...]."""
    kf = ''.join(f'{t / total * 100:.2f}%{{transform:translate({x}px,{y}px)}}' for t, x, y in pts)
    css = f'@keyframes ag{i}{{{kf}}}.ag{i}{{animation:ag{i} {total}s cubic-bezier(.3,.7,.2,1) both}}'
    w = len(name) * 6 + 12
    svg = (f'<g class="agent ag{i}"><g class="bob" style="animation-delay:{total + i * .4}s">'
           f'<path d="M0 0v15.5l4.2-3.6 3 6.6 2.6-1.2-3-6.4h5.6z" fill="{color}" stroke="{BG}"/>'
           f'<rect x="13" y="15" width="{w}" height="17" rx="4" fill="{color}"/>'
           f'<text x="{13 + w / 2}" y="27" text-anchor="middle" font-size="10" font-weight="600" fill="{BG}">{name}</text></g></g>')
    return svg, css


def packet_x(x0, x1, y, dur, name):
    """A red packet that runs along a horizontal line, forever."""
    css = (f'@keyframes {name}{{0%{{transform:translateX(0);opacity:0}}6%,94%{{opacity:1}}'
           f'100%{{transform:translateX({x1 - x0}px);opacity:0}}}}')
    svg = (f'<g class="pk" style="animation:{name} {dur}s linear infinite">'
           f'<circle cx="{x0}" cy="{y}" r="7" fill="{RED}" fill-opacity=".22"/><circle cx="{x0}" cy="{y}" r="3" fill="{RED}"/></g>')
    return svg, css


def packet_y(h, dur):
    """The same packet, falling down the rail."""
    css = (f'@keyframes fall{{0%{{transform:translateY(0);opacity:0}}6%,94%{{opacity:1}}'
           f'100%{{transform:translateY({h}px);opacity:0}}}}')
    svg = (f'<g class="pk" style="animation:fall {dur}s linear infinite">'
           f'<circle cx="{RAIL + .5}" cy="0" r="7" fill="{RED}" fill-opacity=".22"/><circle cx="{RAIL + .5}" cy="0" r="3" fill="{RED}"/></g>')
    return svg, css


def node(y, live=False, delay=0):
    ring = f'<circle class="ring" cx="{RAIL + .5}" cy="{y}" r="5" fill="none" stroke="{RED}" stroke-width="1.5"/>' if live else ''
    return (f'<g class="pop" style="animation-delay:{delay}s">{ring}'
            f'<circle cx="{RAIL + .5}" cy="{y}" r="5" fill="{BG}" stroke="{RED}" stroke-width="1.5"/>'
            + (f'<circle cx="{RAIL + .5}" cy="{y}" r="2" fill="{RED}"/>' if live else '') + '</g>')


def head(n, title, right=''):
    """Section header: number, slash, title, on the rail."""
    w = ANTON.width(n, 20)
    out = node(46, delay=.2) + P(n, 20, X0, 54, RED, cls='rise', delay=.2)
    out += P('/', 20, X0 + w + 9, 54, DIM, cls='rise', delay=.25)
    out += P(title, 20, X0 + w + 9 + ANTON.width('/', 20) + 9, 54, INK, cls='rise', delay=.3)
    return out + right


BASE = f"""
text{{font-family:{SANS}}}
.k{{font-weight:700;letter-spacing:1.5px}}
.mono{{font-family:{MONO}}}
@keyframes rise{{from{{opacity:0;transform:translateY(10px)}}}}
@keyframes fade{{from{{opacity:0}}}}
@keyframes pop{{from{{opacity:0;transform:scale(.6)}}}}
@keyframes on{{from{{fill-opacity:0}}}}
@keyframes letter{{0%{{stroke-opacity:1;stroke-dashoffset:1;fill-opacity:0}}60%{{stroke-opacity:1;stroke-dashoffset:0;fill-opacity:0}}100%{{stroke-opacity:0;stroke-dashoffset:0;fill-opacity:1}}}}
@keyframes grow{{from{{transform:scaleY(0)}}}}
@keyframes ring{{0%{{transform:scale(1);opacity:.8}}100%{{transform:scale(3.4);opacity:0}}}}
@keyframes blink{{50%{{opacity:.2}}}}
@keyframes bob{{50%{{transform:translateY(-4px)}}}}
@keyframes sel{{0%{{opacity:0}}8%,86%{{opacity:1}}100%{{opacity:0}}}}
@keyframes hit{{0%,14%{{fill:{RED};stroke:{RED}}}40%,100%{{fill:{BG};stroke:#3a3a46}}}}
@keyframes boxhit{{0%,16%{{stroke:{RED}}}45%,100%{{stroke:{LINE}}}}}
.rise{{animation:rise .6s cubic-bezier(.2,.8,.2,1) both}}
.fade{{animation:fade .7s ease both}}
.pop{{animation:pop .5s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:center}}
.c{{animation:on 1ms both}}
.lt{{stroke:{BLUE};stroke-width:1.4;stroke-dasharray:1;stroke-opacity:0;animation:letter 1.1s cubic-bezier(.65,0,.35,1) both}}
.rail{{transform-box:fill-box;transform-origin:top;animation:grow .9s cubic-bezier(.65,0,.35,1) both}}
.ring{{transform-box:fill-box;transform-origin:center;animation:ring 2.2s ease-out infinite}}
.blink{{animation:blink 1.6s ease-in-out infinite}}
.bob{{animation:bob 3.6s ease-in-out infinite}}
.sel{{opacity:0;animation:sel 2s linear both}}
.hit{{fill:{BG};stroke:#3a3a46;animation:hit 5s linear infinite}}
.boxhit{{animation:boxhit 6s linear infinite}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.agent,.pk{{display:none}}}}
"""


def panel(name, h, title, body, css='', defs='', rail_top=0):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{html.escape(title)}">'
           f'<title>{esc(title)}</title><style>{BASE}{css}</style>'
           f'<defs><pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#fff" fill-opacity=".07"/></pattern>'
           f'<clipPath id="clip"><rect width="{W}" height="{h}" rx="14"/></clipPath>{defs}</defs>'
           f'<g clip-path="url(#clip)"><rect width="{W}" height="{h}" fill="{BG}"/><rect width="{W}" height="{h}" fill="url(#dots)"/>'
           f'<rect class="rail" x="{RAIL}" y="{rail_top}" width="1" height="{h - rail_top}" fill="{RED}" fill-opacity=".7"/>'
           f'{body}</g><rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="13.5" fill="none" stroke="{LINE}"/></svg>')
    assert chr(0x2014) not in svg, f'em dash in {name}'
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n') as f:
        f.write(svg)
    print(f'{name:14} {len(svg) / 1024:6.1f} KB')


# ---------------------------------------------------------------- hero
def hero():
    H, END = 440, 5.6
    b, css = [], []
    # rulers, like the design canvas the site builds itself on
    defs = ('<pattern id="tx" width="10" height="16" patternUnits="userSpaceOnUse"><path d="M.5 11v5" stroke="#3a3a46"/></pattern>'
            '<pattern id="tx5" width="50" height="16" patternUnits="userSpaceOnUse"><path d="M.5 6v10" stroke="#3a3a46"/></pattern>'
            '<pattern id="ty" width="16" height="10" patternUnits="userSpaceOnUse"><path d="M11 .5h5" stroke="#3a3a46"/></pattern>'
            '<pattern id="ty5" width="16" height="50" patternUnits="userSpaceOnUse"><path d="M6 .5h10" stroke="#3a3a46"/></pattern>')
    b.append(f'<rect width="{W}" height="16" fill="#0e0e13"/><rect width="16" height="{H}" fill="#0e0e13"/>'
             f'<rect width="{W}" height="16" fill="url(#tx)"/><rect width="{W}" height="16" fill="url(#tx5)"/>'
             f'<rect width="16" height="{H}" fill="url(#ty)"/><rect width="16" height="{H}" fill="url(#ty5)"/>'
             f'<rect width="16" height="16" fill="#0e0e13"/><path d="M0 16.5H{W}M16.5 0V{H}" stroke="{LINE}"/>')
    b.append(''.join(f'<text x="{x + 3}" y="8" font-size="7" fill="{DIM}">{x}</text>' for x in range(100, W, 100)))

    b.append(typed(X0, 56, 'AI AUTOMATION ENGINEER / WEB DEVELOPER', .3, size=11, fill=RED, weight=700, extra=' letter-spacing="1.5"'))
    b.append(typed(X0, 73, 'SYSTEMS THAT SURVIVE REAL DATA', .9, size=11, fill=MUTE, weight=700, extra=' letter-spacing="1.5"'))
    b.append(typed(X1, 56, 'Every system, built to hold.', 1.5, cps=40, size=12.5, anchor='end'))

    # "Hello, I'm" in the site's script face, tilted the same 4 degrees
    b.append(f'<g transform="rotate(-4 {X0} 140)">{P("Hello, I’m", 34, X0 + 2, 140, INK, face=SCRIPT, letters=(.6, .05))}</g>')

    size, base = 104, 252
    name_w = ANTON.width('SAAD LABRI', size)
    b.append(P('SAAD LABRI', size, X0, base, INK, letters=(1.0, .1)))
    b.append(P('.', size, X0 + name_w + 3, base, RED, letters=(2.0, 0)))
    full_w = name_w + 3 + ANTON.width('.', size)
    cap = size * CAP
    b.append(sel(X0 - 6, base - cap - 6, full_w + 12, cap + 12, .8, 2.3))

    b.append(P('AI AUTOMATION', 25, X0, 292, RED, cls='rise', delay=2.8))
    b.append(P('ENGINEER', 25, X0, 321, RED, cls='rise', delay=2.95))
    l1 = 'I build agents and pipelines that take repetitive work off a team,'
    b.append(typed(X0, 353, l1, 3.1, cps=95, size=14, fill=INK, extra=' opacity=".8"'))
    b.append(typed(X0, 373, 'and keep running when nobody is watching.', 3.1 + len(l1) / 95, cps=95, size=14, fill=INK, extra=' opacity=".8"'))

    # the three numbers the site leads with
    for i, (v, a, c) in enumerate((('40+', 'PROJECTS', 'DELIVERED'), ('100+', 'WORKFLOWS', 'IN PRODUCTION'), ('15', 'SITES AND APPS', 'LIVE TODAY'))):
        y, d = 196 + i * 62, 3.3 + i * .3
        b.append(f'<g class="pop" style="animation-delay:{d}s">{P(v, 44, 740, y, RED, anchor="end")}'
                 f'{T(752, y - 21, a, 10, MUTE, 700, extra=" letter-spacing=\"1\"")}{T(752, y - 7, c, 10, MUTE, 700, extra=" letter-spacing=\"1\"")}</g>')

    # bottom bar, with a packet that never stops moving
    pk, pcss = packet_x(262, 660, 408.5, 4.5, 'pkh')
    css.append(pcss)
    b.append(f'<g class="fade" style="animation-delay:4.4s"><circle cx="{X0 + 3}" cy="408.5" r="3" fill="{RED}"/>'
             f'{T(X0 + 13, 412, "ORAN, ALGERIA · REMOTE", 10.5, MUTE, 700, extra=" letter-spacing=\"1.4\"")}'
             f'<path d="M262 408.5H660" stroke="{LINE}"/>{pk}'
             f'{T(X1, 412, "SELECTED WORK 2024–2026", 10.5, MUTE, 700, "end", extra=" letter-spacing=\"1.4\"")}</g>')

    # the crew: same names and colours as the agents on saadlabri.com
    nx = X0 + full_w + 8
    for i, (nm, col, pts) in enumerate((
        ('Layout', '#ff5a64', [(0, 910, 300), (.8, nx, 256), (3.0, nx, 256), (3.4, 232, 300), (4.2, 232, 300), (4.7, 236, 414), (5.0, 236, 414), (END, 262, 276)]),
        ('Copy', '#2ad4f0', [(0, -60, 90), (.3, 356, 58), (1.3, 356, 58), (1.6, 668, 62), (2.6, 668, 62), (3.1, 500, 376), (4.6, 500, 376), (END, 520, 330)]),
        ('Motion', '#3ee0a0', [(0, 910, 120), (2.8, 910, 120), (3.3, 770, 204), (3.6, 770, 266), (3.9, 770, 328), (4.4, 770, 328), (END, 566, 150)]),
    )):
        s, c = agent(i, nm, col, pts, END)
        b.append(s)
        css.append(c)
    panel('hero.svg', H, 'Saad Labri, AI automation engineer. Systems that survive real data.', ''.join(b), ''.join(css), defs, rail_top=16)


# ---------------------------------------------------------------- 01 about me
def rows_block(rows, y0, pitch=58, t0=.7, live='last'):
    """Rows hung on the rail: a mono label, a title, one line of detail."""
    out = []
    for i, (when, title, desc) in enumerate(rows):
        y, d = y0 + i * pitch, t0 + i * .22
        lv = live == 'all' or i == len(rows) - 1
        out.append(node(y - 5, lv, d))
        out.append(f'<g class="rise" style="animation-delay:{d:.2f}s">'
                   f'<text class="mono k" x="{X0}" y="{y}" font-size="11" fill="{RED if lv else MUTE}">{when}</text>'
                   f'{T(190, y, title, 15, INK, 600)}{T(190, y + 20, desc, 13, MUTE)}</g>')
    return ''.join(out)


def about():
    rows = [
        ('DEGREE', 'Industrial maintenance and safety engineering', 'Planning for failure became a habit. Final project: predictive maintenance on vibration data.'),
        ('2024', 'Freelance for French and Maghreb businesses', 'Agents that write to live order systems, each behind a validator and a confirmation step.'),
        ('2025', 'A procurement engine for a public transport operator', 'Supplier quotes in, a scored recommendation out. Matching went from hours to seconds.'),
        ('2025 / 2026', 'The AI layer for four businesses under one owner', 'Use case selection, build, deployment, and the method their staff follow afterwards.'),
        ('NOW', 'Agents, pipelines and internal platforms, built solo', 'For teams in Europe, North Africa and the US. Client names stay private.'),
    ]
    y0 = 196
    H = y0 + 58 * (len(rows) - 1) + 20 + 30
    b = [head('01', 'ABOUT ME')]
    for i, s in enumerate(('I am Saad, an engineer from Oran, Algeria. I trained in industrial maintenance, where you assume',
                           'the machine will fail and plan for it. Today I build AI agents, automation pipelines and full web',
                           'apps the same way. I design what I build, and I work in English, French and Arabic.')):
        b.append(T(X0, 96 + i * 22, s, 15, INK, cls='rise', delay=.4 + i * .1, extra=' opacity=".88"'))
    b.append(rows_block(rows, y0))
    pk, pcss = packet_y(H, 6)
    panel('about.svg', H, 'About me: an engineer from Oran, Algeria, from industrial maintenance to production AI systems.', ''.join(b) + pk, pcss)


# ---------------------------------------------------------------- 02 what I do
def does():
    tiles = [
        ('AI AGENTS', ('Agents with real write access to live systems,', 'each behind a validator and a human approval.'), 'Claude API · MCP · RAG · multi-agent'),
        ('AUTOMATION', ('100+ workflows in production: intake, routing,', 'sync and alerts. Mostly self-hosted n8n.'), 'n8n · webhooks · scrapers · OCR'),
        ('WEB APPS', ('Full products end to end: interface, database,', 'auth, deploy, and the monitoring afterwards.'), 'React · TypeScript · Postgres · Workers'),
        ('E-COMMERCE', ('Storefronts, sync plugins and ops tooling', 'for stores that ship every day.'), 'Shopify · WooCommerce · WordPress'),
        ('REAL-WORLD SYSTEMS', ('Scanners, cameras and label printers wired', 'into software that people run by hand.'), 'Python · computer vision · hardware'),
        ('TEACHING', ('Author and instructor of a 13-module course', 'on AI automation.'), '13 modules · 2026'),
    ]
    tw, th, gx, gy, y0 = 383, 118, 14, 14, 82
    H = y0 + 3 * th + 2 * gy + 28
    css = f'@keyframes sw{{to{{transform:translateX({tw - 72}px)}}}}.sw{{animation:sw 4.5s ease-in-out infinite alternate}}'
    b = [head('02', 'WHAT I DO')]
    for i, (title, desc, tools) in enumerate(tiles):
        x, y = X0 + (i % 2) * (tw + gx), y0 + (i // 2) * (th + gy)
        b.append(f'<g class="rise" style="animation-delay:{.5 + i * .12:.2f}s">'
                 f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="10" fill="{PANEL}" stroke="{LINE}"/>'
                 f'<rect class="sw" style="animation-delay:{-i * .9:.1f}s" x="{x + 16}" y="{y}" width="40" height="2" fill="{RED}"/>'
                 f'{P(title, 22, x + 16, y + 40, INK)}'
                 f'{T(x + 16, y + 63, desc[0], 12.5, MUTE)}{T(x + 16, y + 80, desc[1], 12.5, MUTE)}'
                 f'<text class="mono" x="{x + 16}" y="{y + 102}" font-size="9.5" fill="{DIM}">{esc(tools)}</text></g>')
    panel('does.svg', H, 'What I do: AI agents, automation, web apps, e-commerce, real-world systems, teaching.', ''.join(b), css)


# ---------------------------------------------------------------- 03 right now
def rightnow():
    rows = [
        ('BUILDING', 'An internal operations platform for a US company', 'Sole builder, in production. The details stay under NDA.'),
        ('RUNNING', 'A home server with self-hosted n8n and Coolify', 'My own automations live there, with an outside check watching the uptime.'),
        ('TINKERING', 'Local AI models, 3D scenes in Blender, motion graphics in code', 'Where I try new tools before they reach client work.'),
    ]
    y0 = 100
    H = y0 + 58 * (len(rows) - 1) + 20 + 30
    pk, pcss = packet_y(H, 5)
    panel('rightnow.svg', H, 'Right now: building a platform for a US company, running a home server, tinkering with local models.',
          head('03', 'RIGHT NOW') + rows_block(rows, y0, t0=.5, live='all') + pk, pcss)


# ---------------------------------------------------------------- 04 things I built
def shipped():
    tiles = [
        ('PROCUREMENT · OCR', 'QUOTE-TO-TCO ENGINE', ('Supplier quotes in, a ranked cost comparison out.', 'One model reads, a second checks, the ERP stores.'),
         '3 MIN', 'QUOTE TO TCO', ('OCR', 'Validate', 'Decide', 'Output')),
        ('MULTI-AGENT · SAAS', 'TWO-AGENT DM DESK', ('Brain decides what is true. Voice writes the reply', 'and never invents a claim.'),
         '3', 'CHANNELS', ('Message', 'Brain', 'Voice', 'Reply')),
        ('INDUSTRIAL · AUTOMATION', 'PACKING LINE CONTROL', ('Scanner, pedal, cameras and printers as one flow.', 'No parcel is validated without photo proof.'),
         '797/797', 'PARCELS WITH A PHOTO', ('Scan', 'Photo', 'Label', 'Check')),
        ('E-COMMERCE · AI OPS', 'WOOCOMMERCE OPS', ('A daily order sheet, SMS cart recovery, and a bot', 'where Claude Vision checks every packed box.'),
         '12%', 'CART RECOVERY', ('Orders', 'Sheet', 'SMS', 'Vision')),
        ('PERSONAL · LEAD GEN', 'OUTREACH ENGINE', ('Finds small businesses, drafts value-first emails.', 'Sends nothing until I approve it.'),
         '0', 'SENDS WITHOUT APPROVAL', ('Find', 'Qualify', 'Draft', 'Approve')),
        ('PRODUCT · LICENSING', 'DZ-POS', ('A point of sale in French and Arabic, with a', 'license server that verifies offline.'),
         'RS256', 'OFFLINE AUTH', ('Sale', 'Invoice', 'License', 'Sync')),
    ]
    tw, th, gx, gy, y0 = 383, 152, 14, 14, 82
    H = y0 + 3 * th + 2 * gy + 28
    right = T(X1, 52, 'SELECTED SYSTEMS, ALL STILL RUNNING', 10.5, MUTE, 700, 'end', cls='fade', delay=.4, extra=' letter-spacing="1.4"')
    b, css = [head('04', 'THINGS I BUILT', right)], []
    for i, (tag, title, desc, val, lab, steps) in enumerate(tiles):
        x, y = X0 + (i % 2) * (tw + gx), y0 + (i // 2) * (th + gy)
        lx0, lx1, ly = x + 22, x + tw - 22, y + 122
        pk, pcss = packet_x(lx0, lx1, ly, 5, f'pk{i}')
        css.append(pcss)
        dots = ''
        for j, s in enumerate(steps):
            px = lx0 + j * (lx1 - lx0) / 3
            anchor = ('start', 'middle', 'middle', 'end')[j]
            tx = (x + 16, px, px, x + tw - 16)[j]
            dots += (f'<circle class="hit" style="animation-delay:{j * 5 / 3 - .2 + i * .35:.2f}s" cx="{px}" cy="{ly}" r="4"/>'
                     f'<text class="mono" x="{tx}" y="{ly + 17}" font-size="9.5" fill="{DIM}" text-anchor="{anchor}">{s}</text>')
        b.append(f'<g class="rise" style="animation-delay:{.5 + i * .12:.2f}s">'
                 f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="10" fill="{PANEL}" stroke="{LINE}"/>'
                 f'{T(x + 16, y + 25, tag, 9.5, RED, 700, extra=" letter-spacing=\"1.3\"")}'
                 f'{P(title, 22, x + 16, y + 55, INK)}'
                 f'{P(val, 24, x + tw - 16, y + 36, RED, anchor="end")}'
                 f'{T(x + tw - 16, y + 51, lab, 9, MUTE, 700, "end", extra=" letter-spacing=\"1\"")}'
                 f'{T(x + 16, y + 78, desc[0], 12.5, MUTE)}{T(x + 16, y + 95, desc[1], 12.5, MUTE)}'
                 f'<path d="M{lx0} {ly}H{lx1}" stroke="#3a3a46"/>'
                 f'<g style="animation-delay:{i * .35:.2f}s">{pk.replace("infinite", f"infinite;animation-delay:{i * .35:.2f}s")}</g>{dots}</g>')
    panel('shipped.svg', H, 'Things I built: six selected systems, from a procurement engine to a point of sale.', ''.join(b), ''.join(css))


# ---------------------------------------------------------------- 05 toolkit
def toolkit():
    groups = [
        ('AI', ['CLAUDE API', 'CLAUDE CODE', 'MCP', 'RAG', 'MULTI-AGENT', 'LOCAL MODELS']),
        ('AUTOMATION', ['N8N', 'WEBHOOKS', 'PLAYWRIGHT', 'SCRAPING', 'OCR']),
        ('WEB', ['REACT', 'NEXT.JS', 'TYPESCRIPT', 'TAILWIND', 'REACT ROUTER']),
        ('BACKEND', ['PYTHON', 'FASTAPI', 'NODE.JS', 'PHP', 'POSTGRESQL', 'SUPABASE']),
        ('INFRA', ['CLOUDFLARE WORKERS', 'DOCKER', 'COOLIFY', 'GITHUB ACTIONS', 'LINUX']),
        ('COMMERCE', ['SHOPIFY', 'WOOCOMMERCE', 'WORDPRESS', 'ODOO']),
        ('DESIGN', ['FIGMA', 'MOTION', 'BLENDER']),
    ]
    y0, pitch = 100, 38
    H = y0 + pitch * (len(groups) - 1) + 12 + 30
    b, n = [head('05', 'TOOLKIT')], 0
    for r, (label, items) in enumerate(groups):
        y, x = y0 + r * pitch, 190
        b.append(node(y - 4, delay=.4 + r * .08))
        b.append(f'<text class="mono k rise" style="animation-delay:{.4 + r * .08:.2f}s" x="{X0}" y="{y}" font-size="10.5" fill="{MUTE}">{label}</text>')
        for it in items:
            w = ANTON.width(it, 13, .5) + 22
            b.append(f'<g class="pop" style="animation-delay:{.5 + n * .04:.2f}s">'
                     f'<rect class="boxhit" style="animation-duration:9s;animation-delay:{(n * 2.3) % 9:.1f}s" x="{x}" y="{y - 17}" width="{num(w)}" height="25" rx="6" fill="{PANEL}" stroke="{LINE}"/>'
                     f'{P(it, 13, x + 11, y, INK, track=.5)}</g>')
            x += w + 8
            n += 1
    panel('toolkit.svg', H, 'Toolkit: Claude API, Claude Code, MCP, RAG, n8n, React, TypeScript, Python, FastAPI, PostgreSQL, Supabase, Cloudflare Workers, Docker, Shopify, WordPress, Figma.', ''.join(b))


# ---------------------------------------------------------------- 06 how I build
def method():
    steps = [
        ('THE EXAMPLE', ('Send the worst document.', 'One concrete case beats', 'a long brief.')),
        ('THE MAP', ('Score each task on', 'volume, rule stability and', 'the cost of being wrong.')),
        ('THE BUILD', ('Models read messy', 'reality. Plain code does', 'dedup, validation, writes.')),
        ('THE GUARDRAILS', ('Writes sit behind a', 'validator and approval.', 'Failures go to a queue.')),
        ('THE HANDOVER', ('A one-page runbook:', 'what runs, where, what', 'it costs, who to call.')),
    ]
    H, ly, col = 236, 98, (X1 - X0) / 5
    pk, pcss = packet_x(X0, X1, ly, 7, 'pkm')
    b = [head('06', 'HOW I BUILD'), f'<g class="fade" style="animation-delay:.5s"><path d="M{X0} {ly}H{X1}" stroke="#3a3a46"/>{pk}</g>']
    for i, (t, lines) in enumerate(steps):
        x = X0 + i * col
        b.append(f'<g class="rise" style="animation-delay:{.6 + i * .15:.2f}s">'
                 f'<circle class="hit" style="animation-duration:7s;animation-delay:{(i * col + 6) / (X1 - X0) * 7:.2f}s" cx="{x + 6}" cy="{ly}" r="5"/>'
                 f'<text class="mono k" x="{x}" y="{ly + 30}" font-size="10" fill="{RED}">0{i + 1}</text>'
                 f'{P(t, 18, x, ly + 56, INK)}'
                 + ''.join(T(x, ly + 78 + j * 16, s, 11.5, MUTE) for j, s in enumerate(lines)) + '</g>')
    panel('method.svg', H, 'How I build: the example, the map, the build, the guardrails, the handover.', ''.join(b), pcss)


# ---------------------------------------------------------------- 07 contact
def contact():
    H = 282
    quote = f'<g transform="rotate(-2 {X1} 60)">{P("I don’t ship demos that fall over in production.", 19, X1, 60, INK, anchor="end", face=SCRIPT, cls="fade", delay=1.4)}</g>'
    b = [head('07', 'CONTACT', quote)]
    b.append(P('SHIP IT.', 62, X0, 150, INK, letters=(.4, .07)))
    b.append(P('KEEP IT RUNNING.', 62, X0, 216, RED, letters=(.9, .05)))
    for i, (k, v) in enumerate((('SITE', 'saadlabri.com'), ('EMAIL', 'contact@saadlabri.com'),
                                ('LANGUAGES', 'English · Français · العربية'), ('BASED IN', 'Oran, Algeria · Remote'))):
        y = 124 + i * 27
        b.append(f'<g class="rise" style="animation-delay:{1.5 + i * .12:.2f}s">'
                 f'{T(548, y, k, 9.5, MUTE, 700, extra=" letter-spacing=\"1.3\"")}{T(640, y, v, 14, INK, 600 if i < 2 else 400)}</g>')

    # principles marquee: measured in Anton so the loop is seamless
    tools = ['PLAN FOR FAILURE', 'VALIDATE EVERY WRITE', 'A HUMAN APPROVES', 'SELF-HOSTED', 'ONE-PAGE RUNBOOK',
             'NO DEMOS', 'SHIP IT', 'KEEP IT RUNNING']
    one, x = '', 0
    for t in tools:
        one += P(t, 14, x, 262, MUTE, track=.6)
        x += ANTON.width(t, 14, .6) + 16
        one += f'<rect x="{x:.1f}" y="254" width="4" height="4" fill="{RED}"/>'
        x += 20
    reps = f'<g id="row">{one}</g>' + ''.join(f'<use href="#row" x="{num(k * x)}"/>' for k in (1, 2))
    css = f'@keyframes mq{{to{{transform:translateX(-{num(x)}px)}}}}.mq{{animation:mq 38s linear infinite}}'
    defs = (f'<linearGradient id="fl"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="fr"><stop offset="0" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient>')
    b.append(f'<path d="M0 238.5H{W}" stroke="{LINE}"/><rect y="239" width="{W}" height="{H - 239}" fill="{BG}"/>'
             f'<g class="mq">{reps}</g>'
             f'<rect y="239" width="120" height="{H - 240}" fill="url(#fl)"/><rect x="{W - 120}" y="239" width="120" height="{H - 240}" fill="url(#fr)"/>'
             f'<rect x="{RAIL}" y="239" width="1" height="{H - 239}" fill="{RED}" fill-opacity=".7"/>')
    panel('contact.svg', H, 'Ship it. Keep it running. saadlabri.com, contact@saadlabri.com', ''.join(b), css, defs)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for build in (hero, about, does, rightnow, shipped, toolkit, method, contact):
        build()
