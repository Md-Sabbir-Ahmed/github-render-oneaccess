"""Build the HyperFrames project from build/script.json + build/cues.json.

    python -I -X utf8 build/build.py

Writes compositions/sNN.html (one scene per line), index.html (root timeline + voice + sfx) and job.json.
Flat 2D "Credit Bridge" style: one pastel background, soft spot circle, chibi characters with thick outlines,
caption pill with one yellow keyword, UI mockups as HTML cards. Brand colours are CSS variables in index.html.
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SC = json.loads((HERE / "script.json").read_text(encoding="utf-8"))
CUES = json.loads((HERE / "cues.json").read_text(encoding="utf-8"))
W, H = SC["width"], SC["height"]
BG, SPOT = SC["bg"], SC["bg_spot"]
LEAD, TAIL = 0.2, 0.4          # seconds of picture before the voice starts / after it ends
INK = "#1f2233"                # outline colour
YELLOW = "#FFD43B"
LOGO_PNG = (ROOT / "assets/img/logo.png").exists()
PRIMARY = SC.get("brand_primary", "#1B2A4A")   # One Access brand colours: change in build/script.json
ACCENT = SC.get("brand_accent", "#2F6BFF")

# ----------------------------------------------------------------------------- palette
SKIN = {"tanvir": "#C68642", "colleague": "#8D5524", "light": "#E0AC69"}
HAIR = "#1c1c1c"

# ----------------------------------------------------------------------------- svg helpers

def g(inner, x=0, y=0, s=1, id=None, extra=""):
    i = f' id="{id}"' if id else ""
    return f'<g transform="translate({x} {y}) scale({s})"{extra}><g{i}>{inner}</g></g>'


def outline(extra=""):
    return f'stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" {extra}'


def person(id, skin, shirt, pose="down", face="neutral", hair="short", glasses=False, lanyard=False, extra_svg=""):
    """Chibi character. Local origin = base of neck. Head above (cy -170), torso below (0..330)."""
    o = outline()
    parts = []
    # torso
    parts.append(f'<path d="M-150 60 Q-150 0 -90 0 L90 0 Q150 0 150 60 L150 330 L-150 330 Z" fill="{shirt}" {o}/>')
    # collar / neck
    parts.append(f'<path d="M-40 0 L0 40 L40 0" fill="none" {o}/>')
    if lanyard:
        parts.append(f'<path d="M-30 10 L-12 200 M30 10 L12 200" stroke="#2b2b2b" stroke-width="6" fill="none"/>'
                     f'<rect x="-40" y="190" width="80" height="100" rx="10" fill="#f7f4ea" {o}/>'
                     f'<circle cx="0" cy="222" r="14" fill="{skin}" {o}/><rect x="-22" y="246" width="44" height="22" rx="6" fill="#9ab" />')
    # arms
    hand = lambda x, y: f'<circle cx="{x}" cy="{y}" r="34" fill="{skin}" {o}/>'
    arm = lambda d: f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="54" stroke-linecap="round"/><path d="{d}" fill="none" stroke="{shirt}" stroke-width="40" stroke-linecap="round"/>'
    left = arm("M-135 70 Q-200 180 -175 285") + hand(-175, 290)
    if pose == "down":
        right = arm("M135 70 Q200 180 175 285") + hand(175, 290)
    elif pose == "phone":
        right = arm("M135 70 Q230 150 110 215") + hand(112, 215) + \
            f'<g transform="translate(118 160) rotate(-12)"><rect x="-42" y="-80" width="84" height="150" rx="14" fill="{INK}"/><rect x="-34" y="-70" width="68" height="128" rx="8" fill="#d8f0ff"/></g>' + hand(112, 215)
    elif pose == "fist":
        right = arm("M135 70 Q240 0 190 -110") + hand(190, -115)
    elif pose == "chin":
        right = arm("M135 70 Q220 -10 80 -40") + hand(70, -45)
    elif pose == "point":
        right = arm("M135 70 Q240 40 330 10") + hand(335, 8)
    elif pose == "type":
        left = arm("M-135 70 Q-190 170 -110 250") + hand(-105, 255)
        right = arm("M135 70 Q190 170 110 250") + hand(105, 255)
    elif pose == "wave":
        right = arm("M135 70 Q250 20 230 -120") + hand(232, -125)
    else:
        right = arm("M135 70 Q200 180 175 285") + hand(175, 290)
    parts.append(left + right)
    # head
    parts.append(f'<circle cx="-150" cy="-165" r="26" fill="{skin}" {o}/><circle cx="150" cy="-165" r="26" fill="{skin}" {o}/>')
    parts.append(f'<circle cx="0" cy="-170" r="150" fill="{skin}" {o}/>')
    # hair
    if hair == "short":
        parts.append(f'<path d="M-150 -185 Q-160 -330 0 -330 Q160 -330 150 -185 Q110 -235 40 -245 Q-20 -250 -70 -230 Q-120 -215 -150 -185 Z" fill="{HAIR}" {o}/>')
    elif hair == "side":
        parts.append(f'<path d="M-150 -175 Q-165 -335 10 -330 Q165 -325 152 -185 Q120 -250 -10 -240 Q-110 -235 -150 -175 Z" fill="{HAIR}" {o}/>')
    elif hair == "senior":
        parts.append(f'<path d="M-150 -185 Q-120 -300 -60 -300 L-60 -270 Q-110 -260 -150 -185 Z M150 -185 Q120 -300 60 -300 L60 -270 Q110 -260 150 -185 Z" fill="#9a9a9a" {o}/>')
    elif hair == "curly":
        parts.append(f'<path d="M-150 -185 Q-200 -250 -150 -300 Q-120 -360 -50 -340 Q0 -380 50 -340 Q120 -360 150 -300 Q200 -250 150 -185 Q100 -240 0 -245 Q-100 -240 -150 -185 Z" fill="{HAIR}" {o}/>')
    # glasses
    if glasses:
        parts.append(f'<circle cx="-58" cy="-175" r="40" fill="none" stroke="{INK}" stroke-width="7"/><circle cx="58" cy="-175" r="40" fill="none" stroke="{INK}" stroke-width="7"/><path d="M-18 -175 L18 -175" stroke="{INK}" stroke-width="7"/>')
    # cheeks
    parts.append('<circle cx="-95" cy="-125" r="22" fill="#f08a8a" opacity="0.55"/><circle cx="95" cy="-125" r="22" fill="#f08a8a" opacity="0.55"/>')
    # eyes + brows + mouth
    eye = lambda cx, rx, ry: f'<ellipse class="eye" cx="{cx}" cy="-178" rx="{rx}" ry="{ry}" fill="{INK}"/><circle cx="{cx + 6}" cy="-188" r="6" fill="#fff"/>'
    if face == "neutral":
        parts.append(eye(-55, 15, 21) + eye(55, 15, 21))
        parts.append(f'<path d="M-75 -235 Q-55 -248 -30 -238 M30 -238 Q55 -248 75 -235" fill="none" {o}/>')
        parts.append(f'<path d="M-30 -95 Q0 -70 30 -95" fill="none" {o}/>')
    elif face == "surprised":
        parts.append(eye(-55, 22, 28) + eye(55, 22, 28))
        parts.append(f'<path d="M-80 -250 Q-55 -265 -28 -252 M28 -252 Q55 -265 80 -250" fill="none" {o}/>')
        parts.append(f'<ellipse cx="0" cy="-85" rx="24" ry="32" fill="#7a2d2d" {o}/>')
    elif face == "happy":
        parts.append(f'<path d="M-80 -175 Q-55 -205 -30 -175 M30 -175 Q55 -205 80 -175" fill="none" {o}/>')
        parts.append(f'<path d="M-50 -100 Q0 -45 50 -100 Z" fill="#7a2d2d" {o}/><path d="M-36 -98 Q0 -84 36 -98" fill="#fff"/>')
    elif face == "worried":
        parts.append(eye(-55, 15, 21) + eye(55, 15, 21))
        parts.append(f'<path d="M-80 -245 Q-55 -230 -30 -240 M30 -240 Q55 -230 80 -245" fill="none" {o}/>')
        parts.append(f'<path d="M-30 -80 Q0 -100 30 -80" fill="none" {o}/>')
    elif face == "think":
        parts.append(f'<ellipse cx="-50" cy="-185" rx="15" ry="21" fill="{INK}"/><circle cx="-42" cy="-196" r="6" fill="#fff"/><ellipse cx="60" cy="-185" rx="15" ry="21" fill="{INK}"/><circle cx="68" cy="-196" r="6" fill="#fff"/>')
        parts.append(f'<path d="M-75 -240 Q-55 -255 -30 -245 M30 -238 Q55 -248 75 -230" fill="none" {o}/>')
        parts.append(f'<path d="M-25 -90 L25 -90" fill="none" {o}/>')
    parts.append(extra_svg)
    return f'<g id="{id}">{"".join(parts)}</g>'


def spot():
    return f'<circle cx="{W/2}" cy="{H/2 - 60}" r="430" fill="{SPOT}"/>'


def desk(y=1000, color="#8a5a3c"):
    o = outline()
    return f'<rect x="-40" y="{y}" width="{W + 80}" height="{H - y + 40}" fill="{color}" {o}/><rect x="-40" y="{y}" width="{W + 80}" height="26" fill="#a9734f" {o}/>'


def window_bg(x, y, w, h):
    o = outline()
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#e8f6ff" {o}/>'
            f'<path d="M{x + w/2} {y} L{x + w/2} {y + h} M{x} {y + h/2} L{x + w} {y + h/2}" {o} fill="none"/>')


def laptop(x, y, s=1.0, sticker=True):
    o = outline()
    st = f'<g transform="translate(0 -40)"><rect x="-58" y="-18" width="116" height="36" rx="8" fill="#fff" {o}/><g transform="translate(-36 0) scale(0.6)">{star_paths()}</g><text x="12" y="8" font-size="22" font-weight="800" text-anchor="middle" fill="#d9732b" font-family="Anek Bangla">Claude</text></g>' if sticker else ""
    inner = (f'<path d="M-150 -110 Q-150 -120 -140 -120 L140 -120 Q150 -120 150 -110 L150 0 L-150 0 Z" fill="#c9ced6" {o}/>'
             f'<rect x="-135" y="-108" width="270" height="98" rx="6" fill="#101826"/>'
             f'<path d="M-180 0 L180 0 L170 22 L-170 22 Z" fill="#aab2bd" {o}/>{st}')
    return g(inner, x, y, s)


def rickshaw(x, y, s=1.0, id="rick"):
    """Side view of a parked cycle rickshaw (front to the right). Local origin = ground line centre, wheels touch y=200."""
    o = outline()
    wheel = lambda cx: (f'<circle cx="{cx}" cy="110" r="90" fill="#2b2b2b" {o}/><circle cx="{cx}" cy="110" r="66" fill="#eef1f5" {o}/>'
                        + "".join(f'<path d="M{cx} 110 L{cx + 62*dx:.0f} {110 + 62*dy:.0f}" stroke="{INK}" stroke-width="4"/>'
                                  for dx, dy in [(1, 0), (0.5, 0.87), (-0.5, 0.87), (-1, 0), (-0.5, -0.87), (0.5, -0.87)])
                        + f'<circle cx="{cx}" cy="110" r="14" fill="{INK}"/>')
    inner = (
        # frame: chain stay, down tube, seat post, top tube, fork
        f'<path d="M-170 110 L60 110 L290 110 M60 110 L40 -70 M40 -40 L230 -90 M290 110 L225 -150" fill="none" {o}/>'
        f'<path d="M190 -160 L262 -150 M255 -150 L275 -185" fill="none" {o}/>'                      # handlebar
        f'<path d="M5 -78 Q40 -98 80 -78 L70 -64 L15 -64 Z" fill="#2b2b2b" {o}/>'                    # saddle
        f'<circle cx="60" cy="110" r="20" fill="#9aa4ad" {o}/><path d="M60 110 L95 150 M82 150 L110 150" fill="none" {o}/>'  # crank + pedal
        + wheel(-170) + wheel(290) +
        # passenger body
        f'<path d="M-330 40 L-30 40 L-30 70 L-330 70 Z" fill="#4a4a4a" {o}/>'                        # footboard
        f'<path d="M-330 40 L-330 -90 Q-330 -110 -310 -110 L-250 -110 L-250 40 Z" fill="#2f7d4f" {o}/>'  # back panel
        f'<circle cx="-290" cy="-40" r="18" fill="{YELLOW}" {o}/>'
        f'<rect x="-250" y="-60" width="190" height="100" rx="18" fill="#f4d35e" {o}/>'               # seat
        f'<rect x="-250" y="-140" width="50" height="100" rx="14" fill="#f4d35e" {o}/>'               # seat back
        # folding hood
        f'<path d="M-335 -110 Q-340 -340 -120 -350 Q-10 -350 10 -230 L-250 -110 Z" fill="#e45b4b" {o}/>'
        f'<path d="M-250 -110 Q-250 -290 -130 -345 M-250 -110 Q-190 -260 -60 -330 M-250 -110 Q-130 -220 -5 -290" fill="none" stroke="{INK}" stroke-width="5"/>'
        f'<circle cx="-250" cy="-110" r="12" fill="{INK}"/>'
    )
    return g(inner, x, y, s, id)


def meter(x, y, s=1.0, id="meter", value="$ ০", color="#e0312e", label="মিটার"):
    o = outline()
    inner = (f'<rect x="-170" y="-110" width="340" height="220" rx="26" fill="#1f2233" {o}/>'
             f'<rect x="-150" y="-90" width="300" height="130" rx="14" fill="#0a0d16" stroke="#3a4157" stroke-width="4"/>'
             f'<text id="{id}-v" x="0" y="8" font-size="86" font-weight="800" text-anchor="middle" fill="{color}" font-family="Anek Bangla">{value}</text>'
             f'<text x="0" y="86" font-size="30" font-weight="700" text-anchor="middle" fill="#cfd5e4" font-family="Anek Bangla">{label}</text>'
             f'<circle cx="130" cy="-80" r="12" fill="{color}"/>')
    return g(inner, x, y, s, id)


def screen_box(x, y, s=1.0):
    """Inline style placing an HTML screen exactly over phone_hand(x, y, s)'s glass."""
    return f"left:{x - 184*s:.0f}px;top:{y - 284*s:.0f}px;width:{368*s:.0f}px;height:{728*s:.0f}px"


def screen(cls, id, x, y, s, inner):
    """HTML screen sitting exactly on phone_hand(x, y, s)'s glass; content is authored at 368x728 and zoomed."""
    return (f'<div class="screen {cls}" id="{id}" data-layout-ignore style="{screen_box(x, y, s)}">'
            f'<div class="scr-in" style="zoom:{s}">{inner}</div></div>')


def phone_hand(x, y, s=1.0, id="ph", screen=""):
    """A hand holding a phone, screen content given as HTML placed by phone_screen_html()."""
    o = outline()
    inner = (f'<path d="M-120 420 Q-140 560 -40 700 L220 700 L220 560 Q230 470 170 420 Z" fill="{SKIN["tanvir"]}" {o}/>'
             f'<path d="M-130 440 Q-200 420 -190 480 Q-160 520 -120 500 M-120 500 Q-200 500 -180 560 Q-150 590 -110 560" fill="{SKIN["tanvir"]}" {o}/>'
             f'<rect x="-200" y="-300" width="400" height="760" rx="48" fill="{INK}"/>'
             f'<rect x="-184" y="-284" width="368" height="728" rx="36" fill="#f4f6fa"/>'
             f'<rect x="-60" y="-272" width="120" height="14" rx="7" fill="{INK}"/>')
    return g(inner, x, y, s, id)


def padlock(x, y, s=1.0, id="lock"):
    o = outline()
    inner = (f'<g id="{id}-sh"><path d="M-90 -40 L-90 -120 Q-90 -230 0 -230 Q90 -230 90 -120 L90 -40" fill="none" stroke="{INK}" stroke-width="44" stroke-linecap="round"/>'
             f'<path d="M-90 -40 L-90 -120 Q-90 -230 0 -230 Q90 -230 90 -120 L90 -40" fill="none" stroke="#b8bcc8" stroke-width="28" stroke-linecap="round"/></g>'
             f'<rect x="-170" y="-40" width="340" height="260" rx="34" fill="{YELLOW}" {o}/>'
             f'<text x="0" y="110" font-size="92" font-weight="800" text-anchor="middle" fill="{INK}" font-family="Anek Bangla">রেট</text>')
    return g(inner, x, y, s, id)


def check_circle(x, y, s=1.0, id="chk"):
    o = outline()
    inner = f'<circle cx="0" cy="0" r="60" fill="#2ebd6b" {o}/><path d="M-30 2 L-8 26 L34 -24" fill="none" stroke="#fff" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>'
    return g(inner, x, y, s, id)


def question_mark(x, y, s=1.0, id="qm"):
    return g(f'<text x="0" y="0" font-size="260" font-weight="800" text-anchor="middle" fill="#2F6BFF" stroke="{INK}" stroke-width="8" font-family="Anek Bangla">?</text>', x, y, s, id)


# ----------------------------------------------------------------------------- icons (inline SVG, font-independent)

def star_paths(r=20, color="#d9732b", w=5):
    import math
    return "".join(f'<path d="M{math.cos(a)*r*0.25:.1f} {math.sin(a)*r*0.25:.1f} L{math.cos(a)*r:.1f} {math.sin(a)*r:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
                   for a in [k * math.pi / 4 for k in range(8)])


def star(sz=30, color="#d9732b"):
    return f'<svg class="ic" viewBox="-24 -24 48 48" width="{sz}" height="{sz}">{star_paths(20, color, 5)}</svg>'


def tick(sz=30, color="currentColor", w=7):
    return f'<svg class="ic" viewBox="0 0 48 48" width="{sz}" height="{sz}"><path d="M9 25 L20 36 L40 12" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def lock_ic(sz=36):
    return (f'<svg class="ic" viewBox="0 0 48 48" width="{sz}" height="{sz}"><path d="M14 22 V15 a10 10 0 0 1 20 0 V22" fill="none" stroke="{INK}" stroke-width="5"/>'
            f'<rect x="8" y="22" width="32" height="22" rx="5" fill="{YELLOW}" stroke="{INK}" stroke-width="4"/></svg>')


def clock_ic(sz=32):
    return (f'<svg class="ic" viewBox="0 0 48 48" width="{sz}" height="{sz}"><circle cx="24" cy="26" r="17" fill="#fff" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M24 26 V15 M24 26 L32 30 M19 4 H29" stroke="{INK}" stroke-width="5" stroke-linecap="round" fill="none"/></svg>')


def send_ic(sz=28):
    return f'<svg class="ic" viewBox="0 0 48 48" width="{sz}" height="{sz}"><path d="M6 8 L44 24 L6 40 L14 24 Z" fill="currentColor"/></svg>'


def wavy(w=70):
    return f'<svg class="ic" viewBox="0 0 70 20" width="{w}" height="20"><path d="M4 10 Q13 0 22 10 T40 10 T58 10 T66 10" fill="none" stroke="#bbb" stroke-width="4" stroke-linecap="round"/></svg>'


def neq_ic(sz=110):
    return f'<svg class="ic" viewBox="0 0 48 48" width="{sz}" height="{sz}"><path d="M8 18 H40 M8 30 H40 M30 8 L18 40" stroke="#e0312e" stroke-width="6" stroke-linecap="round"/></svg>'


# ----------------------------------------------------------------------------- html helpers

def cap_html(cap):
    inner = re.sub(r"\*(.+?)\*", r'<span class="hl">\1</span>', cap)
    return f'<div class="capwrap"><div class="cap" id="cap">{inner}</div></div>'


def logo_html(size=120, id="logo"):
    if LOGO_PNG:
        return f'<img id="{id}" class="logo" src="assets/img/logo.png" style="width:{size}px;height:{size}px;border-radius:{size*0.22}px;object-fit:cover">'
    r = size * 0.22
    return (f'<div id="{id}" class="logo" style="width:{size}px;height:{size}px;border-radius:{r}px;background:var(--oa-primary);display:flex;align-items:center;justify-content:center;border:{max(4, size*0.05)}px solid {INK}">'
            f'<svg viewBox="0 0 100 100" width="{size*0.7}" height="{size*0.7}"><circle cx="50" cy="50" r="34" fill="none" stroke="#fff" stroke-width="12"/><rect x="43" y="22" width="14" height="56" rx="6" fill="#fff"/><rect x="43" y="22" width="14" height="56" rx="6" fill="#fff"/><circle cx="50" cy="50" r="34" fill="none" stroke="var(--oa-accent)" stroke-width="12" stroke-dasharray="110 300" stroke-linecap="round"/></svg></div>')


def ig_icon(sz=44):
    return (f'<svg viewBox="0 0 48 48" width="{sz}" height="{sz}"><rect x="4" y="4" width="40" height="40" rx="12" fill="none" stroke="currentColor" stroke-width="4"/>'
            f'<circle cx="24" cy="24" r="9" fill="none" stroke="currentColor" stroke-width="4"/><circle cx="35" cy="13" r="3" fill="currentColor"/></svg>')


def fb_icon(sz=44):
    return (f'<svg viewBox="0 0 48 48" width="{sz}" height="{sz}"><rect x="4" y="4" width="40" height="40" rx="12" fill="currentColor"/>'
            f'<path d="M30 14h-4c-3 0-5 2-5 5v4h-4v5h4v12h5V28h4l1-5h-5v-3c0-1 .5-1.5 1.5-1.5H30z" fill="#fff"/></svg>')


def browser(url, body, id, x, y, w, h):
    return (f'<div class="card browser" id="{id}" style="left:{x}px;top:{y}px;width:{w}px">'
            f'<div class="bar"><i></i><i></i><i></i><span class="url">{url}</span></div><div class="body">{body}</div></div>')


BILLING_BODY = ('<div class="claude-h">' + star(34) + ' Claude Platform</div><div class="serif">Billing</div><div class="muted">Promotional credits</div>'
                '<div class="inner"><div class="row"><span><b>API credits</b><br><small>Expires at end of billing cycle</small></span>{badge}</div>'
                '<div class="big">{amount}</div><div class="track"><div class="fill" id="{id}-fill" style="width:{pct}%"></div></div>{foot}</div>')


def billing_card(id, x=90, y=280, amount="$100.00", badge="", pct=100, foot=""):
    return browser("platform.claude.com", BILLING_BODY.format(badge=badge, amount=amount, pct=pct, foot=foot, id=id), id, x, y, 900, 620)


# ----------------------------------------------------------------------------- scene builders
# each returns dict(svg=..., html=..., tl=[js lines], sfx=[(name, t, vol)])

def pop(sel, t, dur=0.55, scale0=0.0, ease="back.out(1.7)"):
    return f'tl.fromTo("{sel}", {{scale: {scale0}, opacity: 0, transformOrigin: "50% 50%"}}, {{scale: 1, opacity: 1, duration: {dur}, ease: "{ease}"}}, {t});'


def rise(sel, t, dur=0.5, dy=50):
    return f'tl.fromTo("{sel}", {{y: {dy}, opacity: 0}}, {{y: 0, opacity: 1, duration: {dur}, ease: "expo.out"}}, {t});'


def slide(sel, t, dx=-120, dur=0.55):
    return f'tl.fromTo("{sel}", {{x: {dx}, opacity: 0}}, {{x: 0, opacity: 1, duration: {dur}, ease: "expo.out"}}, {t});'


def breathe(sel, dur):
    n = max(1, int(dur / 1.6))
    return f'tl.to("{sel}", {{scaleY: 1.018, transformOrigin: "50% 100%", duration: 0.8, yoyo: true, repeat: {2*n - 1}, ease: "sine.inOut"}}, 0.3);'


def blink(sel, dur):
    n = max(0, int(dur / 1.3) - 1)
    return f'tl.to("{sel} .eye", {{scaleY: 0.12, transformOrigin: "50% 50%", duration: 0.07, yoyo: true, repeat: {2*n + 1}, repeatDelay: 1.1, ease: "none"}}, 0.9);'


def stamp(sel, t):
    return f'tl.fromTo("{sel}", {{scale: 3.2, opacity: 0, rotation: -14, transformOrigin: "50% 50%"}}, {{scale: 1, opacity: 1, rotation: -8, duration: 0.35, ease: "power3.in"}}, {t});'


def office_bg():
    return (window_bg(90, 150, 300, 340) + window_bg(690, 150, 300, 340) +
            # rickshaw mural frame on the wall
            f'<rect x="420" y="170" width="240" height="190" rx="12" fill="#fff6d6" {outline()}/>' + rickshaw(545, 300, 0.26, "mural") +
            desk(1010))


def scene_office_intro(d):
    svg = office_bg() + g(person("tan", SKIN["tanvir"], "#2a9d8f", "wave", "happy", "short", lanyard=True), 540, 700)
    o = outline()
    tag = (f'<g transform="translate(540 1085)"><g id="tag"><rect x="-230" y="-52" width="460" height="104" rx="18" fill="#fff" {o}/>'
           f'<text x="0" y="-4" font-size="44" font-weight="800" text-anchor="middle" fill="{INK}" font-family="Anek Bangla">তানভীর</text>'
           f'<text x="0" y="36" font-size="30" font-weight="600" text-anchor="middle" fill="#666" font-family="Anek Bangla">Backend Developer</text></g></g>')
    return dict(svg=svg + tag, tl=[breathe("#tan", d), pop("#tag", 0.35, 0.45, 0.4)], sfx=[("click", 0.38, 0.3)])


def scene_laptop_code(d):
    svg = office_bg() + g(person("tan", SKIN["tanvir"], "#2a9d8f", "type", "neutral", "short", lanyard=True), 540, 770, 0.92) + laptop(540, 1010, 1.25)
    html = ('<div class="card term" id="term"><div class="bar dark"><i></i><i></i><i></i><span>Claude Code</span></div>'
            '<div class="tbody"><div class="tline" id="t1">&gt; claude "fix the fare calculator"</div><div class="tline" id="t2">' + tick(24) + ' src/fare.ts updated</div>'
            '<div class="tline" id="t3">' + tick(24) + ' 12 tests passed</div><div class="tline" id="t4">&gt; <span class="cur"></span></div></div></div>')
    tl = [breathe("#tan", d), blink("#tan", d), pop("#term", 0.2, 0.5, 0.6)] + [rise(f"#t{i}", 0.3 + i * 0.25, 0.25, 12) for i in range(1, 5)]
    return dict(svg=svg, html=html, tl=tl, sfx=[("click", 0.25, 0.35)])


def scene_pricing(d):
    html = ('<div class="card price" id="price"><div class="claude-h">' + star(34) + ' Claude</div><div class="serif">Pricing</div>'
            '<div class="plan"><div class="pname">Claude Max</div><div class="muted">For all-day work</div>'
            '<div class="pamt"><span id="pv">$100</span><small>Per month</small></div>'
            '<div class="tick" id="tick1">' + tick(30) + ' $100 a month in API credits</div><div class="tick on" id="tick2">' + tick(30) + ' সাবস্ক্রিপশন চালু</div></div></div>')
    tl = [pop("#price", 0.1, 0.55, 0.7), rise("#pv", 0.5, 0.4, 30), rise("#tick1", 1.1, 0.35, 16), rise("#tick2", 1.5, 0.35, 16)]
    return dict(svg="", html=html, tl=tl, sfx=[("click", 0.15, 0.35), ("click", 1.1, 0.25)])


def scene_billing(d):
    html = billing_card("bill", amount='<span id="amt">$100.00</span>')
    tl = [pop("#bill", 0.1, 0.55, 0.7), pop("#amt", 0.7, 0.5, 0.3), f'tl.fromTo("#bill-fill", {{scaleX: 0, transformOrigin: "0% 50%"}}, {{scaleX: 1, duration: 0.8, ease: "expo.out"}}, 1.1);']
    return dict(svg="", html=html, tl=tl, sfx=[("click", 0.15, 0.35)])


def scene_think_limit(d):
    svg = office_bg() + g(person("tan", SKIN["tanvir"], "#2a9d8f", "chin", "think", "short", lanyard=True), 540, 760, 0.95)
    o = outline()
    bubble = (f'<g transform="translate(-50 0)"><g id="bub"><circle cx="700" cy="430" r="14" fill="#fff" {o}/><circle cx="740" cy="380" r="22" fill="#fff" {o}/>'
              f'<path d="M700 330 Q690 200 830 190 L1000 190 Q1060 190 1060 250 L1060 310 Q1060 370 1000 370 L830 370 Q740 380 700 330 Z" fill="#fff" {o}/>'
              f'<text x="880" y="260" font-size="40" font-weight="800" text-anchor="middle" fill="{INK}" font-family="Anek Bangla">চ্যাটের লিমিট?</text>'
              f'<g transform="translate(810 318)">{star_paths(18)}</g><text x="900" y="330" font-size="36" font-weight="700" text-anchor="middle" fill="#d9732b" font-family="Anek Bangla">Claude</text></g></g>')
    tl = [breathe("#tan", d), pop("#bub", 0.5, 0.5, 0.3)]
    return dict(svg=svg + bubble, html="", tl=tl, sfx=[("click", 0.55, 0.3)])


def scene_separate(d):
    html = ('<div class="two"><div class="card mini" id="c1"><div class="pname">Claude Code</div><div class="muted">চ্যাট আর কোডের</div><div class="lim">লিমিট</div>'
            '<div class="track"><div class="fill" style="width:62%"></div></div><div class="muted">রোজ চলে</div></div>'
            '<div class="neq" id="neq">' + neq_ic() + '</div>'
            '<div class="card mini yellow" id="c2"><div class="pname">API credit</div><div class="muted">আলাদা ব্যালেন্স</div><div class="lim">$১০০</div>'
            '<div class="track"><div class="fill grey" style="width:0%"></div></div><div class="muted red">পড়ে থাকে</div></div></div>'
            '<div class="pill-note" id="note">একটা শেষ হলেও অন্যটা থাকে</div>')
    tl = [slide("#c1", 0.1, -120), pop("#neq", 0.55, 0.4, 0.2), slide("#c2", 0.75, 120), rise("#note", 1.0, 0.4, 30)]
    return dict(svg="", html=html, tl=tl, sfx=[("click", 0.15, 0.3), ("click", 0.85, 0.3)])


def scene_billing_zero(d):
    html = billing_card("bill", y=250, amount="$100.00", badge='<span class="badge" id="badge">0% ব্যবহার</span>', pct=100,
                        foot='<div class="red" id="foot">পুরোটাই পড়ে আছে</div>')
    tl = [pop("#bill", 0.05, 0.45, 0.8), stamp("#badge", 0.7), rise("#foot", 1.3, 0.4, 20),
          f'tl.to("#bill", {{x: -6, duration: 0.05, yoyo: true, repeat: 5, ease: "none"}}, 0.95);']
    return dict(svg="", html=html, tl=tl, sfx=[("click", 0.72, 0.4)])


def scene_meter_running(d):
    svg = (f'<rect x="-40" y="1000" width="{W+80}" height="400" fill="#9aa4ad" {outline()}/>'
           f'<path d="M-40 1000 L{W+40} 1000" stroke="#fff" stroke-width="10" stroke-dasharray="60 40"/>' +
           rickshaw(520, 800, 0.95) + meter(540, 270, 1.1, "m", "$ ২৩", "#e0312e", "মিটার চলছে") +
           f'<g id="park"><rect x="880" y="470" width="120" height="120" rx="20" fill="#2F6BFF" {outline()}/><text x="940" y="560" font-size="80" font-weight="800" text-anchor="middle" fill="#fff" font-family="Anek Bangla">P</text></g>')
    vals = ["$ ২৩", "$ ৪৭", "$ ৬৮", "$ ৮৬", "$ ১০০"]
    tl = [rise("#rick", 0.05, 0.6, 80), pop("#m", 0.4, 0.5, 0.5), pop("#park", 0.9, 0.4, 0.3)]
    # digits tick: swap the text content through staged opacity flashes (GSAP can't tween text; use set())
    for i, v in enumerate(vals[1:], 1):
        tl.append(f'tl.set("#m-v", {{textContent: "{v}"}}, {0.9 + i * 0.42});')
        tl.append(f'tl.to("#m", {{scale: 1.05, duration: 0.12, yoyo: true, repeat: 1, transformOrigin: "50% 50%"}}, {0.95 + i * 0.42});')
    return dict(svg=svg, html="", tl=tl, sfx=[("click", 0.45, 0.35)] + [("click", 0.9 + i * 0.42, 0.2) for i in range(1, 5)])


def scene_meter_zero(d):
    o = outline()
    svg = (meter(540, 560, 1.7, "m", "$ ১০০", "#e0312e", "API credit") +
           f'<g id="cal"><rect x="740" y="130" width="200" height="200" rx="20" fill="#fff" {o}/><rect x="740" y="130" width="200" height="56" rx="20" fill="#e0312e" {o}/>'
           f'<text id="cal-d" x="840" y="280" font-size="84" font-weight="800" text-anchor="middle" fill="{INK}" font-family="Anek Bangla">৩০</text></g>'
           f'<g id="stamp" opacity="0"><rect x="300" y="760" width="480" height="110" rx="18" fill="none" stroke="#e0312e" stroke-width="10"/>'
           f'<text x="540" y="840" font-size="66" font-weight="800" text-anchor="middle" fill="#e0312e" font-family="Anek Bangla">মেয়াদ শেষ</text></g>')
    tl = [pop("#m", 0.05, 0.5, 0.6), pop("#cal", 0.3, 0.4, 0.4),
          f'tl.set("#cal-d", {{textContent: "১"}}, 1.1);', f'tl.to("#cal", {{rotation: 6, duration: 0.08, yoyo: true, repeat: 3, transformOrigin: "50% 50%"}}, 1.1);',
          f'tl.set("#m-v", {{textContent: "$ ০"}}, 1.4);', f'tl.to("#m", {{x: -10, duration: 0.05, yoyo: true, repeat: 7, ease: "none"}}, 1.4);',
          stamp("#stamp", 1.75)]
    return dict(svg=svg, html="", tl=tl, sfx=[("click", 1.1, 0.3), ("click", 1.75, 0.45)])


def scene_months(d):
    html = "".join(f'<div class="card month" id="mo{i}" style="top:{230 + i*210}px"><div class="mlabel">{m} মাস</div><div class="mamt">API credit <b>$০</b></div><div class="mexp">মেয়াদ শেষ</div></div>'
                   for i, m in enumerate(["১ম", "২য়", "৩য়", "৪র্থ"]))
    tl = [slide(f"#mo{i}", 0.1 + i * 0.4, -160 if i % 2 == 0 else 160) for i in range(4)]
    return dict(svg="", html=html, tl=tl, sfx=[("click", 0.1 + i * 0.4, 0.25) for i in range(4)])


def scene_lunch(d):
    o = outline()
    svg = (window_bg(90, 150, 900, 300) +
           g(person("tan", SKIN["tanvir"], "#2a9d8f", "down", "neutral", "short", lanyard=True), 330, 760, 0.78) +
           g(person("col", SKIN["colleague"], "#f4a261", "point", "happy", "curly", glasses=True), 780, 760, "-0.78 0.78") +
           f'<rect x="-40" y="1010" width="{W+80}" height="400" fill="#c97b4b" {o}/>'
           f'<ellipse cx="330" cy="1040" rx="110" ry="30" fill="#fff" {o}/><ellipse cx="330" cy="1040" rx="70" ry="18" fill="#f2c14e"/>'
           f'<ellipse cx="780" cy="1040" rx="110" ry="30" fill="#fff" {o}/><ellipse cx="780" cy="1040" rx="70" ry="18" fill="#f2c14e"/>'
           f'<rect x="520" y="980" width="60" height="70" rx="10" fill="#fff" {o}/>'
           f'<g id="say"><path d="M640 330 Q640 270 700 270 L860 270 Q920 270 920 330 L920 370 Q920 430 860 430 L760 430 L720 480 L730 430 L700 430 Q640 430 640 370 Z" fill="#fff" {o}/>'
           f'<circle cx="730" cy="350" r="10" fill="{INK}"/><circle cx="780" cy="350" r="10" fill="{INK}"/><circle cx="830" cy="350" r="10" fill="{INK}"/></g>')
    tl = [rise("#tan", 0.05, 0.5, 60), rise("#col", 0.15, 0.5, 60), breathe("#tan", d), pop("#say", 0.7, 0.4, 0.3)]
    return dict(svg=svg, html="", tl=tl, sfx=[("click", 0.72, 0.3)])


def scene_phone_page(d):
    X, Y, S = 540, 590, 1.3
    svg = phone_hand(X, Y, S, "ph")
    posts = "".join(f'<div class="ig-post {c}"><span>{t}</span></div>' for c, t in
                    [("", "credit পড়ে আছে?"), ("b", "২০–২৫%"), ("c", "৫–১০ মিনিট"), ("c", "আগে রেট"), ("", "বিকাশ / নগদ"), ("b", "ইনবক্স")])
    html = screen("", "scr", X, Y, S,
                  f'<div class="ig-top">oneaccessbd</div>'
                  f'<div class="ig-prof">{logo_html(110, "plogo")}<div class="ig-stats"><b>One Access</b><span>Be One, Be Accessible.</span></div></div>'
                  f'<div class="ig-bio">পড়ে থাকা Claude API credit বিক্রি করুন</div>'
                  f'<div class="ig-btns"><span class="ig-btn ig">{ig_icon(26)} Instagram</span><span class="ig-btn fb">{fb_icon(26)} Facebook</span></div>'
                  f'<div class="ig-grid">{posts}</div>')
    tl = [rise("#ph", 0.05, 0.6, 160), rise("#scr", 0.05, 0.6, 160), pop("#plogo", 0.7, 0.45, 0.3)]
    return dict(svg=svg, html=html, tl=tl, sfx=[("click", 0.72, 0.3)])


def scene_rate_lock(d):
    svg = padlock(540, 600, 1.25, "lock") + check_circle(770, 470, 1.1, "chk")
    html = '<div class="pill-note" id="note" style="top:880px">ডিলের আগেই</div>'
    tl = [pop("#lock", 0.1, 0.5, 0.5), f'tl.fromTo("#lock-sh", {{y: -70}}, {{y: 0, duration: 0.3, ease: "power3.in"}}, 0.7);',
          f'tl.to("#lock", {{y: 6, duration: 0.06, yoyo: true, repeat: 3}}, 1.0);', pop("#chk", 1.15, 0.4, 0.2), rise("#note", 1.5, 0.4, 24)]
    return dict(svg=svg, html=html, tl=tl, sfx=[("click", 1.0, 0.5), ("click", 1.15, 0.3)])


def scene_quote(d):
    html = (f'<div class="card quote" id="q"><div class="qh">{logo_html(64, "qlogo")}<b>One Access</b></div>'
            '<div class="qrow" id="r1"><span>আপনার credit</span><b>USD ১০০</b></div>'
            '<div class="qrow" id="r2"><span>রেট (আনুমানিক)</span><b>২০–২৫%</b></div>'
            '<div class="qrow" id="r3"><span>টাকা পাবেন</span><b>ব্যবহারের ৫–১০ মিনিট পর</b></div>'
            '<div class="qget" id="r4"><span>আপনি পেতে পারেন</span><b>USD ২০–২৫</b></div>'
            '<div class="fine">আনুমানিক হিসাব · আসল রেট ডিলের আগে ঠিক হয়<br>স্বাধীন সার্ভিস · Anthropic-এর সাথে কোনো সম্পর্ক নেই</div></div>')
    tl = [pop("#q", 0.1, 0.5, 0.7)] + [rise(f"#r{i}", 0.5 + i * 0.3, 0.35, 18) for i in range(1, 5)]
    return dict(svg="", html=html, tl=tl, sfx=[("click", 0.15, 0.35), ("click", 1.7, 0.35)])


def scene_toggle(d):
    html = ('<div class="card quote" id="tg"><div class="qh"><b>যতটুকু কথা, ততটুকুই!</b></div>'
            '<div class="slider"><div class="mark" id="mark">ঠিক করা</div><div class="strack"><div class="sfill" id="sfill"></div><div class="knob" id="knob">' + tick(40, "#2ebd6b") + '</div><div class="slock">' + lock_ic(40) + '</div></div></div>'
            '<div class="qrow"><span>ব্যবহার</span><b>= যা ঠিক হয়েছে</b></div><div class="red big2" id="nomore">এর বেশি কখনো না।</div></div>')
    tl = [pop("#tg", 0.1, 0.5, 0.7), f'tl.fromTo("#sfill", {{scaleX: 0, transformOrigin: "0% 50%"}}, {{scaleX: 1, duration: 0.9, ease: "power2.inOut"}}, 0.6);',
          f'tl.fromTo("#knob", {{x: 0}}, {{x: 430, duration: 0.9, ease: "power2.inOut"}}, 0.6);', rise("#mark", 1.4, 0.3, 14), rise("#nomore", 1.9, 0.4, 20)]
    return dict(svg="", html=html, tl=tl, sfx=[("click", 1.5, 0.4)])


def scene_bkash(d):
    X, Y, S = 540, 590, 1.3
    svg = phone_hand(X, Y, S, "ph")
    o = outline()
    notes = "".join(f'<g transform="translate({x} {y})"><g id="n{i}"><rect x="-70" y="-36" width="140" height="72" rx="12" fill="#8fd19e" {o}/><circle cx="0" cy="0" r="22" fill="#c9efd2" {o}/>'
                    f'<text x="0" y="12" font-size="32" font-weight="800" text-anchor="middle" fill="{INK}" font-family="Anek Bangla">$</text></g></g>'
                    for i, (x, y) in enumerate([(130, 300), (950, 260), (120, 880), (960, 860)]))
    html = screen("bk", "scr", X, Y, S,
                  '<div class="bk-top">বিকাশ</div><div class="bk-bal">ব্যালেন্স <b>••••</b></div>'
                  '<div class="bk-ok" id="ok"><div class="okc" id="okc">' + tick(96, "#fff", 6) + '</div><div class="okt">টাকা পেয়েছেন</div><div class="oks">One Access থেকে এসেছে</div></div>'
                  '<div class="bk-time" id="tm">' + clock_ic(34) + ' ৫–১০ মিনিট</div>')
    tl = [rise("#ph", 0.05, 0.6, 160), rise("#scr", 0.05, 0.6, 160), pop("#okc", 0.8, 0.5, 0.2), rise("#tm", 1.5, 0.4, 20)] + \
         [pop(f"#n{i}", 1.0 + i * 0.15, 0.4, 0.2) for i in range(4)]
    return dict(svg=svg + notes, html=html, tl=tl, sfx=[("click", 0.82, 0.45)])


LEDGER = ('<div class="card ledger" id="led"><div class="rings">{rings}</div><div class="lt">মাসের হিসাব</div>'
          '<div class="lrow dim"><span>বাজার</span><span>{w}</span></div><div class="lrow dim"><span>বিদ্যুৎ বিল</span><span>{w}</span></div>'
          '<div class="lrow" id="l1"><span>{st} Claude Max</span><b>$১০০</b></div>{rest}</div>')
RINGS = "".join('<i></i>' for _ in range(9))


def scene_ledger(d):
    html = LEDGER.format(rings=RINGS, w=wavy(), st=star(34), rest='<div class="lrow green" id="l2"><span>পড়ে থাকা credit বিক্রি করে ফেরত<br><small>আনুমানিক ২৫% রেটে</small></span><b>−$২৫</b></div>')
    tl = [pop("#led", 0.1, 0.5, 0.7), rise("#l1", 0.35, 0.3, 14), rise("#l2", 0.6, 0.4, 18)]
    return dict(svg="", html=html, tl=tl, sfx=[("click", 0.15, 0.35), ("click", 1.0, 0.35)])


def scene_ledger_75(d):
    html = LEDGER.format(rings=RINGS, w=wavy(), st=star(34), rest='<div class="lrow green"><span>পড়ে থাকা credit বিক্রি করে ফেরত<br><small>আনুমানিক ২৫% রেটে</small></span><b>−$২৫</b></div>'
                                           '<div class="lsum" id="l3"><span>পড়ল</span><b class="redb">$৭৫</b></div>')
    top = '<g transform="translate(818 985) rotate(-6)"><ellipse id="ring" cx="0" cy="0" rx="135" ry="72" fill="none" stroke="#e0312e" stroke-width="9" stroke-linecap="round" stroke-dasharray="680" stroke-dashoffset="680"/></g>'
    tl = [rise("#l3", 0.3, 0.4, 18), f'tl.to("#ring", {{strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut"}}, 0.9);',
          f'tl.to("#l3 b", {{scale: 1.15, duration: 0.2, yoyo: true, repeat: 1, transformOrigin: "50% 50%"}}, 0.9);']
    return dict(svg="", html=html, top=top, tl=tl, sfx=[("click", 0.3, 0.35)])


def scene_meter_off(d):
    svg = (f'<rect x="-40" y="1000" width="{W+80}" height="400" fill="#9aa4ad" {outline()}/>'
           f'<path d="M-40 1000 L{W+40} 1000" stroke="#fff" stroke-width="10" stroke-dasharray="60 40"/>' +
           rickshaw(330, 800, 0.72) + meter(330, 300, 0.95, "m", "বন্ধ", "#2ebd6b", "মিটার") +
           g(person("tan", SKIN["tanvir"], "#2a9d8f", "fist", "happy", "short", lanyard=True), 820, 720, 0.85))
    tl = [rise("#rick", 0.05, 0.5, 60), pop("#m", 0.3, 0.5, 0.5), rise("#tan", 0.5, 0.5, 80), breathe("#tan", d),
          f'tl.to("#tan", {{y: -30, duration: 0.25, yoyo: true, repeat: 1, ease: "power2.out"}}, 1.2);']
    return dict(svg=svg, html="", tl=tl, sfx=[("click", 0.35, 0.35)])


def scene_question(d):
    svg = meter(540, 700, 1.6, "m", "$ ১০০", "#e0312e", "API credit") + question_mark(540, 380, 1.0, "qm")
    tl = [pop("#m", 0.05, 0.5, 0.6), pop("#qm", 0.5, 0.5, 0.2),
          f'tl.to("#qm", {{y: -18, duration: 0.5, yoyo: true, repeat: {max(1, int(d))}, ease: "sine.inOut"}}, 1.0);',
          f'tl.set("#m-v", {{textContent: "$ ০"}}, 1.3);', f'tl.to("#m", {{x: -8, duration: 0.05, yoyo: true, repeat: 5, ease: "none"}}, 1.3);']
    return dict(svg=svg, html="", tl=tl, sfx=[("click", 0.55, 0.35)])


def chat_screen(x, y, s, id="scr"):
    return screen("chat", id, x, y, s,
                  f'<div class="ch-top">{logo_html(48, "clogo")}<b>One Access</b></div>'
                  '<div class="bub me" id="b1">হাই! আমার Claude Max-এর credit পড়ে আছে</div>'
                  '<div class="bub them" id="b2">জি ভাই, বলুন!</div>'
                  '<div class="bub me" id="b3">বিক্রি করতে চাই</div>'
                  '<div class="ch-in">মেসেজ লিখুন <span>' + send_ic() + '</span></div>')


def scene_chat_cta(d):
    X, Y, S = 540, 640, 1.1
    svg = phone_hand(X, Y, S, "ph")
    html = chat_screen(X, Y, S) + '<div class="bigcta" id="cta">ইনবক্সে নক দিন</div>'
    tl = [rise("#cta", 0.05, 0.5, -40), rise("#ph", 0.1, 0.6, 160), rise("#scr", 0.1, 0.6, 160),
          pop("#b1", 0.7, 0.4, 0.4), pop("#b2", 1.1, 0.4, 0.4), pop("#b3", 1.5, 0.4, 0.4)]
    return dict(svg=svg, html=html, tl=tl, sfx=[("click", 0.7, 0.3), ("click", 1.1, 0.3), ("click", 1.5, 0.3)])


def scene_end_card(d):
    html = (f'<div class="end" id="end">{logo_html(230, "elogo")}<div class="ename" id="ename">One Access</div><div class="etag" id="etag">Be One, Be Accessible.</div>'
            f'<div class="social" id="s1"><span class="ig">{ig_icon(54)}</span><span>@oneaccessbd</span></div>'
            f'<div class="social" id="s2"><span class="fb">{fb_icon(54)}</span><span>facebook.com/oneaccessbd</span></div>'
            '<div class="fine center" id="efine">স্বাধীন সার্ভিস · Anthropic-এর সাথে কোনো সম্পর্ক নেই<br>আনুমানিক হিসাব · আসল রেট ডিলের আগে ঠিক হয়</div></div>')
    tl = [pop("#elogo", 0.1, 0.6, 0.3), rise("#ename", 0.5, 0.4, 24), rise("#etag", 0.8, 0.4, 16), slide("#s1", 1.1, -80), slide("#s2", 1.35, 80), rise("#efine", 1.6, 0.4, 10)]
    return dict(svg="", html=html, tl=tl, sfx=[("click", 0.15, 0.4), ("click", 1.2, 0.3), ("click", 1.5, 0.3)])


SCENES = {n[6:]: f for n, f in globals().items() if n.startswith("scene_")}

# ----------------------------------------------------------------------------- css shared by every scene
CSS = """
@font-face { font-family: "Anek Bangla"; src: url("assets/fonts/AnekBangla.ttf") format("truetype"); font-weight: 100 800; }
@font-face { font-family: "Noto Sans Bengali"; src: url("assets/fonts/NotoSansBengali.ttf") format("truetype"); font-weight: 100 900; }
#root { position: absolute; inset: 0; overflow: hidden; background: var(--bg); font-family: "Anek Bangla", "Noto Sans Bengali", sans-serif; color: var(--ink); }
#root * { box-sizing: border-box; margin: 0; }
svg.stage { position: absolute; left: 0; top: 0; }
.capwrap { position: absolute; left: 0; right: 0; top: 1190px; text-align: center; z-index: 50; }
.cap { display: inline-block; background: #141414; color: #fff; font-size: 46px; font-weight: 700; line-height: 1.25; padding: 12px 36px; border-radius: 999px; max-width: 940px; }
.cap .hl { color: var(--hl); }
.card { position: absolute; background: #fff; border: 7px solid var(--ink); border-radius: 30px; box-shadow: 0 16px 0 rgba(0,0,0,0.12); }
.browser .bar { display: flex; align-items: center; gap: 10px; padding: 16px 22px; border-bottom: 5px solid var(--ink); background: #eef1f5; border-radius: 22px 22px 0 0; }
.browser .bar i { width: 20px; height: 20px; border-radius: 50%; background: #ff5f57; display: inline-block; } .browser .bar i:nth-child(2) { background: #febc2e; } .browser .bar i:nth-child(3) { background: #28c840; }
.browser .url { margin-left: 14px; background: #fff; border: 3px solid #cfd5df; border-radius: 999px; padding: 4px 22px; font-size: 28px; font-weight: 600; color: #333; }
.browser .body { padding: 34px 44px 44px; background: #faf8f2; border-radius: 0 0 22px 22px; }
.ic { display: inline-block; vertical-align: -0.15em; flex: none; }
.claude-h { font-size: 30px; font-weight: 700; color: #333; }
.serif { font-family: Georgia, "Times New Roman", serif; font-size: 54px; font-weight: 600; margin-top: 6px; }
.muted { font-size: 28px; color: #777; }
.inner { margin-top: 22px; background: #fff; border: 4px solid #d9d4c7; border-radius: 20px; padding: 24px 30px; position: relative; }
.row { display: flex; justify-content: space-between; align-items: flex-start; font-size: 30px; } .row small { font-size: 28px; color: #777; }
.big { font-size: 96px; font-weight: 800; line-height: 1.1; margin-top: 8px; }
.track { height: 24px; background: #e6e3da; border-radius: 999px; margin-top: 14px; overflow: hidden; }
.fill { height: 100%; background: #2ebd6b; border-radius: 999px; } .fill.grey { background: #bbb; }
.badge { background: #f4a261; color: #1f2233; font-weight: 800; font-size: 30px; padding: 6px 20px; border-radius: 999px; border: 4px solid var(--ink); }
.red { color: #e0312e; font-weight: 800; } .foot { margin-top: 10px; } .inner .red { font-size: 34px; margin-top: 14px; }
.term { left: 440px; top: 60px; width: 590px; height: 330px; background: #101826; border-color: var(--ink); overflow: hidden; }
.term .bar { display: flex; gap: 10px; padding: 14px 18px; background: #1b2434; color: #cfd5e4; font-size: 28px; align-items: center; } .term .bar i { width: 16px; height: 16px; border-radius: 50%; background: #ff5f57; } .term .bar i:nth-child(2) { background: #febc2e; } .term .bar i:nth-child(3) { background: #28c840; }
.term .tbody { padding: 18px 22px; font-family: Consolas, "Courier New", monospace; color: #9ae6b4; font-size: 28px; line-height: 1.6; } .tline { opacity: 0; } .cur { display: inline-block; width: 14px; height: 28px; background: #fff; vertical-align: -4px; }
.price { left: 150px; top: 250px; width: 780px; padding: 40px 50px; background: #faf8f2; }
.plan { margin-top: 24px; background: #fff; border: 5px solid #d9732b; border-radius: 24px; padding: 30px 36px; }
.pname { font-size: 44px; font-weight: 800; } .pamt { display: flex; align-items: baseline; gap: 18px; margin-top: 10px; } .pamt span { font-size: 120px; font-weight: 800; } .pamt small { font-size: 30px; color: #777; }
.tick { font-size: 32px; font-weight: 700; margin-top: 10px; color: #2a7a4b; opacity: 0; } .tick.on { background: #e6f7ec; border-radius: 999px; padding: 6px 20px; display: inline-block; }
.two { position: absolute; left: 0; right: 0; top: 330px; display: flex; justify-content: center; align-items: center; gap: 26px; }
.mini { position: relative; width: 420px; padding: 34px 34px; background: #e8f6ff; } .mini.yellow { background: #fff6cc; } .lim { font-size: 60px; font-weight: 800; margin: 6px 0; } .mini .muted.red { color: #e0312e; font-weight: 800; }
.neq { display: flex; }
.pill-note { position: absolute; left: 0; right: 0; top: 840px; text-align: center; font-size: 48px; font-weight: 800; } .pill-note::before { content: ""; }
.month { left: 140px; width: 800px; height: 170px; padding: 22px 40px; display: flex; align-items: center; gap: 40px; background: #fff; }
.mlabel { background: #cfd5e4; border-radius: 16px; padding: 10px 24px; font-size: 36px; font-weight: 800; } .mamt { font-size: 40px; font-weight: 700; } .mamt b { font-size: 56px; margin-left: 10px; } .mexp { margin-left: auto; color: #e0312e; border: 4px solid #e0312e; border-radius: 12px; padding: 4px 16px; font-size: 30px; font-weight: 800; transform: rotate(-8deg); }
.scr-in { position: relative; width: 368px; height: 728px; }
.screen { position: absolute; border-radius: 36px; overflow: hidden; background: #f4f6fa; font-size: 24px; }
.ig-top { padding: 40px 24px 10px; font-weight: 800; font-size: 26px; border-bottom: 2px solid #ddd; } .ig-prof { display: flex; gap: 16px; align-items: center; padding: 18px 20px; } .ig-stats { display: flex; flex-direction: column; } .ig-stats b { font-size: 30px; } .ig-stats span { font-size: 20px; color: #666; }
.ig-bio { padding: 0 20px 14px; font-size: 21px; font-weight: 600; color: #333; }
.ig-btns { display: flex; gap: 10px; padding: 0 20px; } .ig-btn { flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; border-radius: 12px; padding: 8px 0; font-weight: 700; font-size: 20px; color: #fff; } .ig-btn.ig { background: #d62976; } .ig-btn.fb { background: #1877f2; }
.ig-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; padding: 18px 10px; } .ig-post { aspect-ratio: 4/5; background: #bfe3f7; border-radius: 8px; display: flex; align-items: flex-end; padding: 8px; } .ig-post.b { background: #ffe9a8; } .ig-post.c { background: #cdeed8; } .ig-post span { background: #141414; color: #fff; font-size: 14px; padding: 3px 8px; border-radius: 999px; }
.logo { display: inline-flex; flex: none; }
.quote { left: 110px; top: 300px; width: 860px; padding: 34px 44px; background: #fff; }
.qh { display: flex; align-items: center; gap: 18px; font-size: 44px; font-weight: 800; border-bottom: 5px solid #eee; padding-bottom: 20px; }
.qrow { display: flex; justify-content: space-between; align-items: center; font-size: 32px; padding: 18px 0; border-bottom: 3px dashed #e5e5e5; } .qrow b { font-size: 36px; }
.qget { display: flex; justify-content: space-between; align-items: center; margin-top: 22px; background: #fff2f1; border: 5px solid #e0312e; border-radius: 18px; padding: 16px 24px; font-size: 32px; } .qget b { color: #e0312e; font-size: 52px; }
.fine { font-size: 28px; color: #666; margin-top: 18px; line-height: 1.4; } .fine.center { text-align: center; }
.slider { position: relative; padding: 70px 10px 20px; } .strack { position: relative; height: 70px; background: #e6e3da; border-radius: 999px; border: 5px solid var(--ink); } .sfill { position: absolute; left: 0; top: 0; height: 100%; width: 62%; background: #2ebd6b; border-radius: 999px; }
.knob { position: absolute; left: 0; top: -6px; width: 72px; height: 72px; border-radius: 50%; background: #fff; border: 5px solid var(--ink); display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: 800; color: #2ebd6b; }
.slock { position: absolute; right: 24px; top: 10px; font-size: 36px; } .mark { position: absolute; left: 410px; top: 6px; background: #141414; color: #fff; font-size: 28px; padding: 4px 16px; border-radius: 999px; }
.mark::after { content: ""; position: absolute; left: 50%; top: 100%; width: 4px; height: 36px; background: var(--ink); } .big2 { font-size: 40px; margin-top: 20px; }
.bk { background: #fff; } .bk-top { background: #e2136e; color: #fff; font-size: 34px; font-weight: 800; padding: 46px 24px 16px; } .bk-bal { display: flex; justify-content: space-between; padding: 14px 24px; font-size: 22px; color: #666; }
.bk-ok { text-align: center; padding: 30px 20px; } .okc { width: 140px; height: 140px; margin: 0 auto; border-radius: 50%; background: #2ebd6b; color: #fff; font-size: 90px; font-weight: 800; display: flex; align-items: center; justify-content: center; border: 6px solid var(--ink); }
.okt { font-size: 38px; font-weight: 800; margin-top: 20px; color: #2a7a4b; } .oks { font-size: 22px; color: #666; margin-top: 6px; } .bk-time { margin: 10px 24px; background: #fff6cc; border: 4px solid var(--ink); border-radius: 14px; padding: 10px; text-align: center; font-size: 26px; font-weight: 800; }
.ledger { left: 140px; top: 280px; width: 800px; padding: 60px 50px 40px; background: #fffdf5; border-radius: 20px; }
.rings { position: absolute; left: 40px; right: 40px; top: -26px; display: flex; justify-content: space-between; } .rings i { width: 28px; height: 44px; border: 6px solid var(--ink); border-radius: 14px; background: #fffdf5; }
.lt { font-size: 44px; font-weight: 800; text-align: center; text-decoration: underline; text-decoration-color: #e0312e; text-underline-offset: 10px; margin-bottom: 20px; }
.lrow { display: flex; justify-content: space-between; align-items: center; font-size: 32px; padding: 14px 0; border-bottom: 3px solid #e9e4d6; } .lrow.dim { color: #aaa; } .lrow b { font-size: 40px; } .lrow.green { color: #2a7a4b; } .lrow.green b { color: #2a7a4b; } .lrow small { font-size: 28px; color: #777; }
.lsum { display: flex; justify-content: space-between; align-items: center; font-size: 40px; font-weight: 800; padding-top: 24px; } .redb { color: #e0312e; font-size: 76px; display: inline-block; }
.chat { background: #f0f2f5; } .ch-top { display: flex; align-items: center; gap: 12px; padding: 40px 20px 12px; background: #fff; border-bottom: 3px solid #ddd; font-size: 26px; font-weight: 800; }
.bub { max-width: 82%; padding: 12px 18px; border-radius: 20px; font-size: 23px; font-weight: 600; margin: 18px 14px 0; line-height: 1.35; border: 4px solid var(--ink); } .bub.me { background: var(--oa-accent); color: #fff; margin-left: auto; } .bub.them { background: #fff; }
.ch-in { position: absolute; left: 14px; right: 14px; bottom: 16px; background: #fff; border: 4px solid var(--ink); border-radius: 999px; padding: 10px 20px; font-size: 22px; color: #888; display: flex; justify-content: space-between; } .ch-in span { color: var(--oa-accent); }
.bigcta { position: absolute; left: 0; right: 0; top: 110px; text-align: center; font-size: 110px; font-weight: 800; color: var(--hl); -webkit-text-stroke: 5px var(--ink); paint-order: stroke fill; letter-spacing: 1px; }
.end { position: absolute; left: 0; right: 0; top: 230px; display: flex; flex-direction: column; align-items: center; gap: 22px; }
.ename { font-size: 110px; font-weight: 800; color: var(--oa-primary); -webkit-text-stroke: 4px var(--ink); paint-order: stroke fill; } .etag { font-size: 40px; font-weight: 700; color: #333; }
.social { display: flex; align-items: center; gap: 18px; background: #fff; border: 6px solid var(--ink); border-radius: 999px; padding: 14px 40px; font-size: 40px; font-weight: 800; } .social .ig { color: #d62976; display: inline-flex; } .social .fb { color: #1877f2; display: inline-flex; }
.note { } .month, .mini, .price, .quote, .ledger, .term, .screen, .end, .bigcta, .pill-note { will-change: transform; }
"""

TEMPLATE = """<template>
  <style>{css}</style>
  <div id="root" data-composition-id="{id}" data-width="{w}" data-height="{h}" style="--bg:{bg};--ink:{ink};--hl:{hl};--oa-primary:{primary};--oa-accent:{accent}">
    <svg class="stage" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{spot}{svg}</svg>
    {html}
    <svg class="stage top" viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="pointer-events:none">{top}</svg>
    {cap}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.fromTo("#cap", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.35, ease: "expo.out" }}, 0.05);
    {tl}
    window.__timelines["{id}"] = tl;
  </script>
</template>
"""

INDEX = """<!doctype html>
<html lang="bn">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {w}px; height: {h}px; overflow: hidden; background: {bg}; }}
      #root {{ width: 100%; height: 100%; position: relative; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{w}" data-height="{h}">
{scenes}

{audio}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""


def media_seconds(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())


def main():
    comps = ROOT / "compositions"
    comps.mkdir(exist_ok=True)
    for old in comps.glob("s*.html"):
        old.unlink()
    t = 0.0
    hosts, audio, chapters = [], [], []
    for i, ln in enumerate(SC["lines"]):
        cue = CUES[ln["id"]]
        vo_dur = round(media_seconds(ROOT / cue["file"]), 3)
        dur = round(LEAD + max(vo_dur, cue["duration"]) + TAIL + ln.get("hold", 0), 3)
        sc = SCENES[ln["scene"]](dur)
        html = TEMPLATE.format(css=CSS, id=ln["id"], w=W, h=H, bg=BG, ink=INK, hl=YELLOW, primary=PRIMARY, accent=ACCENT, spot=spot(), svg=sc.get("svg", ""),
                               html=sc.get("html", ""), top=sc.get("top", ""), cap=cap_html(ln["cap"]), tl="\n    ".join(sc["tl"]))
        (comps / f"{ln['id']}.html").write_text(html, encoding="utf-8")
        hosts.append(f'      <div id="{ln["id"]}" data-composition-id="{ln["id"]}" data-composition-src="compositions/{ln["id"]}.html" '
                     f'data-start="{t:.3f}" data-duration="{dur}" data-track-index="1" data-track-kind="graphics" data-width="{W}" data-height="{H}"></div>')
        audio.append(f'      <audio id="vo-{ln["id"]}" class="clip" src="{cue["file"]}" data-start="{t + LEAD:.3f}" data-duration="{vo_dur:.3f}" data-track-index="2" data-volume="1"></audio>')
        if i:
            audio.append(f'      <audio id="sfx-cut{i}" class="clip" src="assets/sfx/whoosh-short.mp3" data-start="{max(0, t - 0.05):.3f}" data-duration="0.57" data-track-index="3" data-volume="0.1"></audio>')
        for k, (name, st, vol) in enumerate(sc.get("sfx", [])):
            if st + 0.4 < dur:
                audio.append(f'      <audio id="sfx-{ln["id"]}-{k}" class="clip" src="assets/sfx/{"click-soft" if name == "click" else name}.mp3" data-start="{t + st:.3f}" data-duration="0.37" data-track-index="{4 + k % 3}" data-volume="{vol}"></audio>')
        chapters.append({"id": ln["id"], "start": round(t, 3), "duration": dur, "cap": ln["cap"]})
        t = round(t + dur, 3)
    total = round(t, 3)
    (ROOT / "index.html").write_text(INDEX.format(w=W, h=H, bg=BG, total=total, scenes="\n".join(hosts), audio="\n".join(audio)), encoding="utf-8")
    (HERE / "chapters.json").write_text(json.dumps({"total": total, "scenes": chapters}, ensure_ascii=False, indent=1), encoding="utf-8")
    job = {"n": 1, "part": 1, "of": 1, "dir": ROOT.name, "folder": ROOT.name, "video_file": SC["title"], "asset": f"{ROOT.name}.mp4",
           "seconds": total, "company": "One Access", "post": SC["title"], "date": f"{int(total // 60)}:{int(total % 60):02d}"}
    (ROOT / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(SC['lines'])} scenes, total {total:.1f} s, logo: {'assets/img/logo.png' if LOGO_PNG else 'placeholder mark'}")


if __name__ == "__main__":
    main()
