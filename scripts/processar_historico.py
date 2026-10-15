"""Normaliza e espacializa os arquivos anuais INPE, em partições ano/mês."""
import argparse, gzip, json
from pathlib import Path
import geopandas as gpd
import pandas as pd
from config import RAW, TERRITORY, FOCI, INDICATORS, AUDIT, WEB, MESH_VERSION, mkdirs
from util import csv_from_zip, find_col, now, save_json

OUT_COLUMNS = ['id_fonte','data_hora_utc','data_local','ano','mes','dia','latitude','longitude','satelite','municipio_ibge','origem_arquivo']

def write_web_points(part):
    """Publica o detalhe compactado, particionado para carregamento sob demanda."""
    if part.empty: return
    year, month = int(part.ano.iloc[0]), int(part.mes.iloc[0])
    dest = WEB / 'focos' / f'ano={year}' / f'mes={month:02d}'; dest.mkdir(parents=True, exist_ok=True)
    p=part[['id_fonte','data_hora_utc','latitude','longitude','satelite','municipio_ibge']].copy(); p['data_hora_utc']=p.data_hora_utc.astype(str)
    features=[{'type':'Feature','geometry':{'type':'Point','coordinates':[r.longitude,r.latitude]},'properties':{'id':r.id_fonte,'data_hora_utc':r.data_hora_utc,'satelite':r.satelite,'municipio_ibge':r.municipio_ibge}} for r in p.itertuples(index=False)]
    with gzip.open(dest/'focos.geojson.gz','wt',encoding='utf-8') as f: json.dump({'type':'FeatureCollection','features':features},f,separators=(',',':'))

def normalize(df, source):
    lat, lon = find_col(df.columns,'lat','latitude'), find_col(df.columns,'lon','longitude','long')
    dt = find_col(df.columns,'datahora','datahorautc','data_hora_gmt','data_pas','data')
    ident = find_col(df.columns,'focoid','idbdq','id','identificador')
    sat = find_col(df.columns,'satelite','satellite')
    if not all((lat,lon,dt)): raise ValueError(f'Colunas obrigatórias ausentes em {source}: {list(df.columns)}')
    x = pd.DataFrame({'id_fonte': df[ident].astype(str) if ident else '', 'data_hora_utc':pd.to_datetime(df[dt], errors='coerce', utc=True), 'latitude':pd.to_numeric(df[lat],errors='coerce'), 'longitude':pd.to_numeric(df[lon],errors='coerce'), 'satelite':df[sat].astype(str) if sat else 'referencia', 'origem_arquivo':source})
    x['data_local'] = x.data_hora_utc.dt.tz_convert('America/Manaus').dt.strftime('%Y-%m-%d %H:%M:%S%z')
    x['ano'],x['mes'],x['dia'] = x.data_hora_utc.dt.year,x.data_hora_utc.dt.month,x.data_hora_utc.dt.day
    return x

def process_file(path, municipalities):
    raw = csv_from_zip(path) if path.suffix.lower()=='.zip' else pd.read_csv(path,low_memory=False)
    x = normalize(raw,path.name); reason = pd.Series('',index=x.index)
    reason[x.data_hora_utc.isna()]='data_invalida'; reason[x.latitude.isna()|x.longitude.isna()]='coordenada_ausente'
    reason[(x.latitude.abs()>90)|(x.longitude.abs()>180)]='coordenada_fora_do_intervalo'
    rejected=x[reason.ne('')].copy(); rejected['motivo']=reason[reason.ne('')]
    x=x[reason.eq('')].copy(); pts=gpd.GeoDataFrame(x,geometry=gpd.points_from_xy(x.longitude,x.latitude),crs='EPSG:4326')
    joined=gpd.sjoin(pts, municipalities[['codigo_ibge','geometry']],predicate='within',how='inner').drop(columns=['index_right','geometry'])
    joined=joined.rename(columns={'codigo_ibge':'municipio_ibge'})[OUT_COLUMNS]
    # A assinatura remove republicações e duplicatas entre fontes.
    joined['_dedup']=joined.id_fonte.where(joined.id_fonte.ne(''), joined.data_hora_utc.astype(str)+'|'+joined.latitude.astype(str)+'|'+joined.longitude.astype(str)+'|'+joined.satelite)
    return joined.drop_duplicates('_dedup').drop(columns='_dedup'), rejected

def rebuild_indicators(municipalities):
    from publicar_historico import publish_history
    publish_history(municipalities)
    manifest=json.loads((WEB/'historico.json').read_text(encoding='utf-8'))
    with gzip.open(WEB/manifest['arquivo'],'rt',encoding='utf-8') as handle:
        series=json.load(handle)
    agg=pd.DataFrame(series['mensais'],columns=['municipio_ibge','ano','mes','focos'])
    area=municipalities[['codigo_ibge','area_intersecao_km2']].rename(columns={'codigo_ibge':'municipio_ibge'})
    agg=agg.merge(area,on='municipio_ibge',how='left'); agg['focos_por_1000_km2']=agg.focos/agg.area_intersecao_km2*1000
    agg['processado_em']=now(); agg['versao_malha']=MESH_VERSION
    annual=agg.groupby(['municipio_ibge','ano'],as_index=False).agg(focos=('focos','sum'),area_intersecao_km2=('area_intersecao_km2','first'))
    annual['focos_por_1000_km2']=annual.focos/annual.area_intersecao_km2*1000
    baseline=annual[annual.ano.isin(manifest['anos_base'])].groupby('municipio_ibge').focos.mean().rename('media_2003_2025'); annual=annual.merge(baseline,on='municipio_ibge',how='left')
    annual['anomalia_historica']=annual.focos-annual.media_2003_2025
    previous=annual[['municipio_ibge','ano','focos']].rename(columns={'focos':'focos_ano_anterior'})
    previous['ano']+=1
    annual=annual.merge(previous,on=['municipio_ibge','ano'],how='left')
    annual['variacao_anual_pct']=(annual.focos/annual.focos_ano_anterior.replace(0,float('nan'))-1)*100
    annual['ranking_regional']=annual.groupby('ano').focos.rank(method='min',ascending=False).astype(int)
    agg.to_parquet(INDICATORS/'agregacoes_municipais.parquet',index=False); annual.to_parquet(INDICATORS/'indicadores_municipais.parquet',index=False)
    records = annual.astype(object).where(annual.notna(), None).to_dict('records')
    save_json({'gerado_em':now(),'versao_malha':MESH_VERSION,'indicadores':records}, WEB/'indicadores_municipais.json')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--anos',default='2003:2025'); args=p.parse_args(); mkdirs()
    start,end=map(int,args.anos.split(':')); municipalities=gpd.read_file(TERRITORY/'municipios_amazonia_legal_analise.gpkg').to_crs('EPSG:4326')
    all_rej=[]; logs=[]
    for year in range(start,end+1):
        paths=list(RAW.glob(f'focos_br_ref_{year}.zip'))
        if not paths: logs.append({'ano':year,'status':'ausente'}); continue
        accepted,rejected=process_file(paths[0],municipalities); all_rej.append(rejected.assign(origem_arquivo=paths[0].name));
        for month,part in accepted.groupby('mes'):
            out=FOCI/f'ano={year}'/f'mes={int(month):02d}'; out.mkdir(parents=True,exist_ok=True); part.to_parquet(out/'focos.parquet',index=False)
            write_web_points(part)
        logs.append({'ano':year,'status':'ok','lidos':len(accepted)+len(rejected),'aceitos':len(accepted),'rejeitados':len(rejected)})
        print(logs[-1])
    if all_rej: pd.concat(all_rej,ignore_index=True).to_parquet(AUDIT/'rejeicoes_historico.parquet',index=False)
    save_json({'processado_em':now(),'arquivos':logs},AUDIT/'processamento_historico.json'); rebuild_indicators(municipalities)
if __name__=='__main__': main()
