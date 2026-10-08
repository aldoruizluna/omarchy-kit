import math, random
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
W, H = 2880, 1800
FR = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf"
FB = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Bold.ttf"
def rgb(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def mix(a,b,t): return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))
def sc(c,k): return tuple(max(0,min(255,int(v*k))) for v in c)
_fc={}
def font(size,bold=False):
    k=(size,bold)
    if k not in _fc: _fc[k]=ImageFont.truetype(FB if bold else FR,size)
    return _fc[k]
class Layer:
    S=2
    def __init__(s,fill=(0,0,0)):
        s.im=Image.new("RGB",(W*s.S,H*s.S),fill); s.d=ImageDraw.Draw(s.im); s.tx=None; s.main_small=None
    def P(s,pts): return [(x*s.S,y*s.S) for x,y in pts]
    def line(s,pts,c,w=2): s.d.line(s.P(pts),fill=c,width=max(1,int(w*s.S)),joint="curve")
    def poly(s,pts,fill=None,outline=None,w=2):
        if fill is not None: s.d.polygon(s.P(pts),fill=fill)
        if outline is not None: s.line(list(pts)+[pts[0]],outline,w)
    def rect(s,x0,y0,x1,y1,fill=None,outline=None,w=2): s.poly([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],fill,outline,w)
    def circle(s,cx,cy,r,fill=None,outline=None,w=2):
        s.d.ellipse([(cx-r)*s.S,(cy-r)*s.S,(cx+r)*s.S,(cy+r)*s.S],fill=fill,outline=outline,width=int(w*s.S))
    def arc(s,cx,cy,r,a0,a1,c,w=2):
        s.d.arc([(cx-r)*s.S,(cy-r)*s.S,(cx+r)*s.S,(cy+r)*s.S],a0,a1,fill=c,width=max(1,int(w*s.S)))
    def pie(s,cx,cy,r,a0,a1,c):
        s.d.pieslice([(cx-r)*s.S,(cy-r)*s.S,(cx+r)*s.S,(cy+r)*s.S],a0,a1,fill=c)
    def text(s,xy,t,c,size=22,bold=False,anchor="la"):
        if s.tx is None: s.tx=Image.new("RGB",(W*s.S,H*s.S),(0,0,0)); s.td=ImageDraw.Draw(s.tx)
        s.td.text((xy[0]*s.S,xy[1]*s.S),t,fill=c,font=font(size*s.S,bold),anchor=anchor)
    def done(s):
        m=s.im.resize((W,H),Image.LANCZOS); s.main_small=m
        if s.tx is not None: return ImageChops.screen(m,s.tx.resize((W,H),Image.LANCZOS))
        return m
def chamfer(x,y,w,h,c=18,tl=True,br=True,tr=False,bl=False):
    p=[]
    p += [(x+c,y),] if tl else [(x,y)]
    if tl: p.append((x,y+c))
    # build clockwise starting top-left
    pts=[]
    pts += [(x,y+c),(x+c,y)] if tl else [(x,y)]
    pts += [(x+w-c,y),(x+w,y+c)] if tr else [(x+w,y)]
    pts += [(x+w,y+h-c),(x+w-c,y+h)] if br else [(x+w,y+h)]
    pts += [(x+c,y+h),(x,y+h-c)] if bl else [(x,y+h)]
    return pts
def background(c0,c1,focus=(0.5,0.5),power=1.0):
    g=Image.radial_gradient("L").resize((W,H),Image.BICUBIC)
    # radial_gradient: 0 at centre -> 255 at edge; shift focus by pasting onto larger canvas
    if focus!=(0.5,0.5):
        big=Image.radial_gradient("L").resize((W*2,H*2),Image.BICUBIC)
        ox=int(W*(1-focus[0])-0); oy=int(H*(1-focus[1])-0)
        g=big.crop((ox,oy,ox+W,oy+H)).resize((W,H))
    g=g.point(lambda v:int(255*((v/255)**power)))
    return Image.composite(Image.new("RGB",(W,H),c1),Image.new("RGB",(W,H),c0),g)
def compose(base,crisp,glow_src=None,glows=((2,0.9),(10,2.0),(30,3.2)),extra=None,vig=0.55,noise=3,seed=1):
    out=ImageChops.screen(base,crisp) if crisp is not None else base
    g=glow_src or crisp
    acc=Image.new("RGB",(W,H),(0,0,0))
    for r,k in glows:
        b=g.filter(ImageFilter.GaussianBlur(r)).point(lambda v,k=k:min(255,int(v*k)))
        acc=ImageChops.add(acc,b)
    out=ImageChops.screen(out,acc)
    if extra is not None: out=ImageChops.screen(out,extra)
    if vig:
        m=Image.radial_gradient("L").resize((W,H),Image.BICUBIC).point(lambda v:int(255*(1-vig*((v/255)**2.2))))
        out=ImageChops.multiply(out,Image.merge("RGB",(m,m,m)))
    if noise:
        n=Image.effect_noise((W,H),noise).convert("RGB")
        out=ImageChops.add(out,n,1.0,-128+noise)
    return out
