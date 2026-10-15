"""Publish the reference series independently from operational detections."""
import gzip
import hashlib
import json
import pandas as pd
import geopandas as gpd
from config import FOCI, AUDIT, WEB, TERRITORY, MESH_VERSION
from util import now


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')), encoding='utf-8')
    temp.replace(path)


def publish_blob(directory, stem, value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
    digest = hashlib.sha256(raw).hexdigest()[:16]
    directory.mkdir(parents=True, exist_ok=True)
    name = f'{stem}-{digest}.json.gz'
    path = directory / name
    if not path.exists():
        tmp = path.with_suffix('.tmp')
        tmp.write_bytes(gzip.compress(raw, mtime=0))
        tmp.replace(path)
    return name


def build_history(points, codes, years):
    """Zero-fill only years whose annual source has been validated in full."""
    counts = points.groupby(['municipio_ibge', 'ano', 'mes']).size()
    index = pd.MultiIndex.from_product([codes, years, range(1, 13)], names=counts.index.names)
    monthly = counts.reindex(index, fill_value=0).rename('focos').reset_index()
    annual = monthly.groupby(['municipio_ibge', 'ano'], as_index=False).focos.sum()
    return {'anuais': annual.values.tolist(), 'mensais': monthly.values.tolist()}


def publish_history(municipalities=None):
    if municipalities is None:
        municipalities = gpd.read_file(TERRITORY / 'municipios_amazonia_legal_analise.gpkg')
    audit = json.loads((AUDIT / 'processamento_historico.json').read_text(encoding='utf-8'))
    years = sorted(x['ano'] for x in audit['arquivos'] if x['status'] == 'ok' and x.get('rejeitados', 0) == 0 and x['ano'] < pd.Timestamp.now(tz='UTC').year)
    frames = []
    for year in years:
        files = sorted((FOCI / f'ano={year}').glob('mes=*/focos.parquet'))
        if not files:
            raise ValueError(f'Série histórica ausente: {year}')
        frames.extend(pd.read_parquet(p, columns=['municipio_ibge', 'ano', 'mes']) for p in files)
    if not frames:
        raise ValueError('Nenhum ano histórico completo validado')
    points = pd.concat(frames, ignore_index=True)
    points['municipio_ibge'] = points.municipio_ibge.astype(str)
    payload = build_history(points, municipalities.codigo_ibge.astype(str).tolist(), years)
    filename = publish_blob(WEB / 'historico', 'serie', payload)
    atomic_json(WEB / 'historico.json', {
        'gerado_em': now(), 'versao_malha': MESH_VERSION, 'anos_completos': years,
        'anos_base': [y for y in years if 2003 <= y <= 2025],
        'fonte': 'INPE — satélite de referência', 'arquivo': f'historico/{filename}',
        'colunas_anuais': ['municipio_ibge', 'ano', 'focos'],
        'colunas_mensais': ['municipio_ibge', 'ano', 'mes', 'focos'],
    })
    print(f'Histórico: {len(years)} anos completos, {len(payload["mensais"])} agregações mensais.')


if __name__ == '__main__':
    publish_history()
