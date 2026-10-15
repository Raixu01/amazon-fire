"""Prepara insumos auditáveis do vídeo; não modifica a aplicação Pulso."""
from pathlib import Path
import json, hashlib, io, concurrent.futures, xml.etree.ElementTree as ET, sys, zipfile
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import shape, Point, mapping

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'entregas'/'altamira'
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'camadas').mkdir(exist_ok=True)
(OUT/'fontes').mkdir(exist_ok=True)
BASE='https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/'
def fetch(day):
    name=f'focos_diario_br_{day:%Y%m%d}.csv'
    p=OUT/'fontes'/name
    if '--local' in sys.argv:
        content=p.read_bytes() if p.exists() else zipfile.ZipFile(OUT/'fontes_inpe_2026-10-08_a_15.zip').read(name)
        old=json.loads((OUT/'auditoria.json').read_text(encoding='utf-8'))
        modified=next(f['last_modified'] for f in old['fontes'] if f['arquivo']==name)
    else:
        r=requests.get(BASE+name,timeout=90); r.raise_for_status();content=r.content;modified=r.headers.get('Last-Modified');p.write_bytes(content)
    df=pd.read_csv(io.BytesIO(content))
    return df,dict(arquivo=name,url=BASE+name,sha256=hashlib.sha256(content).hexdigest(),linhas=len(df),last_modified=modified)
days=pd.date_range('2026-10-08','2026-10-15')
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(fetch,days))
data=pd.concat([r[0] for r in results],ignore_index=True)
data['utc']=pd.to_datetime(data.data_hora_gmt,utc=True)
data['brasilia']=data.utc.dt.tz_convert('America/Sao_Paulo')
data=data[(data.brasilia>=pd.Timestamp('2026-10-08',tz='America/Sao_Paulo'))&(data.brasilia<pd.Timestamp('2026-10-15',tz='America/Sao_Paulo'))].copy()
geo=json.loads((ROOT/'docs/data/municipios_amazonia_legal_web.geojson').read_text(encoding='utf-8'))
alt=next(f for f in geo['features'] if f['properties']['codigo_ibge']=='1500602')
visual_poly=shape(alt['geometry'])
meshpath=ROOT/'Mun_Amazonia_Legal_2024_shp.zip'
if meshpath.exists():
    mesh=gpd.read_file('zip://'+str(meshpath))
    original=mesh[mesh.CD_MUN=='1500602'].to_crs(4326)
else:
    original=gpd.read_file(OUT/'camadas'/'altamira_limite_original.geojson').to_crs(4326)
poly=original.geometry.iloc[0]
original.to_file(OUT/'camadas'/'altamira_limite_original.geojson',driver='GeoJSON')
neighbors=[f for f in geo['features'] if shape(f['geometry']).distance(visual_poly)<0.005]
def save(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False),encoding='utf-8')
save('camadas/limites.geojson',dict(type='FeatureCollection',features=neighbors))
minx,miny,maxx,maxy=poly.bounds
near=data[data.lon.between(minx-.01,maxx+.01)&data.lat.between(miny-.01,maxy+.01)].copy()
inside=near.apply(lambda r:poly.covers(Point(r.lon,r.lat)),axis=1)
data=near[inside].copy()
before=len(data); data=data.drop_duplicates(['data_hora_gmt','lat','lon','satelite'])
data['dia']=data.brasilia.dt.strftime('%Y-%m-%d')
fields=['precipitacao','numero_dias_sem_chuva','risco_fogo','frp']
for k in fields:
    data[k]=pd.to_numeric(data[k],errors='coerce'); data.loc[data[k]<0,k]=float('nan')
data.to_csv(OUT/'camadas'/'focos_periodo.csv',index=False)
features=[]
for _,r in data.iterrows():
    props={k:None if pd.isna(r[k]) else float(r[k]) for k in fields}
    props.update(dia=r.dia,horario_brasilia=r.brasilia.isoformat(),horario_utc=r.utc.isoformat(),satelite=r.satelite,id=str(r.id))
    features.append(dict(type='Feature',geometry=dict(type='Point',coordinates=[r.lon,r.lat]),properties=props))
save('camadas/focos_periodo.geojson',dict(type='FeatureCollection',features=features))
counts={d.strftime('%Y-%m-%d'):int((data.dia==d.strftime('%Y-%m-%d')).sum()) for d in days[:7]}
for day in counts:
    save(f'camadas/focos_{day}.geojson',dict(type='FeatureCollection',features=[f for f in features if f['properties']['dia']==day]))
coverage={k:dict(validos=int(data[k].notna().sum()),total=len(data),percentual=round(100*data[k].notna().mean(),2)) for k in fields}
audit=dict(periodo_brasilia=['2026-10-08T00:00:00-03:00','2026-10-15T00:00:00-03:00'],fim_exclusivo=True,contagens=counts,total=len(data),duplicidades_removidas=before-len(data),cobertura=coverage,fontes=[r[1] for r in results],limite='IBGE Amazônia Legal 2024; recorte pela geometria original, limite simplificado somente na visualização',bbox=list(poly.bounds),vizinhos=[f['properties']['nome'] for f in neighbors],lacunas_arquivos=[],nota='Disponibilidade de arquivos não garante ausência de falhas de aquisição dos sensores. Detecções multissatélite não equivalem a incêndios únicos.')
save('auditoria.json',audit)
save('cena.json',dict(auditoria=audit,limites=neighbors,focos=features))
ns='http://www.opengis.net/kml/2.2'; ET.register_namespace('',ns)
root=ET.Element('{'+ns+'}kml'); doc=ET.SubElement(root,'Document')
ET.SubElement(doc,'name').text='Altamira — teste 14/10/2026 (Brasília)'
for p in (list(visual_poly.geoms) if visual_poly.geom_type=='MultiPolygon' else [visual_poly]):
    pm=ET.SubElement(doc,'Placemark'); ET.SubElement(pm,'name').text='Limite de Altamira — IBGE 2024'
    style=ET.SubElement(pm,'Style'); ls=ET.SubElement(style,'LineStyle'); ET.SubElement(ls,'color').text='ff78e8ff'; ET.SubElement(ls,'width').text='3'
    ps=ET.SubElement(style,'PolyStyle'); ET.SubElement(ps,'fill').text='0'
    pol=ET.SubElement(pm,'Polygon'); ring=ET.SubElement(ET.SubElement(pol,'outerBoundaryIs'),'LinearRing'); ET.SubElement(ring,'coordinates').text=' '.join(f'{x},{y},0' for x,y in p.exterior.coords)
for f in features:
    if f['properties']['dia']!='2026-10-14':continue
    pm=ET.SubElement(doc,'Placemark'); ET.SubElement(pm,'name').text=f['properties']['satelite']+' '+f['properties']['horario_brasilia']
    ET.SubElement(ET.SubElement(pm,'Point'),'coordinates').text=','.join(map(str,f['geometry']['coordinates']))+',0'
ET.ElementTree(root).write(OUT/'camadas'/'teste_2026-10-14.kml',encoding='utf-8',xml_declaration=True)
print(json.dumps(audit,ensure_ascii=False,indent=2))
