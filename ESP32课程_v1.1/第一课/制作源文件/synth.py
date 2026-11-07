import os, json, re, time
from pathlib import Path
import numpy as np
import soundfile as sf
import sherpa_onnx
from lesson import scenes,ROOT

M=Path('/workspace/esp32-course/tools/kokoro-multi-lang-v1_1')
config=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
 kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(model=str(M/'model.onnx'),voices=str(M/'voices.bin'),
 tokens=str(M/'tokens.txt'),lexicon=str(M/'lexicon-us-en.txt')+','+str(M/'lexicon-zh.txt'),
 data_dir=str(M/'espeak-ng-data'),dict_dir=str(M/'dict'),lang='zh'),num_threads=4),
 rule_fsts=','.join(str(M/n) for n in ['date-zh.fst','number-zh.fst','phone-zh.fst']),max_num_sentences=1)
tts=sherpa_onnx.OfflineTts(config)
print('tts loaded',tts.num_speakers,tts.sample_rate,flush=True)
out=ROOT/'output'; (out/'voice_parts').mkdir(exist_ok=True,parents=True)
replacements={'一斯批三十二':'ESP32','一斯批':'ESP','优艾斯比':'USB','比诶勒':'BLE','艾艾弗':'if','优梯艾弗八码':'UTF-8','西三':'C3','艾斯三':'S3'}
timeline=[]; total=0
for i,s in enumerate(scenes):
    for a,b in replacements.items(): s['narr']=s['narr'].replace(a,b)
    parts=[x for x in re.split(r'(?<=[。！？])',s['narr']) if x.strip()]
    chunks=[]; cues=[]; offset=0
    for j,text in enumerate(parts):
        path=out/'voice_parts'/f'{i:02d}_{j:02d}.wav'
        if path.exists(): samples,sr=sf.read(path,dtype='float32')
        else:
            spoken=text.replace('ESP32','伊艾斯皮三十二').replace('ESP','伊艾斯皮').replace('USB','优艾斯比').replace('C3','西三').replace('S3','艾斯三')
            spoken=spoken.replace('UTF-8','优梯艾弗八').replace('BLE','比艾勒').replace('SPP','艾斯皮皮').replace('APK','安装包').replace('APP','应用').replace('App Inventor','应用发明家').replace('readString()','读取字符串函数').replace('readString','读取字符串函数').replace('if','如果').replace('Serial','串口对象').replace('BT','比梯')
            speed=1.00 if s['kind']=='question' else (1.08 if s['kind'] in ['flow','practice'] else 1.06)
            audio=tts.generate(spoken,sid=0,speed=speed)
            samples=np.asarray(audio.samples); sr=audio.sample_rate
            sf.write(path,samples,sr)
        silence=np.zeros(int(sr*0.20),dtype=np.float32)
        chunks.extend([samples,silence]); duration=len(samples)/sr+0.20
        cues.append(dict(start=offset,end=offset+duration,text=text)); offset+=duration
    if s['pause']:
        chunks.append(np.zeros(int(sr*s['pause']),dtype=np.float32));offset+=s['pause']
    else:
        chunks.append(np.zeros(int(sr*0.5),dtype=np.float32));offset+=0.5
    sf.write(out/'voice_parts'/f'scene_{i:02d}.wav',np.concatenate(chunks),sr)
    timeline.append(dict(**s,index=i,start=total,duration=offset,cues=cues))
    total+=offset
    (out/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
    print(i+1,len(parts),round(offset,1),'total',round(total,1),flush=True)
print('done',total,flush=True)
