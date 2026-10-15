"""Check published artifacts, references, counts and isolation before deployment."""
import gzip
import json
from pathlib import Path
from config import WEB


def read(path):
    if path.suffix == '.gz':
        return json.loads(gzip.decompress(path.read_bytes()))
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    geo=read(WEB/'municipios_amazonia_legal_web.geojson')
    codes={f['properties']['codigo_ibge'] for f in geo['features']}
    history=read(WEB/'historico.json')
    series=read(WEB/history['arquivo'])
    annual={(code,year):value for code,year,value in series['anuais']}
    sums={key:0 for key in annual}
    for code,year,month,value in series['mensais']:
        assert code in codes and 1 <= month <= 12 and value >= 0
        sums[(code,year)]+=value
    assert sums==annual, 'Totais anuais e mensais divergentes'
    assert all(2003 <= y <= 2025 for y in history['anos_base'])
    assert len(annual)==len(codes)*len(history['anos_completos'])
    recent=read(WEB/'recentes.json')
    count=0
    for day in recent['dias']:
        rows=read(WEB/day['arquivo'])
        assert len(rows)==day['focos'], day['dia']
        assert len({tuple(r[:4]) for r in rows})==len(rows), 'Duplicatas operacionais'
        assert all(r[4] in codes and r[0].startswith(day['dia']) for r in rows)
        assert day['cobertura'] in ('completa','parcial','ausente')
        assert not rows or day['cobertura']!='ausente'
        count+=len(rows)
    print(f'Publicação válida: {len(codes)} municípios; {len(annual)} agregados anuais; {count} registros recentes.')


if __name__=='__main__':main()
