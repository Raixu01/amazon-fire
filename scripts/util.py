import hashlib
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

def now(): return datetime.now(UTC).isoformat()
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()
def first_file(root, pattern):
    files = list(Path(root).rglob(pattern))
    if not files: raise FileNotFoundError(f'Nenhum {pattern} em {root}')
    return files[0]
def csv_from_zip(path):
    with zipfile.ZipFile(path) as z:
        names = [x for x in z.namelist() if x.lower().endswith('.csv')]
        if not names: raise ValueError(f'ZIP sem CSV: {path.name}')
        with z.open(names[0]) as f:
            return pd.read_csv(f, low_memory=False)
def find_col(columns, *choices):
    norm = {re.sub(r'[^a-z0-9]', '', str(c).lower()): c for c in columns}
    for c in choices:
        key = re.sub(r'[^a-z0-9]', '', str(c).lower())
        if key in norm: return norm[key]
    return None
def save_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
