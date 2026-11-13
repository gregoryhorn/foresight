# Foresight developer entry point

Work on main in the primary checkout. No publish, push or tag without permission.
Core entry points: foresight/api.py and cli.py; cards/ owns data-only mappings and
bounded tests; review/ owns Crystal Ball applicability and retained report assets.
Keep host RPC, storage tables and Desktop UI in Motion Studio. No host imports in
foresight. Keep functions below 300 lines. Use only synthetic test media.

Commands and prerequisites: README.md. Actual implementation/test boundaries:
docs/as-built/extraction.md. Do not read excluded profile content or copy private
media, credentials or machine paths into the distribution. Documentation paths
use ~/ placeholders. Design documentation remains owned by app-design.
