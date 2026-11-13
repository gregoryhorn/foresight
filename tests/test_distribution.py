"""Packaging, privacy and Windows regressions beyond media behavior."""
import importlib.util
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch
from foresight.cards.service import Cards, canonical
from foresight.review import crystal_ball
from test_foresight import checker_available, mapping, still

ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_metadata_exact_pin(self):
        project = tomllib.loads((ROOT/'pyproject.toml').read_text())['project']
        self.assertEqual(project['name'], 'foresight-media')
        self.assertEqual(project['version'], '0.1.0')
        self.assertEqual(project['requires-python'], '>=3.11')
        pin = next(d for d in project['dependencies'] if d.startswith('crystal-ball-media @ '))
        self.assertIn('/v1.2.0/crystal_ball_media-1.2.0-py3-none-any.whl#sha256=', pin)
        self.assertTrue(pin.endswith('e36da1fe33fd91b3971297682840ee3e893a5d8e7465ee9158d4c632a4fe7338'))

    def test_privacy_scanner_rejects_private_data(self):
        spec = importlib.util.spec_from_file_location('privacy', ROOT/'scripts/privacy_scan.py')
        scanner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scanner)
        self.assertTrue(scanner.scan_text('/'+'home'+'/'+'someone/private.txt'))
        self.assertTrue(scanner.scan_text('contact'+'@'+'private.invalid'))
        self.assertTrue(scanner.scan_text('sk-'+'a'*30))
        self.assertFalse(scanner.scan_text('~/Media/example.mp4 contact@example.com'))

    def test_database_connection_closes_and_fingerprint_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            cards = Cards(temporary)
            card = cards.prepare('Synthetic', mapping())
            card.update(status='Tested', fingerprint=dict(path='old', sha256='old'))
            with cards.connect() as db:
                db.execute('UPDATE cards SET body=? WHERE id=?', (canonical(card), card['id']))
            with self.assertRaises(Exception):
                db.execute('SELECT 1')
            with patch('foresight.cards.learning.fingerprint', return_value=dict(path='new', sha256='new')):
                self.assertEqual(cards.read(card['id'])['status'], 'Needs re-test')

    def test_windows_asset_names_and_home_are_portable(self):
        # The real adapter must work without inheriting the user's home/settings.
        import shutil
        if not all(shutil.which(name) for name in ('ffmpeg', 'ffprobe')):
            self.skipTest('FFmpeg required')
        with checker_available():
            result = crystal_ball.run(still(), '.png')
        self.assertIn(result.get('status'), ('PASS', 'WARN'))
        self.assertTrue(any(name.endswith('/full.json') for name in result['assets']))
        self.assertTrue(all('\\' not in name for name in result['assets']))
        for name, body in result['assets'].items():
            if name.endswith(('.json', '.md', '.html')):
                self.assertNotIn(b'director-check-', body)
