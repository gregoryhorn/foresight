"""Standalone local card store with persisted intent before one confirmed test."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from uuid import uuid4
from . import learning
from .schema import Mapping
from foresight.errors import Fault
from foresight.review import crystal_ball, reports, applicability


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


class Cards:
    def __init__(self, home):
        self.home = Path(home).expanduser()
        self.home.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS cards(id TEXT PRIMARY KEY, body TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS tests(command TEXT PRIMARY KEY, payload TEXT NOT NULL, result TEXT)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.home / 'cards.sqlite3', timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def read(self, identifier=None):
        with self.connect() as db:
            if identifier:
                row = db.execute('SELECT body FROM cards WHERE id=?', (identifier,)).fetchone()
                if row is None:
                    raise ValueError('Unknown card')
                card = json.loads(row[0])
                self.refresh(db, card)
                return card
            cards = [json.loads(row[0]) for row in db.execute('SELECT body FROM cards ORDER BY id')]
            for card in cards:
                self.refresh(db, card)
            return cards

    @staticmethod
    def refresh(db, card):
        if card['status'] != 'Tested':
            return
        try:
            drift = learning.fingerprint(card['mapping']) != card['fingerprint']
        except (Fault, OSError):
            drift = True
        if drift:
            card.update(status='Needs re-test', reason='Tool changed; review a new tiny test')
            db.execute('UPDATE cards SET body=? WHERE id=?', (canonical(card), card['id']))

    def prepare(self, name, mapping):
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise ValueError('A card name of 1-120 characters is required')
        mapping = Mapping.model_validate(mapping).model_dump()
        card = dict(id=uuid4().hex, revision=1, name=name, mapping=mapping,
                    status='Untested', failures=0, evidence=[], fingerprint=None)
        with self.connect() as db:
            db.execute('INSERT INTO cards VALUES(?,?)', (card['id'], canonical(card)))
        return card

    def test(self, identifier, *, command, confirmed=False):
        if not confirmed:
            raise Fault('DIRECTOR_CONFIRMATION_REQUIRED', 403)
        if not isinstance(command, str) or not 1 <= len(command) <= 120:
            raise ValueError('A stable command identity is required')
        payload = canonical(dict(id=identifier))
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT payload,result FROM tests WHERE command=?', (command,)).fetchone()
            if previous:
                if previous[0] != payload:
                    raise Fault('COMMAND_CONFLICT', 409)
                return json.loads(previous[1]) if previous[1] else dict(status='Testing', reason='Outcome unresolved; do not repeat')
            row = db.execute('SELECT body FROM cards WHERE id=?', (identifier,)).fetchone()
            if row is None:
                raise ValueError('Unknown card')
            card = json.loads(row[0])
            if card['status'] not in ('Untested', 'Tested', 'Needs re-test'):
                raise Fault('DIRECTOR_TEST_UNAVAILABLE', 409)
            mapping = Mapping.model_validate(card['mapping']).model_dump()
            if mapping['cost'] != 'zero':
                raise Fault('DIRECTOR_SPEND_AUTHORIZATION_REQUIRED', 403)
            pin = learning.fingerprint(mapping)
            db.execute('INSERT INTO tests VALUES(?,?,NULL)', (command, payload))
            card['status'] = 'Testing'
            db.execute('UPDATE cards SET body=? WHERE id=?', (canonical(card), identifier))
        started = time.monotonic()
        try:
            if learning.fingerprint(mapping) != pin:
                raise Fault('DIRECTOR_TOOL_CHANGED', 409)
            data, facts = learning.execute(mapping, pin)
            # Store exact original before checking; never dispatch a second time.
            output = self.home / 'outputs' / (uuid4().hex + '.' + mapping['format'])
            output.parent.mkdir(exist_ok=True)
            with output.open('xb') as target:
                target.write(data)
            result = crystal_ball.run(data, '.' + mapping['format'])
            report = self.home / 'reports' / uuid4().hex
            review = reports.retain(result, report, digest=hashlib.sha256(data).hexdigest(), options=applicability.settings())
            usable = review['status'] in ('PASS', 'WARN') and not review.get('counts', {}).get('FAIL')
            card.update(status='Tested' if usable else 'Untested', fingerprint=pin, failures=0)
            card['evidence'].append(dict(output=str(output), report=str(report), check=review['status'],
                facts=facts, elapsed_seconds=round(time.monotonic()-started, 3), user_verdict='Not reviewed'))
        except Fault as error:
            if error.code in ('DIRECTOR_CONFIRMED_TOOL_FAILURE', 'DIRECTOR_CONFIRMED_OUTPUT_FAILURE'):
                card['failures'] += 1
            card.update(status='Needs re-test' if card['failures'] >= 2 else 'Untested', reason=error.code)
        except Exception:
            # Timeout/crash/unknown delivery is deliberately not eligible for replay.
            return dict(status='Testing', reason='Outcome unresolved; reconcile original test')
        with self.connect() as db:
            db.execute('UPDATE cards SET body=? WHERE id=?', (canonical(card), identifier))
            db.execute('UPDATE tests SET result=? WHERE command=?', (canonical(card), command))
        return card
