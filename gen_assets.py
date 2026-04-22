#!/usr/bin/env python3
"""
gen_assets.py  v5 — Transparent chick sprites (ARGB8888, 160×160) for LVGL.

Pipeline: draw chick on 384×384 RGBA canvas → resize to 160×160 (LANCZOS) → ARGB8888 bytes.
Background is fully transparent — LVGL composites over any background widget.
"""

from PIL import Image, ImageDraw
import struct, os, math

OUT   = 160
DRAW  = 384    # high-res working canvas for quality

OUT_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Palette ───────────────────────────────────────────────────────────────────
OUTLINE  = (28,  18,   8)
YELLOW   = (255, 218,  30)
D_YEL    = (210, 165,  10)
ORANGE   = (255, 132,   0)
COMB_R   = (230,  50,  50)
EYE_WH   = (255, 255, 255)
IRIS_BL  = (80,  160, 240)
EYE_BK   = (20,  12,   4)
BLUSH    = (255, 175, 165)
SHELL    = (210, 205, 182)
MOUTH_IN = (190,  50,  50)
DOT_GY   = (210, 210, 210)
SWEAT    = (160, 220, 255)

S  = DRAW / 192   # scale factor from original 192px coords
OW = round(5 * S)

def sc(v):
    """Scale a coordinate from 192-space to DRAW-space."""
    return int(v * S)

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

# ── Chick components (DRAW×DRAW canvas, RGBA) ────────────────────────────────

def _body(d, dy=0):
    dy = sc(dy)
    _ell(d, [sc(44),sc(124)+dy, sc(148),sc(186)+dy], YELLOW)
    _ell(d, [sc(14),sc(132)+dy, sc(50), sc(166)+dy], D_YEL, ow=round(4*S))
    _ell(d, [sc(142),sc(132)+dy,sc(178),sc(166)+dy], D_YEL, ow=round(4*S))
    _poly(d, [(sc(70),sc(184)+dy),(sc(58),sc(192)+dy),(sc(66),sc(192)+dy)], ORANGE, ow=round(3*S))
    _poly(d, [(sc(122),sc(184)+dy),(sc(126),sc(192)+dy),(sc(134),sc(192)+dy)], ORANGE, ow=round(3*S))
    d.polygon([(sc(44),sc(182)+dy),(sc(54),sc(168)+dy),(sc(64),sc(182)+dy)], fill=OUTLINE+(255,))
    d.polygon([(sc(46),sc(182)+dy),(sc(54),sc(170)+dy),(sc(62),sc(182)+dy)], fill=SHELL+(255,))
    d.polygon([(sc(128),sc(182)+dy),(sc(138),sc(168)+dy),(sc(148),sc(182)+dy)], fill=OUTLINE+(255,))
    d.polygon([(sc(130),sc(182)+dy),(sc(138),sc(170)+dy),(sc(146),sc(182)+dy)], fill=SHELL+(255,))

def _head(d, dy=0):
    dy = sc(dy)
    _ell(d, [sc(36),sc(12)+dy, sc(156),sc(132)+dy], YELLOW)

def _comb(d, dy=0):
    dy = sc(dy)
    ow4 = round(4*S)
    _ell(d, [sc(48), sc(0)+dy,  sc(80), sc(36)+dy], COMB_R, ow=ow4)
    _ell(d, [sc(78), sc(-8)+dy, sc(114),sc(28)+dy], COMB_R, ow=ow4)
    _ell(d, [sc(112),sc(0)+dy,  sc(144),sc(36)+dy], COMB_R, ow=ow4)

def _blush(d, dy=0):
    dy = sc(dy)
    d.ellipse([sc(42),sc(86)+dy, sc(78),sc(104)+dy], fill=BLUSH+(255,))
    d.ellipse([sc(114),sc(86)+dy,sc(150),sc(104)+dy], fill=BLUSH+(255,))

def _eyes_open(d, dy=0, wide=False):
    dy = sc(dy); e = round(4*S) if wide else 0
    for cx in [sc(74), sc(118)]:
        _ell(d, [cx-sc(16)-e, sc(50)+dy, cx+sc(16)+e, sc(82)+dy], EYE_WH, ow=OW+round(S))
        d.ellipse([cx-sc(14)-e, sc(52)+dy, cx+sc(14)+e, sc(80)+dy], fill=IRIS_BL+(255,))
        d.ellipse([cx-sc(9), sc(58)+dy, cx+sc(9), sc(74)+dy], fill=EYE_BK+(255,))
        d.ellipse([cx-sc(8), sc(59)+dy, cx-sc(3), sc(64)+dy], fill=EYE_WH+(255,))

def _eyes_blink(d, dy=0):
    dy = sc(dy); w = round(6*S)
    d.arc([sc(58),sc(58)+dy, sc(90),sc(84)+dy],  195, 345, fill=OUTLINE+(255,), width=w)
    d.arc([sc(102),sc(58)+dy,sc(134),sc(84)+dy], 195, 345, fill=OUTLINE+(255,), width=w)

def _eyes_squint(d, dy=0):
    dy = sc(dy)
    for cx in [sc(74), sc(118)]:
        _ell(d, [cx-sc(16), sc(60)+dy, cx+sc(16), sc(76)+dy], EYE_WH)
        d.ellipse([cx-sc(11), sc(62)+dy, cx+sc(11), sc(74)+dy], fill=EYE_BK+(255,))
        d.ellipse([cx-sc(10), sc(63)+dy, cx-sc(5), sc(68)+dy], fill=EYE_WH+(255,))

def _eyes_sparkle(d, dy=0):
    dy = sc(dy)
    for cx in [sc(74), sc(118)]:
        _ell(d, [cx-sc(16), sc(50)+dy, cx+sc(16), sc(82)+dy], EYE_WH, ow=OW+round(S))
        for ang in range(0, 360, 60):
            a = math.radians(ang)
            x1 = int(cx + sc(12)*math.cos(a))
            y1 = int(sc(66)+dy + sc(12)*math.sin(a))
            d.line([cx, sc(66)+dy, x1, y1], fill=OUTLINE+(255,), width=round(3*S))
        d.ellipse([cx-sc(5), sc(61)+dy, cx+sc(5), sc(71)+dy], fill=EYE_BK+(255,))

def _eyes_sad(d, dy=0):
    dy = sc(dy); w = round(6*S)
    d.line([sc(58),sc(62)+dy, sc(90),sc(72)+dy],  fill=OUTLINE+(255,), width=w)
    d.line([sc(102),sc(62)+dy,sc(134),sc(72)+dy], fill=OUTLINE+(255,), width=w)
    d.ellipse([sc(65),sc(68)+dy, sc(83),sc(82)+dy],  fill=EYE_BK+(255,))
    d.ellipse([sc(109),sc(68)+dy,sc(127),sc(82)+dy], fill=EYE_BK+(255,))

def _beak_closed(d, dy=0):
    dy = sc(dy)
    _poly(d, [(sc(72),sc(96)+dy),(sc(120),sc(96)+dy),(sc(96),sc(120)+dy)], ORANGE)

def _beak_open(d, dy=0):
    dy = sc(dy)
    _poly(d, [(sc(70),sc(90)+dy),(sc(122),sc(90)+dy),(sc(110),sc(110)+dy),(sc(82),sc(110)+dy)], ORANGE)
    _poly(d, [(sc(82),sc(110)+dy),(sc(110),sc(110)+dy),(sc(116),sc(132)+dy),(sc(76),sc(132)+dy)], ORANGE)
    d.ellipse([sc(82),sc(108)+dy, sc(110),sc(132)+dy], fill=MOUTH_IN+(255,))
    d.ellipse([sc(86),sc(118)+dy, sc(106),sc(130)+dy], fill=(225,80,80,255))

def _think_dots(d, phase=0):
    positions = [(sc(124),sc(40)),(sc(142),sc(24)),(sc(160),sc(10))]
    sizes     = [round(9*S), round(12*S), round(15*S)]
    for i, ((x,y),r) in enumerate(zip(positions, sizes)):
        yo = round(-6*S) if i==(phase%3) else 0
        d.ellipse([x-r-1,y-r-1+yo,x+r+1,y+r+1+yo], fill=OUTLINE+(255,))
        d.ellipse([x-r,y-r+yo,x+r,y+r+yo], fill=DOT_GY+(255,))

def _sweat(d):
    d.polygon([(sc(142),sc(52)),(sc(150),sc(34)),(sc(158),sc(52))], fill=OUTLINE+(255,))
    d.polygon([(sc(143),sc(51)),(sc(150),sc(36)),(sc(157),sc(51))], fill=SWEAT+(255,))
    _ell(d, [sc(140),sc(50), sc(160),sc(74)], SWEAT, ow=round(3*S))

# ── Build chick RGBA sprite ───────────────────────────────────────────────────

def _chick_sprite(eyes_fn, beak_fn, extra_fn=None, dy=0):
    img = Image.new('RGBA', (DRAW, DRAW), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    _body(d, dy); _head(d, dy); _comb(d, dy); _blush(d, dy)
    eyes_fn(d, dy)
    beak_fn(d, dy)
    if extra_fn:
        extra_fn(d)
    # Resize to output size with LANCZOS (no pixelation)
    return img.resize((OUT, OUT), Image.LANCZOS)

# ── Encode ARGB8888 (LVGL byte order: B G R A) ───────────────────────────────

def to_argb8888(img):
    """LVGL ARGB8888 stores bytes as B, G, R, A in memory."""
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

# ── Frame factories ───────────────────────────────────────────────────────────

FRAMES = [
    ("idle_0",   lambda: _chick_sprite(_eyes_open,    _beak_closed)),
    ("idle_1",   lambda: _chick_sprite(_eyes_blink,   _beak_closed)),
    ("listen_0", lambda: _chick_sprite(lambda d,dy=0: _eyes_open(d,dy,wide=True), _beak_closed, dy=-6)),
    ("listen_1", lambda: _chick_sprite(lambda d,dy=0: _eyes_open(d,dy,wide=True), _beak_closed, dy=-14)),
    ("think_0",  lambda: _chick_sprite(_eyes_squint,  _beak_closed, extra_fn=lambda d: _think_dots(d,0))),
    ("think_1",  lambda: _chick_sprite(_eyes_squint,  _beak_closed, extra_fn=lambda d: _think_dots(d,1))),
    ("think_2",  lambda: _chick_sprite(_eyes_squint,  _beak_closed, extra_fn=lambda d: _think_dots(d,2))),
    ("speak_0",  lambda: _chick_sprite(_eyes_sparkle, _beak_closed)),
    ("speak_1",  lambda: _chick_sprite(_eyes_sparkle, _beak_open)),
    ("error_0",  lambda: _chick_sprite(_eyes_sad,     _beak_closed, extra_fn=_sweat)),
]

if __name__ == "__main__":
    print(f"Transparent chick sprites  {DRAW}→{OUT}px  ARGB8888  ({len(FRAMES)} frames)")
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
