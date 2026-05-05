#!/usr/bin/env python3
"""
gen_assets.py  v6 — Cuter chick sprites (ARGB8888, 160×160) for LVGL.

Bigger eyes with highlights, heart pupils when speaking, teardrop sad eyes,
floating hearts for speak state, bouncing glow dots for think state.
"""

from PIL import Image, ImageDraw
import struct, os, math

OUT  = 160
DRAW = 384

OUT_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Palette ───────────────────────────────────────────────────────────────────
OUTLINE  = (28,  18,   8)
YELLOW   = (255, 218,  30)
D_YEL    = (215, 168,  12)
LT_YEL   = (255, 238,  95)   # highlight on body/head
ORANGE   = (255, 140,   5)
COMB_R   = (240,  60,  60)
EYE_WH   = (255, 255, 255)
IRIS_BL  = (80,  170, 250)
IRIS_LT  = (155, 215, 255)   # light inner iris gradient
EYE_BK   = (18,  10,   2)
BLUSH    = (255, 160, 148)
SHELL    = (215, 210, 185)
MOUTH_IN = (195,  55,  55)
MOUTH_BT = (160,  38,  38)
DOT_GY   = (210, 210, 210)
SWEAT    = (155, 215, 255)
TEAR     = (135, 200, 255)
HEART_R  = (255,  75, 100)
HEART_PK = (255, 130, 150)

S  = DRAW / 192
OW = round(5 * S)

def sc(v):
    return int(v * S)

# ── Low-level drawing helpers ─────────────────────────────────────────────────

def _ell(d, b, fill, ow=None):
    ow = ow or OW
    d.ellipse([b[0]-ow, b[1]-ow, b[2]+ow, b[3]+ow], fill=OUTLINE+(255,))
    d.ellipse(b, fill=fill+(255,))

def _poly(d, pts, fill, ow=None):
    ow = ow or OW
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    exp = []
    for x, y in pts:
        dx, dy = x-cx, y-cy
        r = math.hypot(dx, dy)
        f = (r+ow)/r if r > 0 else 1
        exp.append((int(cx+dx*f), int(cy+dy*f)))
    d.polygon(exp, fill=OUTLINE+(255,))
    d.polygon(pts, fill=fill+(255,))

# ── Chick body components ─────────────────────────────────────────────────────

def _body(d, dy=0):
    dy = sc(dy)
    # Main body — slightly rounder
    _ell(d, [sc(40), sc(120)+dy, sc(152), sc(190)+dy], YELLOW)
    # Wings — cute ovals on sides
    _ell(d, [sc(10), sc(128)+dy, sc(52),  sc(170)+dy], D_YEL, ow=round(4*S))
    _ell(d, [sc(140),sc(128)+dy, sc(182), sc(170)+dy], D_YEL, ow=round(4*S))
    # Body highlight (gives a rounded 3-D look)
    d.ellipse([sc(66), sc(126)+dy, sc(126), sc(156)+dy], fill=LT_YEL+(140,))
    # Feet
    _poly(d, [(sc(70), sc(188)+dy),(sc(58), sc(196)+dy),(sc(67), sc(196)+dy)], ORANGE, ow=round(3*S))
    _poly(d, [(sc(122),sc(188)+dy),(sc(125),sc(196)+dy),(sc(133),sc(196)+dy)], ORANGE, ow=round(3*S))
    # Shell fragments on lower body
    d.polygon([(sc(42),sc(184)+dy),(sc(52),sc(169)+dy),(sc(62),sc(184)+dy)], fill=OUTLINE+(255,))
    d.polygon([(sc(44),sc(183)+dy),(sc(52),sc(171)+dy),(sc(60),sc(183)+dy)], fill=SHELL+(255,))
    d.polygon([(sc(130),sc(184)+dy),(sc(140),sc(169)+dy),(sc(150),sc(184)+dy)], fill=OUTLINE+(255,))
    d.polygon([(sc(132),sc(183)+dy),(sc(140),sc(171)+dy),(sc(148),sc(183)+dy)], fill=SHELL+(255,))

def _head(d, dy=0):
    dy = sc(dy)
    _ell(d, [sc(34), sc(10)+dy, sc(158), sc(134)+dy], YELLOW)
    # Subtle forehead highlight
    d.ellipse([sc(68), sc(14)+dy, sc(124), sc(50)+dy], fill=LT_YEL+(100,))

def _comb(d, dy=0):
    dy = sc(dy)
    ow4 = round(4*S)
    _ell(d, [sc(46), sc(-2)+dy,  sc(82),  sc(34)+dy], COMB_R, ow=ow4)
    _ell(d, [sc(76), sc(-10)+dy, sc(116), sc(30)+dy], COMB_R, ow=ow4)
    _ell(d, [sc(110),sc(-2)+dy,  sc(146), sc(34)+dy], COMB_R, ow=ow4)

def _blush(d, dy=0):
    dy = sc(dy)
    # Larger, softer oval blush marks below and outside each eye
    d.ellipse([sc(36), sc(88)+dy, sc(80), sc(110)+dy], fill=BLUSH+(195,))
    d.ellipse([sc(112),sc(88)+dy, sc(156),sc(110)+dy], fill=BLUSH+(195,))

# ── Eye variants ──────────────────────────────────────────────────────────────

def _eyes_open(d, dy=0, wide=False):
    dy   = sc(dy)
    r    = sc(22) if not wide else sc(26)
    for cx in [sc(74), sc(118)]:
        cy = sc(64) + dy
        # Outline + white sclera
        d.ellipse([cx-r-OW, cy-r-OW, cx+r+OW, cy+r+OW], fill=OUTLINE+(255,))
        d.ellipse([cx-r, cy-r, cx+r, cy+r],               fill=EYE_WH+(255,))
        # Blue iris
        ir = r - sc(2)
        d.ellipse([cx-ir, cy-ir+sc(3), cx+ir, cy+ir+sc(2)], fill=IRIS_BL+(255,))
        # Light iris upper half (gradient feel)
        d.ellipse([cx-ir+sc(2), cy-ir+sc(3), cx+ir-sc(2), cy+sc(1)], fill=IRIS_LT+(150,))
        # Black pupil (slightly oval, shifted down)
        pr = sc(12)
        d.ellipse([cx-pr, cy-pr+sc(4), cx+pr, cy+pr+sc(4)], fill=EYE_BK+(255,))
        # Main highlight — upper-left teardrop
        d.ellipse([cx-sc(11), cy-sc(10), cx-sc(2), cy-sc(1)], fill=EYE_WH+(255,))
        # Small secondary highlight
        d.ellipse([cx+sc(4), cy+sc(3),  cx+sc(8),  cy+sc(7)], fill=EYE_WH+(190,))
        # Top lash line
        if wide:
            for lx in [-sc(8), 0, sc(8)]:
                d.line([cx+lx, cy-r, cx+lx+sc(1), cy-r-sc(7)],
                       fill=OUTLINE+(255,), width=round(3*S))

def _eyes_blink(d, dy=0):
    dy = sc(dy)
    w  = round(6*S)
    # Closed-eye arcs (～ shape)
    d.arc([sc(54), sc(54)+dy, sc(94),  sc(80)+dy], 200, 340, fill=OUTLINE+(255,), width=w)
    d.arc([sc(98), sc(54)+dy, sc(138), sc(80)+dy], 200, 340, fill=OUTLINE+(255,), width=w)
    # Tiny shine dots so eyes look soft even closed
    d.ellipse([sc(68), sc(76)+dy, sc(75), sc(81)+dy], fill=EYE_WH+(160,))
    d.ellipse([sc(114),sc(76)+dy, sc(121),sc(81)+dy], fill=EYE_WH+(160,))

def _eyes_squint(d, dy=0):
    """Happy thinking squint — upturned arc corners for a content look."""
    dy = sc(dy)
    w  = round(7*S)
    for cx in [sc(74), sc(118)]:
        d.arc([cx-sc(18), sc(54)+dy, cx+sc(18), sc(82)+dy], 200, 340,
              fill=OUTLINE+(255,), width=w)
        # Cute upturned corner marks
        d.line([cx-sc(16), sc(70)+dy, cx-sc(22), sc(66)+dy],
               fill=OUTLINE+(255,), width=round(4*S))
        d.line([cx+sc(16), sc(70)+dy, cx+sc(22), sc(66)+dy],
               fill=OUTLINE+(255,), width=round(4*S))

def _eyes_heart(d, dy=0):
    """Heart-shaped pupils — used when speaking (happy & expressive)."""
    dy = sc(dy)
    r  = sc(22)
    for cx in [sc(74), sc(118)]:
        cy = sc(64) + dy
        # Outline + white sclera
        d.ellipse([cx-r-OW, cy-r-OW, cx+r+OW, cy+r+OW], fill=OUTLINE+(255,))
        d.ellipse([cx-r, cy-r, cx+r, cy+r],               fill=EYE_WH+(255,))
        # Heart — two circles + downward triangle
        hr = sc(13)
        hcy = cy - sc(2)
        d.ellipse([cx-hr, hcy-hr, cx,    hcy+hr//2], fill=HEART_R+(255,))
        d.ellipse([cx,    hcy-hr, cx+hr, hcy+hr//2], fill=HEART_R+(255,))
        d.polygon([(cx-hr, hcy+hr//4), (cx+hr, hcy+hr//4),
                   (cx, hcy+hr+hr//2)],                fill=HEART_R+(255,))
        # Highlight on heart
        d.ellipse([cx-sc(9), hcy-sc(9), cx-sc(2), hcy-sc(2)], fill=EYE_WH+(255,))
        # Small pink highlight on lower half
        d.ellipse([cx+sc(2), hcy+sc(2), cx+sc(6), hcy+sc(6)], fill=HEART_PK+(180,))

def _eyes_sad(d, dy=0):
    """Big sad crescent eyes with teardrops."""
    dy = sc(dy)
    r  = sc(20)
    for cx in [sc(74), sc(118)]:
        cy = sc(64) + dy
        # Outline + white sclera
        d.ellipse([cx-r-OW, cy-r-OW, cx+r+OW, cy+r+OW], fill=OUTLINE+(255,))
        d.ellipse([cx-r, cy-r, cx+r, cy+r],               fill=EYE_WH+(255,))
        # Sad crescent: full iris then erase upper half with white
        ir = r - sc(2)
        d.ellipse([cx-ir, cy-ir+sc(3), cx+ir, cy+ir+sc(2)], fill=IRIS_BL+(255,))
        # Mask upper half to create crescent (iris only visible in bottom half)
        d.ellipse([cx-ir, cy-ir+sc(3), cx+ir, cy+sc(4)],    fill=EYE_WH+(255,))
        # Pupil (only lower region visible)
        d.ellipse([cx-sc(10), cy+sc(2), cx+sc(10), cy+sc(16)], fill=EYE_BK+(255,))
        # Sad eyebrows — inner ends raised (classic sad brow)
        d.line([cx-sc(14), cy-r-sc(4), cx+sc(4), cy-r-sc(10)],
               fill=OUTLINE+(255,), width=round(5*S))
    # Teardrops below each eye
    for cx in [sc(74), sc(118)]:
        cy = sc(64) + dy
        tx, ty = cx - sc(4), cy + r + sc(4)
        d.polygon([(tx, ty), (tx-sc(4), ty+sc(14)), (tx+sc(4), ty+sc(14))],
                  fill=OUTLINE+(255,))
        d.polygon([(tx, ty+sc(2)), (tx-sc(3), ty+sc(13)), (tx+sc(3), ty+sc(13))],
                  fill=TEAR+(255,))

# ── Beak ─────────────────────────────────────────────────────────────────────

def _beak_closed(d, dy=0):
    dy = sc(dy)
    _poly(d, [(sc(70),sc(96)+dy),(sc(122),sc(96)+dy),(sc(96),sc(122)+dy)], ORANGE)
    # Small cute smile crease at beak bottom
    w3 = round(3*S)
    d.line([sc(80), sc(109)+dy, sc(96), sc(113)+dy], fill=OUTLINE+(255,), width=w3)
    d.line([sc(96), sc(113)+dy, sc(112),sc(109)+dy], fill=OUTLINE+(255,), width=w3)

def _beak_open(d, dy=0):
    dy = sc(dy)
    # Upper beak
    _poly(d, [(sc(68),sc(90)+dy),(sc(124),sc(90)+dy),
              (sc(110),sc(112)+dy),(sc(82),sc(112)+dy)], ORANGE)
    # Lower beak
    _poly(d, [(sc(82),sc(112)+dy),(sc(110),sc(112)+dy),
              (sc(116),sc(136)+dy),(sc(76),sc(136)+dy)], ORANGE)
    # Mouth interior
    d.ellipse([sc(80),sc(110)+dy, sc(112),sc(136)+dy], fill=MOUTH_IN+(255,))
    # Tongue (rounded, with center dividing line)
    d.ellipse([sc(84),sc(120)+dy, sc(108),sc(136)+dy], fill=(225,90,90,255))
    d.line([sc(96),sc(120)+dy, sc(96),sc(134)+dy],
           fill=MOUTH_BT+(255,), width=round(3*S))

# ── Per-state decorations ────────────────────────────────────────────────────

def _think_dots(d, phase=0):
    """Bouncing thought dots — active dot glows white."""
    positions = [(sc(126), sc(36)), (sc(148), sc(20)), (sc(168), sc(6))]
    sizes     = [round(9*S), round(12*S), round(15*S)]
    for i, ((x, y), r) in enumerate(zip(positions, sizes)):
        active = (i == phase % 3)
        yo     = round(-8*S) if active else 0
        color  = EYE_WH if active else DOT_GY
        d.ellipse([x-r-1, y-r-1+yo, x+r+1, y+r+1+yo], fill=OUTLINE+(255,))
        d.ellipse([x-r,   y-r+yo,   x+r,   y+r+yo],   fill=color+(255,))
        if active:
            # Shine on active dot
            sr = round(3*S)
            d.ellipse([x-r+sr, y-r+yo+sr, x-r+sr*3, y-r+yo+sr*3], fill=EYE_WH+(200,))

def _sweat(d):
    d.polygon([(sc(142),sc(48)),(sc(152),sc(28)),(sc(162),sc(48))], fill=OUTLINE+(255,))
    d.polygon([(sc(143),sc(47)),(sc(152),sc(30)),(sc(161),sc(47))], fill=SWEAT+(255,))
    _ell(d, [sc(139),sc(46), sc(165),sc(72)], SWEAT, ow=round(3*S))

def _hearts(d):
    """Two floating hearts for speaking state."""
    for x, y, hr, alpha in [(sc(150), sc(52), sc(10), 230),
                             (sc(164), sc(30), sc(7),  180)]:
        d.ellipse([x-hr, y-hr, x,    y+hr//2], fill=HEART_R+(alpha,))
        d.ellipse([x,    y-hr, x+hr, y+hr//2], fill=HEART_R+(alpha,))
        d.polygon([(x-hr, y+hr//4), (x+hr, y+hr//4), (x, y+hr+hr//2)],
                  fill=HEART_R+(alpha,))

# ── Assemble sprite ───────────────────────────────────────────────────────────

def _chick_sprite(eyes_fn, beak_fn, extra_fn=None, dy=0):
    img = Image.new('RGBA', (DRAW, DRAW), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    _body(d, dy)
    _head(d, dy)
    _comb(d, dy)
    _blush(d, dy)
    eyes_fn(d, dy)
    beak_fn(d, dy)
    if extra_fn:
        extra_fn(d)
    return img.resize((OUT, OUT), Image.LANCZOS)

# ── ARGB8888 encoder ─────────────────────────────────────────────────────────

def to_argb8888(img):
    """LVGL ARGB8888 byte order: B G R A."""
    buf = bytearray(OUT * OUT * 4)
    idx = 0
    for y in range(OUT):
        for x in range(OUT):
            r, g, b, a = img.getpixel((x, y))
            buf[idx]   = b
            buf[idx+1] = g
            buf[idx+2] = r
            buf[idx+3] = a
            idx += 4
    return bytes(buf)

# ── Frame definitions ─────────────────────────────────────────────────────────

FRAMES = [
    ("idle_0",   lambda: _chick_sprite(_eyes_open,   _beak_closed)),
    ("idle_1",   lambda: _chick_sprite(_eyes_blink,  _beak_closed)),
    ("listen_0", lambda: _chick_sprite(lambda d, dy=0: _eyes_open(d, dy, wide=True),
                                       _beak_closed, dy=-4)),
    ("listen_1", lambda: _chick_sprite(lambda d, dy=0: _eyes_open(d, dy, wide=True),
                                       _beak_closed, dy=-12)),
    ("think_0",  lambda: _chick_sprite(_eyes_squint, _beak_closed,
                                       extra_fn=lambda d: _think_dots(d, 0))),
    ("think_1",  lambda: _chick_sprite(_eyes_squint, _beak_closed,
                                       extra_fn=lambda d: _think_dots(d, 1))),
    ("think_2",  lambda: _chick_sprite(_eyes_squint, _beak_closed,
                                       extra_fn=lambda d: _think_dots(d, 2))),
    ("speak_0",  lambda: _chick_sprite(_eyes_heart,  _beak_closed, extra_fn=_hearts)),
    ("speak_1",  lambda: _chick_sprite(_eyes_heart,  _beak_open,   extra_fn=_hearts)),
    ("error_0",  lambda: _chick_sprite(_eyes_sad,    _beak_closed, extra_fn=_sweat)),
]

if __name__ == "__main__":
    print(f"Cute chick sprites  {DRAW}→{OUT}px  ARGB8888  ({len(FRAMES)} frames)")
    total = 0
    for name, fn in FRAMES:
        img  = fn()
        data = to_argb8888(img)
        with open(os.path.join(OUT_DIR, f"chick_{name}.bin"), "wb") as f:
            f.write(data)
        img.save(os.path.join(OUT_DIR, f"chick_{name}.png"))
        total += len(data)
        print(f"  {name}  {len(data):,} B")
    print(f"Total {total:,} B  ({total/1024:.1f} KB)")
