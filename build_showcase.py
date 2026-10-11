"""Build small demo GIFs and a social card from actual model output and saved logs.

Requires Node.js and Pillow (python -m pip install Pillow). Model engines and
included experiment logs are read only. No simulation results are overwritten.
"""
import csv
import json
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from simulate import make_route

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'docs'/'media'
BG='#101a28'; PANEL='#162436'; MUTED='#a8bacb'; TEXT='#edf3f7'
COLORS=['#ff9e99','#8de2c5','#b7a3ff']; GOLD='#f1d285'

def font(size,bold=False):
    candidates=[Path('C:/Windows/Fonts')/('segoeuib.ttf' if bold else 'segoeui.ttf'),
        Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
    return next((ImageFont.truetype(str(p),size) for p in candidates if p.exists()),ImageFont.load_default(size=size))

def text(draw,xy,value,size=15,color=TEXT,bold=False):
    face=font(size,bold)
    if any('\u4e00'<=char<='\u9fff' for char in value):
        for path in [Path('C:/Windows/Fonts/msyh.ttc'),Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')]:
            if path.exists():face=ImageFont.truetype(str(path),size);break
    draw.text(xy,value,font=face,fill=color)
def star(draw,x,y,r=9):
    points=[(x+math.cos(-math.pi/2+i*math.pi/5)*(r if i%2==0 else r*.45),y+math.sin(-math.pi/2+i*math.pi/5)*(r if i%2==0 else r*.45)) for i in range(10)]
    draw.polygon(points,fill=GOLD)
def base(title,subtitle,time):
    image=Image.new('RGB',(640,400),BG);draw=ImageDraw.Draw(image)
    text(draw,(24,18),title,24,bold=True);text(draw,(24,53),subtitle,13,MUTED)
    text(draw,(24,375),'RECORDED MODEL OUTPUT · '+f't = {time:.1f} s',12,MUTED)
    return image,draw

def path_frame(sample,route):
    time,points=sample;image,d=base('01 / Robot path tracking','S-curve · speed 1 m/s · command delay 0.5 s · lookahead 1 m',time)
    def xy(x,y):return (30+x/20*580,225-y/5*110)
    for x in range(0,21,5):
        px,_=xy(x,0);d.line((px,100,px,332),fill='#26384b');text(d,(px,338),str(x)+' m',11,MUTED)
    routepx=[xy(x,y) for x,y in route]
    for a,b in zip(routepx[::2],routepx[1::2]):d.line((*a,*b),fill=MUTED,width=2)
    for i,(row,history) in enumerate(points):
        trace=[xy(r['x_m'],r['y_m']) for r in history]
        if len(trace)>1:d.line(trace,fill=COLORS[i],width=3)
        px,py=xy(row['x_m'],row['y_m']);angle=row['yaw_rad']
        d.ellipse((px-7,py-7,px+7,py+7),fill=COLORS[i]);d.line((px,py,px+15*math.cos(angle),py-15*math.sin(angle)),fill=TEXT,width=2)
        label=['Pure Pursuit','Predicted-state PP'][i];text(d,(24+i*290,78),label,14,COLORS[i],True)
    return image

def star_frame(sample):
    time,target,ships=sample;image,d=base('02 / Don’t overshoot','More push, more wobble · delay 0.4 s · gain 4 · braking 0.2',time)
    lo,hi=-12,12
    def x(value):return 128+(max(lo,min(hi,value))-lo)/(hi-lo)*470
    for i,pos in enumerate(ships):
        y=130+i*80;d.line((128,y,598,y),fill='#32465c',width=2);star(d,x(target),y)
        d.polygon([(x(pos)+13,y),(x(pos)-9,y-8),(x(pos)-5,y),(x(pos)-9,y+8)],fill=[COLORS[1],COLORS[0],COLORS[2]][i])
        text(d,(18,y-18),['Instant','Delayed','Predictive'][i],14,[COLORS[1],COLORS[0],COLORS[2]][i],True)
    text(d,(128,333),'Display range −12 to +12 simulation units',12,MUTED)
    return image

def arm_frame(sample):
    time,target,arms=sample;image,d=base('03 / Catch the Stars','Same target and limits · Kp 16 · Kd 1.5 · zero command delay',time)
    for i,q in enumerate(arms):
        cx=165+i*310;cy=245;scale=72
        d.ellipse((cx-1.8*scale,cy-1.8*scale,cx+1.8*scale,cy+1.8*scale),outline='#34475d',width=1)
        d.ellipse((cx-.2*scale,cy-.2*scale,cx+.2*scale,cy+.2*scale),outline='#34475d',width=1)
        elbow=(cx+math.cos(q[0])*scale,cy-math.sin(q[0])*scale)
        tip=(elbow[0]+.8*math.cos(q[0]+q[1])*scale,elbow[1]-.8*math.sin(q[0]+q[1])*scale)
        d.line(((cx,cy),elbow,tip),fill=COLORS[i],width=8)
        for x,y in [(cx,cy),elbow,tip]:d.ellipse((x-5,y-5,x+5,y+5),fill=BG,outline=COLORS[i],width=2)
        star(d,cx+target['x']*scale,cy-target['y']*scale)
        text(d,(46+i*310,86),['Position only · P','Position + braking · PD'][i],15,COLORS[i],True)
    return image

def save_gif(name,frames):
    frames[0].save(OUT/name,save_all=True,append_images=frames[1:],duration=100,loop=0,optimize=True,disposal=2)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summaries=list(csv.DictReader((ROOT/'results_v02'/'summary.csv').open(encoding='utf-8')))
    selected=[r for r in summaries if r['group']=='comparison' and r['route']=='s_curve' and float(r['speed_m_s'])==1 and float(r['delay_s'])==.5]
    logs=[]
    for kind in ['pp','predictor']:
        case=next(r for r in selected if r['controller']==kind)
        logs.append([{k:float(v) for k,v in row.items()} for row in csv.DictReader((ROOT/'results_v02'/'logs'/(case['case_id']+'.csv')).open(encoding='utf-8'))])
    route=make_route('s_curve',201)
    pathframes=[]
    for tick in range(0,min(len(r) for r in logs),5):
        if logs[0][tick]['time_s']>15:break
        sample=(logs[0][tick]['time_s'],[(rows[tick],rows[:tick+1:5]) for rows in logs])
        pathframes.append(path_frame(sample,route))
    code="""
const S=require('./docs/engine.js'),A=require('./docs/arm/engine.js');
const star=new S.Experiment(S.presets.chaos),arm=new A.Experiment(A.presets.overshoot);
const stars=[[0,1.2,star.ships.slice(0,3).map(s=>s.state.x)]],arms=[[0,arm.target,arm.arms.map(a=>a.q)]];
for(let i=0;i<2400;i++){const target=S.targetAt(star.time,star.settings.motion);star.step(target);if((i+1)%12===0)stars.push([star.time,target.x,star.ships.slice(0,3).map(s=>s.state.x)]);}
while(!arm.done){arm.step();if(arm.stepCount%10===0)arms.push([arm.time,arm.target,arm.arms.map(a=>a.q)]);}
process.stdout.write(JSON.stringify({stars,arms}));
"""
    data=json.loads(subprocess.check_output(['node','-e',code],cwd=ROOT))
    starframes=[star_frame(sample) for sample in data['stars']]
    armframes=[arm_frame(sample) for sample in data['arms']]
    for name,frames in [('path-tracking.gif',pathframes),('star-chase.gif',starframes),('catch-the-stars.gif',armframes)]:save_gif(name,frames)
    card=Image.new('RGB',(1280,640),BG);d=ImageDraw.Draw(card)
    text(d,(48,38),'ROBOT DELAY LAB',44,bold=True)
    text(d,(48,103),'Play with feedback, delay and prediction.',25,GOLD)
    text(d,(48,146),'3 experiments · No hardware · 中文 / English',19,MUTED)
    # Each thumbnail comes from the same generated model frames as its GIF.
    for i,frames in enumerate([pathframes,starframes,armframes]):
        thumbnail=frames[min(len(frames)-1,35)].resize((378,236),Image.Resampling.LANCZOS)
        card.paste(thumbnail,(48+i*400,207))
        text(d,(48+i*400,470),['Path tracking','Star Chase','Catch the Stars'][i],22,COLORS[i if i<2 else 2],True)
    text(d,(48,533),'Play in your browser. Reproduce with Python. Keep your findings.',22)
    text(d,(48,589),'flessnerchernosky-ops/robot-delay-lab · MIT · Educational models · AI-assisted',16,MUTED)
    card.save(OUT/'social-preview.png',optimize=True)
    metadata={'path':{'route':'s_curve','speed_m_s':1,'delay_s':.5,'lookahead_m':1,'source_cases':[r['case_id'] for r in selected],'display_duration_s':15},'star_preset':'chaos','arm_preset':'overshoot','frame_interval_s':.1,'gif_duration_ms':100,'note':'Recorded model output; not hardware footage. Font rendering may vary by platform.'}
    (OUT/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({p.name:p.stat().st_size for p in OUT.iterdir()},indent=2))

if __name__=='__main__':main()
