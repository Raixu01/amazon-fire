"""Verifica reconciliação das entregas e o conteúdo renderizado, inclusive mapas diários."""
from pathlib import Path
import json, hashlib, subprocess
import pandas as pd
import numpy as np
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'entregas/atm-2026'
a=json.loads((OUT/'auditoria.json').read_text(encoding='utf-8'))
d=json.loads((ROOT/'remotion/src/atm-dados.json').read_text(encoding='utf-8'))
df=pd.read_csv(OUT/'camadas/focos_amazonia_NOAA20.csv.gz')
assert set(df.satelite)=={'NOAA-20'}
assert not df.duplicated(['data_hora_gmt','lat','lon','satelite']).any()
assert df.groupby('mes').size().to_dict()==d['monthly']==a['contagens_mensais']
g=json.loads((OUT/'camadas/focos_regiao.geojson').read_text(encoding='utf-8'))
rows=pd.DataFrame([f['properties'] for f in g['features']])
assert rows.groupby('dia').size().to_dict()==d['daily']==a['contagens_diarias']
assert rows.groupby('NM_MUN').size().to_dict()=={r['name']:r['count'] for r in d['rank']}
assert sum(d['daily'].values())==sum(r['count'] for r in d['rank'])==d['total']
assert all(x['contagem']==x['contador']==x['recontagem_fontes_atuais'] for x in a['auditoria_edicao_anterior'])
for day,count in d['daily'].items():
    day_geo=json.loads((OUT/f'camadas/focos_{day}.geojson').read_text(encoding='utf-8'))
    assert len(day_geo['features'])==count
    assert all(f['properties']['dia']==day for f in day_geo['features'])
    assert hashlib.sha256((ROOT/f'remotion/public/atm/dia-{day}.png').read_bytes()).hexdigest()==a['hashes_camadas'][day]
ff=imageio_ffmpeg.get_ffmpeg_exe();results=[]
for name,seconds in [('previa-pulso-atm.mp4',19),('pulso-atm-2026.mp4',100)]:
    p=OUT/name
    reader=imageio_ffmpeg.read_frames(str(p));meta=next(reader);reader.close()
    assert meta['size']==(1920,1080) and meta['fps']==30 and abs(meta['duration']-seconds)<.05,meta
    decoded=subprocess.run([ff,'-v','error','-i',str(p),'-f','null','-'],capture_output=True)
    assert decoded.returncode==0 and not decoded.stderr,decoded.stderr
    results.append(dict(arquivo=name,duracao=meta['duration'],fps=meta['fps'],tamanho=meta['size'],codec=meta['codec'],decodificacao_completa=True,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
masks=[]
for i in range(15):
    r=subprocess.run([ff,'-v','error','-ss',str(43+2*i),'-i',str(OUT/'pulso-atm-2026.mp4'),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True)
    frame=np.frombuffer(r.stdout,np.uint8).reshape(1080,1920,3)
    m=frame[193:1001,601:1879].astype(float)
    mask=(m[:,:,0]>175)&(m[:,:,1]>65)&(m[:,:,1]<180)&(m[:,:,2]<135)&(m[:,:,0]>1.35*m[:,:,1])
    assert mask.sum()>20,f'Dia {i+1} sem pontos visíveis'
    masks.append(mask)
differences=[]
for i in range(14):
    union=np.logical_or(masks[i],masks[i+1]).sum()
    change=float(np.logical_xor(masks[i],masks[i+1]).sum()/union)
    assert change>.05,f'Mapa repetido entre dias {i+1} e {i+2}: {change}'
    differences.append(dict(dias=[i+1,i+2],fracao_pixels_laranja_diferentes=round(change,4)))
report=dict(dados_conciliados=True,camadas_diarias=15,videos=results,mapas_no_video=differences)
(OUT/'verificacao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
