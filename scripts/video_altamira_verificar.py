"""Verificação da entrega e empacotamento das camadas auditáveis."""
from pathlib import Path
import json, subprocess, zipfile, hashlib
from collections import Counter
import xml.etree.ElementTree as ET
import imageio_ffmpeg
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'entregas'/'altamira'
a=json.loads((OUT/'auditoria.json').read_text(encoding='utf-8'))
features=json.loads((OUT/'camadas/focos_periodo.geojson').read_text(encoding='utf-8'))['features']
assert Counter(f['properties']['dia'] for f in features)==a['contagens']
assert len(features)==a['total']==11922
assert len({(f['properties']['horario_utc'],*f['geometry']['coordinates'],f['properties']['satelite']) for f in features})==len(features)
for day,n in a['contagens'].items():
    layer=json.loads((OUT/f'camadas/focos_{day}.geojson').read_text(encoding='utf-8'))
    assert len(layer['features'])==n
for f in features:
    t=pd.Timestamp(f['properties']['horario_brasilia'])
    assert t.utcoffset().total_seconds()==-10800
    assert pd.Timestamp('2026-10-08T00:00:00-03:00')<=t<pd.Timestamp('2026-10-15T00:00:00-03:00')
assert len(ET.parse(OUT/'camadas/teste_2026-10-14.kml').findall('.//{*}Point'))==a['contagens']['2026-10-14']
projection=json.loads((OUT/'projecao.json').read_text())
assert len(projection)==len(features)
assert all(p and 0<=p[0]<1920 and 150<=p[1]<1015 for p in projection)
for source in a['fontes']:
    assert hashlib.sha256((OUT/'fontes'/source['arquivo']).read_bytes()).hexdigest()==source['sha256']
report={'dados':'OK','pontos_visiveis':len(features),'periodo_brasilia':a['periodo_brasilia'],'videos':[]}
ff=imageio_ffmpeg.get_ffmpeg_exe()
for file,duration in [('teste_altamira_2026-10-14.mp4',6),('altamira_2026-10-08_a_14_fullhd.mp4',60)]:
    stream=imageio_ffmpeg.read_frames(str(OUT/file));meta=next(stream);stream.close()
    assert meta['size']==(1920,1080) and meta['fps']==30 and meta['codec']=='h264' and abs(meta['duration']-duration)<.04
    check=subprocess.run([ff,'-v','error','-i',str(OUT/file),'-f','null','-'],capture_output=True,text=True)
    assert check.returncode==0 and not check.stderr,check.stderr
    count,seconds=imageio_ffmpeg.count_frames_and_secs(str(OUT/file));assert count==duration*30
    report['videos'].append(dict(arquivo=file,metadados=meta,quadros=count,decodificacao_integral='OK',bytes=(OUT/file).stat().st_size))
(OUT/'verificacao_final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(OUT/'camadas_e_notas.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in (OUT/'camadas').glob('*'):z.write(f,f.relative_to(OUT))
    for name in ['NOTA.txt','LEIA-ME.md','auditoria.json','auditoria_recorte_original.json','verificacao_final.json']:
        z.write(OUT/name,name)
print(json.dumps(report,ensure_ascii=False,indent=2))
