"""Cria a camada municipal canônica usando o recorte oficial IBGE 2024."""
import json, sys, tempfile, zipfile
from pathlib import Path
import geopandas as gpd
from shapely.validation import make_valid
from config import RAW, TERRITORY, WEB, MESH_VERSION, mkdirs
from util import first_file, now

METRIC_CRS = 'EPSG:5880' # SIRGAS 2000 / Brasil Policônico

def unzip_shp(zip_path):
    target = Path(tempfile.mkdtemp(prefix='amazon_fire_'))
    with zipfile.ZipFile(zip_path) as z: z.extractall(target)
    return first_file(target, '*.shp')

def clean(gdf, label, fixes):
    bad = ~gdf.geometry.is_valid
    if bad.any():
        fixes.append({'camada': label, 'geometrias_corrigidas': int(bad.sum())})
        gdf.loc[bad, 'geometry'] = gdf.loc[bad, 'geometry'].apply(make_valid)
    return gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()

def main():
    mkdirs(); fixes = []
    mun_zip = first_file(RAW, 'Mun_Amazonia_Legal_2024_shp.zip')
    lim_zip = first_file(RAW, 'Limites_Amazonia_Legal_2024_shp.zip')
    mun, limit = gpd.read_file(unzip_shp(mun_zip)), gpd.read_file(unzip_shp(lim_zip))
    if mun.crs is None or limit.crs is None: raise ValueError('CRS ausente na malha IBGE')
    mun, limit = clean(mun, 'municipios', fixes), clean(limit, 'limite', fixes)
    code = next((x for x in mun.columns if x.upper() in ('CD_MUN','CD_MUN7','CODIGO_IBGE','GEOCODIGO')), None)
    name = next((x for x in mun.columns if x.upper() in ('NM_MUN','NOME','NOME_MUN')), None)
    uf = next((x for x in mun.columns if x.upper() in ('SIGLA_UF','SG_UF','UF')), None)
    if not code: raise ValueError(f'Código IBGE de 7 dígitos não encontrado: {list(mun.columns)}')
    mun = mun.to_crs(METRIC_CRS); limit = limit.to_crs(METRIC_CRS)
    # Um único polígono do limite reduz drasticamente o custo e evita duplicação
    # nas bordas entre as feições que compõem o arquivo oficial.
    official_limit = limit.union_all()
    clip = mun.copy()
    clip['geometry'] = clip.geometry.intersection(official_limit)
    clip = clip[clip.geometry.geom_type.isin(['Polygon', 'MultiPolygon']) & ~clip.geometry.is_empty].copy()
    clip['codigo_ibge'] = clip[code].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(7)
    clip['nome'] = clip[name].astype(str) if name else clip['codigo_ibge']
    clip['uf'] = clip[uf].astype(str) if uf else ''
    clip = clip.dissolve('codigo_ibge', as_index=False, aggfunc={'nome':'first','uf':'first'})
    clip['area_intersecao_km2'] = clip.area / 1_000_000
    if not clip.codigo_ibge.is_unique: raise ValueError('Códigos IBGE duplicados após dissolução')
    out = clip[['codigo_ibge','nome','uf','area_intersecao_km2','geometry']]
    out.to_file(TERRITORY / 'municipios_amazonia_legal_analise.gpkg', driver='GPKG')
    web = out.to_crs('EPSG:4326').copy(); web['geometry'] = web.geometry.simplify(0.002, preserve_topology=True)
    web.to_file(TERRITORY / 'municipios_amazonia_legal_web.geojson', driver='GeoJSON')
    (WEB / 'municipios_amazonia_legal_web.geojson').write_text((TERRITORY / 'municipios_amazonia_legal_web.geojson').read_text(encoding='utf-8'), encoding='utf-8')
    report = {'processado_em':now(), 'versao_malha':MESH_VERSION, 'municipios':len(out), 'area_intersecao_km2':float(out.area_intersecao_km2.sum()), 'area_limite_km2':float(limit.union_all().area/1e6), 'correcoes':fixes}
    (TERRITORY / 'relatorio_territorio.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
if __name__ == '__main__': main()
