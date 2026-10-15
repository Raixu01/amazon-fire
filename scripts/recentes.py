"""Fetch and publish operational detections independently of reference history."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import io
import json
import re
import geopandas as gpd
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import RAW, TERRITORY, AUDIT, WEB, PROCESSED, INPE_DAILY, INPE_10MIN, mkdirs
from processar_historico import process_file, normalize
from publicar_historico import atomic_json, publish_blob
from util import now, sha256

CACHE = PROCESSED / 'cache_recentes'
PATTERN = re.compile(r'focos_(?:diario_br_\d{8}|10min_\d{8}_\d{4})\.csv')


def session():
    client = requests.Session()
    client.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))
    return client


def file_date(name):
    return datetime.strptime(re.search(r'(\d{8})', name).group(1), '%Y%m%d').replace(tzinfo=timezone.utc)


def validate_csv(content, name):
    frame = pd.read_csv(io.BytesIO(content), low_memory=False)
    normalized = normalize(frame, name)
    if normalized.data_hora_utc.isna().any() or normalized.latitude.isna().any() or normalized.longitude.isna().any():
        raise ValueError('Datas ou coordenadas inválidas')
    if (normalized.latitude.abs() > 90).any() or (normalized.longitude.abs() > 180).any():
        raise ValueError('Coordenadas fora do intervalo')
    if len(normalized) and normalized.satelite.eq('referencia').any():
        raise ValueError('Satélite ausente na fonte operacional')


def fetch_one(item):
    """Revalidate cached sources; invalid responses never replace a valid file."""
    base, name = item
    dest = CACHE / name
    meta_path = CACHE / (name + '.http.json')
    metadata = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    headers = {}
    if dest.exists():
        if metadata.get('etag'): headers['If-None-Match'] = metadata['etag']
        if metadata.get('modified'): headers['If-Modified-Since'] = metadata['modified']
    try:
        with session() as client:
            response = client.get(base + name, headers=headers, timeout=(15, 90))
        if response.status_code == 304 and dest.exists():
            return dest, None
        response.raise_for_status()
        validate_csv(response.content, name)
        tmp = dest.with_suffix('.tmp')
        tmp.write_bytes(response.content)
        tmp.replace(dest)
        atomic_json(meta_path, {'etag': response.headers.get('ETag'), 'modified': response.headers.get('Last-Modified')})
        return dest, None
    except Exception as exc:
        return (dest if dest.exists() else None), f'{name}: {exc}'


def deduplicate(frame):
    # 10-minute files lack IDs. Satellite distinguishes coincident observations.
    return frame.sort_values('origem_arquivo', ascending=False).drop_duplicates(
        ['data_hora_utc', 'latitude', 'longitude', 'satelite'])


def coverage_for_day(day, paths, current, failed_names=()):
    stamp = day.strftime('%Y%m%d')
    daily = f'focos_diario_br_{stamp}.csv'
    names = {p.name for p in paths} - set(failed_names)
    intervals = {n for n in names if n.startswith(f'focos_10min_{stamp}_')}
    if day.date() >= current.date():
        return 'parcial' if daily in names or intervals else 'ausente'
    # File timestamps describe publication batches, not exact observation windows.
    return 'completa' if daily in names else ('parcial' if intervals else 'ausente')


def run(local=False, days=30):
    mkdirs()
    CACHE.mkdir(parents=True, exist_ok=True)
    current = datetime.now(timezone.utc)
    start = (current - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    issues, files, failed_names = [], [], set()
    queried = False
    if local:
        files = sorted(p for p in RAW.glob('focos_*.csv') if PATTERN.fullmatch(p.name) and start <= file_date(p.name) <= current)
    else:
        tasks = []
        catalog_ok = 0
        for base in (INPE_DAILY, INPE_10MIN):
            try:
                with session() as client:
                    response = client.get(base, timeout=(15, 60))
                response.raise_for_status()
                names = set(PATTERN.findall(response.text))
                if not names: raise ValueError('Catálogo sem arquivos reconhecidos')
                catalog_ok += 1
                cutoff = start if base == INPE_DAILY else current.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
                tasks.extend((base, n) for n in names if cutoff <= file_date(n) <= current)
            except Exception as exc:
                issues.append(f'Catálogo {base}: {exc}')
        with ThreadPoolExecutor(max_workers=6) as pool:
            for path, error in pool.map(fetch_one, sorted(tasks)):
                if path: files.append(path)
                if error:
                    issues.append(error)
                    failed_names.add(error.split(':', 1)[0])
        queried = catalog_ok == 2 and not issues
        # Existing local inputs are a fallback, with downloaded/revalidated files taking precedence.
        available = {p.name:p for p in RAW.glob('*.csv') if PATTERN.fullmatch(p.name) and start <= file_date(p.name) <= current}
        available.update({p.name:p for p in CACHE.glob('*.csv') if PATTERN.fullmatch(p.name) and start <= file_date(p.name) <= current})
        files = sorted(available.values())
    municipalities = gpd.read_file(TERRITORY / 'municipios_amazonia_legal_analise.gpkg').to_crs('EPSG:4326')
    accepted, valid_files = [], []
    processed = CACHE / 'espacializados'
    processed.mkdir(exist_ok=True)
    mesh_hash = sha256(TERRITORY / 'municipios_amazonia_legal_analise.gpkg')[:12]
    for path in files:
        try:
            digest = sha256(path)
            cached = processed / f'{digest}-{mesh_hash}.parquet'
            if cached.exists():
                frame = pd.read_parquet(cached)
            else:
                validate_csv(path.read_bytes(), path.name)
                frame, rejected = process_file(path, municipalities)
                if len(rejected): raise ValueError(f'{len(rejected)} registros inválidos')
                frame.to_parquet(cached, index=False)
            accepted.append(frame)
            valid_files.append(path)
        except Exception as exc:
            issues.append(f'{path.name}: {exc}')
            failed_names.add(path.name)
            queried = False
    old_path = WEB / 'recentes.json'
    old = json.loads(old_path.read_text(encoding='utf-8')) if old_path.exists() else {}
    timestamp = now()
    if issues and old.get('dias'):
        # Keep the entire last validated snapshot on collection failure.
        status = dict(old, tentativa_em=timestamp, erros=issues, consulta_ok=False)
        atomic_json(old_path, status)
        atomic_json(AUDIT / 'ultima_atualizacao.json', status)
        raise RuntimeError('Coleta incompleta; última versão publicada preservada.')
    if not accepted:
        atomic_json(old_path, dict(old, tentativa_em=timestamp, erros=issues or ['Nenhum arquivo disponível'], consulta_ok=False))
        raise RuntimeError('Nenhum arquivo válido; dados anteriores preservados.')
    frame = deduplicate(pd.concat(accepted, ignore_index=True))
    # Empty CSVs may carry an object dtype after concat (pandas 3).
    frame['data_hora_utc'] = pd.to_datetime(frame.data_hora_utc, utc=True)
    frame = frame[(frame.data_hora_utc >= start) & (frame.data_hora_utc <= current)].copy()
    frame['utc_day'] = frame.data_hora_utc.dt.strftime('%Y-%m-%d')
    groups = {day: rows for day, rows in frame.groupby('utc_day')}
    partitions = []
    for day in pd.date_range(start, current, freq='D'):
        label = day.strftime('%Y-%m-%d')
        rows = groups.get(label)
        records = [] if rows is None else [[r.data_hora_utc.isoformat(), float(r.latitude), float(r.longitude), str(r.satelite), str(r.municipio_ibge)] for r in rows.itertuples()]
        coverage = coverage_for_day(day, valid_files, current, failed_names)
        if records and coverage == 'ausente':
            coverage = 'parcial'
        filename = publish_blob(WEB / 'recentes', label, records)
        partitions.append({'dia': label, 'arquivo': f'recentes/{filename}', 'focos': len(records), 'cobertura': coverage})
    manifest = {
        'gerado_em': timestamp, 'tentativa_em': timestamp,
        'ultima_consulta_ok': timestamp if queried else old.get('ultima_consulta_ok'),
        'consulta_ok': queried, 'origem': 'arquivos locais' if local else 'INPE',
        'observacao_mais_recente': frame.data_hora_utc.max().isoformat() if len(frame) else None,
        'inicio_disponivel': start.isoformat(), 'fim_disponivel': current.isoformat(),
        'colunas': ['data_hora_utc', 'latitude', 'longitude', 'satelite', 'municipio_ibge'],
        'dias': partitions, 'erros': issues,
    }
    atomic_json(old_path, manifest)
    atomic_json(AUDIT / 'ultima_atualizacao.json', manifest)
    print(f'Recentes: {len(frame)} focos, {len(valid_files)} arquivos, {len(issues)} falhas; consulta online: {queried}.')
    if issues and not local:
        raise RuntimeError('Publicação com cobertura incompleta; consulte a auditoria.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--local', action='store_true', help='Usar arquivos locais sem afirmar atualização online.')
    parser.add_argument('--dias', type=int, default=30)
    args = parser.parse_args()
    run(args.local, args.dias)


if __name__ == '__main__':
    main()
