"""Portable unit and real media checks; no private media or host needed."""
from contextlib import contextmanager
import importlib.metadata
import io
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
import zlib

from foresight import check, inventory
from foresight.cards.schema import Mapping
from foresight.cards.service import Cards
from foresight.cards import learning
from foresight.errors import Fault
from foresight.review import applicability, crystal_ball, reports
from foresight import process
from foresight.cli import main
from foresight.hermes import register


def still():
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>2I5B', 32, 32, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress((b'\x00'+b'\x10\x80\xf0'*32)*32)) + chunk(b'IEND', b'')


def audio():
    output = io.BytesIO()
    with wave.open(output, 'wb') as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(44100)
        target.writeframes(struct.pack('<44100h', *[1000 if n % 200 < 100 else -1000 for n in range(44100)]))
    return output.getvalue()


def mapping(**changes):
    value = dict(executable='ffmpeg', operation='Tiny blue MP4', arguments=['-v','error','-f','lavfi','-i',
        'color=c=blue:s=160x90:d=0.6','-c:v','libx264','-pix_fmt','yuv420p','{output}'],
        format='mp4', version='local', cost='zero', shape='160x90', seconds=0.6)
    return dict(value, **changes)


@contextmanager
def checker_available():
    """Use installed pin where available, otherwise explicit sibling-source fixture.

    Source fallback is test-only; the production adapter still rejects PYTHONPATH.
    """
    try:
        installed = importlib.metadata.version('crystal-ball-media') == '1.2.0'
    except importlib.metadata.PackageNotFoundError:
        installed = False
    if installed:
        yield
        return
    sibling = Path(__file__).resolve().parents[2] / 'crystal-ball'
    if not (sibling / 'crystal_ball/core.py').is_file():
        raise unittest.SkipTest('Pinned installed checker or sibling source fixture required')
    original = process.call
    def launch(argv, *, cwd, env, timeout):
        return original(argv, cwd=cwd, env=dict(env, PYTHONPATH=str(sibling)), timeout=timeout)
    with patch.object(crystal_ball.importlib.metadata, 'version', return_value='1.2.0'), patch.object(process, 'call', side_effect=launch):
        yield


class CoreTests(unittest.TestCase):
    def test_passive_inventory_scope(self):
        which = lambda name: '/tools/' + name
        cached = dict(profile='one', session='a', items=[dict(name='Known', kind='tool'), dict(name='../bad', kind='tool')])
        self.assertEqual(len(inventory('one', 'a', cached=cached, which=which)['items']), 7)
        self.assertEqual(len(inventory('two', 'a', cached=cached, which=which)['items']), 6)
        self.assertEqual(inventory('one', '', cached=cached, which=which)['items'], [])

    def test_mapping_rejects_arbitrary_shell(self):
        for changes in [dict(arguments=['sh', '{output}']), dict(executable='python'), dict(seconds=2), dict(extra=True)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                Mapping.model_validate(mapping(**changes))

    def test_summary_fail_and_omissions(self):
        missing = dict(id='audio', status='SKIP', summary='Not checked: no audio', skip_reason='not_applicable')
        self.assertEqual(applicability.summarize([dict(id='decode', status='FAIL'), missing], {}, None)['status'], 'FAIL')
        result = applicability.summarize([dict(id='decode', status='PASS'), missing], {}, 'image')
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['not_checked_details'][0], {k: missing[k] for k in ('id', 'summary', 'skip_reason')})
        self.assertNotIn('status', applicability.summarize([missing], {}, None))

    def test_options_invalid_and_effective(self):
        with self.assertRaises(ValueError):
            applicability.settings(mode='maybe')
        options = applicability.settings(platform='youtube')
        self.assertEqual(applicability.effective('image', options)['platform'], 'custom')
        self.assertEqual(applicability.effective('video', options)['platform'], 'youtube')
        self.assertNotEqual(applicability.identity('image', options, '1'), applicability.identity('image', options, '2'))

    def test_wrong_checker_and_missing_binary(self):
        with patch.object(crystal_ball.importlib.metadata, 'version', return_value='old'):
            self.assertNotIn('status', crystal_ball.run(still(), '.png'))
        with patch.object(crystal_ball.importlib.metadata, 'version', return_value='1.2.0'), patch.object(crystal_ball.shutil, 'which', return_value=None):
            self.assertNotIn('status', crystal_ball.run(still(), '.png'))

    def test_timeout_not_pass(self):
        with patch.object(crystal_ball.importlib.metadata, 'version', return_value='1.2.0'), patch.object(process, 'call', side_effect=subprocess.TimeoutExpired('ffprobe', 1)):
            self.assertNotIn('status', crystal_ball.run(still(), '.png'))

    def test_report_traversal_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ['../escape', '/escape', 'C:\\escape', '..\\escape']:
                with self.assertRaises(ValueError):
                    reports.retain(dict(assets={name:b'x'}), root/'bad', digest='x', options=applicability.settings())
            result = reports.retain(dict(status='PASS', media_kind='image', assets={'a/full.json':b'{}'}), root/'good', digest='x', options=applicability.settings())
            self.assertEqual(result['input_sha256'], 'x')
            self.assertEqual((root/'good/assets/a/full.json').read_bytes(), b'{}')
            with self.assertRaises(FileExistsError):
                reports.retain({}, root/'good', digest='x', options=applicability.settings())

    def test_process_timeout_cleanup(self):
        import os
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(subprocess.TimeoutExpired):
                process.call([sys.executable, '-c', 'import time; time.sleep(10)'], cwd=temporary, env=os.environ.copy(), timeout=0.1)

    def test_cli_inventory_and_templates(self):
        with patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(main(['inventory']), 0)
            self.assertIn('items', json.loads(out.getvalue()))
        with patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(main(['card', 'templates']), 0)
            self.assertTrue(all(x['status'] == 'Untested' for x in json.loads(out.getvalue())))

    def test_cli_error_is_nonzero_and_safe(self):
        with patch('sys.stderr', new_callable=io.StringIO) as out:
            self.assertEqual(main(['check', 'missing-private-file.png']), 2)
            self.assertNotIn('missing-private', out.getvalue())

    def test_plugin_registration_and_dispatch(self):
        class Context:
            def register_tool(self, **kw):
                self.tool = kw
                return 'handle'
        ctx = Context()
        self.assertEqual(register(ctx), 'handle')
        self.assertEqual(ctx.tool['name'], 'foresight')
        self.assertIn('templates', json.loads(ctx.tool['handler'](dict(action='card'))))
        self.assertIn('error', json.loads(ctx.tool['handler'](dict(action='invalid'))))
        with patch('foresight.hermes.check', return_value=dict(status='PASS')) as invoke:
            result = json.loads(ctx.tool['handler'](dict(action='check', file='fixture.png')))
            self.assertEqual(result['status'], 'PASS')
            invoke.assert_called_once()


class CardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.cards = Cards(self.temporary.name)
        self.card = self.cards.prepare('Tiny video', mapping())

    def test_prepare_read_and_confirmation(self):
        self.assertEqual(self.cards.read(self.card['id'])['status'], 'Untested')
        self.assertEqual(len(self.cards.read()), 1)
        with self.assertRaises(Fault):
            self.cards.test(self.card['id'], command='one')

    def test_unknown_cost_never_executes(self):
        other = self.cards.prepare('Unknown cost', mapping(cost='unknown'))
        with patch.object(learning, 'execute') as execute, self.assertRaises(Fault):
            self.cards.test(other['id'], command='unknown', confirmed=True)
        execute.assert_not_called()

    def test_unknown_delivery_blocks_all_replay(self):
        with patch.object(learning, 'fingerprint', return_value={}), patch.object(learning, 'execute', side_effect=TimeoutError()) as execute:
            self.assertEqual(self.cards.test(self.card['id'], command='once', confirmed=True)['status'], 'Testing')
            self.assertEqual(self.cards.test(self.card['id'], command='once', confirmed=True)['status'], 'Testing')
            with self.assertRaises(Fault):
                self.cards.test(self.card['id'], command='different', confirmed=True)
            self.assertEqual(execute.call_count, 1)
        reopened = Cards(self.temporary.name)
        self.assertEqual(reopened.test(self.card['id'], command='once', confirmed=True)['status'], 'Testing')

    def test_command_conflict(self):
        other = self.cards.prepare('Second', mapping())
        with patch.object(learning, 'fingerprint', return_value={}), patch.object(learning, 'execute', side_effect=TimeoutError()):
            self.cards.test(self.card['id'], command='once', confirmed=True)
        with self.assertRaises(Fault):
            self.cards.test(other['id'], command='once', confirmed=True)

    def test_two_confirmed_failures_need_retest(self):
        with patch.object(learning, 'fingerprint', return_value={}), patch.object(learning, 'execute', side_effect=Fault('DIRECTOR_CONFIRMED_OUTPUT_FAILURE')):
            self.assertEqual(self.cards.test(self.card['id'], command='one', confirmed=True)['status'], 'Untested')
            result = self.cards.test(self.card['id'], command='two', confirmed=True)
            self.assertEqual(result['status'], 'Needs re-test')
            self.assertEqual(result['failures'], 2)

    def test_unchecked_never_qualifies(self):
        with patch.object(learning, 'fingerprint', return_value={}), patch.object(learning, 'execute', return_value=(b'bytes', {})), patch.object(crystal_ball, 'run', return_value=dict(reason='Unavailable')):
            result = self.cards.test(self.card['id'], command='one', confirmed=True)
            self.assertEqual(result['status'], 'Untested')
            self.assertEqual(result['evidence'][0]['check'], 'Not checked')


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
class RealMediaTests(unittest.TestCase):
    def test_image_audio_and_disguised_bytes(self):
        with checker_available():
            for suffix, kind, data in [('.png','image',still()), ('.wav','audio-only',audio()), ('.mp4','image',still())]:
                with self.subTest(kind=kind, suffix=suffix):
                    result = crystal_ball.run(data, suffix, platform='youtube')
                    self.assertIn(result.get('status'), ('PASS','WARN'), result)
                    self.assertEqual(result['media_kind'], kind)
                    doc = next(json.loads(body) for name, body in result['assets'].items() if name.endswith('/full.json'))
                    self.assertEqual(doc['platform'], 'custom')
                    self.assertTrue(result['not_checked_details'])

    def test_explicit_shape_failure(self):
        with checker_available():
            self.assertEqual(crystal_ball.run(still(), '.png', shape='9:16')['status'], 'FAIL')

    def test_api_retains_real_assets(self):
        with tempfile.TemporaryDirectory() as temporary, checker_available():
            path = Path(temporary)/'fixture.png'
            path.write_bytes(still())
            result = check(path, report_dir=Path(temporary)/'report')
            self.assertIn(result['status'], ('PASS', 'WARN'))
            self.assertTrue(list((Path(temporary)/'report/assets').rglob('full.json')))
            with patch('sys.stdout', new_callable=io.StringIO) as out:
                self.assertEqual(main(['check', str(path), '--report-dir', str(Path(temporary)/'cli-report')]), 0)
                self.assertIn(json.loads(out.getvalue())['status'], ('PASS', 'WARN'))

    def test_real_confirmed_mp4_once(self):
        with tempfile.TemporaryDirectory() as temporary, checker_available():
            cards = Cards(temporary)
            card = cards.prepare('Tiny MP4', mapping())
            result = cards.test(card['id'], command='confirmed-once', confirmed=True)
            self.assertEqual(result['status'], 'Tested', result)
            evidence = result['evidence'][0]
            self.assertGreater(Path(evidence['output']).stat().st_size, 0)
            self.assertEqual(cards.test(card['id'], command='confirmed-once', confirmed=True), result)
            self.assertEqual(Cards(temporary).read(card['id']), result)


if __name__ == '__main__':
    unittest.main()
