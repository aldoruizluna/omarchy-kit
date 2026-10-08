def lum(h):
    h=h.lstrip('#'); r,g,b=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    f=lambda c: c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)
def cr(a,b):
    la,lb=lum(a),lum(b)
    if la<lb: la,lb=lb,la
    return (la+0.05)/(lb+0.05)

BASE = dict(
 accent="#a874ff", selection="#2f1b57", muted="#9686bf",
 background="#0b0614", dark_background="#070310", darker_background="#04020a", lighter_background="#1a1030",
 foreground="#d7f2ff", dark_foreground="#8174aa", light_foreground="#b3d4e6", bright_foreground="#f2fcff",
 red="#ff5468", yellow="#f5c83d", orange="#ff9330", green="#7aef3e", cyan="#3fd0e6", blue="#6b8fff", magenta="#c07cff", brown="#a8703a",
 bright_red="#ff7384", bright_yellow="#ffe375", bright_green="#b4ff7a", bright_cyan="#7cecfa", bright_blue="#97b0ff", bright_magenta="#d6a3ff",
)
RED = dict(BASE,
 accent="#ff5a36", selection="#4a1620", muted="#b08a9a",
 background="#0d0510", dark_background="#080309", darker_background="#050207", lighter_background="#1f0e1c",
 foreground="#ffeee6", dark_foreground="#8f6f80", light_foreground="#e8cfc6", bright_foreground="#fff8f4",
 red="#ff4f68", yellow="#f5c83d", orange="#ff8c2e", green="#7aef3e", cyan="#47d3e8", blue="#7b92ff", magenta="#c27dff", brown="#b27b45",
 bright_red="#ff7a80", bright_yellow="#ffe375", bright_green="#b4ff7a", bright_cyan="#85ebf8", bright_blue="#a0b2ff", bright_magenta="#d9a6ff",
)
ORDER=["accent","selection","muted","background","dark_background","darker_background","lighter_background","foreground","dark_foreground","light_foreground","bright_foreground","red","yellow","orange","green","cyan","blue","magenta","brown","bright_red","bright_yellow","bright_green","bright_cyan","bright_blue","bright_magenta"]
def checks(P):
    bg=P['background']; rows=[]
    for k in ["foreground","bright_foreground","light_foreground","muted","dark_foreground","accent","orange","brown"]:
        rows.append((k,"background",cr(P[k],bg)))
    for k in ["red","green","yellow","blue","magenta","cyan","bright_red","bright_green","bright_yellow","bright_blue","bright_magenta","bright_cyan"]:
        rows.append((k,"background",cr(P[k],bg)))
    rows.append(("foreground","selection",cr(P['foreground'],P['selection'])))
    rows.append(("bright_foreground","selection",cr(P['bright_foreground'],P['selection'])))
    rows.append(("foreground","lighter_background",cr(P['foreground'],P['lighter_background'])))
    rows.append(("muted","lighter_background",cr(P['muted'],P['lighter_background'])))
    rows.append(("accent","lighter_background",cr(P['accent'],P['lighter_background'])))
    rows.append(("accent","selection",cr(P['accent'],P['selection'])))
    rows.append(("background","accent (button text)",cr(P['background'],P['accent'])))
    rows.append(("red","lighter_background",cr(P['red'],P['lighter_background'])))
    rows.append(("green","lighter_background",cr(P['green'],P['lighter_background'])))
    return rows
if __name__=="__main__":
    for n,P in (("BASE",BASE),("RED",RED)):
        print(n)
        for a,b,c in checks(P): print(f"  {a:20s}/{b:20s} {c:5.2f}", "" if c>=4.5 else "  <-- LOW")
