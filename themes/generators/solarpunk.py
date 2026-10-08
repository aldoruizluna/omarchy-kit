"""Solarpunk and Solarpunk Dusk wallpapers: original SVG scenes rasterised with rsvg-convert, then written as JPEG.

usage: solarpunk.py day|dusk OUTDIR [1|2|3|4|5 ...]     (called by themes/make-wallpapers)
"""
import math, random, subprocess, os, sys
from PIL import Image
W,H=2880,1800
R=random.Random

def hexmix(a,b,t):
    a=a.lstrip('#');b=b.lstrip('#')
    return '#'+''.join('%02x'%round(int(a[i:i+2],16)*(1-t)+int(b[i:i+2],16)*t) for i in (0,2,4))

class SVG:
    def __init__(s): s.defs=[];s.b=[];s.n=0
    def add(s,x): s.b.append(x)
    def _st(s,stops): return ''.join('<stop offset="%s" stop-color="%s" stop-opacity="%s"/>'%(t[0],t[1],t[2] if len(t)>2 else 1) for t in stops)
    def grad(s,stops,x1=0,y1=0,x2=0,y2=1):
        s.n+=1;i='g%d'%s.n
        s.defs.append('<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>'%(i,x1,y1,x2,y2,s._st(stops)))
        return 'url(#%s)'%i
    def rad(s,stops,cx,cy,r):
        s.n+=1;i='g%d'%s.n
        s.defs.append('<radialGradient id="%s" gradientUnits="userSpaceOnUse" cx="%.1f" cy="%.1f" r="%.1f">%s</radialGradient>'%(i,cx,cy,r,s._st(stops)))
        return 'url(#%s)'%i
    def out(s):
        return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><defs>%s</defs>%s</svg>'%(W,H,W,H,''.join(s.defs),''.join(s.b))

def rect(x,y,w,h,fill,ex=''): return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" %s/>'%(x,y,w,h,fill,ex)
def circ(x,y,r,fill,ex=''): return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" %s/>'%(x,y,r,fill,ex)
def poly(pts,fill,ex=''): return '<polygon points="%s" fill="%s" %s/>'%(' '.join('%.1f,%.1f'%p for p in pts),fill,ex)
def path(d,fill='none',ex=''): return '<path d="%s" fill="%s" %s/>'%(d,fill,ex)

def ridge(base,comps):
    return lambda x: base-sum(a*math.sin(2*math.pi*f*x/W+p) for a,f,p in comps)
def rcomps(r,amp):
    return [(amp*r.uniform(.7,1.1),0.55,r.uniform(0,6.28)),(amp*.45*r.uniform(.7,1.2),1.3,r.uniform(0,6.28)),(amp*.18*r.uniform(.7,1.2),2.9,r.uniform(0,6.28))]
def hill(s,y,fill,ex=''):
    pts=' '.join('%d,%.1f'%(x,y(x)) for x in range(0,W+1,12))
    s.add('<polygon points="0,%d %s %d,%d" fill="%s" %s/>'%(H+2,pts,W,H+2,fill,ex))

def leaf(cx,cy,L,Wd,ang,fill,vein=None,op=1,vw=3):
    d='M0,0 C%.1f,%.1f %.1f,%.1f %.1f,0 C%.1f,%.1f %.1f,%.1f 0,0Z'%(.3*L,-Wd,.7*L,-.8*Wd,L,.7*L,.8*Wd,.3*L,Wd)
    g='<g transform="translate(%.1f,%.1f) rotate(%.1f)" opacity="%s"><path d="%s" fill="%s"/>'%(cx,cy,ang,op,d,fill)
    if vein: g+='<path d="M0,0 Q%.1f,%.1f %.1f,0" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round"/>'%(.5*L,-Wd*.06,.94*L,vein,vw)
    return g+'</g>'

def turbine(s,x,y,h,col,sh,rot):
    tw,tb=h*.034,h*.011
    s.add(poly([(x-tw,y),(x+tw,y),(x+tb,y-h),(x-tb,y-h)],col))
    s.add(poly([(x+tw*.3,y),(x+tw,y),(x+tb,y-h),(x+tb*.2,y-h)],sh,'opacity=".6"'))
    L,w=h*.62,h*.026
    for k in range(3):
        a=math.radians(rot+k*120);u=(math.cos(a),math.sin(a));v=(-u[1],u[0])
        loc=[(0,.6*w),(.2*L,w),(L,0),(.2*L,-.35*w),(0,-.6*w)]
        s.add(poly([(x+(h and 0)+u[0]*a1+v[0]*b1, y-h+u[1]*a1+v[1]*b1) for a1,b1 in loc],col))
    s.add(circ(x,y-h,h*.026,sh))

def clouds(s,r,col,op,n,ymin,ymax):
    for _ in range(n):
        cx,cy=r.uniform(0,W),r.uniform(ymin,ymax);sc=r.uniform(.7,1.5)
        for k in range(5):
            s.add('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s" opacity="%s"/>'%(cx+k*70*sc-140*sc,cy+r.uniform(-14,14),r.uniform(90,170)*sc,r.uniform(24,40)*sc,col,op))

def stars(s,r,n,ymax,col):
    for _ in range(n):
        x,y=r.uniform(0,W),r.uniform(0,ymax*(0.3+0.7*r.random()))
        s.add(circ(x,y,r.uniform(1,2.8),col,'opacity="%.2f"'%r.uniform(.3,.95)))
    for _ in range(14):
        x,y,k=r.uniform(0,W),r.uniform(0,ymax*.8),r.uniform(8,16)
        s.add(poly([(x,y-k),(x+k*.18,y-k*.18),(x+k,y),(x+k*.18,y+k*.18),(x,y+k),(x-k*.18,y+k*.18),(x-k,y),(x-k*.18,y-k*.18)],col,'opacity=".8"'))

def motes(s,r,n,cols,y0,y1,glow):
    for _ in range(n):
        x,y=r.uniform(0,W),r.uniform(y0,y1);c=r.choice(cols);rr=r.uniform(2.5,7)
        if glow: s.add(circ(x,y,rr*4,s.rad([(0,c,.5),(1,c,0)],x,y,rr*4)))
        s.add(circ(x,y,rr,c,'opacity=".9"'))

def rays(s,cx,cy,n,rad,col,op,rot=0,half=.035):
    for i in range(n):
        a=rot+i*2*math.pi/n
        s.add(poly([(cx,cy),(cx+rad*math.cos(a-half),cy+rad*math.sin(a-half)),(cx+rad*math.cos(a+half),cy+rad*math.sin(a+half))],col,'opacity="%s"'%op))

# ---------- scene 1: hills, solar fields, wind ----------
def scene_hills(A,dusk,seed=1):
    r=R(seed);s=SVG()
    s.add(rect(0,0,W,H,A['sky'][-1][1]))
    s.add(rect(0,0,W,H*.72,s.grad(A['sky'])))
    if dusk: stars(s,r,160,H*.5,'#fff6d8')
    sx,sy=W*.68,H*.55
    s.add(circ(sx,sy,1000,s.rad([(0,A['glow'],.8),(.3,A['glow'],.32),(1,A['glow'],0)],sx,sy,1000)))
    rays(s,sx,sy,28,2200,A['glow'],.16 if not dusk else .12,rot=-1.57,half=.03)
    s.add(circ(sx,sy,150,A['sun']))
    if not dusk: clouds(s,r,'#ffffff',.55,7,H*.1,H*.42)
    else: clouds(s,r,'#f0a85a',.12,5,H*.3,H*.5)
    bases=[.58,.64,.71,.78,.86,.95]; amps=[34,42,50,56,60,50]
    ridges=[ridge(H*b,rcomps(r,a)) for b,a in zip(bases,amps)]
    for i,y in enumerate(ridges):
        hill(s,y,A['hills'][i])
        if i==0 or i==1:
            for k in range(7 if i==0 else 5):
                x=r.uniform(.04,.96)*W; turbine(s,x,y(x)+4,(90 if i==0 else 150),A['turb'] if not dusk else A['turb'],A['turb_sh'],r.uniform(0,120))
        if i==3:
            for (xa,xb) in ((.04,.46),(.76,.99)):
                for row in range(5):
                    pw=64+row*13;ph=26+row*6;x=xa*W+row*15
                    while x<xb*W:
                        yy=y(x)+34+row*38
                        top=pw*.82;ox=(pw-top)/2
                        s.add(poly([(x+ox,yy),(x+ox+top,yy),(x+pw,yy+ph),(x,yy+ph)],A['panel']))
                        s.add(poly([(x+ox,yy),(x+ox+top*.45,yy),(x+pw*.35,yy+ph),(x,yy+ph)],A['panel_hi'],'opacity=".35"'))
                        s.add(rect(x+pw/2-1.5,yy+ph,3,9,A['hills'][i+1]))
                        x+=pw*1.2
        if i==4:
            for k in range(4):
                x=W*(.12+k*.07)+r.uniform(-20,20);yb=y(x)+16;w=r.uniform(70,100)
                s.add(rect(x,yb-w*.55,w,w*.55,A['cream']))
                s.add(poly([(x-8,yb-w*.55),(x+w/2,yb-w*1.0),(x+w+8,yb-w*.55)],A['clay']))
                s.add(rect(x+w*.4,yb-w*.3,w*.2,w*.3,A['clay2']))
                s.add(rect(x+w*.1,yb-w*.42,w*.18,w*.14,A['lit'] if dusk else A['win']))
                s.add(circ(x+w*1.18,yb-w*.2,w*.24,A['leafs'][0]))
            turbine(s,W*.9,y(W*.9)+20,430,A['turb'],A['turb_sh'],25)
            turbine(s,W*.78,y(W*.78)+20,330,A['turb'],A['turb_sh'],70)
    # foreground leaves
    for (bx,by,sgn) in ((0,H,1),(W,H,-1)):
        for k in range(9):
            ang=-(25+k*9) if sgn==1 else -(180-25-k*9)
            L=r.uniform(380,760);s.add(leaf(bx,by+20,L,L*.2,ang,A['leafs'][k%len(A['leafs'])],A['vein'],1))
    motes(s,r,70,A['motes'],H*.4,H*.95,dusk)
    return s.out()

# ---------- scene 2: green towers & airships ----------
def airship(s,cx,cy,L,A,ang=-4):
    hh=L*.28
    s.add('<g transform="translate(%.1f,%.1f) rotate(%s)">'%(cx,cy,ang))
    s.add(poly([(-L*.5,0),(-L*.62,-hh*.55),(-L*.36,-hh*.2)],A['fin']));s.add(poly([(-L*.5,0),(-L*.62,hh*.55),(-L*.36,hh*.2)],A['fin']))
    s.add('<ellipse cx="0" cy="0" rx="%.1f" ry="%.1f" fill="%s"/>'%(L/2,hh/2,A['air']))
    s.add('<ellipse cx="0" cy="0" rx="%.1f" ry="%.1f" fill="%s" opacity=".9"/>'%(L*.48,hh*.1,A['air2']))
    s.add(rect(-L*.2,-hh*.4,L*.4,hh*.07,A['panel']))
    s.add('<path d="M%.1f,%.1f L%.1f,%.1f M%.1f,%.1f L%.1f,%.1f" stroke="%s" stroke-width="%.1f"/>'%(-L*.1,hh*.45,-L*.1,hh*.62,L*.1,hh*.45,L*.1,hh*.62,A['air2'],max(1.5,L*.006)))
    s.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s"/>'%(-L*.14,hh*.6,L*.28,hh*.2,hh*.08,A['gondola']))
    s.add(circ(L*.52,0,hh*.08,A['air2']));s.add('</g>')

def tower(s,r,x,w,h,base,A,layer,dusk):
    body=A['towers'][layer];top=base-h
    s.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s"/>'%(x,top,w,h,w*.06,body))
    if layer==0: return
    tiers=max(3,int(h/140));th=h/tiers;sc=1.0 if layer==2 else .75
    for i in range(tiers):
        ty=top+i*th+th*.84;ov=w*.07
        cols=max(2,int(w/38))
        for c in range(cols):
            for rw in range(3):
                wx=x+14+c*(w-28)/cols;wy=top+i*th+th*.1+rw*th*.22
                lit=dusk and r.random()<.45
                s.add(rect(wx,wy,(w-28)/cols*.55,th*.11,A['lit'] if lit else A['win'],'opacity="%s"'%(1 if lit else .75)))
        s.add(rect(x-ov,ty,w+2*ov,th*.09,A['slab']))
        n=max(3,int(w/20))
        for k in range(n):
            bx=x-ov+(k+r.random()*.8)*(w+2*ov)/n
            s.add(circ(bx,ty,r.uniform(9,19)*sc,r.choice(A['greens'])))
            if r.random()<.4:
                s.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" fill="%s" opacity=".9"/>'%(bx-2,ty,4,r.uniform(20,60)*sc,r.choice(A['greens'])))
    kind=r.choice(['dome','garden','spire'])
    if kind=='dome':
        s.add('<path d="M%.1f,%.1f A%.1f,%.1f 0 0 1 %.1f,%.1f Z" fill="%s" opacity=".85"/>'%(x+w*.1,top,w*.4,w*.4,x+w*.9,top,A['glass']))
    elif kind=='garden':
        for k in range(int(w/26)): s.add(circ(x+14+k*26,top-6,r.uniform(12,24)*sc,r.choice(A['greens'])))
        turbine(s,x+w*.5,top,w*.9,A['turb'],A['turb_sh'],r.uniform(0,120))
    else:
        s.add(poly([(x+w*.42,top),(x+w*.58,top),(x+w*.5,top-h*.22)],A['slab']));s.add(circ(x+w*.5,top-h*.22,7,A['sun']))

def scene_towers(A,dusk,seed=2):
    r=R(seed);s=SVG()
    s.add(rect(0,0,W,H,A['sky'][-1][1]));s.add(rect(0,0,W,H*.8,s.grad(A['sky'])))
    if dusk: stars(s,r,140,H*.45,'#fff6d8')
    sx,sy=W*.46,H*.62
    s.add(circ(sx,sy,1100,s.rad([(0,A['glow'],.9),(.3,A['glow'],.35),(1,A['glow'],0)],sx,sy,1100)))
    rays(s,sx,sy,36,2400,A['glow'],.12,rot=-1.57,half=.022)
    s.add(circ(sx,sy,200,A['sun']))
    if not dusk: clouds(s,r,'#ffffff',.5,6,H*.08,H*.4)
    airship(s,W*.22,H*.2,560,A,-5);airship(s,W*.78,H*.3,330,A,3);airship(s,W*.62,H*.13,200,A,-2)
    for layer,(hmin,hmax,wmin,wmax,base,gap) in enumerate([(380,820,110,190,H*.8,10),(560,1150,150,240,H*.88,26),(700,1320,190,300,H*.97,60)]):
        x=-60 if layer!=1 else 40
        while x<W:
            w=r.uniform(wmin,wmax)*(1 if layer<2 else 1);h=r.uniform(hmin,hmax)
            if layer==2 and abs(x+w/2-W*.46)<260: x+=w*.35;continue
            tower(s,r,x,w,h,base,A,layer,dusk);x+=w+r.uniform(gap*.4,gap*1.8)
        if layer==1:   # skybridges
            for k in range(6):
                y=H*(.42+k*.07);xa=r.uniform(.05,.8)*W
                s.add('<rect x="%.1f" y="%.1f" width="%.1f" height="10" rx="5" fill="%s"/>'%(xa,y,r.uniform(180,360),A['slab']))
    # canopy
    s.add(rect(0,H*.94,W,H*.07,A['canopy'][0]))
    for row,(yb,col) in enumerate(zip((.94,.965,.99),A['canopy'])):
        x=-40
        while x<W:
            rr=r.uniform(40,90);s.add(circ(x,H*yb+r.uniform(-12,12),rr,col));x+=rr*r.uniform(.8,1.3)
    motes(s,r,80,A['motes'],H*.3,H*.9,dusk)
    return s.out()

# ---------- scene 3: art nouveau ----------
def bez(p,t):
    (x0,y0),(x1,y1),(x2,y2),(x3,y3)=p;u=1-t
    return (u**3*x0+3*u*u*t*x1+3*u*t*t*x2+t**3*x3,u**3*y0+3*u*u*t*y1+3*u*t*t*y2+t**3*y3)
def bang(p,t):
    a=bez(p,max(0,t-.01));b=bez(p,min(1,t+.01));return math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
def flower(s,cx,cy,rad,A,n=9):
    for k in range(n):
        s.add('<g transform="translate(%.1f,%.1f) rotate(%.1f)"><ellipse cx="%.1f" cy="0" rx="%.1f" ry="%.1f" fill="%s"/></g>'%(cx,cy,k*360/n,rad*.62,rad*.42,rad*.2,A['petal'][0]))
    for k in range(n):
        s.add('<g transform="translate(%.1f,%.1f) rotate(%.1f)"><ellipse cx="%.1f" cy="0" rx="%.1f" ry="%.1f" fill="%s"/></g>'%(cx,cy,k*360/n+180/n,rad*.4,rad*.28,rad*.14,A['petal'][1]))
    s.add(circ(cx,cy,rad*.17,A['petal'][2]))
def scene_nouveau(A,dusk,seed=3):
    r=R(seed);s=SVG()
    s.add(rect(0,0,W,H,s.grad(A['nv_bg'],0,0,0,1)))
    sx,sy=W*.72,H*.36
    for k,rr in enumerate((560,470,390,320)):
        s.add(circ(sx,sy,rr,A['nv_rings'][k],'opacity="%s"'%(.55 if dusk else .7)))
    s.add(circ(sx,sy,250,s.rad([(0,A['sun']),(1,A['sun2'])],sx,sy,250)))
    rays(s,sx,sy,24,700,A['sun'],.14,half=.04)
    stems=[[(-120,H*.98),(W*.28,H*1.02),(W*.02,H*.34),(W*.46,H*.1)],
           [(W+120,H*1.02),(W*.62,H*.92),(W*.9,H*.5),(W*.52,H*.34)],
           [(W*.3,H*1.05),(W*.34,H*.7),(W*.18,H*.62),(W*.22,H*.4)],
           [(W*.78,H*1.05),(W*.7,H*.8),(W*.84,H*.7),(W*.8,H*.58)]]
    for si,p in enumerate(stems):
        pts=[bez(p,i/80) for i in range(81)]
        L=[];Rr=[]
        for i,(x,y) in enumerate(pts):
            t=i/80;a=math.radians(bang(p,t)+90);w=(16-9*t) if si<2 else (11-6*t)
            L.append((x+math.cos(a)*w,y+math.sin(a)*w));Rr.append((x-math.cos(a)*w,y-math.sin(a)*w))
        s.add(poly(L+Rr[::-1],A['stem']))
        n=11 if si<2 else 7
        for k in range(n):
            t=.1+.85*k/(n-1);x,y=bez(p,t);a=bang(p,t);side=1 if k%2==0 else -1
            L0=(260 if si<2 else 170)*(1-.45*t)*r.uniform(.85,1.1)
            s.add(leaf(x,y,L0,L0*.3,a+side*58,A['nv_leaf'][k%len(A['nv_leaf'])],A['vein'],1,4))
        x,y=bez(p,1);flower(s,x,y,150 if si<2 else 100,A)
    for k in range(60):
        t=k/59;a=2.6+t*2.4;rr=420+60*math.sin(t*9)
        s.add(circ(sx+rr*math.cos(a),sy+rr*math.sin(a),r.uniform(3,8),A['sun'],'opacity=".7"'))
    m=60;s.add(rect(m,m,W-2*m,H-2*m,'none','stroke="%s" stroke-width="6" rx="40"'%A['frame']))
    s.add(rect(m+26,m+26,W-2*m-52,H-2*m-52,'none','stroke="%s" stroke-width="2.5" rx="26" opacity=".8"'%A['frame']))
    for (x,y) in ((m,m),(W-m,m),(m,H-m),(W-m,H-m)):
        s.add(poly([(x,y-24),(x+24,y),(x,y+24),(x-24,y)],A['frame']))
    motes(s,r,50,A['motes'],H*.1,H*.9,dusk)
    return s.out()

# ---------- scene 4: sun-ray fan ----------
def scene_fan(A,dusk,seed=4):
    r=R(seed);s=SVG()
    s.add(rect(0,0,W,H,s.grad(A['fan_bg'])))
    cx,cy=W/2,H*.8
    rays(s,cx,cy,48,3600,A['sun'],.13 if not dusk else .09,rot=-math.pi,half=math.pi/96)
    if dusk: stars(s,r,120,H*.5,'#fff6d8')
    for rr,c in zip((1500,1280,1080,900,740,600,480,370,270),A['fan']):
        s.add('<path d="M%.1f,%.1f A%d,%d 0 0 1 %.1f,%.1f Z" fill="%s"/>'%(cx-rr,cy,rr,rr,cx+rr,cy,c))
    for rr in (1500,1080,740,480,270):
        s.add('<path d="M%.1f,%.1f A%d,%d 0 0 1 %.1f,%.1f" fill="none" stroke="%s" stroke-width="3" opacity=".6"/>'%(cx-rr,cy,rr,rr,cx+rr,cy,A['gold']))
    s.add(rect(0,cy,W,H-cy,A['fan_ground']))
    y=ridge(H*.86,rcomps(r,26));hill(s,y,A['hills'][3]);y2=ridge(H*.95,rcomps(r,22));hill(s,y2,A['hills'][5])
    for (bx,by,sgn) in ((W*.5,H*.93,0),):
        for k in range(15):
            ang=-90+(k-7)*11;L=r.uniform(260,520)
            s.add(leaf(bx+(k-7)*28,by+40,L,L*.18,ang,A['leafs'][k%len(A['leafs'])],A['vein']))
    for (bx,sg) in ((0,1),(W,-1)):
        for k in range(8):
            ang=-(20+k*10) if sg==1 else -(160-k*10);L=r.uniform(380,700)
            s.add(leaf(bx,H+10,L,L*.2,ang,A['leafs'][k%len(A['leafs'])],A['vein']))
    motes(s,r,70,A['motes'],H*.25,H*.9,dusk)
    return s.out()

# ---------- scene 5: circuit leaf ----------
def scene_circuit(A,dusk,seed=5):
    r=R(seed);s=SVG()
    s.add(rect(0,0,W,H,s.grad(A['cc_bg'])))
    g=48;dirs=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
    for _ in range(70):
        x,y=r.randrange(0,W//g)*g,r.randrange(0,H//g)*g;d=r.randrange(8);pts=[(x,y)]
        for k in range(r.randint(3,6)):
            d=(d+r.choice((-1,0,1)))%8;ln=r.randint(2,6)
            x+=dirs[d][0]*ln*g;y+=dirs[d][1]*ln*g;pts.append((x,y))
        s.add('<polyline points="%s" fill="none" stroke="%s" stroke-width="4" stroke-linejoin="round" opacity="%s"/>'%(' '.join('%d,%d'%p for p in pts),A['cc_line'],r.choice((.14,.2,.28))))
        for p in (pts[0],pts[-1]): s.add('<circle cx="%d" cy="%d" r="9" fill="none" stroke="%s" stroke-width="4" opacity=".3"/>'%(p[0],p[1],A['cc_line']))
    def bigleaf(cx,cy,L,ang,op,seedv):
        rr=R(seedv);Wh=L*.36
        o='<g transform="translate(%.1f,%.1f) rotate(%.1f)" opacity="%s">'%(cx,cy,ang,op)
        o+='<path d="M0,0 C%.1f,%.1f %.1f,%.1f %.1f,0 C%.1f,%.1f %.1f,%.1f 0,0Z" fill="%s" stroke="%s" stroke-width="7"/>'%(.25*L,-Wh*1.6,.72*L,-Wh*1.25,L,.72*L,Wh*1.25,.25*L,Wh*1.6,A['cc_leaf'],A['cc_edge'])
        o+='<path d="M0,0 L%.1f,0" stroke="%s" stroke-width="9" stroke-linecap="round"/>'%(L*.97,A['cc_edge'])
        n=15
        for k in range(1,n):
            t=.06+.86*k/n;x=t*L;hw=Wh*1.18*math.sin(math.pi*t**.9)*(1-.2*t)
            for sg in (1,-1):
                v=hw*rr.uniform(.55,.82);run=rr.uniform(.04,.1)*L
                o+='<polyline points="%.1f,0 %.1f,%.1f %.1f,%.1f" fill="none" stroke="%s" stroke-width="6" stroke-linejoin="round"/>'%(x,x+v*.9,sg*v*.9,x+v*.9+run,sg*v*.9,A['cc_edge'])
                o+='<circle cx="%.1f" cy="%.1f" r="9" fill="%s"/>'%(x+v*.9+run,sg*v*.9,A['cc_node'] if k%3 else A['cc_edge'])
        return o+'<circle cx="0" cy="0" r="16" fill="%s"/></g>'%A['cc_node']
    s.add(bigleaf(W*.12,H*.78,1750,-28,1,11))
    s.add(bigleaf(W*.78,H*1.05,1150,-128,.8,12))
    s.add(bigleaf(W*.92,H*.12,700,150,.55,13))
    motes(s,r,60,A['motes'],0,H,dusk)
    return s.out()

DAY=dict(
 sky=[(0,'#7fcfda'),(.4,'#bfe6d8'),(.75,'#fbf0c6'),(1,'#fedc92')],sun='#ffcf45',sun2='#f6a92a',glow='#fff1b8',
 hills=['#b9dba6','#96c888','#6db26b','#469659','#2f7a47','#1f5f3a'],cream='#fbf6e4',panel='#2b5f86',panel_hi='#9bd6e6',
 turb='#fffaf0',turb_sh='#b9c9b4',clay='#c4663f',clay2='#e8a46c',gold='#e0a526',vein='#1f5f3a',lit='#ffe9a0',win='#9fd3df',
 leafs=['#2f7a47','#469659','#6db26b','#1f5f3a','#8cc86c'],motes=['#fff6d0','#ffe08a','#ffffff'],
 towers=['#cfe4d4','#ede6cb','#fbf6e6'],slab='#c4663f',greens=['#3f8a4f','#5fae5e','#8cc86c','#2f6f45'],glass='#8fd5dc',
 air='#fbf6e6',air2='#c4663f',fin='#e8a46c',gondola='#8a5a3c',canopy=['#5fae5e','#3f8a4f','#2f6f45'],
 nv_bg=[(0,'#f9f3df'),(1,'#efe5c4')],nv_rings=['#e7efc9','#cfe6c4','#b6dcc4','#9fd4c8'],stem='#2f7a47',frame='#c9962a',
 nv_leaf=['#3f8a4f','#6db26b','#1d8c86','#8cc86c','#2f7a47'],petal=['#e8a46c','#c4663f','#ffd45e'],
 fan_bg=[(0,'#eaf6ea'),(.6,'#fbf3d2'),(1,'#fde3a5')],fan=['#cfeadb','#a6dcca','#6fc4b4','#9ccf80','#e6d56a','#f7bf3c','#f3a33a','#f6c14c','#ffd95e'],fan_ground='#2f7a47',
 cc_bg=[(0,'#f9f3df'),(1,'#ece3c2')],cc_line='#2f7a47',cc_leaf='#bfdcae',cc_edge='#1f5f3a',cc_node='#c9962a')
DUSK=dict(
 sky=[(0,'#06161a'),(.28,'#0b2d31'),(.55,'#15483e'),(.76,'#7d8a4a'),(.9,'#e8a23f'),(1,'#f27d3c')],sun='#ffc65a',sun2='#f08a3a',glow='#f7a94c',
 hills=['#1d5c48','#154b3c','#103e33','#0c3029','#08241f','#051914'],cream='#d9e8cf',panel='#0f3b4f',panel_hi='#5fe3d4',
 turb='#d3e8d6',turb_sh='#7fb59a',clay='#c98a3a',clay2='#e6b25a',gold='#f2c14e',vein='#7ee6c0',lit='#ffd978',win='#1f6a63',
 leafs=['#0c3029','#103e33','#154b3c','#1d5c48','#0a2a22'],motes=['#7ff0c0','#ffd86a','#b8ffe0'],
 towers=['#1b4f45','#12382f','#0a241e'],slab='#c98a3a',greens=['#2f9a5f','#54c987','#7ee6a8','#1e7a4a'],glass='#5fe3d4',
 air='#d9e8cf',air2='#f0a43a',fin='#7ee6c0',gondola='#6b4a2f',canopy=['#1e7a4a','#12603a','#0a4a2c'],
 nv_bg=[(0,'#0b2019'),(1,'#143a2c')],nv_rings=['#133b30','#175040','#1c6650','#238061'],stem='#2f9a5f',frame='#f2c14e',
 nv_leaf=['#2f9a5f','#54c987','#1d9a98','#7ee6a8','#1e7a4a'],petal=['#f08a3a','#c98a3a','#ffd978'],
 fan_bg=[(0,'#06161a'),(.6,'#0f3a30'),(1,'#1d5a45')],fan=['#0e3a36','#12493f','#17604f','#1d7a5e','#3aa064','#7cc15a','#e8b13e','#f6c04a','#ffd878'],fan_ground='#0c3029',
 cc_bg=[(0,'#0b2019'),(1,'#12362a')],cc_line='#54c987',cc_leaf='#14402f',cc_edge='#7ee6c0',cc_node='#f2c14e')

SCENES=[('1-sun-hills',scene_hills),('2-green-towers',scene_towers),('3-nouveau-garden',scene_nouveau),('4-sunray-fan',scene_fan),('5-circuit-leaf',scene_circuit)]
if __name__=='__main__':
    import tempfile
    variants={'day':(DAY,False),'dusk':(DUSK,True)}
    if len(sys.argv)<3 or sys.argv[1] not in variants: sys.exit('usage: solarpunk.py day|dusk OUTDIR [1|2|3|4|5 ...]')
    A,dusk=variants[sys.argv[1]];dest=sys.argv[2];only=sys.argv[3:]
    os.makedirs(dest,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='solarpunk-') as scratch:
        for name,fn in SCENES:
            if only and name.split('-')[0] not in only: continue
            svg=fn(A,dusk);sp=os.path.join(scratch,name+'.svg');open(sp,'w').write(svg)
            png=sp[:-4]+'.png';subprocess.run(['rsvg-convert','-w',str(W),'-h',str(H),sp,'-o',png],check=True)
            im=Image.open(png).convert('RGB');out=os.path.join(dest,name+'.jpg')
            for q in (88,85,82,78,74,70):
                im.save(out,quality=q,optimize=True,progressive=True)
                if os.path.getsize(out)<=680_000: break
            print(name+'.jpg',os.path.getsize(out)//1024,'KB q',q,flush=True)
