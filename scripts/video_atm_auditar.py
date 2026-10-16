"""Auditoria reproduzível da edição Pulso | .ATM, corte em 15/10/2026.

python scripts/video_atm_auditar.py --download  # valida fontes na origem
python scripts/video_atm_auditar.py             # usa snapshot já arquivado
"""
from pathlib import Path
import concurrent.futures as cf
import hashlib, json, sys, io
from datetime import datetime, timezone
import pandas as pd
import geopandas as gpd
import numpy as np
import requests
import shapely
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'entregas/atm-2026'
CACHE=ROOT/'.cache/atm-2026'
ASSET=ROOT/'remotion/public/atm'
for p in [OUT, CACHE, ASSET, OUT/'camadas']: p.mkdir(parents=True,exist_ok=True)
BASE='https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/'
SAT='NOAA-20'
KEY=['data_hora_gmt','lat','lon','satelite']
def save(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def digest(b): return hashlib.sha256(b).hexdigest()
names=[f'focos_mensal_br_2026{m:02d}.csv' for m in range(1,10)]+[f'focos_diario_br_202610{d:02d}.csv' for d in range(1,16)]
def fetch(name):
    url=BASE+('mensal' if 'mensal' in name else 'diario')+'/Brasil/'+name
    path=CACHE/name; meta_path=CACHE/(name+'.json')
    if '--download' in sys.argv:
        r=requests.get(url,timeout=180); r.raise_for_status()
        assert r.content.startswith(b'id,'), f'CSV inválido: {name}'
        path.write_bytes(r.content)
        save(meta_path,dict(url=url,arquivo=name,obtido_utc=datetime.now(timezone.utc).isoformat(),last_modified=r.headers.get('Last-Modified'),sha256=digest(r.content)))
    if not path.exists():
        raise RuntimeError(f'Fonte não arquivada: {name}. Execute --download.')
    meta=json.loads(meta_path.read_text(encoding='utf-8')); content=path.read_bytes()
    assert digest(content)==meta['sha256']
    df=pd.read_csv(io.BytesIO(content),usecols=['id','lat','lon','data_hora_gmt','satelite','municipio_id'])
    expected=name.rsplit('_',1)[1].split('.')[0]
    actual=df.data_hora_gmt.str.replace('-','',regex=False).str.slice(0,len(expected))
    meta['datas_fora_periodo_arquivo']=int((actual!=expected).sum())
    assert meta['datas_fora_periodo_arquivo']==0, f'Datas incompatíveis com o arquivo {name}'
    meta['linhas']=len(df)
    meta['inicio_utc']=df.data_hora_gmt.min();meta['fim_utc']=df.data_hora_gmt.max()
    print(name,len(df),flush=True)
    return df,meta

with cf.ThreadPoolExecutor(max_workers=4) as pool: files=list(pool.map(fetch,names))
allrows=pd.concat([x[0] for x in files],ignore_index=True)
allrows['utc']=pd.to_datetime(allrows.data_hora_gmt,utc=True,errors='coerce')
invalid=int((allrows.utc.isna()|~allrows.lat.between(-90,90)|~allrows.lon.between(-180,180)).sum())
assert invalid==0, f'{invalid} registros inválidos exigem investigação'
allrows['brasilia']=allrows.utc.dt.tz_convert('America/Sao_Paulo')
before=len(allrows);allrows=allrows.drop_duplicates(KEY).copy(); duplicates=before-len(allrows)
allrows=allrows[(allrows.brasilia>=pd.Timestamp('2026-01-01',tz='America/Sao_Paulo'))&(allrows.brasilia<pd.Timestamp('2026-10-16',tz='America/Sao_Paulo'))].copy()
allrows['dia']=allrows.brasilia.dt.strftime('%Y-%m-%d');allrows['mes']=allrows.brasilia.dt.strftime('%Y-%m')
cutoff=allrows.brasilia.max()
sensor_table=pd.crosstab(allrows.mes,allrows.satelite)
sensor_table.to_csv(OUT/'sensores_por_mes.csv')
selected=allrows[allrows.satelite==SAT].copy()
assert set(selected.mes)=={f'2026-{m:02d}' for m in range(1,11)}
available=set(selected.dia)
missing=[x.strftime('%Y-%m-%d') for x in pd.date_range('2026-01-01','2026-10-14') if x.strftime('%Y-%m-%d') not in available]
assert not missing, f'Dias sem registros nacionais do sensor: {missing}'
legal=gpd.read_file('zip://'+str(ROOT/'Limites_Amazonia_Legal_2024_shp.zip')).to_crs(4326)
mesh=gpd.read_file('zip://'+str(ROOT/'Mun_Amazonia_Legal_2024_shp.zip')).to_crs(4326)
poly=legal.geometry.union_all();shapely.prepare(poly)
inside=shapely.covers(poly,shapely.points(selected.lon.to_numpy(),selected.lat.to_numpy()))
amazon=selected[inside].copy()
alt=mesh.loc[mesh.CD_MUN=='1500602'].geometry.iloc[0]
neighbors=mesh[mesh.geometry.touches(alt)].copy()
assert len(neighbors)>0
region_mesh=pd.concat([mesh[mesh.CD_MUN=='1500602'],neighbors]).copy()
october=amazon[amazon.mes=='2026-10'].copy()
points=gpd.GeoDataFrame(october,geometry=gpd.points_from_xy(october.lon,october.lat),crs=4326)
joined=gpd.sjoin(points,region_mesh[['CD_MUN','NM_MUN','geometry']],how='inner',predicate='intersects')
boundary_duplicates=int(joined.index.duplicated().sum())
joined=joined.sort_values('CD_MUN').loc[lambda x:~x.index.duplicated()].copy()
ranking=joined.groupby(['CD_MUN','NM_MUN']).size().sort_values(ascending=False)
top=[c for c,n in ranking.index if c!='1500602'][:5]
chosen=['1500602']+top
region=joined[joined.CD_MUN.isin(chosen)].copy()
chosen_mesh=region_mesh[region_mesh.CD_MUN.isin(chosen)].copy()
counts=region.groupby('dia').size().reindex([f'2026-10-{d:02d}' for d in range(1,16)],fill_value=0)
monthly=amazon.groupby('mes').size().reindex([f'2026-{m:02d}' for m in range(1,11)],fill_value=0)
daily_table=pd.crosstab(region.dia,region.NM_MUN).reindex(counts.index,fill_value=0)
daily_table.to_csv(OUT/'contagens_diarias_municipios.csv')
monthly.rename('deteccoes').to_csv(OUT/'contagens_mensais_amazonia.csv')
ranking.rename('deteccoes').to_csv(OUT/'ranking_todos_vizinhos.csv')
amazon.drop(columns=['utc','brasilia']).to_csv(OUT/'camadas/focos_amazonia_NOAA20.csv.gz',index=False,compression='gzip')
export_cols=['id','lat','lon','data_hora_gmt','satelite','municipio_id','dia','CD_MUN','NM_MUN','geometry']
region[export_cols].to_file(OUT/'camadas/focos_regiao.geojson',driver='GeoJSON')
chosen_mesh[['CD_MUN','NM_MUN','geometry']].to_file(OUT/'camadas/municipios_selecionados.geojson',driver='GeoJSON')
legal.to_file(OUT/'camadas/amazonia_legal.geojson',driver='GeoJSON')
for day in counts.index:
    region.loc[region.dia==day,export_cols].to_file(OUT/f'camadas/focos_{day}.geojson',driver='GeoJSON')

# Geometria original para análise; simplificação apenas para a arte.
merc_legal=legal.to_crs(3857);merc_mesh=region_mesh.to_crs(3857)
RATIO=1280/810
def extent(bounds,pad):
    x0,y0,x1,y1=bounds;cx=(x0+x1)/2;cy=(y0+y1)/2
    w=(x1-x0)*(1+pad);h=(y1-y0)*(1+pad)
    w=max(w,h*RATIO);h=w/RATIO
    return [cx-w/2,cy-h/2,cx+w/2,cy+h/2]
national=extent(merc_legal.total_bounds,.10)
regional=extent(chosen_mesh.to_crs(3857).total_bounds,.19)
def svgbox(b): return [b[0],-b[3],b[2]-b[0],b[3]-b[1]]
def pathgeom(geo):
    polys=list(geo.geoms) if geo.geom_type=='MultiPolygon' else [geo]
    chunks=[]
    for pol in polys:
        for ring in [pol.exterior,*pol.interiors]:
            chunks.append('M'+' L'.join(f'{x:.1f},{-y:.1f}' for x,y in ring.coords)+' Z')
    return ' '.join(chunks)
paths=[dict(code=r.CD_MUN,name=r.NM_MUN,path=pathgeom(r.geometry.simplify(700)),chosen=r.CD_MUN in chosen) for _,r in merc_mesh.iterrows()]
all_paths=[pathgeom(geometry.simplify(4500)) for geometry in mesh.to_crs(3857).geometry]
labels=[]
for _,r in chosen_mesh.to_crs(3857).iterrows():
    p=r.geometry.representative_point();labels.append(dict(code=r.CD_MUN,name=r.NM_MUN,x=p.x,y=-p.y))
def layer(df,b,name,radius):
    coords=gpd.GeoSeries(gpd.points_from_xy(df.lon,df.lat),crs=4326).to_crs(3857)
    im=Image.new('RGBA',(2560,1620));draw=ImageDraw.Draw(im)
    xs=(coords.x.to_numpy()-b[0])/(b[2]-b[0])*2560
    ys=(b[3]-coords.y.to_numpy())/(b[3]-b[1])*1620
    for x,y in zip(xs,ys): draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(255,119,76,230))
    im.save(ASSET/name)
    return digest((ASSET/name).read_bytes())
layer_hashes={}
for m in monthly.index: layer_hashes[m]=layer(amazon[amazon.mes==m],national,f'mes-{m}.png',3)
for d in counts.index: layer_hashes[d]=layer(region[region.dia==d],regional,f'dia-{d}.png',5)
layer(region,regional,'acumulado.png',5)
assert len({layer_hashes[d] for d in counts.index})==15,'Camadas diárias idênticas'
day_keys={d:set(map(tuple,region.loc[region.dia==d,KEY].to_numpy())) for d in counts.index}
day_coords={d:set(map(tuple,region.loc[region.dia==d,['lat','lon']].to_numpy())) for d in counts.index}
comparisons=[]
for d1,d2 in zip(counts.index[:-1],counts.index[1:]):
    comparisons.append(dict(dia1=d1,dia2=d2,registros_identicos=len(day_keys[d1]&day_keys[d2]),coordenadas_repetidas=len(day_coords[d1]&day_coords[d2]),camadas_iguais=layer_hashes[d1]==layer_hashes[d2]))
assert all(x['registros_identicos']==0 and not x['camadas_iguais'] for x in comparisons)
# Auditoria independente da edição antiga, sem alterar seus arquivos.
old=json.loads((ROOT/'entregas/altamira/cena.json').read_text(encoding='utf-8'))
old_checks=[]
oct_all=allrows[allrows.mes=='2026-10'].copy()
shapely.prepare(alt)
old_inside=shapely.covers(alt,shapely.points(oct_all.lon.to_numpy(),oct_all.lat.to_numpy()))
old_recount=oct_all[old_inside].groupby('dia').size()
for d,c in old['auditoria']['contagens'].items():
    fs=[f for f in old['focos'] if f['properties']['dia']==d]
    layer_old=ROOT/'remotion/public'/f'focos-{d}.png'
    old_checks.append(dict(dia=d,contagem=len(fs),contador=c,recontagem_fontes_atuais=int(old_recount.get(d,0)),sha256_camada=digest(layer_old.read_bytes())))
assert all(x['contagem']==x['contador'] for x in old_checks)
audit=dict(satelite=SAT,nota_sensor='Seleção editorial de um sensor constante; não é a série oficial de satélite de referência. Contagens não equivalem a incêndios únicos.',periodo_inicio='2026-01-01T00:00:00-03:00',corte_observacoes_brasilia=cutoff.isoformat(),ultimo_registro_sensor_brasilia=selected.brasilia.max().isoformat(),dia15_parcial=True,fontes=[x[1] for x in files],registros_invalidos=invalid,duplicatas_removidas=duplicates,empates_divisa=boundary_duplicates,dias_sem_registro_nacional_sensor=missing,contagens_mensais={k:int(v) for k,v in monthly.items()},contagens_diarias={k:int(v) for k,v in counts.items()},total_regional=len(region),municipios_selecionados=chosen,municipios_vizinhos=neighbors.NM_MUN.tolist(),comparacoes_diarias=comparisons,hashes_camadas=layer_hashes,auditoria_edicao_anterior=old_checks,diagnostico_anterior='Contadores e dados de cada dia conferem; hashes das camadas diárias são distintos. A composição conservava os dias anteriores em cinza, provocando persistência espacial. Nova edição remove camadas anteriores.',limites_sha256={p:digest((ROOT/p).read_bytes()) for p in ['Limites_Amazonia_Legal_2024_shp.zip','Mun_Amazonia_Legal_2024_shp.zip']},limitacao='Presença de registros e arquivos não comprova completude de todas as passagens. Dia 15 parcial; outubro não comparável diretamente a meses completos.')
save(OUT/'auditoria.json',audit)
rank=[dict(code=c,name=n,count=int(v)) for (c,n),v in ranking.items() if c in chosen]
meta=dict(sensor=SAT,cutoff=cutoff.strftime('%d/%m/%Y às %Hh%M'),monthly=audit['contagens_mensais'],daily=audit['contagens_diarias'],rank=rank,total=len(region),nationalBox=svgbox(national),regionalBox=svgbox(regional),legalPath=pathgeom(merc_legal.geometry.union_all().simplify(2200)),allPaths=all_paths,paths=paths,labels=labels,extentNational=national,extentRegional=regional)
save(ROOT/'remotion/src/atm-dados.json',meta)
save(OUT/'mapa.json',meta)
print(json.dumps(dict(total=len(region),monthly=meta['monthly'],daily=meta['daily'],rank=rank,cutoff=meta['cutoff'],neighbors=neighbors.NM_MUN.tolist()),ensure_ascii=False,indent=2),flush=True)
