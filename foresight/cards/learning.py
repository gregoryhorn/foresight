"""Bounded local qualification primitives. Persistence/consent belong to the caller."""
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
from foresight.errors import Fault
from foresight.process import call
from .validation import inspect_media

STARTERS = ('FFmpeg assembly', 'Hermes image', 'Hermes voice', 'Hermes video', 'ComfyUI', 'whisper', 'Crystal Ball')


def fingerprint(mapping):
    executable = shutil.which(mapping['executable'])
    if not executable:
        raise Fault('DIRECTOR_TOOL_UNAVAILABLE', 409)
    path = Path(executable).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def execute(mapping, pin, *, inspector=None):
    with tempfile.TemporaryDirectory(prefix='director-tiny-test-') as temporary:
        root = Path(temporary)
        output = root / ('output.'+mapping['format'])
        argv = [pin['path'], *[str(output) if token == '{output}' else token for token in mapping['arguments']]]
        env = {key: os.environ[key] for key in ('PATH', 'SYSTEMROOT', 'WINDIR', 'TMPDIR', 'TMP', 'TEMP') if key in os.environ}
        env.update(HOME=str(root), USERPROFILE=str(root), LOCALAPPDATA=str(root / 'AppData' / 'Local'),
                   APPDATA=str(root / 'AppData' / 'Roaming'), MAGICK_THREAD_LIMIT='1', OMP_NUM_THREADS='1',
                   MAGICK_MEMORY_LIMIT='64MiB', MAGICK_MAP_LIMIT='64MiB', MAGICK_DISK_LIMIT='64MiB')
        result = call(argv, cwd=root, env=env, timeout=15)
        if result.returncode != 0 or not output.is_file() or output.is_symlink() or output.stat().st_size > 1024*1024:
            raise Fault('DIRECTOR_CONFIRMED_TOOL_FAILURE', 409)
        data = output.read_bytes()
        try:
            facts = (inspector or inspect_media)(data, mapping['format'])
        except Fault:
            raise Fault('DIRECTOR_CONFIRMED_OUTPUT_FAILURE', 409) from None
        if mapping['format'] in ('wav', 'mp4') and facts.get('duration', 100) > 1:
            raise Fault('DIRECTOR_CONFIRMED_OUTPUT_FAILURE', 409)
        if mapping['format'] == 'png' and (facts.get('width', 10000) > 64 or facts.get('height', 10000) > 64):
            raise Fault('DIRECTOR_CONFIRMED_OUTPUT_FAILURE', 409)
        return data, facts
