"""Arquiva mosaicos de referência Esri para renderização offline alinhada em EPSG:3857."""
from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
import requests
from PIL import Image
from io import BytesIO

ROOT=Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'remotion/src/atm-dados.json').read_text(encoding='utf-8'))
service='https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
records=[]
for name,key in [('amazonia','extentNational'),('regiao','extentRegional')]:
    params=dict(bbox=','.join(map(str,meta[key])),bboxSR=3857,imageSR=3857,size='2560,1620',format='jpg',f='image')
    r=requests.get(service+'/export',params=params,timeout=120);r.raise_for_status()
    im=Image.open(BytesIO(r.content));assert im.size==(2560,1620)
    p=ROOT/f'remotion/public/atm/{name}.jpg';p.write_bytes(r.content)
    records.append(dict(nome=name,url=r.url,sha256=hashlib.sha256(r.content).hexdigest(),obtido_utc=datetime.now(timezone.utc).isoformat()))
    print(name,im.size,len(r.content),flush=True)
r=requests.get(service,params=dict(f='json'),timeout=30);r.raise_for_status()
credits=r.json().get('copyrightText','Esri e fornecedores de imagens')
(ROOT/'entregas/atm-2026/fundo.json').write_text(json.dumps(dict(fontes=records,creditos=credits,nota='Mosaico de datas diversas; não representa outubro de 2026.'),ensure_ascii=False,indent=2),encoding='utf-8')
print(credits)
