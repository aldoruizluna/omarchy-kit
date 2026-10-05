"""Live data for the Omarchy Kit server: the current Omarchy theme as CSS, and a background sampler that
keeps ~30 minutes of hardware history for the System page. Everything here is read-only except
set_theme(), which runs Omarchy's own `omarchy-theme-set` with a name from the installed theme list.
"""
import colorsys, glob, os, re, shutil, subprocess, threading, time
from pathlib import Path

STATE = Path.home() / ".local/state/omarchy/current"
THEME_DIR = STATE / "theme"
THEMES = [Path("/usr/share/omarchy/themes"), Path.home() / ".config/omarchy/themes"]


def read(path):
    try:
        with open(path) as f: return f.read().strip()
    except Exception:
        return ""


def run_text(*cmd, timeout=2):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception:
        return ""


# ------------------------------------------------------------------ theme
def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _css(rgb):
    return "#%02x%02x%02x" % tuple(round(max(0, min(1, v)) * 255) for v in rgb)


def _mix(a, b, t):  # t = share of b
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _lum(rgb):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = map(f, rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _readable(c, bg, fg, need):
    """Nudge c toward fg until it reaches the contrast ratio `need` against bg."""
    for i in range(21):
        x = _mix(c, fg, i / 20)
        if contrast(x, bg) >= need: return x
    return fg


def _hue_ok(c, lo, hi):
    h, l, s = colorsys.rgb_to_hls(*c)
    h *= 360
    return s > 0.25 and (lo <= h <= hi if lo < hi else h >= lo or h <= hi)


def theme_colors(path=None):
    raw = {}
    for line in read(path or THEME_DIR / "colors.toml").splitlines():
        m = re.match(r'\s*(\w+)\s*=\s*"([^"]*)"', line)
        if m: raw[m[1]] = m[2]
    return raw


def theme_name():
    return read(STATE / "theme.name")


def theme_version():
    """Changes whenever Omarchy switches theme or wallpaper (both rewrite these files/links)."""
    try:
        bg = os.path.realpath(STATE / "background")
        return f"{theme_name()}|{os.stat(THEME_DIR / 'colors.toml').st_mtime_ns}|{bg}"
    except Exception:
        return theme_name()


def theme_css(path=None):
    """Map the Omarchy theme onto every variable name the Kit pages use. Semantic colors (ok/warn/bad) come
    from the theme only when they really are green/amber/red and readable, since some themes repurpose them."""
    r = theme_colors(path)
    if "background" not in r or "foreground" not in r: return "/* no Omarchy theme found */\n"
    dark = r.get("mode", "dark") != "light"
    bg, fg = _hex(r["background"]), _hex(r["foreground"])
    if contrast(fg, bg) < 7: fg = _readable(fg, bg, (1, 1, 1) if dark else (0, 0, 0), 7)
    white, black = (1, 1, 1), (0, 0, 0)
    card = _mix(bg, fg, .05) if dark else _mix(bg, white, .55)
    line = _mix(bg, fg, .15)
    kbd = _mix(bg, fg, .10)
    mut = _readable(_mix(bg, fg, .6), card, fg, 4.6)
    acc0 = _hex(r.get("accent", "#7fb2e8"))
    acc = _readable(acc0, card, fg, 4.5)  # text/links
    accfill = acc0 if contrast(acc0, bg) >= 3 else acc  # buttons, bars, rings
    on_acc = black if contrast(accfill, black) >= contrast(accfill, white) else white

    def sem(key, lo, hi, fallback):
        c = _hex(r[key]) if key in r and _hue_ok(_hex(r[key]), lo, hi) else _hex(fallback)
        return _readable(c, card, fg, 4.5)
    ok = sem("green", 75, 170, "#68d391" if dark else "#2f855a")
    warn = sem("yellow", 25, 60, "#f6c453" if dark else "#b7791f")
    bad = sem("red", 340, 20, "#fc8181" if dark else "#c53030")
    soft = _mix(card, accfill, .14)
    v = {"bg": bg, "fg": fg, "mut": mut, "card": card, "line": line, "acc": acc, "acc-fill": accfill, "on-acc": on_acc,
         "kbd": kbd, "kbdl": _mix(bg, fg, .3), "ok": ok, "warn": warn, "bad": bad, "info": acc, "soft": soft,
         "act": warn, "pend": mut, "no": mut, "stage1": _mix(bg, fg, .08), "stage2": _mix(bg, fg, .2),
         "bg-deep": _hex(r.get("darker_background", r["background"])) if dark else _mix(bg, black, .04)}
    body = ";".join(f"--{k}:{_css(c)}" for k, c in v.items())
    font = run_text("omarchy-font-current") or "JetBrainsMono Nerd Font"
    # :root:root:root outranks each page's own light/dark :root rules, so the theme always wins.
    return (f"/* Omarchy theme: {theme_name()} ({'dark' if dark else 'light'}) */\n"
            f":root:root:root{{{body};--mono:'{font}',ui-monospace,monospace;color-scheme:{'dark' if dark else 'light'}}}\n")


def wallpaper():
    p = os.path.realpath(STATE / "background")
    return p if re.search(r"\.(jpe?g|png|webp)$", p, re.I) and os.path.isfile(p) else None


def theme_list():
    names = set()
    for d in THEMES:
        if d.is_dir(): names.update(p.name for p in d.iterdir() if (p / "colors.toml").exists())
    out = []
    for n in sorted(names):
        f = next((d / n / "colors.toml" for d in THEMES if (d / n / "colors.toml").exists()), None)
        c = {}
        for line in read(f).splitlines():
            m = re.match(r'\s*(\w+)\s*=\s*"([^"]*)"', line)
            if m: c[m[1]] = m[2]
        out.append({"id": n, "name": re.sub(r"(^|-)([a-z])", lambda m: (" " if m[1] else "") + m[2].upper(), n).replace("-", " "),
                    "bg": c.get("background"), "fg": c.get("foreground"), "acc": c.get("accent"), "mode": c.get("mode", "dark")})
    return out


def set_theme(tid):
    if tid not in {t["id"] for t in theme_list()}: return False
    subprocess.Popen(["omarchy-theme-set", tid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


# ------------------------------------------------------------------ live sampler
INTERVAL = 2
KEEP = 900  # 30 minutes
_hist, _lock = [], threading.Lock()
_wifi = {"t": 0, "v": None}


def _cpu_times():
    f = read("/proc/stat").splitlines()[0].split()[1:]
    v = list(map(int, f))
    return sum(v), v[3] + v[4]


def _net_bytes():
    rx = tx = 0
    for d in glob.glob("/sys/class/net/*"):
        n = os.path.basename(d)
        if n == "lo" or n.startswith(("tailscale", "docker", "veth", "virbr")): continue
        rx += int(read(d + "/statistics/rx_bytes") or 0); tx += int(read(d + "/statistics/tx_bytes") or 0)
    return rx, tx


def _hwmon(name, f="temp1_input"):
    for hw in glob.glob("/sys/class/hwmon/hwmon*"):
        if read(hw + "/name") == name: return int(read(f"{hw}/{f}") or 0)
    return None


def gpu_power():
    return read("/sys/bus/pci/devices/0000:01:00.0/power_state") or "?"


def wifi():
    """Wi-Fi link via `iw` (fast; nmcli can take seconds because it rescans). Cached for 10 s."""
    if time.time() - _wifi["t"] < 10: return _wifi["v"]
    dev = next((os.path.basename(d) for d in glob.glob("/sys/class/net/*") if os.path.isdir(d + "/wireless")), None)
    v = None
    if dev:
        out = run_text("iw", "dev", dev, "link")
        if out.startswith("Connected"):
            ssid = re.search(r"SSID: (.*)", out); freq = re.search(r"freq: ([\d.]+)", out); sig = re.search(r"signal: (-?\d+)", out)
            name = ssid[1] if ssid else ""
            try: name = name.encode("latin-1").decode("unicode_escape").encode("latin-1").decode("utf-8")
            except Exception: pass
            v = {"dev": dev, "ssid": name, "ghz": round(float(freq[1]) / 1000, 1) if freq else None,
                 "dbm": int(sig[1]) if sig else None}
        else:
            v = {"dev": dev, "ssid": None}
    _wifi.update(t=time.time(), v=v)
    return v


def _sample(prev):
    now = time.time()
    tot, idle = _cpu_times()
    rx, tx = _net_bytes()
    s = {"t": round(now, 1)}
    if prev:
        dt = max(now - prev["_t"], .5)
        dtot = tot - prev["_tot"]
        s["cpu"] = round(100 * (1 - (idle - prev["_idle"]) / dtot), 1) if dtot else 0
        s["rx"] = round((rx - prev["_rx"]) / dt); s["tx"] = round((tx - prev["_tx"]) / dt)
    temp = _hwmon("coretemp")
    s["temp"] = round(temp / 1000, 1) if temp else None
    fans = [int(read(f) or 0) for f in sorted(glob.glob("/sys/devices/platform/applesmc.768/fan*_input"))]
    s["fan"] = max(fans) if fans else None
    mem = dict(re.findall(r"(\w+):\s+(\d+)", read("/proc/meminfo")))
    if mem.get("MemTotal"): s["mem"] = round(100 * (1 - int(mem["MemAvailable"]) / int(mem["MemTotal"])), 1)
    bat = "/sys/class/power_supply/BAT0"
    full = int(read(bat + "/charge_full") or 0)
    if full: s["bat"] = round(100 * int(read(bat + "/charge_now") or 0) / full, 1)
    cur, volt = int(read(bat + "/current_now") or 0), int(read(bat + "/voltage_now") or 0)
    s["watts"] = round(cur * volt / 1e12, 1)
    s["_t"], s["_tot"], s["_idle"], s["_rx"], s["_tx"] = now, tot, idle, rx, tx
    return s


def _loop():
    prev = None
    while True:
        try:
            prev = _sample(prev)
            with _lock:
                _hist.append(prev)
                del _hist[:-KEEP]
        except Exception:
            pass
        time.sleep(INTERVAL)


def start_sampler():
    threading.Thread(target=_loop, daemon=True, name="kit-sampler").start()


def history(since=0):
    with _lock:
        return [{k: v for k, v in s.items() if not k.startswith("_")} for s in _hist if s["t"] > since]


def snapshot():
    """Slower-changing facts shown next to the graphs."""
    bat = "/sys/class/power_supply/BAT0"
    full, design = int(read(bat + "/charge_full") or 0), int(read(bat + "/charge_full_design") or 0)
    du = shutil.disk_usage("/")
    up = float(read("/proc/uptime").split()[0] or 0)
    panel = "unknown"
    for link in glob.glob("/sys/class/drm/card*-eDP-1"):
        dev = os.path.realpath(link)
        panel = "nvidia" if "0000:01:00.0" in dev else "intel" if "0000:00:02.0" in dev else "unknown"
    gp = gpu_power()
    gtemp = _hwmon("nouveau") if gp == "D0" else None
    return {"panel": panel, "nvidia": gp, "gpu_temp": round(gtemp / 1000) if gtemp else None,
            "battery": {"status": read(bat + "/status"), "health": round(100 * full / design) if design else None,
                        "cycles": read(bat + "/cycle_count"), "ac": read("/sys/class/power_supply/ADP1/online") == "1"},
            "disk": {"used": du.used, "total": du.total}, "uptime": up, "load": read("/proc/loadavg").split()[:3],
            "profile": run_text("powerprofilesctl", "get"), "wifi": wifi(), "kernel": os.uname().release,
            "mem_total": int(dict(re.findall(r"(\w+):\s+(\d+)", read("/proc/meminfo"))).get("MemTotal", 0)) * 1024}


def _proc_ticks():
    out = {}
    for d in glob.glob("/proc/[0-9]*"):
        st = read(d + "/stat")
        if not st: continue
        name, rest = st[st.find("(") + 1:st.rfind(")")], st[st.rfind(")") + 2:].split()
        out[d] = (name, int(rest[11]) + int(rest[12]), int(rest[21]) * os.sysconf("SC_PAGE_SIZE"))
    return out


def top(n=6):
    """Current CPU use per app (summed by process name) over a half-second window; ps would give lifetime averages."""
    a = _proc_ticks(); t0 = time.time(); time.sleep(.5); b = _proc_ticks(); dt = time.time() - t0
    hz, agg = os.sysconf("SC_CLK_TCK"), {}
    for pid, (name, ticks, rss) in b.items():
        cpu = (ticks - a[pid][1]) / hz / dt * 100 if pid in a else 0
        g = agg.setdefault(name, [0, 0]); g[0] += cpu; g[1] += rss
    rows = sorted(agg.items(), key=lambda kv: -kv[1][0])[:n]
    return [{"name": k, "cpu": round(v[0], 1), "mb": round(v[1] / 2**20)} for k, v in rows]
