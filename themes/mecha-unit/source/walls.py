import sys, os, math, random
from art import *
from palette import BASE, RED

def roles(P, variant):
    c={k:rgb(v) for k,v in P.items()}
    if variant=="base":
        return dict(bg=c['background'],main=c['accent'],second=c['green'],spot=c['orange'],alert=c['red'],text=c['foreground'],soft=c['magenta'],cy=c['cyan'],warn=c['orange'])
    return dict(bg=c['background'],main=c['accent'],second=c['magenta'],spot=c['green'],alert=c['red'],text=c['foreground'],soft=c['orange'],cy=c['cyan'],warn=c['yellow'])

def base_bg(R,focus=(0.5,0.5),k=0.16):
    return background(sc(R['bg'],0.8),mix(R['bg'],R['main'],k),focus,0.9)

# ---------- 1 hex force-field ----------
def hexfield(R,seed):
    rnd=random.Random(seed); L=Layer(); F=Layer()
    Rh=58; dx=1.5*Rh; dy=math.sqrt(3)*Rh
    fx,fy=(W*rnd.uniform(.55,.7),H*rnd.uniform(.35,.5))
    cols=int(W/dx)+3; rows=int(H/dy)+3
    for i in range(-1,cols):
        for j in range(-1,rows):
            cx=i*dx; cy=j*dy+(dy/2 if i%2 else 0)
            d=math.hypot(cx-fx,cy-fy); f=math.exp(-(d/760)**2)
            ring=abs(d-560)<34 or abs(d-930)<26
            active=rnd.random()<0.05+0.18*f
            pts=[(cx+Rh*math.cos(math.radians(60*k)),cy+Rh*math.sin(math.radians(60*k))) for k in range(6)]
            col=mix(sc(R['main'],0.22),R['main'],min(1,f*1.25))
            if ring: col=mix(col,R['second'],0.85)
            if active:
                F.poly(pts,fill=sc(mix(R['bg'],R['main'] if rnd.random()<.8 else R['second'],0.5),0.34*(0.4+f)))
                col=mix(col,R['text'],0.35)
            for k in range(6):
                if (i+j+k)%7==0 and not active and f<0.3: continue
                L.line([pts[k],pts[(k+1)%6]],col,2 if f<.4 else 3)
    # impact core
    for r in (70,130,210):
        L.circle(fx,fy,r,outline=mix(R['main'],R['text'],0.5),w=2)
    L.circle(fx,fy,18,fill=R['text'])
    for a in range(0,360,45):
        L.line([(fx+34*math.cos(math.radians(a)),fy+34*math.sin(math.radians(a))),(fx+300*math.cos(math.radians(a)),fy+300*math.sin(math.radians(a)))],sc(R['text'],0.55),1)
    L.text((90,H-140),"FIELD INTEGRITY  92.4%",sc(R['text'],0.6),30,True)
    L.text((90,H-100),"SECTOR GRID  H-07 // LATTICE STABLE",sc(R['main'],0.9),22)
    c=L.done(); fl=F.done()
    return compose(base_bg(R,(fx/W,fy/H)),ImageChops.screen(c,fl),glow_src=L.main_small)

# ---------- 2 radar ----------
def radar(R,seed):
    rnd=random.Random(seed); L=Layer(); Sw=Layer()
    cx,cy=W*rnd.uniform(.58,.66),H*rnd.uniform(.5,.58)
    radii=[110,250,390,540,700,880,1080,1300]
    for n,r in enumerate(radii):
        col=mix(sc(R['main'],.45),R['main'],n/len(radii)*.8)
        if n%2: 
            for a in range(0,360,6): L.arc(cx,cy,r,a,a+3.2,col,2)
        else: L.circle(cx,cy,r,outline=col,w=2)
    r=700
    for a in range(0,360,2):
        ln=10; 
        if a%10==0: ln=22
        if a%30==0: ln=44
        ang=math.radians(a-90)
        L.line([(cx+(r-ln)*math.cos(ang),cy+(r-ln)*math.sin(ang)),(cx+r*math.cos(ang),cy+r*math.sin(ang))],mix(R['main'],R['text'],.3 if a%30==0 else 0),2 if a%30==0 else 1)
        if a%30==0:
            tx=cx+(r+48)*math.cos(ang); ty=cy+(r+48)*math.sin(ang)
            L.text((tx,ty),f"{a:03d}",sc(R['text'],.75),24,True,"mm")
    for a in (0,90,180,270):
        ang=math.radians(a)
        L.line([(cx+150*math.cos(ang),cy+150*math.sin(ang)),(cx+1300*math.cos(ang),cy+1300*math.sin(ang))],sc(R['main'],.55),1)
    L.circle(cx,cy,10,fill=R['second'])
    L.poly([(cx,cy-34),(cx+30,cy+20),(cx-30,cy+20)],outline=R['second'],w=2)
    for k,rr in enumerate(radii[1:6]): L.text((cx+8,cy-rr-4),f"{(k+1)*800:04d}",sc(R['main'],.8),18,False,"lb")
    # sweep
    a0=rnd.uniform(-70,-20)
    for k in range(70):
        Sw.pie(cx,cy,1300,a0-k*0.9,a0-k*0.9+1.0,sc(mix(R['second'],R['main'],.4),0.30*(1-k/70)**1.8))
    ang=math.radians(a0+1)
    L.line([(cx,cy),(cx+1300*math.cos(ang),cy+1300*math.sin(ang))],R['second'],3)
    # blips
    for k in range(9):
        a=rnd.uniform(0,2*math.pi); rr=rnd.uniform(160,1150)
        bx,by=cx+rr*math.cos(a),cy+rr*math.sin(a)
        hot=k in (1,5)
        col=R['alert'] if hot else (R['spot'] if k%3==0 else R['second'])
        L.rect(bx-9,by-9,bx+9,by+9,outline=col,w=2); L.circle(bx,by,3,fill=col)
        if hot or k%2==0:
            L.line([(bx+14,by-14),(bx+60,by-60),(bx+150,by-60)],sc(col,.8),1)
            L.text((bx+66,by-84),f"T-{k+1:02d}  {int(rr*3.7):04d}M",col,20,hot)
    # HUD
    hud=[("RNG","4800"),("BRG","087"),("SYNC","87.3%"),("MODE","STANDBY")]
    for k,(a,b) in enumerate(hud):
        L.text((90,110+k*54),a,sc(R['main'],.9),22); L.text((260,110+k*54),b,R['text'],30,True)
    L.poly(chamfer(60,70,420,260,24,True,True),outline=sc(R['main'],.7),w=2)
    c=L.done(); sw=Sw.done()
    return compose(base_bg(R,(cx/W,cy/H),.2),ImageChops.screen(c,sw),glow_src=L.main_small)

# ---------- 3 data panels ----------
def hexdump(L,x,y,rows,col,rnd,cw=20):
    for r in range(rows):
        addr=0xA400+r*16+rnd.randrange(0,2)*0x1000
        bs=" ".join(f"{rnd.randrange(256):02X}" for _ in range(8))
        L.text((x,y+r*28),f"{addr:06X}  {bs}",sc(col,.85 if r%5 else 1.2),19)
def bars(L,x,y,w,n,R,rnd,labels):
    for k in range(n):
        v=rnd.uniform(.25,1); yy=y+k*44
        L.text((x,yy),labels[k%len(labels)],sc(R['text'],.7),19)
        L.rect(x+130,yy+2,x+w,yy+22,outline=sc(R['main'],.7),w=1)
        col=R['alert'] if v>.9 else (R['spot'] if v>.75 else R['second'])
        L.rect(x+133,yy+5,x+133+(w-136)*v,yy+19,fill=sc(col,.75))
        L.text((x+w+14,yy),f"{v*100:5.1f}",sc(col,.95),19,True)
def wave(L,x,y,w,h,R,rnd,col):
    for k in range(0,w,40): L.line([(x+k,y),(x+k,y+h)],sc(R['main'],.22),1)
    for k in range(0,h,40): L.line([(x,y+k),(x+w,y+k)],sc(R['main'],.22),1)
    ph=[rnd.uniform(0,6) for _ in range(3)]; am=[rnd.uniform(.12,.3) for _ in range(3)]
    pts=[(x+i,y+h/2+h*sum(am[j]*math.sin(i/(60+j*37)+ph[j]) for j in range(3))*(0.6+0.4*math.sin(i/230))) for i in range(0,w,3)]
    L.line(pts,col,3)
    pts2=[(x+i,y+h/2+h*.7*sum(am[j]*math.sin(i/(40+j*29)+ph[j]*2) for j in range(3))*.5) for i in range(0,w,3)]
    L.line(pts2,sc(R['main'],.7),2)
def panel(L,x,y,w,h,title,R,tag=""):
    L.poly(chamfer(x,y,w,h,22,True,True),outline=sc(R['main'],.75),w=2)
    L.rect(x+34,y-2,x+34+len(title)*14+26,y+8,fill=R['main'])
    L.text((x+34,y+22),title,R['text'],21,True)
    if tag: L.text((x+w-20,y+22),tag,sc(R['second'],.95),19,True,"ra")
def datapanels(R,seed):
    rnd=random.Random(seed); L=Layer()
    m=84; gx=36
    # left column
    panel(L,m,m,560,520,"MEM DUMP",R,"BANK 3"); hexdump(L,m+34,m+80,15,R['main'],rnd)
    panel(L,m,m+560,560,520,"HEX TRACE",R,"RX"); hexdump(L,m+34,m+640,15,R['second'],rnd)
    panel(L,m,m+1120,560,420,"LINK STATUS",R,"4/4")
    for k,(a,b,col) in enumerate([("UPLINK-A","ACTIVE",R['second']),("UPLINK-B","ACTIVE",R['second']),("RELAY-C","STANDBY",R['spot']),("RELAY-D","OFFLINE",R['alert']),("ARRAY","NOMINAL",R['second'])]):
        L.text((m+34,m+1190+k*58),a,sc(R['text'],.8),24); L.text((m+520,m+1190+k*58),b,col,24,True,"ra")
    # centre
    cx0=m+560+gx; cw=1100
    panel(L,cx0,m,cw,640,"SYNC // PRIMARY",R,"87.3%")
    L.text((cx0+44,m+90),"87.3",R['text'],190,True); L.text((cx0+470,m+210),"% SYNC RATIO",sc(R['main'],1.0),34,True)
    L.text((cx0+44,m+330),"HARMONICS  STABLE   DRIFT  +0.04   LOCK  GREEN",sc(R['text'],.7),24)
    wave(L,cx0+44,m+390,cw-88,200,R,rnd,R['second'])
    panel(L,cx0,m+680,cw,420,"WAVEFORM B",R,"CH-02")
    wave(L,cx0+44,m+750,cw-88,290,R,rnd,R['spot'])
    panel(L,cx0,m+1140,cw,400,"EVENT LOG",R,"LIVE")
    ev=["00:41:07  SYNC ADJUST  OK","00:41:12  FIELD CHECK  PASS","00:41:19  RELAY-C  STANDBY","00:41:26  THERMAL  NOMINAL","00:41:31  AUTH TOKEN  VALID","00:41:38  STANDBY"]
    for k,t in enumerate(ev): L.text((cx0+44,m+1200+k*52),t,sc(R['text'],.85 if k<5 else 1.2),23,k==5)
    # right
    rx=cx0+cw+gx; rw=W-m-rx
    panel(L,rx,m,rw,700,"CHANNEL LOAD",R,"AUTO")
    bars(L,rx+34,m+90,rw-190,12,R,rnd,["CH-01","CH-02","CH-03","CH-04","CH-05","CH-06"])
    panel(L,rx,m+740,rw,380,"THERMAL",R,"C")
    for k in range(6):
        v=rnd.uniform(30,78); L.text((rx+34,m+810+k*46),f"ZONE {k+1}",sc(R['text'],.75),21); L.text((rx+rw-30,m+810+k*46),f"{v:4.1f}",R['spot'] if v>68 else R['second'],21,True,"ra")
    panel(L,rx,m+1160,rw,380,"STANDBY",R,"READY")
    L.text((rx+34,m+1240),"STANDBY",R['text'],72,True); L.text((rx+34,m+1340),"AWAITING OPERATOR INPUT",sc(R['main'],1.0),22)
    for k in range(18): L.rect(rx+34+k*24,m+1410,rx+34+k*24+16,m+1440,fill=sc(R['second'] if k<13 else R['main'],.7))
    c=L.done()
    dim=Layer(); 
    for y in range(0,H,6): dim.line([(0,y),(W,y)],(7,6,9),1)   # faint scanlines
    return compose(base_bg(R,(.5,.5),.1),c,glow_src=L.main_small,glows=((2,.8),(8,1.5),(24,2.2)),vig=.6)

# ---------- 4 armour plates + hazard ----------
def armour(R,seed):
    rnd=random.Random(seed); B=Layer(R['bg']); L=Layer()
    sl=[]
    ang=math.radians(-28); 
    def band(x0,x1,y0,y1,shade,edge):
        pts=[(x0,y0),(x1,y0+ (x1-x0)*math.tan(ang)*-0.0),(x1,y1),(x0,y1)]
    # big skewed slabs
    slabs=[
     [(-100,300),(1500,-60),(1500,420),(-100,860)],
     [(1500,-60),(3000,-60),(3000,520),(1500,420)],
     [(-100,860),(1500,420),(1700,1180),(-100,1500)],
     [(1500,420),(3000,520),(3000,1200),(1700,1180)],
     [(-100,1500),(1700,1180),(2200,1700),(-100,1900)],
     [(1700,1180),(3000,1200),(3000,1900),(2200,1700)],
    ]
    for n,p in enumerate(slabs):
        t=0.05+0.05*((n*7)%5)/4+rnd.uniform(0,.03)
        B.poly(p,fill=mix(sc(R['bg'],1.0),R['main'],t))
        # lit edge top, shadow on bottom
        L.line([p[0],p[1]],sc(R['main'],.55 if n%2 else .8),3)
        L.line([p[3],p[2]],sc(R['bg'],.0) if False else sc(R['main'],.18),2)
        # inset seam
        q=[(p[0][0]+60,p[0][1]+70),(p[1][0]-60,p[1][1]+70),(p[2][0]-60,p[2][1]-70),(p[3][0]+60,p[3][1]-70)]
        L.poly(q,outline=sc(R['main'],.30),w=2)
        for (rx,ry) in q:
            L.circle(rx+(18 if rx<p[1][0]-100 else -18),ry+(14 if ry<p[3][1]-100 else -14),5,outline=sc(R['main'],.5),w=2)
        mx=(p[0][0]+p[2][0])/2; my=(p[0][1]+p[2][1])/2
        L.text((mx-90,min(my,1450)-12),f"PLATE {n+1:02d}-{'ABCDEF'[n]}",sc(R['text'],.34),26,True)
    # a few neon accent seams
    for (a,b) in [((-100,300),(1500,-60)),((1700,1180),(3000,1200))]:
        L.line([a,b],R['second'],3)
    L.line([(1500,420),(1700,1180)],R['main'],3)
    L.line([(1500,-60),(1500,420)],R['spot'],3)
    # hazard band, bottom
    y0,y1=1590,1668
    B.rect(0,y0,W,y1,fill=sc(R['bg'],.6))
    for x in range(-200,W,96):
        B.poly([(x,y1),(x+48,y1),(x+48+(y1-y0),y0),(x+(y1-y0),y0)],fill=sc(R['warn'] if True else R['main'],.62))
    L.line([(0,y0),(W,y0)],sc(R['warn'],.9),2); L.line([(0,y1),(W,y1)],sc(R['warn'],.9),2)
    L.text((90,y0-52),"HAZARD  //  SECTOR 04  //  AUTHORISED PERSONNEL ONLY",sc(R['warn'],.95),26,True)
    L.text((W-90,y0-52),"BAY 12-C",sc(R['text'],.6),26,True,"ra")
    # warning triangle
    tx,ty=2520,230
    L.poly([(tx,ty-90),(tx+104,ty+90),(tx-104,ty+90)],outline=R['warn'],w=4); L.rect(tx-5,ty-34,tx+5,ty+28,fill=R['warn']); L.rect(tx-6,ty+44,tx+6,ty+58,fill=R['warn'])
    c=L.done(); return compose(B.done(),c,glow_src=L.main_small,glows=((2,.7),(10,1.4),(30,2.0)),vig=.5)

# ---------- 5 circuit traces + chip ----------
def circuit(R,seed):
    rnd=random.Random(seed); L=Layer(); G=Layer()
    cx,cy=W*.64,H*.5
    # concentric hexagons
    for k,r in enumerate((120,230,350,490,650)):
        pts=[(cx+r*math.cos(math.radians(60*i+30)),cy+r*math.sin(math.radians(60*i+30))) for i in range(6)]
        L.poly(pts,outline=mix(sc(R['main'],.4),R['main'],k/5),w=3 if k in (1,3) else 2)
        if k==2:
            for i in range(6): 
                a=math.radians(60*i+30); L.line([(cx+r*math.cos(a),cy+r*math.sin(a)),(cx+(r+250)*math.cos(a),cy+(r+250)*math.sin(a))],R['main'],2)
    pts=[(cx+80*math.cos(math.radians(60*i+30)),cy+80*math.sin(math.radians(60*i+30))) for i in range(6)]
    G.poly(pts,fill=sc(R['second'],.9)); L.poly(pts,outline=R['text'],w=3)
    L.text((cx,cy),"CORE",R['bg'],26,True,"mm")
    # traces
    dirs=[(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    for n in range(46):
        side=rnd.choice("LRTB")
        if side=="L": x,y,d=-20,rnd.uniform(60,H-60),(1,0)
        elif side=="R": x,y,d=W+20,rnd.uniform(60,H-60),(-1,0)
        elif side=="T": x,y,d=rnd.uniform(60,W-60),-20,(0,1)
        else: x,y,d=rnd.uniform(60,W-60),H+20,(0,-1)
        pts=[(x,y)]
        seglen=rnd.randrange(160,460)
        for s in range(rnd.randrange(4,9)):
            x+=d[0]*seglen*(0.7 if d[0] and d[1] else 1); y+=d[1]*seglen*(0.7 if d[0] and d[1] else 1)
            pts.append((x,y))
            # turn 45 degrees
            i=dirs.index(d); i=(i+rnd.choice((-1,1))*(4 if False else 1))%8
            ok=[dd for dd in dirs if dd[0]*d[0]+dd[1]*d[1]>=0]  # no reversal
            d=rnd.choice(ok); seglen=rnd.randrange(120,420)
            if math.hypot(x-cx,y-cy)<700: break
        hi=rnd.random()
        col=R['second'] if hi<.18 else (R['spot'] if hi<.24 else sc(R['main'],.35+.5*rnd.random()))
        w=3 if hi<.24 else 2
        (G if hi<.24 else L).line(pts,col,w)
        ex,ey=pts[-1]; L.circle(ex,ey,9,outline=col,w=3)
        if hi<.24: L.circle(ex,ey,4,fill=col); L.text((ex+16,ey-24),f"BUS-{n:02X}",sc(col,.9),19,True)
        for (px,py) in pts[1:-1]:
            if rnd.random()<.5: L.circle(px,py,4,fill=sc(col,.8))
    L.text((90,H-110),"BUS ARBITER  //  14 LANES  //  LOAD 61%",sc(R['text'],.55),26,True)
    L.text((90,H-70),"CORE CLOCK 2.40 GHZ  TEMP 41 C",sc(R['main'],.9),21)
    c=L.done(); g=G.done()
    return compose(base_bg(R,(cx/W,cy/H),.2),ImageChops.screen(c,g),glow_src=ImageChops.screen(g,sc_img(L.main_small)),vig=.55)
def sc_img(im): return im.point(lambda v:int(v*.5))

GENS=[("1-hex-field",hexfield),("2-radar-rings",radar),("3-data-panels",datapanels),("4-armour-plates",armour),("5-circuit-core",circuit)]
def save(im,path,maxkb=555):
    for q in (92,90,88,86,84,82,80,78,75,72,68,64):
        im.save(path,"JPEG",quality=q,optimize=True,progressive=True,subsampling=0 if q>=86 else 2)
        if os.path.getsize(path)<=maxkb*1024: return q
    return -1
if __name__=="__main__":
    variant=sys.argv[1]; outdir=sys.argv[2]; only=sys.argv[3:] 
    P=BASE if variant=="base" else RED
    R=roles(P,variant); os.makedirs(outdir,exist_ok=True)
    for i,(name,fn) in enumerate(GENS):
        if only and name.split('-')[0] not in only: continue
        im=fn(R,seed=11+i*7+(100 if variant!="base" else 0))
        q=save(im,os.path.join(outdir,name+".jpg"))
        print(name,im.size,q,os.path.getsize(os.path.join(outdir,name+".jpg"))//1024,"KB",flush=True)
