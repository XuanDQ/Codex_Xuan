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

R=Path('/workspace/esp32-course');O=R/'output';T=R/'tools';FPS=15
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
    (O/'第二课_同步字幕.srt').write_text(srt)
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
    cmd(['ffmpeg','-v','error','-y','-i',str(T/'voice.wav'),'-c:a','libmp3lame','-b:a','128k',str(O/'第二课_纯人声讲解.mp3')])
    cmd(['ffmpeg','-v','error','-y','-i',str(T/'voice.wav'),'-i',str(T/'bgm.wav'),'-filter_complex','[0:a][1:a]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]','-map','[a]','-ar','24000',str(T/'mix.wav')])
    # Six small voice files are convenient for replaying a single concept or activity.
    pack=O/'语音包';pack.mkdir(exist_ok=True)
    chapter_names=['任务与路线','双向转发代码','手机接收逻辑','消息边界','实验与排错','通关回顾']
    for ch,name in enumerate(chapter_names,1):
        ss=[s for s in timeline if s['ch']==ch];a=ss[0]['start'];b=ss[-1]['start']+ss[-1]['video_duration']
        cmd(['ffmpeg','-v','error','-y','-ss',str(a),'-i',str(T/'voice.wav'),'-t',str(b-a),'-c:a','libmp3lame','-b:a','128k',str(pack/f'{ch:02d}_{name}.mp3')])
    (T/'concat.txt').write_text('\n'.join(f"file '{T}/render/scene_{i:02d}.mp4'" for i in range(40)))
    cmd(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(T/'concat.txt'),'-i',str(T/'mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k','-t',str(offset),'-movflags','+faststart',str(O/'第二课_蓝牙聊天室_互动视频.mp4')])
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
    prs.save(O/'第二课_互动讲解配套.pptx')
    script_sections=[]
    for s in timeline:
        script_sections.append((f"{s['index']+1:02d} · {mark(s['start'])} · {s['title']}",[s['narr'], '画面：'+'；'.join(s['lines'])]+(['思考留白6秒；下一场景给出答案与原因。'] if s['pause'] else [])))
    make_doc('第二课：蓝牙聊天室逐场景讲稿',script_sections,O/'第二课_讲稿与分镜.docx')
    chapters=[]
    for ch,name in enumerate(chapter_names,1):
        ss=[s for s in timeline if s['ch']==ch];chapters.append(f"{mark(ss[0]['start'])}  {name}")
    teacher=[('课堂安排',[f'本视频讲解时长{mark(offset)}；现场练习另计。建议以六个章节组织播放，动手站暂停，完成后再继续。']+chapters),
      ('课前准备',['硬件：支持经典蓝牙的原版ESP32、USB数据线、Android手机、电脑与驱动。软件：Arduino IDE及相应ESP32板包、课程使用的App Inventor类积木平台。','先用板包自带SerialToSerialBT示例核对环境；选择正确板型、端口并确认9600波特率。确定手机权限及配对可用，再让学生实验。PIN设置按当前板包官方示例，不直接复制原课件中BT.pinCode的写法。']),
      ('现场暂停点',[f"{mark(s['start'])}  {s['title']}："+'；'.join(s['lines']) for s in timeline if s['kind']=='practice']),
      ('思考题与答案',[f"{mark(s['start'])}  {s['title']}\n问题：{s['narr']}\n参考答案与原因：{timeline[i+1]['narr']}" for i,s in enumerate(timeline[:-1]) if s['kind']=='question']),
      ('实验验收',['手机→电脑、电脑→手机各发3条；核对中文、消息数量、前缀方向、历史保留和断开重连。基础版消息拆合现象应能解释；升级版按统一换行约定重新比较。','未做硬件实测：附带代码和动画是教学示例，需在机构现有板型/板包/手机环境预先验证。不要把本地动画等同于真实蓝牙连通。']),
      ('原课件覆盖与调整',['原第1—4页：视频场景1—6，回顾、任务、目标、设备边界。原第5—6页：场景5，聚焦本课SPP，纠正单向/双向分类及功耗过度概括。','原第7页：场景7—13，双向程序、对象、前缀、初始化、等待。原第8—14页：场景14—28，界面、连接、计时器、字节缓存、发送接收积木、可选消息分条。','原第15—16页：场景29—36，完整路线、安装、暂停练习、排错。原第17页：场景37—40，验收、问答回顾、延伸挑战。原第18页为空，不加入。原课件内嵌71秒手机操作视频单独保留，供教师补充演示。'])]
    make_doc('第二课：教师播放与现场答疑手册',teacher,O/'第二课_教师手册.docx')
    # Shared standard v1.1 is written by first-lesson production.
    (O/'先读我.md').write_text('# 第二课：ESP32蓝牙聊天室\n\n本次已修正英文技术缩写的配音读法，并按共同规范复核。第一课已收到可读取文件并同步制作，不再有文件读取阻碍。配套PPT、讲稿、教师手册、字幕与语音均在本包。\n讲解时长：'+mark(offset)+'。硬件实验仍需教师课前在机构设备上验证。\n')
    shutil.copy(R/'assets/media1.mp4',O/'原课件_内嵌实操演示.mp4')
    for name in ['synth.py','render.py','finalize_v11.py']:
        shutil.copy(T/name,O/'制作源文件'/name)
    shutil.copy(O/'timeline.json',O/'制作源文件/timeline.json')
    (O/'制作状态.json').write_text(json.dumps({'lesson2':'produced','duration_seconds':offset,'scene_count':40,'questions':7,'hardware_tested':False,'standard':'v1.1','pronunciation_updated':True},ensure_ascii=False,indent=2))
    print('updated second lesson complete',flush=True)

if __name__=='__main__':main()
