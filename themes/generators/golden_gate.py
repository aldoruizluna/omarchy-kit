"""Golden Gate and Golden Gate Night wallpapers: original SVG scenes rasterised with rsvg-convert, then written as JPEG.

A suspension bridge in the fog, drawn from simple shapes (two stepped towers, a catenary main cable, a deck, fog banks), and a few soft colour
fields in the spirit of macOS wallpapers. Nothing here copies a photograph or an Apple wallpaper.

usage: golden_gate.py day|night OUTDIR [1|2|3|4|5 ...]     (called by themes/make-wallpapers)
"""
import math, os, random, subprocess, sys
from PIL import Image, ImageFilter

W, H = 2880, 1800
R = random.Random

# Light ("day") and dark ("night") palettes. Colours of the scene only; the desktop palette is in colors.toml.
PAL = {
    "day": dict(sky=[(0, "#9cc4ee"), (0.45, "#cfe0f5"), (0.78, "#f6e4d2"), (1, "#fbd9bd")], sun="#fff3dc", hill=["#8aa3c4", "#9db4d1", "#b7c8de"],
                fog="#ffffff", sea=["#cfe0f1", "#a9c5e2"], bridge="#c4442a", bridge_far="#d98d7c", ink="#27406a",
                blob=["#7fb3ff", "#ffb48a", "#ff8fa3", "#9be0d1"], bg="#e8f0fb"),
    "night": dict(sky=[(0, "#070b18"), (0.5, "#101c3a"), (0.82, "#2a3560"), (1, "#5a4a78")], sun="#ffd6a8", hill=["#101a36", "#162347", "#1d2d58"],
                  fog="#7f8fc4", sea=["#1a2a54", "#0e1836"], bridge="#a8362a", bridge_far="#4a3a66", ink="#bcc9ff",
                  blob=["#2f5bd6", "#7c3fd0", "#d0407a", "#27a3b8"], bg="#0b1226"),
}


def hexmix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    return "#" + "".join("%02x" % round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t) for i in (0, 2, 4))


class SVG:
    def __init__(self):
        self.defs, self.body, self.n = [], [], 0

    def add(self, x):
        self.body.append(x)

    def grad(self, stops, x1=0, y1=0, x2=0, y2=1):
        self.n += 1
        i = "g%d" % self.n
        s = "".join('<stop offset="%s" stop-color="%s" stop-opacity="%s"/>' % (t[0], t[1], t[2] if len(t) > 2 else 1) for t in stops)
        self.defs.append('<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>' % (i, x1, y1, x2, y2, s))
        return "url(#%s)" % i

    def rad(self, stops, cx, cy, r):
        self.n += 1
        i = "g%d" % self.n
        s = "".join('<stop offset="%s" stop-color="%s" stop-opacity="%s"/>' % (t[0], t[1], t[2] if len(t) > 2 else 1) for t in stops)
        self.defs.append('<radialGradient id="%s" gradientUnits="userSpaceOnUse" cx="%.1f" cy="%.1f" r="%.1f">%s</radialGradient>' % (i, cx, cy, r, s))
        return "url(#%s)" % i

    def blur(self, sd):
        self.n += 1
        i = "b%d" % self.n
        self.defs.append('<filter id="%s" x="-60%%" y="-80%%" width="220%%" height="260%%"><feGaussianBlur stdDeviation="%s"/></filter>' % (i, sd))
        return "url(#%s)" % i

    def out(self):
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><defs>%s</defs>%s</svg>'
                % (W, H, W, H, "".join(self.defs), "".join(self.body)))


def rect(x, y, w, h, fill, ex=""):
    return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" %s/>' % (x, y, w, h, fill, ex)


def circ(x, y, r, fill, ex=""):
    return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" %s/>' % (x, y, r, fill, ex)


def poly(pts, fill, ex=""):
    return '<polygon points="%s" fill="%s" %s/>' % (" ".join("%.1f,%.1f" % p for p in pts), fill, ex)


def path(d, fill="none", ex=""):
    return '<path d="%s" fill="%s" %s/>' % (d, fill, ex)


def ridge(r, base, amp):
    comps = [(amp * r.uniform(.7, 1.1), 0.6, r.uniform(0, 6.28)), (amp * .4 * r.uniform(.7, 1.2), 1.5, r.uniform(0, 6.28)),
             (amp * .15 * r.uniform(.7, 1.2), 3.1, r.uniform(0, 6.28))]
    return lambda x: base - sum(a * math.sin(2 * math.pi * f * x / W + p) for a, f, p in comps)


def hill(s, fn, fill, ex=""):
    pts = " ".join("%d,%.1f" % (x, fn(x)) for x in range(0, W + 1, 16))
    s.add('<polygon points="0,%d %s %d,%d" fill="%s" %s/>' % (H + 2, pts, W, H + 2, fill, ex))


def tower(s, x, deck_y, top_y, col, shade, scale=1.0):
    """A stepped, slightly tapering art-deco style tower with two legs and cross braces."""
    leg = 34 * scale
    gap = 120 * scale
    for sx in (-1, 1):
        cx = x + sx * (gap / 2 + leg / 2)
        s.add(poly([(cx - leg / 2, deck_y + 160), (cx + leg / 2, deck_y + 160), (cx + leg * .38, top_y), (cx - leg * .38, top_y)], col))
        s.add(poly([(cx + leg * .05, deck_y + 160), (cx + leg / 2, deck_y + 160), (cx + leg * .38, top_y), (cx + leg * .05, top_y)], shade, 'opacity=".55"'))
        s.add(rect(cx - leg * .62, top_y - 14 * scale, leg * 1.24, 16 * scale, col))
    span = gap + leg
    for k in range(6):
        y = top_y + (deck_y - top_y) * (k + .7) / 6.4
        s.add(rect(x - span / 2 - leg * .1, y, span + leg * .2, 12 * scale, col))
    s.add(rect(x - span / 2 - leg * .3, top_y + (deck_y - top_y) * .36, span + leg * .6, 16 * scale, shade, 'opacity=".5"'))


def bridge(s, p, y_deck, x1, x2, t1, t2, top_y, scale, far=False, op=1.0):
    col = p["bridge_far"] if far else p["bridge"]
    shade = hexmix(col, "#000000", .3)
    g = '<g opacity="%s">' % op
    s.add(g)
    # deck and its truss line
    s.add(rect(0, y_deck, W, 14 * scale, col))
    s.add(rect(0, y_deck + 14 * scale, W, 8 * scale, shade, 'opacity=".5"'))
    tower(s, t1, y_deck, top_y, col, shade, scale)
    tower(s, t2, y_deck, top_y, col, shade, scale)
    # main cable: a parabola between the tower tops, plus the shallow side spans going off screen
    span = t2 - t1
    sag = (y_deck - top_y) * .86
    def cable(xa, xb, ya, yb, dip, ox=0):
        mx = (xa + xb) / 2
        return "M%.1f,%.1f Q%.1f,%.1f %.1f,%.1f" % (xa + ox, ya, mx + ox, (ya + yb) / 2 + dip * 2, xb + ox, yb)
    for off in (-(70 * scale), 70 * scale):
        s.add(path(cable(t1 + off, t2 - off, top_y + 6 * scale, top_y + 6 * scale, sag), "none", 'stroke="%s" stroke-width="%.1f" stroke-linecap="round"' % (col, 6 * scale)))
        s.add(path(cable(-200, t1 + off, y_deck - 40 * scale, top_y + 6 * scale, (y_deck - top_y) * .18), "none", 'stroke="%s" stroke-width="%.1f"' % (col, 5 * scale)))
        s.add(path(cable(t2 - off, W + 200, top_y + 6 * scale, y_deck - 40 * scale, (y_deck - top_y) * .18), "none", 'stroke="%s" stroke-width="%.1f"' % (col, 5 * scale)))
    # suspenders
    n = 46
    for k in range(1, n):
        u = k / n
        x = t1 + span * u
        y = top_y + 6 * scale + 4 * sag * u * (1 - u)
        if y < y_deck - 4:
            s.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" opacity=".8"/>' % (x, y, x, y_deck, col, 2.2 * scale))
    s.add("</g>")


def fog(s, p, y, h, r, n, op, blur):
    f = s.blur(blur)
    for _ in range(n):
        cx = r.uniform(-200, W + 200)
        w = r.uniform(500, 1100)
        s.add('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s" opacity="%.2f" filter="%s"/>' % (cx, y + r.uniform(-h / 3, h / 3), w, h * r.uniform(.5, 1), p["fog"], op * r.uniform(.6, 1), f))


def scene_bridge(p, seed, high=False):
    r = R(seed)
    s = SVG()
    s.add(rect(0, 0, W, H, s.grad([(o, c) for o, c in p["sky"]])))
    sx, sy = W * r.uniform(.40, .60), H * (.58 if not high else .46)
    s.add(circ(sx, sy, 640, s.rad([(0, p["sun"], .9), (.3, p["sun"], .38), (1, p["sun"], 0)], sx, sy, 640)))
    s.add(circ(sx, sy, 64, p["sun"], 'opacity=".9"'))
    for i, c in enumerate(p["hill"]):
        hill(s, ridge(r, H * (.64 + .05 * i), 60 - 8 * i), c, 'opacity="%.2f"' % (.5 + .2 * i))
    fog(s, p, H * .68, 150, r, 6, .45, 30)
    sea_y = H * .70
    s.add(rect(0, sea_y, W, H - sea_y, s.grad([(0, hexmix(p["sea"][0], p["fog"], .35)), (.35, p["sea"][0]), (1, p["sea"][1])])))
    # a soft reflection of the sun on the water
    s.add('<ellipse cx="%.1f" cy="%.1f" rx="260" ry="%.1f" fill="%s" opacity=".35" filter="%s"/>' % (sx, sea_y + 180, 190, p["sun"], s.blur(46)))
    bridge(s, p, H * .60, 0, W, W * .22, W * .78, H * .15, 1.5)
    fog(s, p, H * .73, 170, r, 7, .55, 38)
    fog(s, p, H * .90, 240, r, 5, .30, 50)
    return s


def scene_towers(p, seed):
    r = R(seed)
    s = SVG()
    s.add(rect(0, 0, W, H, s.grad([(o, c) for o, c in p["sky"]], 0, 0, .2, 1)))
    cx, cy = W * .72, H * .42
    s.add(circ(cx, cy, 700, s.rad([(0, p["sun"], .8), (.5, p["sun"], .18), (1, p["sun"], 0)], cx, cy, 700)))
    for i, c in enumerate(p["hill"]):
        hill(s, ridge(r, H * (.7 + .05 * i), 90), c, 'opacity="%.2f"' % (.5 + .25 * i))
    fog(s, p, H * .72, 220, r, 9, .55, 40)
    bridge(s, p, H * .70, 0, W, W * .18, W * .66, H * .08, 2.3)
    fog(s, p, H * .86, 360, r, 10, .6, 54)
    return s


def scene_fields(p, seed, flip=False):
    """Soft overlapping colour fields: blurred shapes on a calm ground, the kind of wallpaper macOS ships next to its photographs."""
    r = R(seed)
    s = SVG()
    s.add(rect(0, 0, W, H, p["bg"]))
    f = s.blur(150)
    cols = p["blob"]
    for i in range(7):
        c = cols[(i + seed) % len(cols)]
        x, y = r.uniform(.05, .95) * W, r.uniform(.05, .95) * H
        rx, ry = r.uniform(380, 900), r.uniform(280, 700)
        s.add('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s" opacity="%.2f" filter="%s" transform="rotate(%d %.1f %.1f)"/>'
              % (x, y, rx, ry, c, r.uniform(.55, .85), f, r.uniform(-40, 40), x, y))
    s.add(rect(0, 0, W, H, s.grad([(0, "#ffffff", .10), (1, "#000000", .10)])))
    return s


def scene_gradient(p, seed):
    r = R(seed)
    s = SVG()
    a, b = p["blob"][0], p["blob"][1]
    s.add(rect(0, 0, W, H, s.grad([(0, hexmix(a, p["bg"], .35)), (.55, p["bg"]), (1, hexmix(b, p["bg"], .4))], 0, 0, 1, 1)))
    f = s.blur(220)
    s.add('<ellipse cx="%.1f" cy="%.1f" rx="900" ry="520" fill="%s" opacity=".55" filter="%s"/>' % (W * r.uniform(.2, .5), H * r.uniform(.15, .4), p["blob"][3], f))
    s.add('<ellipse cx="%.1f" cy="%.1f" rx="800" ry="460" fill="%s" opacity=".45" filter="%s"/>' % (W * r.uniform(.55, .85), H * r.uniform(.6, .85), p["blob"][2], f))
    return s


SCENES = {1: lambda p: scene_bridge(p, 11), 2: lambda p: scene_fields(p, 3), 3: lambda p: scene_towers(p, 5), 4: lambda p: scene_bridge(p, 29, high=True),
          5: lambda p: scene_gradient(p, 8)}


def render(svg_text, out_path, seed, grain):
    svg_path = out_path + ".svg"
    png_path = out_path + ".png"
    open(svg_path, "w").write(svg_text)
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-o", png_path, svg_path], check=True)
    os.remove(svg_path)
    im = Image.open(png_path).convert("RGB")
    os.remove(png_path)
    # a little film grain so the gradients do not band on an 8-bit panel
    noise = Image.effect_noise((W, H), 14).convert("RGB")
    im = Image.blend(im, Image.blend(im, noise, .5), grain)
    im.save(out_path, "JPEG", quality=92, optimize=True)


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in PAL:
        sys.exit(__doc__)
    variant, outdir = sys.argv[1], sys.argv[2]
    nums = [int(a) for a in sys.argv[3:]] or sorted(SCENES)
    os.makedirs(outdir, exist_ok=True)
    for n in nums:
        out = os.path.join(outdir, "%d-golden-gate-%s.jpg" % (n, variant))
        render(SCENES[n](PAL[variant]).out(), out, n, 0.035)
        print("wrote", out)


if __name__ == "__main__":
    main()
