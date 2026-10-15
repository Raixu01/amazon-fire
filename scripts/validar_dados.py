"""Valida presença, rastreabilidade e esquema dos insumos antes da publicação."""
import csv, hashlib
from pathlib import Path
from config import RAW, AUDIT, INPE_ANNUAL, INPE_DAILY, IBGE_SOURCE, mkdirs
from util import csv_from_zip, find_col, now, sha256, save_json

def main():
 mkdirs(); rows=[]; missing=[]
 for year in range(2003,2026):
  files=list(RAW.glob(f'focos_br_ref_{year}.zip'))
  if not files: missing.append(year); continue
  f=files[0]; sample=csv_from_zip(f).head(2); cols=list(sample.columns)
  rows.append({'arquivo':f.name,'origem':INPE_ANNUAL+f.name,'adquirido_em':now(),'sha256':sha256(f),'latitude':find_col(cols,'lat','latitude') is not None,'longitude':find_col(cols,'lon','longitude','long') is not None,'data_hora':find_col(cols,'data_pas','datahora','data') is not None,'satelite':find_col(cols,'satelite','satellite') is not None,'id_foco':find_col(cols,'focoid','idbdq','id') is not None})
 for pattern,source in [('Mun_Amazonia_Legal_2024_shp.zip',IBGE_SOURCE),('Limites_Amazonia_Legal_2024_shp.zip',IBGE_SOURCE)]:
  for f in RAW.glob(pattern): rows.append({'arquivo':f.name,'origem':source,'adquirido_em':now(),'sha256':sha256(f)})
 readme=['# Inventário de dados brutos','','Gerado automaticamente por `scripts/validar_dados.py`. A data de aquisição abaixo é a data de inventário quando o metadado original não foi fornecido.','','| arquivo | origem | data de aquisição/inventário | SHA-256 |','|---|---|---|---|']
 for r in rows: readme.append(f"| {r['arquivo']} | {r['origem']} | {r['adquirido_em']} | `{r['sha256']}` |")
 if missing: readme += ['',f'**Anos ausentes:** {", ".join(map(str,missing))}. Não processe a série como completa antes de obtê-los.']
 (RAW/'dados-brutos').mkdir(exist_ok=True); (RAW/'dados-brutos'/'README.md').write_text('\n'.join(readme)+'\n',encoding='utf-8')
 report={'validado_em':now(),'anos_ausentes':missing,'arquivos':rows,'aprovado':not missing and all(r.get('latitude',True) and r.get('longitude',True) and r.get('data_hora',True) for r in rows)}
 save_json(report,AUDIT/'validacao_insumos.json'); print(report); return 0 if report['aprovado'] else 2
if __name__=='__main__': raise SystemExit(main())
