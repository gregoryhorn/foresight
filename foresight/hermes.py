"""Hermes tool adapter. No hooks, automatic tests, installs or registry inspection."""
import json
from .api import check, inventory
from .cards.learning import STARTERS


def register(ctx):
    def handle(params, **context):
        try:
            action = params['action']
            if action == 'inventory':
                # Cached inventory must be injected by a trusted host, never caller metadata.
                result = inventory(context.get('profile', ''), context.get('session_id', ''))
            elif action == 'card':
                result = dict(templates=[dict(name=name, status='Untested') for name in STARTERS],
                    next_action='Use the CLI card commands for local preparation and a disclosed confirmed test')
            elif action == 'check':
                result = check(params['file'], mode=params.get('mode', 'quick'),
                               platform=params.get('platform', 'custom'), shape=params.get('shape'))
            else:
                raise ValueError('Unknown action')
            return json.dumps(result)
        except Exception:
            return json.dumps(dict(error='FORESIGHT_ERROR', reason='Operation could not complete; check input and dependency setup'))
    return ctx.register_tool(name='foresight', toolset='foresight', schema={
        'name': 'foresight',
        'description': 'Know available tools and untested starter cards; check media using Crystal Ball. No automatic generation or qualification. Technical PASS is not creative approval.',
        'parameters': {'type': 'object', 'properties': {
            'action': {'type': 'string', 'enum': ['inventory', 'card', 'check']},
            'file': {'type': 'string', 'description': 'Local media path for check'},
            'mode': {'type': 'string', 'enum': ['quick', 'full']},
            'platform': {'type': 'string', 'enum': ['custom', 'youtube', 'shorts', 'reels', 'tiktok']},
            'shape': {'type': 'string', 'enum': ['9:16', '16:9', '1:1']},
        }, 'required': ['action'], 'additionalProperties': False},
    }, handler=handle)
