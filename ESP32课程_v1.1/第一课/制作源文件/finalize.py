import json,math,re,shutil,subprocess,zipfile,time
from pathlib import Path
import numpy as np
import soundfile as sf
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pptx import Presentation
from pptx.util import Inches,Pt as PptPt
from pptx.dml.color import RGBColor
from render import subtitle_frames

R=Path('/workspace/esp32-lesson1');O=R/'output';T=R/'tools';FPS=15
def cmd(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def stamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
def mark(t):return f'{int(t)//60:02d}:{int(t)%60:02d}'
def make_doc(title,sections,path):
    doc=Document();style=doc.styles['Normal'];style.font.name='Microsoft YaHei';style.font.size=Pt(11)
    style.element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
    doc.add_heading(title,0)
    for head,paras in sections:
        doc.add_heading(head,1)
        for p in paras:doc.add_paragraph(p)
    doc.save(path)
    (path.with_suffix('.md')).write_text('# '+title+'\n\n'+'\n\n'.join('## '+h+'\n\n'+'\n\n'.join(p) for h,p in sections))

def main():
    timeline=json.loads((O/'timeline.json').read_text());assert len(timeline)==40
    for i,s in enumerate(timeline):assert (T/'render'/f'scene_{i:02d}.mp4').exists()
    sr=24000;offset=0;samples=[];cues=[]
    for s in timeline:
        s['start']=offset;s['video_duration']=math.ceil(s['duration']*FPS)/FPS
        audio,rate=sf.read(O/'voice_parts'/f"scene_{s['index']:02d}.wav",dtype='float32');assert rate==sr
        n=round(s['video_duration']*sr)
        audio=np.pad(audio,(0,max(0,n-len(audio))))[:n];samples.append(audio)
        for a,b,t in subtitle_frames(s):cues.append((offset+a,offset+b,t))
        offset+=s['video_duration']
    (O/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
    sf.write(T/'narration_raw.wav',np.concatenate(samples),sr)
    srt='\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{t}' for i,(a,b,t) in enumerate(cues))+'\n'
    (O/'第一课_同步字幕.srt').write_text(srt)
    # A gentle, original pentatonic underscore. Keep it below speech; quieter on code pages.
    n=round(offset*sr);bgm=np.zeros(n,dtype=np.float32)
    for k,start in enumerate(np.arange(0,offset,1.6)):
        note=[261.626,329.628,391.995,440,391.995,329.628][k%6]
        tt=np.arange(int(sr*1.15))/sr;env=np.minimum(tt/.035,1)*np.exp(-tt*4)
        tone=(np.sin(2*np.pi*note*tt)+.18*np.sin(2*np.pi*note*2*tt))*env*.0035
        a=int(start*sr);b=min(n,a+len(tt));bgm[a:b]+=tone[:b-a]
    for s in timeline:
        a=round(s['start']*sr);b=round((s['start']+s['video_duration'])*sr)
        if s['kind'] in ['code','image']:bgm[a:b]*=.4
        if s['pause']:
            for j in range(s['pause']):
                a=round((s['start']+s['duration']-s['pause']+j)*sr)
                tt=np.arange(int(sr*.09))/sr;tone=.009*np.sin(2*np.pi*(660 if j<5 else 880)*tt)*np.exp(-tt*30)
                b=min(n,a+len(tt));bgm[a:b]+=tone[:b-a]
    sf.write(T/'bgm.wav',bgm,sr)
    voicefx='asetrate=24840,aresample=24000,atempo=0.9661835749,highpass=f=85,lowpass=f=10500,loudnorm=I=-17:TP=-2:LRA=8'
    cmd(['ffmpeg','-v','error','-y','-i',str(T/'narration_raw.wav'),'-af',voicefx,'-ar','24000',str(T/'voice.wav')])
    cmd(['ffmpeg','-v','error','-y','-i',str(T/'voice.wav'),'-c:a','libmp3lame','-b:a','128k',str(O/'第一课_纯人声讲解.mp3')])
    cmd(['ffmpeg','-v','error','-y','-i',str(T/'voice.wav'),'-i',str(T/'bgm.wav'),'-filter_complex','[0:a][1:a]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]','-map','[a]','-ar','24000',str(T/'mix.wav')])
    # Six small voice files are convenient for replaying a single concept or activity.
    pack=O/'语音包';pack.mkdir(exist_ok=True)
    chapter_names=['任务与无线基础','发现与连接','ESP32接收程序','手机APP搭建','实验与排错','通关回顾']
    for ch,name in enumerate(chapter_names,1):
        ss=[s for s in timeline if s['ch']==ch];a=ss[0]['start'];b=ss[-1]['start']+ss[-1]['video_duration']
        cmd(['ffmpeg','-v','error','-y','-ss',str(a),'-i',str(T/'voice.wav'),'-t',str(b-a),'-c:a','libmp3lame','-b:a','128k',str(pack/f'{ch:02d}_{name}.mp3')])
    (T/'concat.txt').write_text('\n'.join(f"file '{T}/render/scene_{i:02d}.mp4'" for i in range(40)))
    cmd(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(T/'concat.txt'),'-i',str(T/'mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k','-t',str(offset),'-movflags','+faststart',str(O/'第一课_蓝牙文字传输_互动视频.mp4')])
    print('audio and video complete',offset,flush=True)
    # Editable companion deck: text/code remain editable; notes retain full narration.
    prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
    def textbox(sl,x,y,w,h,txt,size=28,color='F1F6FF'):
        sh=sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h));tf=sh.text_frame;tf.word_wrap=True
        for i,line in enumerate(txt.split('\n')):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.size=PptPt(size);p.font.name='Microsoft YaHei';p.font.color.rgb=RGBColor.from_string(color)
        return sh
    for s in timeline:
        sl=prs.slides.add_slide(prs.slide_layouts[6]);sl.background.fill.solid();sl.background.fill.fore_color.rgb=RGBColor(16,28,50)
        textbox(sl,.5,.2,12,.4,f"蓝牙小实验室  /  CH{s['ch']:02d}  /  {mark(s['start'])}",16,'65EADB')
        textbox(sl,.5,.8,12,1,s['title'],32)
        if s['kind']=='image':
            textbox(sl,.6,2,4,4.3,'\n\n'.join(s['lines']),23)
            from PIL import Image
            asset=R/'assets'/s['asset'];im=Image.open(asset);ratio=im.height/im.width;w=min(7.5,4.7/ratio)
            sl.shapes.add_picture(str(asset), Inches(5), Inches(2), width=Inches(w))
        elif s.get('code'):
            textbox(sl,.7,1.95,12,3.7,'\n'.join(s['code']),23,'65EADB')
            textbox(sl,.7,5.75,12,1,' · '.join(s['lines']),19,'FFCA7A')
        else:textbox(sl,.8,2.1,12,4,'\n\n'.join(s['lines']),28)
        textbox(sl,.6,7,12,.3,f"{s['index']+1:02d}/40  ·  思考题后有答案与原因  ·  实操处可暂停",12,'B5C5DC')
        sl.notes_slide.notes_text_frame.text=s['narr']+('\n【思考留白：6秒；答案在下一页】' if s['pause'] else '')
    prs.save(O/'第一课_互动讲解配套.pptx')
    script_sections=[]
    for s in timeline:
        script_sections.append((f"{s['index']+1:02d} · {mark(s['start'])} · {s['title']}",[s['narr'], '画面：'+'；'.join(s['lines'])]+(['思考留白6秒；下一场景给出答案与原因。'] if s['pause'] else [])))
    make_doc('第一课：蓝牙文字传输逐场景讲稿',script_sections,O/'第一课_讲稿与分镜.docx')
    from docs import write_docs
    write_docs(timeline,chapter_names,offset,make_doc,mark)

if __name__=='__main__':main()
