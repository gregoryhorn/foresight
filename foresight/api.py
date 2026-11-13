"""Host-independent public entry points; no host configuration or tool dispatch."""
import hashlib
from pathlib import Path
from .cards.inventory import inventory
from .review import applicability, crystal_ball, reports


def check(file, *, mode='quick', platform='custom', shape=None, report_dir=None):
    path = Path(file).expanduser()
    options = applicability.settings(mode=mode, platform=platform, shape=shape)
    data = path.read_bytes()
    result = crystal_ball.run(data, path.suffix, **options)
    digest = hashlib.sha256(data).hexdigest()
    if report_dir is not None:
        compact = reports.retain(result, report_dir, digest=digest, options=options)
        compact['report'] = str(Path(report_dir).expanduser())
    else:
        compact = reports.summary(result, options)
        compact['input_sha256'] = digest
    return compact
