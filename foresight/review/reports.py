"""Portable report summaries and explicit retained assets, without host tables."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import time
from . import applicability, crystal_ball


def summary(result, options, *, identifier=None):
    keys = ('status', 'reason', 'counts', 'not_checked', 'not_checked_details',
            'not_checked_omitted_count', 'omitted_details', 'media_kind')
    compact = {key: result[key] for key in keys if key in result}
    compact.setdefault('status', 'Not checked')
    compact.update(checker='Crystal Ball', version=crystal_ball.VERSION,
                   options=applicability.identity(result.get('media_kind'), options, crystal_ball.VERSION),
                   checked_at=time.time(), user_review='Not reviewed')
    if identifier is not None:
        compact['report'] = identifier
    return compact


def retain(result, directory, *, digest, options):
    """Create a new report directory. Refuse overwrites and unsafe asset names."""
    directory = Path(directory).expanduser()
    assets = result.get('assets', {})
    for name in assets:
        path = PurePosixPath(name.replace('\\', '/'))
        if path.is_absolute() or '..' in path.parts or ':' in name or not path.parts:
            raise ValueError('Unsafe report asset name')
    directory.mkdir(parents=True, exist_ok=False)
    compact = summary(result, options)
    compact['input_sha256'] = digest
    (directory / 'summary.json').write_text(json.dumps(compact, indent=2), encoding='utf-8')
    for name, body in assets.items():
        target = directory / 'assets' / Path(name.replace('\\', '/'))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    return compact
