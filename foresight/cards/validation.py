"""Portable bounded tiny-output validation with no network protocols."""
import io
import json
import math
import os
from pathlib import Path
import tempfile
import wave
from foresight.errors import Fault
from foresight.process import call


def inspect_media(data, format):
    if not 0 < len(data) <= 1024 * 1024:
        raise Fault('DIRECTOR_CONFIRMED_OUTPUT_FAILURE', 409)
    if format == 'wav':
        try:
            with wave.open(io.BytesIO(data)) as audio:
                frames, rate = audio.getnframes(), audio.getframerate()
                if not 0 < frames <= rate or audio.getnchannels() not in (1, 2):
                    raise ValueError('Invalid tiny audio')
                if len(audio.readframes(frames)) != frames * audio.getnchannels() * audio.getsampwidth():
                    raise ValueError('Truncated audio')
                return dict(mime='audio/wav', duration=frames/rate, rate=rate, channels=audio.getnchannels())
        except (wave.Error, EOFError, ValueError):
            raise Fault('DIRECTOR_CONFIRMED_OUTPUT_FAILURE', 409) from None
    valid = data.startswith(b'\x89PNG\r\n\x1a\n') if format == 'png' else len(data) > 12 and data[4:8] == b'ftyp'
    if format not in ('png', 'mp4') or not valid:
        raise Fault('DIRECTOR_CONFIRMED_OUTPUT_FAILURE', 409)
    with tempfile.TemporaryDirectory(prefix='foresight-validate-') as temporary:
        root = Path(temporary)
        path = root / ('output.' + format)
        path.write_bytes(data)
        env = {key: os.environ[key] for key in ('PATH', 'SYSTEMROOT', 'WINDIR', 'TMPDIR', 'TMP', 'TEMP') if key in os.environ}
        options = ['-protocol_whitelist', 'file', '-f', 'png_pipe' if format == 'png' else 'mov']
        if format == 'mp4':
            options += ['-enable_drefs', '0', '-use_absolute_path', '0']
        options += ['-i', str(path)]
        probe = call(['ffprobe', '-v', 'error', *options, '-show_streams', '-show_format', '-of', 'json'], cwd=root, env=env, timeout=15)
        try:
            if probe.returncode or len(probe.stdout) > 65536:
                raise ValueError('Probe failed')
            doc = json.loads(probe.stdout)
            streams = doc['streams']
            if len(streams) != 1 or streams[0]['codec_type'] != 'video':
                raise ValueError('Unexpected streams')
            video = streams[0]
            width, height = int(video['width']), int(video['height'])
            limit = 64 if format == 'png' else 4096
            if not (0 < width <= limit and 0 < height <= limit):
                raise ValueError('Unexpected dimensions')
            if video['codec_name'] not in (('png',) if format == 'png' else ('h264', 'mpeg4')):
                raise ValueError('Unexpected codec')
            facts = dict(mime='image/png' if format == 'png' else 'video/mp4', width=width, height=height)
            if format == 'mp4':
                duration = float(doc['format']['duration'])
                if not math.isfinite(duration) or not 0 < duration <= 1:
                    raise ValueError('Unexpected duration')
                facts['duration'] = duration
            decoded = call(['ffmpeg', '-v', 'error', '-nostdin', '-xerror', '-threads', '1', *options, '-f', 'null', '-'], cwd=root, env=env, timeout=15)
            if decoded.returncode:
                raise ValueError('Decode failed')
            return facts
        except (KeyError, ValueError, TypeError):
            raise Fault('DIRECTOR_CONFIRMED_OUTPUT_FAILURE', 409) from None
