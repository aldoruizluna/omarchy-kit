"""Kawaii Bow and Kawaii Bow Night wallpapers: original SVG art rasterised with rsvg-convert, then written as JPEG.

usage: kawaii.py light|dark OUTDIR [1|2|3|4|5 ...]     (called by themes/make-wallpapers)
"""
import random, math, subprocess, os, sys, json
from PIL import Image, ImageChops
W,H=2880,1800
import tempfile
OUT=None   # set from the command line
SCR=tempfile.mkdtemp(prefix="kawaii-")   # scratch SVG and PNG files; removed at exit
import atexit, shutil; atexit.register(shutil.rmtree, SCR, True)

LIGHT=dict(name="kawaii-bow",dark=False,bg1="#ffdfe9",bg2="#fff7f2",pink="#ff9fc0",pink2="#ffc9dc",pale="#ffeaf1",red="#e3243f",red_hi="#ff6c82",red_ed="#a8142c",
  pink_hi="#ffd2e2",pink_ed="#d4628c",blue="#bfe2fb",blue_hi="#eaf6ff",blue_ed="#6aa8e0",butter="#ffe7a0",mint="#c6efdc",cream="#fff8f4",white="#ffffff",white_ed="#f0a8c0",
  seed="#fff3c4",leaf="#6fc291",berry="#c2406b",dot="#ffffff",dotop=0.6)
DARK=dict(name="kawaii-bow-night",dark=True,bg1="#241022",bg2="#4b1b45",pink="#ff93c9",pink2="#ffc1de",pale="#5d2a55",red="#ff617d",red_hi="#ffa3b2",red_ed="#a91f3c",
  pink_hi="#ffd0e6",pink_ed="#c2548f",blue="#93cbff",blue_hi="#d3eaff",blue_ed="#5b95d6",butter="#ffe08a",mint="#93e6b4",cream="#ffe9f0",white="#fff3f7",white_ed="#d89ab9",
  seed="#fff0b8",leaf="#5fbf8a",berry="#8a2f6b",dot="#ff93c9",dotop=0.13)

def f(x): return f"{x:.1f}"
def bow(x,y,s,rot,body,hi,ed,tails=True,glow=None):
    o=""
    if glow: o+=f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(190*s)}" fill="url(#halo)" opacity="{glow}"/>'
    g=f'<g transform="translate({f(x)},{f(y)}) rotate({rot:.1f}) scale({s:.3f})" stroke="{ed}" stroke-width="3.6" stroke-linejoin="round">'
    loop="M-6,0 C-14,-62 -112,-78 -122,-14 C-128,46 -42,56 -6,8 Z"
    inner="M-30,-3 C-40,-36 -92,-46 -100,-17 C-104,10 -58,22 -30,3 Z"
    tail="M-8,14 C-24,50 -52,84 -66,110 L-34,106 C-26,90 -10,64 0,30 Z"
    for m in ("1","-1"):
        g+=f'<g transform="scale({m},1)">'
        if tails: g+=f'<path d="{tail}" fill="{body}"/>'
        g+=f'<path d="{loop}" fill="{body}"/><path d="{inner}" fill="{hi}" stroke="none" opacity="0.6"/>'
        g+=f'<path d="M-14,2 C-44,-8 -76,-12 -106,-16" fill="none" stroke-opacity="0.35" stroke-width="3"/></g>'
    g+=f'<rect x="-19" y="-21" width="38" height="42" rx="15" fill="{body}"/><ellipse cx="-5" cy="-8" rx="6" ry="9" fill="{hi}" stroke="none" opacity="0.7"/></g>'
    return o+g
def sparkle(x,y,r,fill,op=1,rot=0):
    return f'<path transform="translate({f(x)},{f(y)}) rotate({rot}) scale({f(r)})" d="M0,-1 Q0.09,-0.09 1,0 Q0.09,0.09 0,1 Q-0.09,0.09 -1,0 Q-0.09,-0.09 0,-1 Z" fill="{fill}" opacity="{op}"/>'
def heart(x,y,r,fill,rot=0,op=1):
    return f'<path transform="translate({f(x)},{f(y)}) rotate({rot}) scale({f(r)})" d="M0,-0.3 C0.1,-0.95 1,-0.95 1,-0.2 C1,0.4 0.4,0.65 0,1 C-0.4,0.65 -1,0.4 -1,-0.2 C-1,-0.95 -0.1,-0.95 0,-0.3 Z" fill="{fill}" opacity="{op}"/>'
def cloud(x,y,s,fill,op=0.95):
    c=[(-1.25,0.1,0.75),(-0.45,-0.35,1.0),(0.55,-0.25,0.9),(1.25,0.15,0.7)]
    o=f'<g transform="translate({f(x)},{f(y)}) scale({f(s)})" fill="{fill}" opacity="{op}">'
    for cx,cy,r in c: o+=f'<circle cx="{cx}" cy="{cy}" r="{r}"/>'
    return o+'<rect x="-1.25" y="0.1" width="2.5" height="0.75" rx="0.37"/></g>'
def berry(x,y,s,rot,P):
    o=f'<g transform="translate({f(x)},{f(y)}) rotate({rot:.1f}) scale({f(s)})">'
    o+=f'<path d="M0,-0.85 C0.95,-1.0 1.15,-0.2 0.72,0.5 C0.42,1.0 0.12,1.2 0,1.2 C-0.12,1.2 -0.42,1.0 -0.72,0.5 C-1.15,-0.2 -0.95,-1.0 0,-0.85 Z" fill="{P["red"]}" stroke="{P["red_ed"]}" stroke-width="0.05"/>'
    o+=f'<path d="M-0.5,-0.55 C-0.7,-0.3 -0.65,0.0 -0.5,0.2" fill="none" stroke="{P["red_hi"]}" stroke-width="0.1" stroke-linecap="round" opacity="0.8"/>'
    for sx,sy in [(-0.45,-0.15),(0.0,-0.3),(0.45,-0.15),(-0.25,0.2),(0.25,0.2),(0.0,0.6),(-0.55,0.4),(0.55,0.4)]:
        o+=f'<ellipse cx="{sx}" cy="{sy}" rx="0.06" ry="0.09" fill="{P["seed"]}"/>'
    for a in (-75,-38,0,38,75):
        o+=f'<ellipse transform="translate(0,-0.85) rotate({a})" cx="0" cy="-0.22" rx="0.14" ry="0.3" fill="{P["leaf"]}"/>'
    return o+'</g>'
BOWS=lambda P:[(P["red"],P["red_hi"],P["red_ed"]),(P["pink"],P["pink_hi"],P["pink_ed"]),(P["white"],P["pale"],P["white_ed"]),(P["blue"],P["blue_hi"],P["blue_ed"]),(P["red"],P["red_hi"],P["red_ed"]),(P["pink"],P["pink_hi"],P["pink_ed"])]
def place(rng,n,rmin,rmax,taken,gap=26,tries=6000):
    out=[]
    for _ in range(tries):
        if len(out)>=n: break
        r=rng.uniform(rmin,rmax); x=rng.uniform(0,W); y=rng.uniform(0,H)
        if all(math.hypot(x-a,y-b)>=r+c+gap for a,b,c in taken+out): out.append((x,y,r))
    return out
def defs(P):
    d=f'<linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="{P["bg1"]}"/><stop offset="1" stop-color="{P["bg2"]}"/></linearGradient>'
    d+=f'<radialGradient id="halo"><stop offset="0" stop-color="{P["pink"]}" stop-opacity="0.55"/><stop offset="1" stop-color="{P["pink"]}" stop-opacity="0"/></radialGradient>'
    d+=f'<radialGradient id="vig" cx="0.5" cy="0.45" r="0.75"><stop offset="0" stop-color="{P["bg2"] if not P["dark"] else P["bg2"]}" stop-opacity="{0.0 if not P["dark"] else 0.0}"/><stop offset="1" stop-color="{P["bg1"]}" stop-opacity="0.55"/></radialGradient>'
    d+=f'<pattern id="dots" width="170" height="170" patternUnits="userSpaceOnUse"><circle cx="42" cy="42" r="24" fill="{P["dot"]}" fill-opacity="{P["dotop"]}"/><circle cx="127" cy="127" r="24" fill="{P["dot"]}" fill-opacity="{P["dotop"]}"/></pattern>'
    gc1,gc2,go=((P["cream"],P["pink"],0.42) if not P["dark"] else ("#32142d",P["pink"],0.2))
    d+=f'<pattern id="gingham" width="180" height="180" patternUnits="userSpaceOnUse"><rect width="180" height="180" fill="{gc1}"/><rect width="180" height="90" fill="{gc2}" fill-opacity="{go}"/><rect width="90" height="180" fill="{gc2}" fill-opacity="{go}"/></pattern>'
    return d
def scatter_extras(rng,P,taken,nh=22,ns=26):
    o=""
    for x,y,r in place(rng,nh,18,40,taken,gap=40):
        o+=heart(x,y,r,rng.choice([P["pink"],P["red"],P["pink2"]]),rng.uniform(-25,25),0.9); taken.append((x,y,r))
    for x,y,r in place(rng,ns,14,38,taken,gap=30):
        o+=sparkle(x,y,r,rng.choice([P["butter"],P["white"] if not P["dark"] else P["cream"],P["blue"]]),0.95,rng.uniform(-15,15)); taken.append((x,y,r))
    return o
def w_bows(P,rng):
    o='<rect width="100%" height="100%" fill="url(#bg)"/>'
    taken=[]; sets=BOWS(P)
    for n,(a,b),th in ((6,(1.7,2.5),0.38),(14,(0.85,1.3),0.3),(26,(0.4,0.6),0.2)):
        for x,y,r in place(rng,n,110*a,110*b,taken,gap=34):
            s=r/110; c=rng.choice(sets); taken.append((x,y,r))
            o+=bow(x,y,s,rng.uniform(-28,28),*c,tails=(s>0.9),glow=(th if P["dark"] else None))
    return o+scatter_extras(rng,P,taken)
def w_gingham(P,rng):
    o='<rect width="100%" height="100%" fill="url(#gingham)"/><rect width="100%" height="100%" fill="url(#vig)"/>'
    taken=[]; sets=BOWS(P)
    big=[(330,330,2.6,-14),(W-320,H-300,3.0,12),(W-420,300,1.5,18),(380,H-330,1.7,-10)]
    for x,y,s,rot in big:
        o+=bow(x,y,s,rot,*sets[(len(taken))%len(sets)] if len(taken)<2 else sets[1+len(taken)%2],tails=True,glow=(0.4 if P["dark"] else None)); taken.append((x,y,110*s))
    return o+scatter_extras(rng,P,taken,nh=26,ns=22)
def w_polka(P,rng):
    if P["dark"]:
        d='<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a0f2e"/><stop offset="0.55" stop-color="#3a1840"/><stop offset="1" stop-color="#6a2a58"/></linearGradient>'
    else:
        d=f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{P["blue"]}"/><stop offset="0.55" stop-color="#ffdbe8"/><stop offset="1" stop-color="#fff3ea"/></linearGradient>'
    o=f'<defs>{d}</defs><rect width="100%" height="100%" fill="url(#sky)"/><rect width="100%" height="100%" fill="url(#dots)"/>'
    taken=[]
    if P["dark"]:
        o+=f'<mask id="mm"><rect width="{W}" height="{H}" fill="#fff"/><circle cx="2350" cy="360" r="172" fill="#000"/></mask><circle cx="2250" cy="420" r="190" fill="{P["butter"]}" mask="url(#mm)"/>'; taken.append((2300,400,300))
    cc="#ffffff" if not P["dark"] else "#7a3d73"
    for x,y,r in place(rng,9,170,330,taken,gap=40):
        if y>H*0.35: o+=cloud(x,y,r/1.5,cc,0.95 if not P["dark"] else 0.9); taken.append((x,y,r*0.8))
    sets=BOWS(P)
    for x,y,r in place(rng,4,160,230,taken,gap=40):
        o+=bow(x,y,r/110,rng.uniform(-20,20),*rng.choice(sets),tails=True,glow=(0.35 if P["dark"] else None)); taken.append((x,y,r))
    return o+scatter_extras(rng,P,taken,nh=10,ns=(60 if P["dark"] else 30))
def w_waves(P,rng):
    o='<rect width="100%" height="100%" fill="url(#bg)"/>'
    cols=([P["pink2"],P["pink"],P["red"],P["blue"],P["butter"],P["pink2"],P["white"],P["pink"]] if not P["dark"] else ["#6a2a58",P["berry"],P["red"],"#7a4fa0",P["pink"],"#5d2a55",P["pink2"],"#3e1a3a"])
    for i,c in enumerate(cols):
        y=170+i*205; amp=rng.uniform(150,240); ph=rng.uniform(-90,90); w=rng.uniform(80,150)
        p=f'M-150,{f(y)} C{f(W*.18)},{f(y-amp+ph)} {f(W*.33)},{f(y+amp+ph)} {f(W*.5)},{f(y)} S{f(W*.82)},{f(y-amp-ph)} {W+150},{f(y)}'
        op=0.9 if not P["dark"] else 0.8
        o+=f'<path d="{p}" fill="none" stroke="{c}" stroke-width="{f(w)}" stroke-linecap="round" opacity="{op}"/>'
        o+=f'<path d="{p}" transform="translate(0,-{f(w*0.22)})" fill="none" stroke="#ffffff" stroke-opacity="0.28" stroke-width="{f(w*0.1)}" stroke-linecap="round"/>'
    taken=[]; sets=BOWS(P)
    for x,y,s,rot in [(560,520,2.2,-12),(2250,1280,2.5,10),(1500,300,1.2,8)]:
        o+=bow(x,y,s,rot,*sets[(int(x)//7)%len(sets)] if False else sets[[0,2,1][len(taken)%3]],tails=True,glow=(0.4 if P["dark"] else None)); taken.append((x,y,110*s))
    return o+scatter_extras(rng,P,taken,nh=14,ns=26)
def w_berries(P,rng):
    o='<rect width="100%" height="100%" fill="url(#bg)"/><rect width="100%" height="100%" fill="url(#dots)"/>'
    taken=[]
    for x,y,r in place(rng,34,62,120,taken,gap=34):
        o+=berry(x,y,r/1.05,rng.uniform(-35,35),P); taken.append((x,y,r))
    sets=BOWS(P)
    for x,y,r in place(rng,3,150,210,taken,gap=40):
        o+=bow(x,y,r/110,rng.uniform(-20,20),*rng.choice(sets),tails=True,glow=(0.35 if P["dark"] else None)); taken.append((x,y,r))
    return o+scatter_extras(rng,P,taken,nh=18,ns=22)
WALLS=[("1-bow-garden",w_bows,11),("2-gingham-picnic",w_gingham,22),("3-polka-clouds",w_polka,33),("4-ribbon-waves",w_waves,44),("5-strawberry-patch",w_berries,55)]
def render(P,key,fn,seed):
    rng=random.Random(seed)
    body=fn(P,rng)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{defs(P)}</defs>{body}</svg>'
    sp=f"{SCR}/{P['name']}-{key}.svg"; pp=sp[:-4]+".png"
    open(sp,"w").write(svg)
    subprocess.run(["rsvg-convert","-w",str(W),"-h",str(H),sp,"-o",pp],check=True)
    im=Image.open(pp).convert("RGB")
    noise=Image.effect_noise((W,H),1.6).convert("RGB")
    im=ImageChops.add(im,noise,1.0,-128)
    q=85; dst=f"{OUT}/{key}.jpg"
    while True:
        im.save(dst,"JPEG",quality=q,optimize=True,progressive=True)
        if os.path.getsize(dst)<=680_000 or q<=60: break
        q-=5
    return dst,os.path.getsize(dst),q
if __name__=="__main__":
    variants={"light":LIGHT,"dark":DARK}
    if len(sys.argv)<3 or sys.argv[1] not in variants: sys.exit("usage: kawaii.py light|dark OUTDIR [wallpaper ...]")
    P=variants[sys.argv[1]]; OUT=sys.argv[2]; only=sys.argv[3:]
    os.makedirs(OUT,exist_ok=True)
    for key,fn,seed in WALLS:
        if only and key not in only and key.split("-")[0] not in only: continue
        d,sz,q=render(P,key,fn,seed); print(os.path.basename(d),sz//1024,"KB q",q,flush=True)
