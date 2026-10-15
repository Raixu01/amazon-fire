import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pandas as pd
import recentes
from publicar_historico import build_history, publish_blob, atomic_json


class DataTests(unittest.TestCase):
    def test_empty_feed_is_valid_but_bad_schema_is_not(self):
        recentes.validate_csv(b'lat,lon,satelite,data\n', 'focos_10min_20261015_0000.csv')
        with self.assertRaises(ValueError):
            recentes.validate_csv(b'<html>error</html>', 'feed.csv')
        with self.assertRaises(ValueError):
            recentes.validate_csv(b'lat,lon,satelite,data\n999,0,GOES,2026-10-15\n', 'feed.csv')

    def test_dedup_ignores_source_id_but_preserves_other_satellites(self):
        rows = pd.DataFrame([
            ['2026-10-15', -2., -54., 'GOES', 'daily', 'abc'],
            ['2026-10-15', -2., -54., 'GOES', '10min', ''],
            ['2026-10-15', -2., -54., 'AQUA', 'daily', 'def'],
        ], columns=['data_hora_utc','latitude','longitude','satelite','origem_arquivo','id_fonte'])
        self.assertEqual(len(recentes.deduplicate(rows)), 2)

    def test_missing_day_is_not_zero_coverage(self):
        day = datetime(2026, 10, 14, tzinfo=timezone.utc)
        now = datetime(2026, 10, 15, 12, tzinfo=timezone.utc)
        paths = [Path('focos_diario_br_20261014.csv')]
        self.assertEqual(recentes.coverage_for_day(day, [], now), 'ausente')
        self.assertEqual(recentes.coverage_for_day(day, paths, now), 'completa')
        self.assertEqual(recentes.coverage_for_day(day, paths, now, [paths[0].name]), 'ausente')
        self.assertEqual(recentes.coverage_for_day(now, [Path('focos_diario_br_20261015.csv')], now), 'parcial')

    def test_history_month_and_year_agree_and_exclude_recent(self):
        points = pd.DataFrame([['A',2024,1],['A',2024,1],['A',2024,2],['A',2026,1]],columns=['municipio_ibge','ano','mes'])
        data = build_history(points, ['A','B'], [2024,2025])
        self.assertEqual([r for r in data['anuais'] if r[:2]==['A',2024]][0][2],3)
        self.assertEqual(sum(r[3] for r in data['mensais']),3)
        self.assertEqual([r for r in data['mensais'] if r[:3]==['A',2024,1]][0][3],2)
        self.assertEqual(len(data['mensais']),48)
        self.assertEqual([r for r in data['anuais'] if r[:2]==['B',2025]][0][2],0)

    def test_invalid_download_preserves_cache(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(recentes,'CACHE',Path(directory)):
            name='focos_diario_br_20261014.csv'
            path=Path(directory)/name
            old=b'lat,lon,satelite,data\n'
            path.write_bytes(old)
            response=MagicMock(status_code=200, content=b'<html>invalid</html>')
            client=MagicMock();client.__enter__.return_value.get.return_value=response
            with patch.object(recentes,'session',return_value=client):
                cached,error=recentes.fetch_one(('https://example.test/',name))
            self.assertIsNotNone(error)
            self.assertEqual(cached,path)
            self.assertEqual(path.read_bytes(),old)

    def test_conditional_fetch(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(recentes,'CACHE',Path(directory)):
            name='focos_diario_br_20261014.csv'
            path=Path(directory)/name;path.write_bytes(b'lat,lon,satelite,data\n')
            atomic_json(Path(directory)/(name+'.http.json'), {'etag':'abc'})
            response=MagicMock(status_code=304)
            client=MagicMock();client.__enter__.return_value.get.return_value=response
            with patch.object(recentes,'session',return_value=client):
                cached,error=recentes.fetch_one(('https://example.test/',name))
            self.assertIsNone(error)
            self.assertEqual(client.__enter__.return_value.get.call_args.kwargs['headers'],{'If-None-Match':'abc'})

    def test_immutable_blobs_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            a=publish_blob(root,'day',[[1]])
            self.assertEqual(a,publish_blob(root,'day',[[1]]))
            self.assertNotEqual(a,publish_blob(root,'day',[[2]]))
            with self.assertRaises(ValueError):publish_blob(root,'bad',[float('nan')])

    def test_collection_outage_preserves_published_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            old={'dias':[{'dia':'2026-10-14','arquivo':'keep.json.gz','cobertura':'completa'}], 'ultima_consulta_ok':'2026-10-14T00:00:00Z'}
            atomic_json(root/'recentes.json',old)
            client=MagicMock();client.__enter__.return_value.get.side_effect=RuntimeError('unavailable')
            with patch.multiple(recentes,WEB=root,AUDIT=root,RAW=root,CACHE=root/'cache',mkdirs=lambda:None), patch.object(recentes,'session',return_value=client), patch.object(recentes.gpd,'read_file',return_value=MagicMock()), patch.object(recentes,'sha256',return_value='mesh'):
                with self.assertRaisesRegex(RuntimeError,'preservada'):
                    recentes.run()
            result=json.loads((root/'recentes.json').read_text(encoding='utf-8'))
            self.assertEqual(result['dias'],old['dias'])
            self.assertEqual(result['ultima_consulta_ok'],old['ultima_consulta_ok'])
            self.assertFalse(result['consulta_ok'])


if __name__=='__main__':unittest.main()
