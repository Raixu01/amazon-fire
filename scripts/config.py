from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Os dados já baixados podem permanecer na raiz. Altere para dados-brutos/ se desejar.
RAW = Path(__import__('os').environ.get('AMAZON_FIRE_RAW_DIR', ROOT))
PROCESSED = ROOT / 'dados-processados'
TERRITORY = PROCESSED / 'territorio'
INDICATORS = PROCESSED / 'indicadores'
FOCI = PROCESSED / 'focos'
AUDIT = PROCESSED / 'auditoria'
WEB = ROOT / 'docs' / 'data'
MESH_VERSION = 'IBGE-Amazonia-Legal-2024'
INPE_ANNUAL = 'https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/Brasil_sat_ref/'
INPE_10MIN = 'https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/10min/'
INPE_DAILY = 'https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/'
IBGE_SOURCE = 'https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/amazonia_legal/2024/'

def mkdirs():
    for p in (TERRITORY, INDICATORS, FOCI, AUDIT, WEB):
        p.mkdir(parents=True, exist_ok=True)
