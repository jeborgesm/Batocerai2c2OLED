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

def find_art_from_gamelist(base_dir, rom_fullpath):
    gamelist = os.path.join(base_dir, "gamelist.xml")
    if not os.path.exists(gamelist):
        return None
    try:
        root = ET.parse(gamelist).getroot()
        target = os.path.basename(rom_fullpath)
        for game in root.findall("game"):
            p = (game.findtext("path", default="") or "").replace("\\","/")
            if os.path.basename(p) == target:
                for tag in ("marquee", "image"):
                    val = (game.findtext(tag, default="") or "").strip()
                    cand = resolve_media_path(val, base_dir)
                    if cand and os.path.exists(cand):
                        return cand
    except Exception:
        pass
    return None

def find_art(base_dir, rom_fullpath):
    art = find_art_from_gamelist(base_dir, rom_fullpath)
    if art:
        return art
    rom_base = os.path.splitext(os.path.basename(rom_fullpath))[0]
    img_dir = os.path.join(base_dir, "images")
    if os.path.isdir(img_dir):
        for ext in (".png",".jpg",".jpeg"):
            for pat in (
                os.path.join(img_dir, f"{rom_base}-marquee{ext}"),
                os.path.join(img_dir, f"{rom_base}-wheel{ext}"),
                os.path.join(img_dir, f"{rom_base}-logo{ext}"),
                os.path.join(img_dir, f"{rom_base}{ext}"),
            ):
                if os.path.exists(pat):
                    return pat
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
            "scale=128:48:force_original_aspect_ratio=decrease,"
            "pad=128:48:(ow-iw)/2:(oh-ih)/2,format=monow",
            "-f","rawvideo","pipe:1"
        ]
        raw = subprocess.check_output(cmd)
        if len(raw) < RAW_NEED:
            return False

        # invert: BLUE pixels on BLACK background
        raw = bytes((b ^ 0xFF) for b in raw[:RAW_NEED])

        try:
            with open(CACHE_RAW, "wb") as f: f.write(raw)
            with open(CACHE_KEY, "w") as f: f.write(key)
        except Exception:
            pass

        _blit_raw_to_blue(buf, raw)
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
