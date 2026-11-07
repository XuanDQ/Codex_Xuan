import json, math, os, subprocess, time
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont

R=Path('/workspace/esp32-course'); O=R/'output'; TMP=R/'tools/render'; TMP.mkdir(exist_ok=True)
W,H,FPS=1280,720,15
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
BOLD='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
BG='#101c32'; WHITE='#f1f6ff'; MUTED='#b5c5dc'; AQUA='#65eadb'; ORANGE='#ffca7a'; BLUE='#8fb7ff'
@lru_cache(None)
def font(n,b=False):return ImageFont.truetype(BOLD if b else FONT,n)
def text(d,xy,t,n=30,c=WHITE,b=False): d.text(xy,t,font=font(n,b),fill=c)
def wrap(t,n,width):
    lines=['']
    for c in t:
        if font(n).getlength(lines[-1]+c)>width:lines.append(c)
        else:lines[-1]+=c
    return lines
def para(d,xy,t,n=28,width=1100,c=WHITE,gap=8,b=False):
    x,y=xy
    for line in wrap(t,n,width):text(d,(x,y),line,n,c,b);y+=n+gap
    return y
def box(d,xy,fill='#1c2d48',outline=None,r=20,width=2):d.rounded_rectangle(xy,radius=r,fill=fill,outline=outline,width=width)
def mascot(d,t):
    # Original vector robot: no third-party character or copied identity.
    x,y=1164,38
    d.line((x+31,y-8,x+31,y),fill=AQUA,width=3);d.ellipse((x+26,y-15,x+36,y-5),fill=ORANGE)
    box(d,(x,y,x+65,y+45),AQUA,r=15);box(d,(x+7,y+8,x+58,y+34),BG,r=10)
    for dx in [20,44]:d.ellipse((x+dx-3,y+16,x+dx+3,y+23),fill=WHITE)
    d.arc((x+23,y+23,x+42,y+34),0,180,fill=WHITE,width=2)
    d.line((x+68,y+29,x+78,y+14+int(5*math.sin(t*3))),fill=AQUA,width=5)
def base(s):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    for x in range(20,W,40):
        for y in range(20,590,40):d.ellipse((x,y,x+1,y+1),fill='#27344b')
    d.rectangle((0,0,W,7),fill=AQUA)
    text(d,(48,23),'蓝牙小实验室  /  ESP32 蓝牙通信基础 2',23,AQUA,True)
    text(d,(48,66),s['title'],42,WHITE,True)
    box(d,(50,554,1228,595),'#1b2d47',r=12)
    text(d,(67,561),f"CH {s['ch']:02d}  ·  "+['任务与路线','双向转发代码','手机接收逻辑','消息边界','实验与排错','通关回顾'][s['ch']-1],21,MUTED)
    text(d,(1000,561),f"{s['index']+1:02d} / 40",21,AQUA)
    return im
def arrow(d,x1,x2,y,color=AQUA):
    d.line((x1,y,x2,y),fill=color,width=5)
    sign=1 if x2>x1 else -1
    d.polygon([(x2,y),(x2-sign*12,y-9),(x2-sign*12,y+9)],fill=color)
def content(s,t,d,im):
    kind=s['kind']; lines=s['lines']; dur=s['duration']
    cue=0
    for i,c in enumerate(s['cues']):
        if t>=c['start']:cue=i
    if kind=='flow':
        xs=[165,630,1100]; labels=['手机','ESP32','电脑']
        for x,lab in zip(xs,labels):
            box(d,(x-95,165,x+95,290),'#213953',AQUA,r=22)
            if lab=='手机':
                box(d,(x-28,178,x+28,237),BG,WHITE,r=7);d.line((x-13,228,x+13,228),fill=AQUA,width=3)
            elif lab=='ESP32':
                box(d,(x-30,184,x+30,232),BG,AQUA,r=5)
                for q in range(6):
                    d.line((x-40,188+q*8,x-30,188+q*8),fill=ORANGE,width=3)
                    d.line((x+30,188+q*8,x+40,188+q*8),fill=ORANGE,width=3)
            else:
                box(d,(x-42,179,x+42,227),BG,WHITE,r=5);d.line((x,228,x,240),fill=WHITE,width=3)
            text(d,(x-font(26,True).getlength(lab)/2,246),lab,26,WHITE,True)
        for a,b,l in [(270,520,'蓝牙 SPP'),(740,990,'USB 串口')]:
            arrow(d,a,b,203);arrow(d,b,a,258,ORANGE);text(d,((a+b)/2-64,150),l,20,MUTED)
            u=(t*0.55)%1
            for y,frac,color in [(203,u,AQUA),(258,1-u,ORANGE)]:
                x=a+(b-a)*frac;box(d,(x-17,y-11,x+17,y+11),color,r=7)
        for j,l in enumerate(lines):
            box(d,(75,320+j*67,1200,375+j*67),'#20324c',r=13)
            text(d,(96,329+j*67),l,27,AQUA if cue%3==j else WHITE)
    elif kind=='buffer':
        for j,l in enumerate(lines):para(d,(70,155+j*65),l,29,1130,AQUA if j==cue%len(lines) else WHITE)
        text(d,(80,381),'接收缓存',24,MUTED)
        for j in range(8):
            active=j<int((t*1.6)%9)
            box(d,(270+j*108,370,358+j*108,448),AQUA if active else '#233753',r=12)
            text(d,(289+j*108,387),['E4','BD','A0','E5','A5','BD','0A','…'][j],27,BG if active else MUTED)
        text(d,(270,474),'示意：“你好”占 6 字节，0A 是换行。',26,ORANGE)
    elif kind=='code':
        box(d,(62,146,1218,448),'#091321',r=18)
        code=s['code']
        lineh=min(38,274//max(1,len(code)))
        # Match each narrated sentence to the code operation being discussed.
        step_map={7:[1,1,4,1,4,1,6],8:[0,1,3,3,0,0,0],9:[0,1,4,4,1,4,4],26:[0,1,1,2,4,3]}
        sequence=step_map.get(s['index'])
        active=(sequence[min(cue,len(sequence)-1)] if sequence else min(len(code)-1,int(t/max(1,dur)*len(code))))
        for j,line in enumerate(code):
            y=160+j*lineh
            if j==active:box(d,(74,y-1,1204,y+lineh-1),'#284e63',r=5)
            text(d,(88,y),f'{j+1:02d}',22,MUTED);text(d,(145,y),line,26,AQUA if j==active else WHITE)
        para(d,(77,469),lines[cue%len(lines)],27,1120,ORANGE)
    elif kind=='image':
        y=160
        for j,l in enumerate(lines):
            y=para(d,(60,y),l,26,378,AQUA if j==cue%len(lines) else WHITE,gap=8)+24
        box(d,(463,148,1226,533),'#ecf1f5',r=16)
        asset=Image.open(R/'assets'/s['asset']).convert('RGBA')
        # Fit original teaching screenshot without distorting its aspect ratio.
        bg=Image.new('RGBA',asset.size,'white');bg.alpha_composite(asset);asset=bg.convert('RGB')
        asset.thumbnail((735,350)); im.paste(asset,(844-asset.width//2,340-asset.height//2))
        d=ImageDraw.Draw(im);text(d,(480,507),'原课件图例 · 配合左侧步骤阅读',17,'#394c65')
        # Moving focus strip ties emphasis to the current narrated step.
        yy=174+(cue%3)*100;d.line((456,yy,456,yy+72),fill=AQUA,width=5)
    elif kind=='question':
        box(d,(67,154,1216,480),'#25314c',ORANGE,r=24)
        text(d,(94,166),'想一想  ·  先说预测，再说理由',27,ORANGE,True)
        y=233
        for l in lines:y=para(d,(106,y),l,30,1000,WHITE)+19
        remaining=dur-t
        if remaining<=s['pause']:
            num=max(1,math.ceil(remaining));x,y=1120,467
            d.ellipse((x-43,y-43,x+43,y+43),fill=ORANGE)
            text(d,(x-13,y-33),str(num),43,BG,True)
            text(d,(91,491),'可以暂停视频，和同桌交流；下一页揭晓答案。',24,AQUA)
    else:
        y=156
        for j,l in enumerate(lines):
            box(d,(65,y,1215,y+104),'#213650',AQUA if cue%len(lines)==j else None,r=19)
            box(d,(85,y+22,139,y+76),AQUA if kind!='practice' else ORANGE,r=15)
            text(d,(102,y+25),str(j+1),29,BG,True)
            para(d,(162,y+27),l,29,1000,WHITE)
            y+=120
        if kind=='practice':text(d,(83,516),'暂停动手  /  完成后再继续播放',23,ORANGE)
    mascot(d,t)

def subtitle_frames(s):
    # Each synthesized sentence owns its exact audio interval. Split long sentences
    # into short visual phrases so subtitles stay large and track speech.
    cues=[]
    for c in s['cues']:
        pieces=[x for x in __import__('re').split(r'(?<=[，；：])',c['text']) if x]
        groups=[];current=''
        for p in pieces:
            if font(30).getlength(current+p)>1120 and current:groups.append(current);current=p
            else:current+=p
        if current:groups.append(current)
        weights=[len(x) for x in groups];start=c['start']
        for txt,w in zip(groups,weights):
            end=start+(c['end']-c['start'])*w/sum(weights)
            cues.append((start,end,txt));start=end
    return cues

def render_scene(s):
    path=TMP/f"scene_{s['index']:02d}.mp4"
    if path.exists() and path.stat().st_size>10000:return
    poster=base(s); cues=subtitle_frames(s); total=math.ceil(s['duration']*FPS)
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
         '-an','-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-threads','1',str(path)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    # Cache text and content once per cue/code-step; only animate small overlays per frame.
    cached_key=None;cached=None
    for frame in range(total):
        t=frame/FPS
        ci=next((i for i,c in enumerate(cues) if c[0]<=t<c[1]),-1)
        key=(ci,int(t/max(1,s['duration'])*len(s.get('code') or [0])),math.ceil(s['duration']-t) if s['kind']=='question' else 0)
        if key!=cached_key:
            cached=poster.copy();d=ImageDraw.Draw(cached);content(s,t,d,cached)
            box(d,(36,612,1244,704),'#070e1b',r=13)
            if ci>=0:
                ls=wrap(cues[ci][2],30,1150)
                for j,line in enumerate(ls[:2]):text(d,((W-font(30).getlength(line))/2,621+j*38),line,30,WHITE)
            elif s['pause'] and t>s['duration']-s['pause']:
                text(d,(300,631),'思考中……下一页给出答案和原因',30,ORANGE)
            cached_key=key
        im=cached.copy();d=ImageDraw.Draw(im)
        # Small moving packet timeline keeps the changing signal visible throughout.
        d.line((57,600,1226,600),fill='#36506a',width=3)
        x=57+1169*(t/s['duration']);d.ellipse((x-5,595,x+5,605),fill=AQUA)
        if s['kind']=='flow':
            for a,b in [(270,520),(740,990)]:
                u=(t*.5)%1
                for y,frac,color in [(203,u,AQUA),(258,1-u,ORANGE)]:
                    xx=a+(b-a)*frac;box(d,(xx-16,y-10,xx+16,y+10),color,r=6)
        if s['kind']=='buffer':
            j=int(t*2)%8;x=270+j*108
            d.rounded_rectangle((x-3,367,x+91,451),radius=13,outline=ORANGE,width=4)
        p.stdin.write(im.tobytes())
        if frame==total//2:
            im.save(TMP/f"poster_{s['index']:02d}.jpg",quality=91)
    p.stdin.close()
    if p.wait()!=0:raise RuntimeError('ffmpeg scene failed')
    print('rendered',s['index']+1,'duration',round(s['duration'],1),flush=True)

if __name__=='__main__':
    for index in range(40):
        while True:
            try:timeline=json.loads((O/'timeline.json').read_text())
            except (FileNotFoundError,json.JSONDecodeError):timeline=[]
            if len(timeline)>index:break
            time.sleep(2)
        render_scene(timeline[index])
