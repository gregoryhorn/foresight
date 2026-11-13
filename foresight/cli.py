"""Foresight's JSON CLI. Tests require explicit confirmation and a replay identity."""
import argparse
import json
from pathlib import Path
import sys
from .api import check, inventory
from .cards.service import Cards
from .cards.learning import STARTERS


def parser():
    cli = argparse.ArgumentParser(prog='foresight')
    cli.add_argument('--version', action='version', version='0.1.0')
    commands = cli.add_subparsers(dest='action', required=True)
    inv = commands.add_parser('inventory', help='Passive local tool presence; never executes tools')
    inv.add_argument('--profile', default='standalone')
    inv.add_argument('--session', default='local')
    card = commands.add_parser('card', help='Local data-only tool cards')
    card.add_argument('--home', type=Path, default=Path('~/.foresight').expanduser())
    operations = card.add_subparsers(dest='operation', required=True)
    operations.add_parser('list')
    operations.add_parser('templates')
    prepare = operations.add_parser('prepare')
    prepare.add_argument('file', type=Path, help='JSON object with name and mapping')
    read = operations.add_parser('read')
    read.add_argument('id')
    test = operations.add_parser('test')
    test.add_argument('id')
    test.add_argument('--command', required=True, help='Reuse this identity after a lost response')
    test.add_argument('--confirmed', action='store_true', help='Authorize one disclosed tiny local test')
    media = commands.add_parser('check')
    media.add_argument('file', type=Path)
    media.add_argument('--mode', choices=['quick', 'full'], default='quick')
    media.add_argument('--platform', choices=['custom', 'youtube', 'shorts', 'reels', 'tiktok'], default='custom')
    media.add_argument('--shape', choices=['9:16', '16:9', '1:1'])
    media.add_argument('--report-dir', type=Path)
    media.add_argument('--json', action='store_true', help='JSON is the default output')
    return cli


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.action == 'inventory':
            result = inventory(args.profile, args.session)
        elif args.action == 'check':
            result = check(args.file, mode=args.mode, platform=args.platform, shape=args.shape, report_dir=args.report_dir)
        elif args.operation == 'templates':
            result = [dict(name=name, status='Untested') for name in STARTERS]
        else:
            cards = Cards(args.home)
            if args.operation == 'prepare':
                body = json.loads(args.file.read_text(encoding='utf-8'))
                result = cards.prepare(body['name'], body['mapping'])
            elif args.operation == 'test':
                result = cards.test(args.id, command=args.command, confirmed=args.confirmed)
            else:
                result = cards.read(getattr(args, 'id', None))
        print(json.dumps(result, indent=2))
        return 1 if isinstance(result, dict) and result.get('status') in ('FAIL', 'Not checked') else 0
    except Exception as error:
        print(json.dumps(dict(error=getattr(error, 'code', 'FORESIGHT_ERROR'), reason='Operation could not complete; check input and dependency setup')), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
