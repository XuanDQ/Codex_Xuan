import json,shutil
from pathlib import Path

def write_docs(timeline,chapter_names,offset,make_doc,mark):
    R=Path('/workspace/esp32-lesson1');O=R/'output';T=R/'tools'
    chapters=[]
    for ch,name in enumerate(chapter_names,1):
        ss=[s for s in timeline if s['ch']==ch];chapters.append(f"{mark(ss[0]['start'])}  {name}")
    teacher=[
      ('播放安排',[f'本视频讲解时长{mark(offset)}，学生动手时间另计。按六章播放，实操站暂停；老师主要解决设备与个别操作问题。']+chapters),
      ('课前准备',['支持经典蓝牙SPP的原版ESP32、可传数据的USB线、Arduino IDE和相应ESP32板包、Android手机及课堂采用的App Inventor类平台。ESP32-C3/S3和普通iPhone不能直接套用本课方案。','确认板型、驱动、端口、供电、手机权限与配对，串口波特率为9600。设备名应加组号。代码先参考当前板包自带BluetoothSerial示例。原稿BT.pinCode不能未经核对复制；本次基础示例不设置固定PIN。']),
      ('现场暂停与验收点',[f"{mark(s['start'])}  {s['title']}："+'；'.join(s['lines']) for s in timeline if s['kind']=='practice']),
      ('思考题、答案与原因',[f"{mark(s['start'])}  {s['title']}\n提问：{s['narr']}\n答案与原因：{timeline[i+1]['narr']}" for i,s in enumerate(timeline[:-1]) if s['kind']=='question']),
      ('定位问题的最短路线',['编译失败：先看第一条错误、板型和接口版本。找不到设备：检查板型是否支持经典蓝牙、程序是否运行、配对、手机权限和距离。','手机有本地记录但电脑没有：检查连接返回结果、蓝牙接收、串口打印和电脑监视器。电脑整体乱码：先核对波特率。仅中文异常：进一步查编码与数据完整性。','readString会等待超时；一次发送不等于一次完整读取。基础版合并或拆分现象不应隐瞒，可作为第二课消息边界的引入。不能以手机本地记录充当对方收到的证据。','本制作环境未接ESP32实体硬件，因此不声称硬件连通、板包编译或手机安装测试已通过。请机构教师在现有设备上课前验证。']),
      ('原课件覆盖与修订',['原第1—4页：场景1—4及开场目标，回顾串口、建立消息路线。原第5页：场景5—10，蓝牙、2.4GHz、跳频、经典蓝牙与BLE、设备边界。修正“本课是BLE”和跳频必然安全的表述，不把功耗、电池寿命、距离说成固定保证。','原第6—7页：场景11—15，重新绘制发现—配对—连接—传输—断开流程。区分已配对与应用当前连接，不保证总能自动重连。原动画改为清晰示意，不依赖内嵌视频。','原第8—9页：场景16—22，库、对象、begin、available、readString、串口显示，核对旧PIN接口和等待行为。','原第10—15页：场景23—32，界面、客户端、初始化、连接返回结果、发送判断、列表刷新、断开。原第16—18页：场景33—40，安装、实验、排错、验收、总结。原第19页为空，不加入。','附件的媒体关系中仍能看到旧视频引用，但本次只读取实际可用的静态内容，不需要老师再补视频。'])]
    make_doc('第一课：教师播放与现场答疑手册',teacher,O/'第一课_教师手册.docx')
    norms=[
      ('适用对象、时长与版本',['适用小学五年级至初二。用户确定：每节15—20分钟讲解，现场练习另计。视频负责讲解、提问、示范和答案，老师负责现场设备与个别问题。','v1.1：第一课已根据新上传的压缩版课件制作，沿用第二课已确定的风格，并将第一课技术核查结果补入标准；第二课按相同项目复核。两课的硬件实测均未在制作环境执行。']),
      ('固定教学结构',['任务情境 → 预测问题 → 六秒思考留白 → 明确答案 → 因果解释 → 下一知识点 → 可暂停实操 → 验收。每道思考题必须在后续给出答案和为什么；本次两课均安排7题，并在下一场景回应。','题目围绕实际现象和接下来的知识点，不靠无意义猜词。课堂交流可暂停延长；六秒是视频内基础留白，不是限制学生发言时间。','类比后紧跟真实技术概念：小桥对应转发，信箱对应接收缓存；不能用类比替代因果解释。技术深度包括数据路线、对象和API、判断条件、执行顺序、故障原因。']),
      ('声音与课堂节奏',['沿用轻快、偏可爱的中文通用合成女声，适度语速变化、停顿和轻微音高提亮；不冒充特定动漫角色。提问略慢、解释清晰、总结提振，避免夸张幼儿化。','使用同一Kokoro通用音色和后期声线处理。第一课按稿件长度微调语速，确保在15—20分钟内完成；不额外拖长静态页面凑时长。','原创背景音乐非常轻，代码和积木段进一步降低，倒计时仅简短提示音。交付完整纯人声MP3与6章语音，老师可自由选择是否播放音乐。']),
      ('画面与字幕',['1280×720、15帧/秒。每个知识点拆成独立场景，大字要点、逐句/短语字幕、可读代码和积木原图相互配合。字幕最多两行，避免遮挡关键内容。','第一课重绘单向消息路线、跳频示意、五阶段连接流程、缓存和代码高亮；第二课采用双向消息与缓存动画。运动方向必须与所讲路线一致，不能给第一课的单向程序画出已经实现的回程。','动画服务于理解。不得长时间把整页PPT当静态底图，也不堆无关装饰。思考题先不露答案，倒计时后切换答案页，实操页明确提示暂停。','字幕根据合成语句时长定位，长句按语义短语分屏，属于句级/短语级近似对齐，不宣称逐字强制对齐。']),
      ('第一课必须核查的技术点',['本课BluetoothSerial与客户端走经典蓝牙SPP；不要因ESP32也支持BLE而把本课误标成BLE。原版ESP32与C3/S3的能力不同；手机方案以Android为准。','手机→ESP32为蓝牙，ESP32→电脑为USB串口，不能说整个系统都无需线。9600是本课电脑串口设置，不是蓝牙无线链路的统一速率。','跳频与加密分别解释；距离、功耗、电池寿命取决于条件，不能绝对保证。配对、连接、自动重连、断开与删除配对记录要区分。','设备名不是密码，配对码不能固定套所有版本；BT.pinCode先核对官方API，不能当作可直接编译的通用接口。','available检查缓存数据，不是检查配对；读取会取走数据；readString可能等待超时；本地发送列表不是对方到达确认。']),
      ('第二课复核点',['双向程序分别处理蓝牙与串口；两个方向独立检查，不把回程藏在另一分支内。电脑仍通过USB串口连接ESP32。','手机接收使用连接检查、定时轮询、数据/非空判断和列表刷新；100毫秒约每秒10次，但系统调度可能延迟。','字节数不等于字符数；缓存中的数据不天然分成聊天消息。换行分条需双方统一约定，接收端避免等待缺失结尾导致卡住。']),
      ('实操、教师接力与交付验收',['每个暂停任务都给成功条件，学生描述现象、路线和已检查步骤，老师处理现场差异。讲解视频不代替学生真正操作。','检查40场景覆盖、7题答案、音视频流、总时长、字幕顺序、配音完整性和文档可读性；抽查代码页、积木页、提问倒计时、答案页、片头片尾。','实际硬件实测、视频原理动画、源码静态核对和文件解码检查必须分开记录。交付MP4、纯人声/章节语音、SRT、PPTX、讲稿、教师手册、本规范和源脚本。'])]
    make_doc('ESP32互动视频课程制作规范 v1.1',norms,O/'课程制作规范_v1.1.docx')
    # The standard is shared across both lessons. Keep the old version as history.
    other=Path('/workspace/esp32-course/output')
    for ext in ['docx','md']:shutil.copy(O/f'课程制作规范_v1.1.{ext}',other/f'课程制作规范_v1.1.{ext}')
    (O/'先读我.md').write_text(f'''# 第一课：ESP32蓝牙文字传输 · 互动课程包

本课依据用户新上传的《07.ESP32蓝牙通信基础1-压缩版.pptx》制作，不是根据第二课倒推的替代稿。
讲解时长：{mark(offset)}。40个场景，7道有答案与原因的思考题，6秒思考停顿，3处可暂停实验/验收。
视频、纯人声、6章语音、字幕、可编辑文字/代码的配套PPT、逐场景讲稿、教师手册、规范和基础示例代码均在本包。
PPT备注包含完整讲稿；动态效果以MP4为准。无须恢复已移除的原内嵌视频。
实体ESP32、手机安装和板包编译未在本制作环境实测，老师应先在机构设备上验证。
两课按课程制作规范v1.1统一；第二课视频已交付，本次新增第一课并复核第二课文件。
''')
    (O/'素材与技术来源.md').write_text('''# 素材与技术来源

- 第一课内容与积木/界面截图：用户上传《07.ESP32蓝牙通信基础1-压缩版.pptx》。附件内的教学说明按素材理解，未当作用户指令执行。
- 自绘：单向路线、频道/跳频示意、五阶段连接流程、缓存、代码高亮、小蓝机器人及倒计时。
- 音乐：脚本生成的轻量五声音阶旋律。配音：Kokoro-82M-v1.1-zh通用音色，由sherpa-onnx本地合成，后期轻微提亮音高；无特定人物模仿。模型随附Apache-2.0许可。
- 模型发布：https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models
- 蓝牙参考：https://docs.espressif.com/projects/arduino-esp32/en/latest/api/bluetooth.html
- App Inventor：https://ai2.appinventor.mit.edu/reference/components/connectivity.html
- 字体：Noto Sans CJK。技术数值与API需以课堂现有设备、软件版本和官方示例核对。
''')
    shutil.copy(Path('/workspace/esp32-course/tools/kokoro-multi-lang-v1_1/LICENSE'),O/'语音模型_LICENSE.txt')
    src=O/'制作源文件';src.mkdir(exist_ok=True)
    for name in ['lesson.py','synth.py','render.py','finalize.py','docs.py']:shutil.copy(T/name,src/name)
    shutil.copy(O/'timeline.json',src/'timeline.json')
    (src/'复用说明.md').write_text('运行环境：/workspace/esp32-course/.venv/bin/python，工作目录为/workspace/esp32-lesson1。先运行lesson.py，随后synth.py与render.py，全部40场景完成后运行finalize.py。需要原项目保留的Kokoro模型、ffmpeg、Noto CJK字体和assets截图。源脚本不是无需依赖的跨平台安装包。旧版第二课仍在/workspace/esp32-course；本课独立输出，避免覆盖其视频和语音。')
    (O/'制作状态.json').write_text(json.dumps({'lesson1':'produced','duration_seconds':offset,'scene_count':40,'questions':7,'hardware_tested':False,'standard':'v1.1'},ensure_ascii=False,indent=2))
    print('documents complete',flush=True)
