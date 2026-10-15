"""Compõe e codifica a edição sem áudio a partir da cena Cesium validada."""
from pathlib import Path
import json, math, subprocess, sys
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
import numpy as np

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'entregas'/'altamira'
D=json.loads((OUT/'cena.json').read_text(encoding='utf-8')); A=D['auditoria']
P=json.loads((OUT/'projecao.json').read_text()); F=D['focos']; DAYS=list(A['contagens'])
BASE=Image.open(OUT/'paisagem.png').convert('RGB')
WHITE='#f4f5ed'; MUTED='#aebfc1'; GOLD='#ffe492'; CORAL='#ff764e'; CYAN='#63d9d7'; BG='#071c24'
def font(s,b=False):return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if b else 'C:/Windows/Fonts/arial.ttf',s)
def text(d,xy,s,size=28,fill=WHITE,b=False):d.text(xy,s,font=font(size,b),fill=fill)
def num(n):return f'{n:,}'.replace(',','.')
def panel(im,rect,alpha=235):
    layer=Image.new('RGBA',im.size); dr=ImageDraw.Draw(layer);dr.rounded_rectangle(rect,18,fill=(5,23,31,alpha));return Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
def frame_base(title,section,base=None):
    im=(base or BASE).copy(); im=panel(im,(36,30,1884,150));d=ImageDraw.Draw(im)
    text(d,(64,48),'PULSO  /  AMAZÔNIA',22,CYAN,True);text(d,(64,82),title,44,WHITE,True)
    text(d,(1470,52),'ALTAMIRA · PARÁ',26,GOLD,True);text(d,(1470,92),section,24,MUTED)
    # Stable, explicit source attribution on every shot.
    d.rectangle((0,1015,1920,1080),fill=BG)
    text(d,(38,1024),'Focos: INPE • Limites: IBGE 2024 • Cena: CesiumJS • Relevo: Esri World Elevation',20,MUTED)
    text(d,(38,1050),'Fundo: Esri, Vantor, Earthstar Geographics e GIS User Community — mosaico de datas diversas',20,MUTED)
    return im
def points(im,day=None,risk=False,allpoints=False,only=False):
    dr=ImageDraw.Draw(im)
    order=sorted(range(len(F)),key=lambda i:F[i]['properties']['dia'])
    for i in order:
        if P[i] is None:continue
        f=F[i]['properties']; dd=f['dia']; x,y=P[i]
        if day and dd>day:continue
        if only and dd!=day:continue
        if risk:
            v=f['risco_fogo']; color='#8d979a' if v is None else tuple(int(a+(b-a)*v) for a,b in zip((79,193,193),(255,94,60))); r=2.3
        elif allpoints:color=CYAN;r=2.2
        else:color=CORAL if dd==day else '#637f88';r=3 if dd==day else 1.8
        dr.ellipse((x-r,y-r,x+r,y+r),fill=color)
    return im
def legend(im,risk=False,only=False):
    im=panel(im,(1390,760,1884,992));d=ImageDraw.Draw(im)
    text(d,(1420,780),'COMO LER',22,GOLD,True)
    if risk:
        for x in range(380):
            v=x/379;d.line((1420+x,830,1420+x,852),fill=tuple(int(a+(b-a)*v) for a,b in zip((79,193,193),(255,94,60))))
        text(d,(1420,860),'0',23);text(d,(1784,860),'1',23)
        text(d,(1420,902),'Índice modelado nos focos',24)
        text(d,(1420,940),'Cinza: dado indisponível',22,MUTED)
    else:
        d.ellipse((1420,828,1432,840),fill=CORAL);text(d,(1450,818),'Detecções do dia',25)
        if not only:
            d.ellipse((1420,875,1432,887),fill='#637f88');text(d,(1450,866),'Dias anteriores',25)
            text(d,(1420,914),'Atenuação visual ≠ extinção',23,MUTED)
        else:text(d,(1420,875),'Somente 14 de outubro',25,MUTED)
        text(d,(1420,950),'Pontos sem escala de área',22,MUTED)
    return im
def day_frame(k,test=False):
    day=DAYS[k]; im=frame_base('Sete dias de detecções','08–14 OUT 2026');im=points(im,day,only=test);im=legend(im,only=test)
    im=panel(im,(36,180,484,980));d=ImageDraw.Draw(im)
    text(d,(64,208),'TESTE VISUAL' if test else f'DIA {k+1} DE 7',24,CYAN,True)
    text(d,(64,255),f'{day[8:10]} OUT 2026',40,WHITE,True)
    text(d,(64,310),'00h–24h · Brasília (UTC−3)',24,MUTED)
    text(d,(64,374),num(A['contagens'][day]),76,CORAL,True)
    text(d,(64,461),'detecções neste dia',27)
    text(d,(64,535),'EVOLUÇÃO DIÁRIA',22,CYAN,True)
    maximum=max(A['contagens'].values())
    for j,(dt,n) in enumerate(A['contagens'].items()):
        y=582+j*43;text(d,(64,y),dt[8:],23,MUTED)
        d.rounded_rectangle((106,y+4,106+210*n/maximum,y+25),4,fill=CORAL if j==k else '#3c5963')
        text(d,(336,y),num(n),23,WHITE if j==k else MUTED)
    text(d,(64,913),'Focos não são incêndios únicos.',23,MUTED)
    # Map labels placed in the interior, outside the point concentrations.
    text(d,(990,455),'ALTAMIRA',25,GOLD,True);text(d,(1555,210),'N ↑',26,WHITE,True)
    return im
def risk_frame():
    im=frame_base('O contexto ambiental','RISCO DE FOGO');im=points(im,risk=True);im=legend(im,True)
    im=panel(im,(36,180,520,980));d=ImageDraw.Draw(im)
    text(d,(64,208),'VARIÁVEL MODELADA',23,CYAN,True)
    text(d,(64,262),'Risco de fogo',42,WHITE,True)
    text(d,(64,338),str(A['cobertura']['risco_fogo']['percentual']).replace('.',',')+'%',70,CORAL,True)
    for y,s in [(426,'dos registros têm valor válido'),(480,'08–14 de outubro de 2026'),(552,'A cor indica o índice associado'),(588,'a cada detecção do período.'),(660,'Não representa a cobertura'),(696,'contínua de todo o município.'),(768,'Não é previsão de incêndios'),(804,'nem medida de área queimada.')]:text(d,(64,y),s,25,MUTED if y>500 else WHITE)
    text(d,(64,913),'Fonte: campos ambientais do INPE',22,CYAN)
    return im
def distribution():
    im=frame_base('Onde as detecções se concentram','DISTRIBUIÇÃO'); im=points(im,allpoints=True)
    im=panel(im,(36,180,520,980));d=ImageDraw.Draw(im)
    west=sum(f['geometry']['coordinates'][0]<-54 for f in F)/len(F)*100
    text(d,(64,210),'08–14 OUT · BRASÍLIA',24,CYAN,True)
    text(d,(64,275),num(len(F)),70,CORAL,True)
    text(d,(64,364),'detecções no período',29)
    text(d,(64,440),f'{west:.1f}%'.replace('.',','),62,WHITE,True)
    text(d,(64,518),'a oeste do meridiano 54° O',25)
    for y,s in [(602,'Uma mesma área pode aparecer'),(638,'em várias passagens de satélites.'),(718,'Imagens recentes avaliadas:'),(754,'nuvens e lacunas limitam a visão.'),(834,'O fundo é um mosaico histórico;'),(870,'os pontos são observações recentes.')]:text(d,(64,y),s,24,MUTED)
    return im
def summary():
    im=BASE.copy().point(lambda x:int(x*.28));im=frame_base('Altamira | síntese do período','08–14 OUT 2026',im);d=ImageDraw.Draw(im)
    text(d,(80,205),num(len(F)),112,CORAL,True);text(d,(83,338),'detecções · 7 dias completos · múltiplos satélites',35)
    text(d,(83,422),'Maior contagem diária: 8 de outubro · '+num(max(A['contagens'].values()))+' detecções',31)
    for y,s in [(515,'Focos e contexto ambiental: INPE / Programa Queimadas'),(562,'Limite municipal e vizinhos: IBGE / Amazônia Legal 2024'),(609,'Visualização: CesiumJS + Esri World Imagery / World Elevation'),(690,'Datas e horários em Brasília (UTC−3). Sem narração.'),(737,'Detecção não equivale a incêndio único ou área queimada.'),(784,'Ausência de pontos não comprova ausência de fogo.'),(865,'Camadas, fontes e limitações acompanham esta edição.')]:text(d,(83,y),s,29,MUTED if y>=690 else WHITE)
    return im
def intro(i):
    u=i/239*47; k=int(u)
    a=Image.open(OUT/'intro_chaves'/f'{k:04d}.png').convert('RGB')
    b=Image.open(OUT/'intro_chaves'/f'{min(47,k+1):04d}.png').convert('RGB')
    im=Image.blend(a,b,u-k);im=frame_base('Da Amazônia a Altamira','LOCALIZAÇÃO',im)
    im=panel(im,(36,180,490,445));d=ImageDraw.Draw(im)
    text(d,(64,208),'08–14 OUTUBRO 2026',27,CYAN,True)
    text(d,(64,267),'Altamira, Pará',42,WHITE,True)
    text(d,(64,340),'Limite municipal em amarelo',25,GOLD)
    text(d,(64,383),'Vizinhos em linhas discretas',24,MUTED)
    return im
def encode(path,frames,n):
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=[ff,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
    with (OUT/'codificacao.log').open('a') as log:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
        for i,im in enumerate(frames):
            proc.stdin.write(im.tobytes())
            if i%300==0:print('ENCODE',path.name,i,'/',n,flush=True)
        proc.stdin.close();assert proc.wait()==0
if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'test'
    if mode=='test':
        im=day_frame(6,True);im.save(OUT/'teste_frame.png');encode(OUT/'teste_altamira_2026-10-14.mp4',(im for _ in range(180)),180)
    else:
        ds=[day_frame(k) for k in range(7)];risk=risk_frame();dist=distribution();end=summary()
        for name,im in [('risco',risk),('distribuicao',dist),('sintese',end)]:im.save(OUT/f'revisao_{name}.png')
        def frames():
            previous=None
            for i in range(1800):
                t=i/30
                if i<240:im=intro(i)
                elif i<960:im=ds[min(6,int((t-8)/24*7))]
                elif i<1320:im=risk
                elif i<1560:im=dist
                else:im=end
                yield im
        encode(OUT/'altamira_2026-10-08_a_14_fullhd.mp4',frames(),1800)
