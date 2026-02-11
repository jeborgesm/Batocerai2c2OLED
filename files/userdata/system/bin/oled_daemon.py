#!/usr/bin/env python3
import os, time, subprocess, socket, re, platform
import xml.etree.ElementTree as ET

FB = "/dev/fb1"
W, H = 128, 64
BPL = W // 8
SIZE = BPL * H
STATE = "/tmp/oled.state"

YELLOW_H = 16
BLUE_Y0 = YELLOW_H
BLUE_H = 48

CACHE_RAW = "/tmp/oled.marquee.raw"
CACHE_KEY = "/tmp/oled.marquee.key"
RAW_NEED  = 128 * 48 // 8

MENU_PAGE_SECONDS = 5  # menu page rotate speed

# Full 5x7 ASCII font: chars 32..126 (95 glyphs * 5 bytes)
FONT5X7 = [
0x00,0x00,0x00,0x00,0x00,  0x00,0x00,0x5F,0x00,0x00,  0x00,0x07,0x00,0x07,0x00,  0x14,0x7F,0x14,0x7F,0x14,
0x24,0x2A,0x7F,0x2A,0x12,  0x23,0x13,0x08,0x64,0x62,  0x36,0x49,0x55,0x22,0x50,  0x00,0x05,0x03,0x00,0x00,
0x00,0x1C,0x22,0x41,0x00,  0x00,0x41,0x22,0x1C,0x00,  0x14,0x08,0x3E,0x08,0x14,  0x08,0x08,0x3E,0x08,0x08,
0x00,0x50,0x30,0x00,0x00,  0x08,0x08,0x08,0x08,0x08,  0x00,0x60,0x60,0x00,0x00,  0x20,0x10,0x08,0x04,0x02,
0x3E,0x51,0x49,0x45,0x3E,  0x00,0x42,0x7F,0x40,0x00,  0x42,0x61,0x51,0x49,0x46,  0x21,0x41,0x45,0x4B,0x31,
0x18,0x14,0x12,0x7F,0x10,  0x27,0x45,0x45,0x45,0x39,  0x3C,0x4A,0x49,0x49,0x30,  0x01,0x71,0x09,0x05,0x03,
0x36,0x49,0x49,0x49,0x36,  0x06,0x49,0x49,0x29,0x1E,  0x00,0x36,0x36,0x00,0x00,  0x00,0x56,0x36,0x00,0x00,
0x08,0x14,0x22,0x41,0x00,  0x14,0x14,0x14,0x14,0x14,  0x00,0x41,0x22,0x14,0x08,  0x02,0x01,0x51,0x09,0x06,
0x32,0x49,0x79,0x41,0x3E,  0x7E,0x11,0x11,0x11,0x7E,  0x7F,0x49,0x49,0x49,0x36,  0x3E,0x41,0x41,0x41,0x22,
0x7F,0x41,0x41,0x22,0x1C,  0x7F,0x49,0x49,0x49,0x41,  0x7F,0x09,0x09,0x09,0x01,  0x3E,0x41,0x49,0x49,0x7A,
0x7F,0x08,0x08,0x08,0x7F,  0x00,0x41,0x7F,0x41,0x00,  0x20,0x40,0x41,0x3F,0x01,  0x7F,0x08,0x14,0x22,0x41,
0x7F,0x40,0x40,0x40,0x40,  0x7F,0x02,0x0C,0x02,0x7F,  0x7F,0x04,0x08,0x10,0x7F,  0x3E,0x41,0x41,0x41,0x3E,
0x7F,0x09,0x09,0x09,0x06,  0x3E,0x41,0x51,0x21,0x5E,  0x7F,0x09,0x19,0x29,0x46,  0x46,0x49,0x49,0x49,0x31,
0x01,0x01,0x7F,0x01,0x01,  0x3F,0x40,0x40,0x40,0x3F,  0x1F,0x20,0x40,0x20,0x1F,  0x7F,0x20,0x18,0x20,0x7F,
0x63,0x14,0x08,0x14,0x63,  0x07,0x08,0x70,0x08,0x07,  0x61,0x51,0x49,0x45,0x43,  0x00,0x7F,0x41,0x41,0x00,
0x02,0x04,0x08,0x10,0x20,  0x00,0x41,0x41,0x7F,0x00,  0x04,0x02,0x01,0x02,0x04,  0x40,0x40,0x40,0x40,0x40,
0x00,0x01,0x02,0x04,0x00,  0x20,0x54,0x54,0x54,0x78,  0x7F,0x48,0x44,0x44,0x38,  0x38,0x44,0x44,0x44,0x20,
0x38,0x44,0x44,0x48,0x7F,  0x38,0x54,0x54,0x54,0x18,  0x08,0x7E,0x09,0x01,0x02,  0x0C,0x52,0x52,0x52,0x3E,
0x7F,0x08,0x04,0x04,0x78,  0x00,0x44,0x7D,0x40,0x00,  0x20,0x40,0x44,0x3D,0x00,  0x7F,0x10,0x28,0x44,0x00,
0x00,0x41,0x7F,0x40,0x00,  0x7C,0x04,0x18,0x04,0x78,  0x7C,0x08,0x04,0x04,0x78,  0x38,0x44,0x44,0x44,0x38,
0x7C,0x14,0x14,0x14,0x08,  0x08,0x14,0x14,0x18,0x7C,  0x7C,0x08,0x04,0x04,0x08,  0x48,0x54,0x54,0x54,0x20,
0x04,0x3F,0x44,0x40,0x20,  0x3C,0x40,0x40,0x20,0x7C,  0x1C,0x20,0x40,0x20,0x1C,  0x3C,0x40,0x30,0x40,0x3C,
0x44,0x28,0x10,0x28,0x44,  0x0C,0x50,0x50,0x50,0x3C,  0x44,0x64,0x54,0x4C,0x44,  0x00,0x08,0x36,0x41,0x00,
0x00,0x00,0x7F,0x00,0x00,  0x00,0x41,0x36,0x08,0x00,  0x08,0x04,0x08,0x10,0x08,
]

def glyph_cols(ch):
    o = ord(ch)
    if 32 <= o <= 126:
        i = (o - 32) * 5
        return FONT5X7[i:i+5]
    i = (ord('?') - 32) * 5
    return FONT5X7[i:i+5]

def _idx_bit(x, y):
    y = (H - 1) - y
    i = y * BPL + (x >> 3)
    b = (x & 7)
    return i, b

def setpx(buf, x, y):
    if 0 <= x < W and 0 <= y < H:
        i, b = _idx_bit(x, y)
        buf[i] |= (1 << b)

def clearpx(buf, x, y):
    if 0 <= x < W and 0 <= y < H:
        i, b = _idx_bit(x, y)
        buf[i] &= ~(1 << b)

def fill_rect_on(buf, x0, y0, x1, y1):
    for y in range(y0, y1):
        for x in range(x0, x1):
            setpx(buf, x, y)

def clear_rect(buf, x0, y0, x1, y1):
    for y in range(y0, y1):
        for x in range(x0, x1):
            clearpx(buf, x, y)

def draw_text(buf, s, x, y, invert=False):
    cx = x
    for ch in s:
        cols = glyph_cols(ch)
        for col, bits in enumerate(cols):
            for row in range(7):
                if bits & (1 << row):
                    (clearpx if invert else setpx)(buf, cx + col, y + row)
        cx += 6

def draw_text_scaled(buf, s, x, y, scale=2, invert=False):
    cx = x
    for ch in s:
        cols = glyph_cols(ch)
        for col, bits in enumerate(cols):
            for row in range(7):
                if bits & (1 << row):
                    for dx in range(scale):
                        for dy in range(scale):
                            (clearpx if invert else setpx)(buf, cx + col*scale + dx, y + row*scale + dy)
        cx += 6 * scale

def write_fb(buf):
    with open(FB, "wb", buffering=0) as f:
        f.write(buf)

def read_state():
    d = {}
    try:
        with open(STATE) as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    d[k] = v
    except Exception:
        pass
    return d

def ip_addr():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("1.1.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"

def cpu_temp():
    try:
        t = int(open("/sys/class/thermal/thermal_zone0/temp").read().strip())
        return f"{t/1000:.1f}C"
    except Exception:
        return "n/a"

def mem_mb():
    try:
        avail = total = 0
        with open("/proc/meminfo","r") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    avail = int(line.split()[1])
                elif line.startswith("MemTotal:"):
                    total = int(line.split()[1])
        return avail // 1024, total // 1024
    except Exception:
        return 0, 0

def cpu_cores():
    return os.cpu_count() or 0

def cpu_max_mhz():
    for path in (
        "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq",
        "/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq",
    ):
        try:
            v = open(path,"r").read().strip()
            if v.isdigit():
                return int(v) // 1000
        except Exception:
            pass
    try:
        mhz = []
        with open("/proc/cpuinfo","r") as f:
            for line in f:
                if line.lower().startswith("cpu mhz"):
                    try:
                        mhz.append(float(line.split(":")[1].strip()))
                    except Exception:
                        pass
        return int(max(mhz)) if mhz else 0
    except Exception:
        return 0

def uptime_hm():
    try:
        sec = float(open("/proc/uptime","r").read().split()[0])
        m = int(sec // 60)
        h = m // 60
        m = m % 60
        return f"{h:02d}:{m:02d}"
    except Exception:
        return "00:00"

def pi_kind():
    # Minimal “what kind of Raspberry”
    try:
        m = open("/proc/device-tree/model","rb").read().decode("utf-8","ignore").replace("\x00","")
    except Exception:
        m = ""
    m = m.lower()
    if "raspberry pi 5" in m: return "Pi5"
    if "raspberry pi 4" in m: return "Pi4"
    if "raspberry pi 3" in m: return "Pi3"
    if "raspberry pi zero" in m: return "Pi0"
    if "raspberry pi" in m: return "Pi"
    return "Pi"

def has_cmd(cmd):
    try:
        subprocess.check_call(["sh","-lc", f"command -v {cmd} >/dev/null 2>&1"])
        return True
    except Exception:
        return False

def rom_base_dir_from_path(rompath):
    rp = (rompath or "").replace("\\","/").strip()
    if rp.startswith("/userdata/roms/"):
        parts = rp.split("/")
        if len(parts) >= 4:
            base = "/".join(parts[:4])
            if os.path.isdir(base):
                return base
    return None

def resolve_arcade_to_real_base(rompath):
    rp = (rompath or "").replace("\\","/").strip()
    name = os.path.basename(rp)
    if not name:
        return None, None
    for sys in ("mame","fbneo","mame2003","mame2010","mame2015","neogeo"):
        cand = f"/userdata/roms/{sys}/{name}"
        if os.path.exists(cand):
            return f"/userdata/roms/{sys}", cand
    return None, None

def resolve_media_path(value, base_dir):
    if not value:
        return None
    v = value.strip()
    if v.startswith("./"):
        v = v[2:]
    if v.startswith("/"):
        return v
    return os.path.join(base_dir, v)



def _norm_path(s: str) -> str:
    return (s or "").strip().replace("\\", "/")

def _looks_like_screenshot(path: str) -> bool:
    """
    Heuristic: treat screenshots/title screens as last resort because they dither into 'static'.
    """
    s = _norm_path(path).lower()
    return any(k in s for k in (
        "screenshot", "screenshots", "snap", "snapshots",
        "title", "titles", "ingame", "ingame", "mixrbv",
        "fanart", "background"
    ))
def find_art_from_gamelist(base_dir, rom_fullpath):
    """
    Strict priority:
      1) gamelist.xml <marquee> (ALWAYS first)
      2) other gamelist tags (wheel/logo/box/thumbnail/image last)
    """
    gamelist = os.path.join(base_dir, "gamelist.xml")
    if not os.path.exists(gamelist):
        return None

    try:
        root = ET.parse(gamelist).getroot()
        target = os.path.basename(rom_fullpath)

        for game in root.findall("game"):
            pth = (game.findtext("path", default="") or "").strip().replace("\\", "/")
            if os.path.basename(pth) != target:
                continue

            # 1) marquee ALWAYS first
            val = (game.findtext("marquee", default="") or "").strip()
            cand = resolve_media_path(val, base_dir)
            if cand and os.path.exists(cand):
                return cand

            # 2) fallbacks in order (put screenshots last)
            fallback_tags = [
                "wheel",
                "logo",
                "box2d",
                "box3d",
                "box",
                "thumbnail",
                "mix",
                "image",   # often screenshot -> LAST
                "fanart",
            ]
            for tag in fallback_tags:
                val = (game.findtext(tag, default="") or "").strip()
                cand = resolve_media_path(val, base_dir)
                if cand and os.path.exists(cand):
                    return cand

            return None
    except Exception:
        return None
def find_art(base_dir, rom_fullpath):
    # First: gamelist (marquee first)
    art = find_art_from_gamelist(base_dir, rom_fullpath)
    if art:
        return art

    # Second: filesystem fallbacks (marquee first)
    rom_base = os.path.splitext(os.path.basename(rom_fullpath))[0]
    img_dir = os.path.join(base_dir, "images")
    if not os.path.isdir(img_dir):
        return None

    exts = (".png", ".jpg", ".jpeg")
    patterns = [
        "-marquee",
        "-wheel",
        "-logo",
        "-box2d",
        "-box3d",
        "-box",
        "-thumb",
        "",          # plain filename as last resort
    ]

    for suf in patterns:
        for ext in exts:
            cand = os.path.join(img_dir, f"{rom_base}{suf}{ext}")
            if os.path.exists(cand):
                return cand

    return None




def _is_valid_png(path):
    try:
        st = os.stat(path)
        if st.st_size < 64:
            return False
        with open(path, "rb") as f:
            sig = f.read(8)
        return sig == b"\x89PNG\r\n\x1a\n"
    except Exception:
        return False

def _cache_key(path):
    try:
        st = os.stat(path)
        return f"{path}|{st.st_size}|{int(st.st_mtime)}"
    except Exception:
        return ""

def _blit_raw_to_blue(buf, raw):
    idx = 0
    for y in range(48):
        for xb in range(16):
            b = raw[idx]; idx += 1
            for bit in range(8):
                if b & (1 << (7-bit)):
                    setpx(buf, xb*8 + bit, BLUE_Y0 + y)
def render_monow_to_blue(buf, img_path):
    clear_rect(buf, 0, BLUE_Y0, W, BLUE_Y0 + BLUE_H)

    if img_path.lower().endswith(".png") and not _is_valid_png(img_path):
        return False

    key = _cache_key(img_path)
    try:
        old = open(CACHE_KEY, "r").read().strip()
    except Exception:
        old = ""

    if key and key == old and os.path.exists(CACHE_RAW):
        try:
            raw = open(CACHE_RAW, "rb").read()
            if len(raw) >= RAW_NEED:
                _blit_raw_to_blue(buf, raw[:RAW_NEED])
                return True
        except Exception:
            pass

    try:
        cmd = [
            "ffmpeg","-hide_banner","-loglevel","error",
            "-i", img_path,
            "-vf",
            "format=rgba,"
            "scale=128:48:force_original_aspect_ratio=decrease:flags=lanczos,"
            "pad=128:48:(ow-iw)/2:(oh-ih)/2:color=black@0,"
            "format=rgba",
            "-f","rawvideo","pipe:1"
        ]
        rgba = subprocess.check_output(cmd)
        need = 128 * 48 * 4
        if len(rgba) < need:
            return False
        rgba = rgba[:need]

        # Luma + alpha
        lum = [[0]*128 for _ in range(48)]
        alp = [[0]*128 for _ in range(48)]
        alpha_on = 0

        idx = 0
        for y in range(48):
            ly = lum[y]
            ay = alp[y]
            for x in range(128):
                r = rgba[idx]; g = rgba[idx+1]; b = rgba[idx+2]; a = rgba[idx+3]
                idx += 4
                ly[x] = (r*30 + g*59 + b*11) // 100
                ay[x] = a
                if a > 48:
                    alpha_on += 1

        total = 128*48
        alpha_ratio = alpha_on / float(total)

        # Content mask:
        # - If alpha meaningful => use alpha
        # - Else => background-from-corners difference mask
        mask = [[False]*128 for _ in range(48)]
        if 0.02 < alpha_ratio < 0.98:
            for y in range(48):
                my = mask[y]; ay = alp[y]
                for x in range(128):
                    my[x] = (ay[x] > 48)
        else:
            bg = (lum[0][0] + lum[0][127] + lum[47][0] + lum[47][127]) // 4
            # Slightly looser so SSF2 shadows/top borders stay in mask
            TOL = 14
            for y in range(48):
                my = mask[y]; ly = lum[y]
                for x in range(128):
                    v = ly[x]
                    dv = v - bg
                    if dv < 0: dv = -dv
                    my[x] = (dv >= TOL)

        mask_count = sum(1 for y in range(48) for x in range(128) if mask[y][x])
        if mask_count < 40:
            return False

        ink = [[False]*128 for _ in range(48)]

        # If mask is text-like (Mario), render it directly (no dithering).
        TEXT_MAX = 1600
        if mask_count <= TEXT_MAX and (0.02 < alpha_ratio < 0.98):
            for y in range(48):
                my = mask[y]; row = ink[y]
                for x in range(128):
                    row[x] = my[x]
        else:
            # EDGE + DITHER mode for complex marquees (MVC, SSF2, gradients, shadows)
            # 1) Edges inside mask (preserve interior letters)
            EDGE_THR = 22
            edges = [[False]*128 for _ in range(48)]
            for y in range(1, 47):
                my  = mask[y]
                myu = mask[y-1]
                myd = mask[y+1]
                ly  = lum[y]
                lyu = lum[y-1]
                lyd = lum[y+1]
                er  = edges[y]
                for x in range(1, 127):
                    if not my[x]:
                        continue
                    # require neighborhood in mask to avoid just outlining the blob boundary
                    if not (my[x-1] and my[x+1] and myu[x] and myd[x]):
                        continue
                    dx = ly[x+1] - ly[x-1]
                    if dx < 0: dx = -dx
                    dy = lyd[x] - lyu[x]
                    if dy < 0: dy = -dy
                    if (dx + dy) >= EDGE_THR:
                        er[x] = True

            # 2) Dithered fill from luminance inside mask (keeps gradients/shadows)
            # Bayer 4x4 thresholds scaled 0..255
            bayer4 = [
                [  0, 128,  32, 160],
                [192,  64, 224,  96],
                [ 48, 176,  16, 144],
                [240, 112, 208,  80],
            ]

            # Auto-contrast within mask so gradients don't disappear
            lo, hi = 255, 0
            for y in range(48):
                my = mask[y]; ly = lum[y]
                for x in range(128):
                    if my[x]:
                        v = ly[x]
                        if v < lo: lo = v
                        if v > hi: hi = v
            if hi <= lo:
                lo, hi = 0, 255

            def stretch(v):
                # map lo..hi -> 0..255
                if v <= lo: return 0
                if v >= hi: return 255
                return (v - lo) * 255 // (hi - lo)

            dfill = [[False]*128 for _ in range(48)]
            for y in range(48):
                my = mask[y]; ly = lum[y]
                dr = dfill[y]
                bt = bayer4[y & 3]
                for x in range(128):
                    if not my[x]:
                        continue
                    v = stretch(ly[x])
                    # IMPORTANT: darker pixels should become "ink" (blue)
                    # So compare inverted luminance against Bayer threshold.
                    inv = 255 - v
                    if inv > bt[x & 3]:
                        dr[x] = True

            # 3) Combine: edges OR dither fill (inside mask)
            for y in range(48):
                row = ink[y]
                er  = edges[y]
                dr  = dfill[y]
                my  = mask[y]
                for x in range(128):
                    row[x] = my[x] and (er[x] or dr[x])

        # Pack to 1bpp with your polarity (pre-invert background=1, ink=0, then XOR -> ink=1)
        out = bytearray(RAW_NEED)
        oi = 0
        for y in range(48):
            for xb in range(16):
                b = 0
                for bit in range(8):
                    x = xb*8 + bit
                    if not ink[y][x]:
                        b |= (1 << (7-bit))
                out[oi] = b
                oi += 1

        raw = bytes((bb ^ 0xFF) for bb in out)

        try:
            with open(CACHE_RAW, "wb") as f: f.write(raw)
            with open(CACHE_KEY, "w") as f: f.write(key)
        except Exception:
            pass

        _blit_raw_to_blue(buf, raw)
        return True

    except Exception:
        return False








    def _gray(bg_color):
        # bg_color: "black" or "white" — composites alpha during pad
        cmd = [
            "ffmpeg","-hide_banner","-loglevel","error",
            "-i", img_path,
            "-vf",
            "format=rgba,"
            "scale=128:48:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad=128:48:(ow-iw)/2:(oh-ih)/2:color={bg_color},"
            "format=gray",
            "-f","rawvideo","pipe:1"
        ]
        raw = subprocess.check_output(cmd)
        return raw[:128*48] if raw and len(raw) >= 128*48 else None

    # Thresholds tuned for thin “light text on transparent”
    THR_LIGHT = 150   # pixel >= THR_LIGHT considered "light"
    MIN_INK   = 40    # if fewer than this, try opposite background

    # Pass A: assume light logo on transparent => composite on black, logo pixels are light
    g = _gray("black")
    if g is None:
        return False

    # Build logo mask
    # logo_mask[y][x] True = logo pixel (should be ON/blue)
    logo = [[False]*128 for _ in range(48)]
    cnt = 0
    i = 0
    for y in range(48):
        row = logo[y]
        for x in range(128):
            v = g[i]; i += 1
            if v >= THR_LIGHT:
                row[x] = True
                cnt += 1

    # If almost nothing was detected, this might be a dark logo; try white background
    if cnt < MIN_INK:
        g2 = _gray("white")
        if g2 is None:
            return False
        logo = [[False]*128 for _ in range(48)]
        i = 0
        cnt = 0
        for y in range(48):
            row = logo[y]
            for x in range(128):
                v = g2[i]; i += 1
                # On white bg, dark logo pixels are "ink"
                if v < THR_LIGHT:
                    row[x] = True
                    cnt += 1
        if cnt < MIN_INK:
            return False

    # 1px dilation so thin text doesn't disappear
    dil = [[False]*128 for _ in range(48)]
    for y in range(48):
        for x in range(128):
            if logo[y][x]:
                for yy in (y-1,y,y+1):
                    if 0 <= yy < 48:
                        for xx in (x-1,x,x+1):
                            if 0 <= xx < 128:
                                dil[yy][xx] = True
    logo = dil

    # Pack to 1bpp in the SAME polarity your daemon expects:
    # We create raw_pre with 0 bits where logo is, 1 bits elsewhere,
    # then your existing invert (xor) will make logo bits become 1 (blue), background 0 (black).
    out = bytearray(RAW_NEED)
    oi = 0
    for y in range(48):
        for xb in range(16):
            b = 0
            for bit in range(8):
                x = xb*8 + bit
                # raw_pre bit = 0 for logo, 1 for background
                if not logo[y][x]:
                    b |= (1 << (7-bit))
            out[oi] = b
            oi += 1

    # Keep your existing behavior: BLUE pixels on BLACK background
    raw = bytes((b ^ 0xFF) for b in out)

    try:
        with open(CACHE_RAW, "wb") as f: f.write(raw)
        with open(CACHE_KEY, "w") as f: f.write(key)
    except Exception:
        pass

    _blit_raw_to_blue(buf, raw)
    return True


    def _ffmpeg_gray(bg):
        # bg: "black" or "white" for alpha compositing
        cmd = [
            "ffmpeg","-hide_banner","-loglevel","error",
            "-i", img_path,
            "-vf",
            "format=rgba,"
            "scale=128:48:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad=128:48:(ow-iw)/2:(oh-ih)/2:color={bg},"
            "format=gray",
            "-f","rawvideo","pipe:1"
        ]
        return subprocess.check_output(cmd)

    def _pack_1bpp_from_gray(gray_bytes, ink_mode):
        # ink_mode: "bright" => logo pixels are bright (white logo on dark bg)
        #           "dark"   => logo pixels are dark (black logo on white bg)
        # output: 1bpp, row-major, MSB-first per byte (matches what monow/rawvideo expects)
        out = bytearray(RAW_NEED)
        idx = 0
        out_i = 0
        for y in range(48):
            for xb in range(16):  # 128/8
                b = 0
                for bit in range(8):
                    v = gray_bytes[idx]; idx += 1
                    if ink_mode == "bright":
                        on = (v >= 200)     # tweak 200 if needed
                    else:
                        on = (v <= 55)      # tweak 55 if needed
                    if on:
                        b |= (1 << (7-bit))  # MSB-first
                out[out_i] = b
                out_i += 1
        return bytes(out)

    try:
        # Pass A: composite alpha on black -> good for WHITE logos
        g_black = _ffmpeg_gray("black")
        if len(g_black) < 128*48:
            return False
        g_black = g_black[:128*48]

        bright = sum(1 for v in g_black if v >= 200)

        # If we have enough bright pixels, it’s probably a white logo -> use bright ink
        if bright >= 80:
            raw1 = _pack_1bpp_from_gray(g_black, "bright")
        else:
            # Pass B: composite alpha on white -> good for BLACK logos
            g_white = _ffmpeg_gray("white")
            if len(g_white) < 128*48:
                return False
            g_white = g_white[:128*48]

            dark = sum(1 for v in g_white if v <= 55)
            if dark < 80:
                # Nothing usable (avoid static): just leave cleared area
                return False

            raw1 = _pack_1bpp_from_gray(g_white, "dark")

        try:
            with open(CACHE_RAW, "wb") as f: f.write(raw1)
            with open(CACHE_KEY, "w") as f: f.write(key)
        except Exception:
            pass

        _blit_raw_to_blue(buf, raw1)
        return True
    except Exception:
        return False


    def _ffmpeg_gray(bg):
        # bg: "black" or "white" for alpha compositing
        cmd = [
            "ffmpeg","-hide_banner","-loglevel","error",
            "-i", img_path,
            "-vf",
            "format=rgba,"
            "scale=128:48:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad=128:48:(ow-iw)/2:(oh-ih)/2:color={bg},"
            "format=gray",
            "-f","rawvideo","pipe:1"
        ]
        return subprocess.check_output(cmd)

    def _pack_1bpp_from_gray(gray_bytes, ink_mode):
        # ink_mode: "bright" => logo pixels are bright (white logo on dark bg)
        #           "dark"   => logo pixels are dark (black logo on white bg)
        # output: 1bpp, row-major, MSB-first per byte (matches what monow/rawvideo expects)
        out = bytearray(RAW_NEED)
        idx = 0
        out_i = 0
        for y in range(48):
            for xb in range(16):  # 128/8
                b = 0
                for bit in range(8):
                    v = gray_bytes[idx]; idx += 1
                    if ink_mode == "bright":
                        on = (v >= 200)     # tweak 200 if needed
                    else:
                        on = (v <= 55)      # tweak 55 if needed
                    if on:
                        b |= (1 << (7-bit))  # MSB-first
                out[out_i] = b
                out_i += 1
        return bytes(out)

    try:
        # Pass A: composite alpha on black -> good for WHITE logos
        g_black = _ffmpeg_gray("black")
        if len(g_black) < 128*48:
            return False
        g_black = g_black[:128*48]

        bright = sum(1 for v in g_black if v >= 200)

        # If we have enough bright pixels, it’s probably a white logo -> use bright ink
        if bright >= 80:
            raw1 = _pack_1bpp_from_gray(g_black, "bright")
        else:
            # Pass B: composite alpha on white -> good for BLACK logos
            g_white = _ffmpeg_gray("white")
            if len(g_white) < 128*48:
                return False
            g_white = g_white[:128*48]

            dark = sum(1 for v in g_white if v <= 55)
            if dark < 80:
                # Nothing usable (avoid static): just leave cleared area
                return False

            raw1 = _pack_1bpp_from_gray(g_white, "dark")

        try:
            with open(CACHE_RAW, "wb") as f: f.write(raw1)
            with open(CACHE_KEY, "w") as f: f.write(key)
        except Exception:
            pass

        _blit_raw_to_blue(buf, raw1)
        return True
    except Exception:
        return False


def draw_menu_pages(buf, page_idx):
    # 4 items per page: y positions in blue area
    y_lines = [18, 30, 42, 54]

    ip = ip_addr()
    temp = cpu_temp()
    avail, total = mem_mb()
    cores = cpu_cores()
    mhz = cpu_max_mhz()
    up = uptime_hm()
    kind = pi_kind()

    # Custom line: kind of raspberry + cores (nothing else)
    pi_line = f"{kind} Cores:{cores}"

    pages = [
        [f"IP:{ip}", f"CPU:{temp}", f"MEM:{avail}/{total}MB", pi_line],
        [f"Uptime:{up}", f"Linux:{platform.release()}", f"Max:{mhz}MHz" if mhz else "Max:n/a", pi_line],
    ]

    page = pages[page_idx % len(pages)]

    clear_rect(buf, 0, BLUE_Y0, W, BLUE_Y0 + BLUE_H)
    for i, line in enumerate(page):
        draw_text(buf, line[:21], 0, y_lines[i])


def render_triangle_outline(buf, cx=18, top_y=0, tip_y=15, half_w=10):
    """
    Draw a VERY thin outlined triangle BEHIND the joystick:
      apex at (cx, tip_y), top edge around (top_y), outlined only.
    """
    # left edge
    for y in range(top_y, tip_y + 1):
        t = (y - top_y) / max(1, (tip_y - top_y))
        x = int(round(cx - half_w * (1 - t)))
        clearpx(buf, x, y)

    # right edge
    for y in range(top_y, tip_y + 1):
        t = (y - top_y) / max(1, (tip_y - top_y))
        x = int(round(cx + half_w * (1 - t)))
        clearpx(buf, x, y)

    # top edge (thin)
    for x in range(cx - half_w, cx + half_w + 1):
        clearpx(buf, x, top_y)

    # tip pixel
    clearpx(buf, cx, tip_y)


def render_joystick(buf):
    # Triangle outline first (so joystick draws on top of it)
    render_triangle_outline(buf, cx=18, top_y=1, tip_y=15, half_w=10)

    # Forum-style joystick proportions (drawn over triangle)
    cx = 18
    cy = 6
    r = 4

    # Ball
    for y in range(-r, r+1):
        for x in range(-r, r+1):
            if x*x + y*y <= r*r:
                clearpx(buf, cx+x, cy+y)

    # Stem (thin)
    for y in range(8, 12):
        for x in range(17, 19):
            clearpx(buf, x, y)

    # Base (wide)
    for y in range(12, 15):
        for x in range(12, 24):
            clearpx(buf, x, y)

    # Slight base rounding corners
    clearpx(buf, 12, 13)
    clearpx(buf, 23, 13)


def draw_banner(buf):
    fill_rect_on(buf, 0, 0, W, YELLOW_H)
    render_joystick(buf)

    # Handmade BATOCERA wordmark (correct bitmap)
    word = [
        "............................................",
        "###....###.#####.####...###.####..###...###.",
        "#..#..#...#..#..#....#.#....#....#...#.#...#",
        "####..#####..#..#....#.#....####.####..#####",
        "#...#.#...#..#..#....#.#....#....#.#...#...#",
        "####..#...#..#...####...###.####.#..#..#...#",
        "............................................",
    ]
    scale = 2
    x0 = 38   # tighter gap between logo and text
    y0 = 1

    for y, row in enumerate(word):
        for x, ch in enumerate(row):
            if ch == "#":
                for dy in range(scale):
                    for dx in range(scale):
                        clearpx(buf, x0 + x*scale + dx, y0 + y*scale + dy)


def main():
    if not os.path.exists(FB):
        return

    ff = has_cmd("ffmpeg")

    while True:
        buf = bytearray(SIZE)
        draw_banner(buf)

        st = read_state()
        if st.get("mode") == "game":
            rom = st.get("rom","")
            base_dir = rom_base_dir_from_path(rom)
            real_rom = rom
            if not base_dir or base_dir.endswith("/arcade"):
                base_dir, real_rom = resolve_arcade_to_real_base(rom)

            art = find_art(base_dir, real_rom) if base_dir and real_rom else None

            if art and ff and os.path.exists(art):
                ok = render_monow_to_blue(buf, art)
                if not ok:
                    clear_rect(buf, 0, BLUE_Y0, W, BLUE_Y0 + BLUE_H)
                    draw_text(buf, "Now Playing", 0, 24)
                    draw_text(buf, os.path.splitext(os.path.basename(real_rom))[0][:21], 0, 40)
            else:
                clear_rect(buf, 0, BLUE_Y0, W, BLUE_Y0 + BLUE_H)
                draw_text(buf, "Now Playing", 0, 24)
                draw_text(buf, os.path.splitext(os.path.basename(real_rom))[0][:21], 0, 40)
        else:
            draw_menu_pages(buf, int(time.time() // MENU_PAGE_SECONDS))

        write_fb(buf)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
