# SPDX-License-Identifier: MPL-2.0
"""Typed effect custody and monotonic dispositions within the Hybrid controller.
from ..shared.resources import RESOURCE_ROOT

No native writes, background timers, or independent persistence authority.
"""
from copy import deepcopy
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
import json, runpy
from .persistence.receipts import DeliveryState, StateStore
from ..shared.items import ITEMS
from ..shared import effects as effect_contract
_shared = vars(effect_contract)
SPECS, CONTRACT, delay_frames = (_shared[k] for k in ('SPECS', 'CONTRACT', 'delay_frames'))
TERMINAL = frozenset(('completed', 'completed_noop', 'disposed_interrupted'))
STATES = TERMINAL | {'queued', 'scheduled', 'committed', 'activated'}

def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()

def prefix(value):
    if not isinstance(value, list):
        raise ValueError('Effect prefix must be an array')
    for row in value:
        if not isinstance(row, list) or len(row) != 4 or any((type(v) is not int for v in row)) or (row[0] not in ITEMS) or (row[2] < 0) or (not 0 <= row[3] <= 7):
            raise ValueError('Invalid complete NetworkItem tuple')
    return value

def empty():
    return dict(contract=CONTRACT, prefix=[], records={}, last_entry=0)

def validate(value):
    if not isinstance(value, dict) or set(value) != {'contract', 'prefix', 'records', 'last_entry'} or value['contract'] != CONTRACT:
        raise ValueError('Unknown effect controller contract')
    rows = prefix(value['prefix'])
    records = value['records']
    entry = value['last_entry']
    if type(entry) is not int or entry < 0 or (not isinstance(records, dict)):
        raise ValueError('Invalid effect entry/history')
    if set(records) != {str(i) for i, row in enumerate(rows) if row[0] in SPECS}:
        raise ValueError('Effect custody must account for every indexed effect')
    owners = 0
    for key, r in records.items():
        i = int(key)
        if not isinstance(r, dict) or set(r) != {'index', 'receipt', 'kind', 'state', 'entry', 'token', 'reason', 'delay_frames'}:
            raise ValueError('Incomplete effect disposition')
        if r['index'] != i or type(r['index']) is not int or r['receipt'] != digest(rows[i]) or (r['kind'] != SPECS[rows[i][0]][1]) or (r['state'] not in STATES):
            raise ValueError('Effect receipt identity/state changed')
        if not isinstance(r['reason'], str) or not r['reason'] or len(r['reason']) > 256:
            raise ValueError('Missing terminal/transition reason')
        if r['state'] == 'queued':
            if any((r[k] is not None for k in ('entry', 'token', 'delay_frames'))):
                raise ValueError('Queued effect owns stale activation')
        else:
            if type(r['entry']) is not int or not 1 <= r['entry'] <= entry or type(r['delay_frames']) is not int or (r['delay_frames'] not in range(240, 1081, 60)):
                raise ValueError('Effect attempt/delay invalid')
            if r['state'] == 'scheduled':
                if r['token'] is not None:
                    raise ValueError('Schedule already has activation permission')
            elif not isinstance(r['token'], str) or len(r['token']) != 64 or any((c not in '0123456789abcdef' for c in r['token'])):
                raise ValueError('Effect activation lacks bound token')
        owners += r['state'] in ('scheduled', 'committed', 'activated')
    if owners > 1:
        raise ValueError('Multiple effect owners')
    return value

def extends(old, new):
    """Validate forward custody and immutable/monotonic consumed dispositions."""
    validate(old)
    validate(new)
    if len(new['prefix']) < len(old['prefix']) or new['prefix'][:len(old['prefix'])] != old['prefix'] or new['last_entry'] < old['last_entry']:
        raise ValueError('Effect authoritative prefix/entry regressed')
    for i, r in old['records'].items():
        n = new['records'][i]
        if r['state'] in TERMINAL and n != r:
            raise ValueError('Terminal effect disposition changed')
        if r['state'] in ('committed', 'activated'):
            if n['state'] not in {'committed', 'activated'} | TERMINAL or any((n[k] != r[k] for k in ('entry', 'token', 'delay_frames'))):
                raise ValueError('Committed effect cannot rearm or change activation identity')
            if r['state'] == 'activated' and n['state'] == 'committed':
                raise ValueError('Activated effect regressed')
    return new

def recovered(value):
    result = deepcopy(validate(value))
    for r in result['records'].values():
        if r['state'] == 'scheduled':
            r.update(state='queued', entry=None, token=None, delay_frames=None, reason='cold Resume before activation commitment')
        elif r['state'] in ('committed', 'activated'):
            r.update(state='disposed_interrupted', reason='cold Resume: committed native outcome is not replayable')
    return validate(result)

@dataclass
class EffectDelivery(DeliveryState):
    effects: dict = field(default_factory=empty)

    def receive(self, received):
        received = deepcopy(prefix(received))
        old = self.as_dict()
        if received[:len(self.effects['prefix'])] != self.effects['prefix']:
            raise ValueError('Authoritative effect receipt prefix changed/truncated')
        self.observe_items([(i, r[0]) for i, r in enumerate(received)])
        self.effects['prefix'] = received
        for i, row in enumerate(received):
            if row[0] not in SPECS:
                continue
            if str(i) not in self.effects['records']:
                self.effects['records'][str(i)] = dict(index=i, receipt=digest(row), kind=SPECS[row[0]][1], state='queued', entry=None, token=None, reason='validated indexed custody', delay_frames=None)
            self.acknowledge(i, 'applied')
        validate(self.effects)
        return self.as_dict() != old

    def schedule(self, index, entry):
        if type(entry) is not int or entry <= self.effects['last_entry']:
            raise ValueError('Effect entry already selected')
        if any((r['state'] in ('scheduled', 'committed', 'activated') for r in self.effects['records'].values())):
            raise ValueError('Previous effect still owns activation')
        self.effects['last_entry'] = entry
        if index is None:
            return
        r = self.effects['records'][str(index)]
        if r['state'] != 'queued':
            raise ValueError('Cannot schedule consumed effect')
        r.update(state='scheduled', entry=entry, reason='oldest compatible entry snapshot', delay_frames=delay_frames(self.identity.seed, self.identity.team, self.identity.slot, index, entry))

    def commit(self, index, entry, run, area):
        r = self.effects['records'][str(index)]
        if r['state'] != 'scheduled' or r['entry'] != entry:
            raise ValueError('Readiness differs from scheduled effect')
        r.update(state='committed', token=digest([CONTRACT, self.identity.as_dict(), run, index, r['receipt'], entry, area]), reason='durable activation commitment')

    def outcome(self, index, entry, token, state, reason):
        r = self.effects['records'][str(index)]
        if r['entry'] != entry or r['token'] != token:
            raise ValueError('Effect outcome token mismatch')
        if state == 'queued':
            if r['state'] != 'scheduled':
                raise ValueError('Committed native request cannot requeue')
            r.update(state='queued', entry=None, token=None, delay_frames=None, reason=reason)
        elif state in TERMINAL or state == 'activated':
            if r['state'] not in ('committed', 'activated'):
                raise ValueError('Outcome without commitment')
            r.update(state=state, reason=reason)
        else:
            raise ValueError('Unknown native effect outcome')
        validate(self.effects)

    def overlay(self, value):
        value = deepcopy(validate(value))
        self.receive(value['prefix'])
        self.effects = value

    def as_dict(self):
        return dict(super().as_dict(), schema=10, effects=deepcopy(self.effects))

def validate_delivery(data):
    if data.get('schema') != 10:
        raise ValueError('requires fresh delivery schema10')
    e = validate(data.get('effects'))
    if data['items'] != {str(i): r[0] for i, r in enumerate(e['prefix'])}:
        raise ValueError('Delivery/effect complete prefix mismatch')
    if any((data['handled'].get(i) != 'applied' for i in e['records'])):
        raise ValueError('Effect custody is not handled')
    if any((i < 0 for i in data['pending'])) or set(map(str, data['pending'])) | set(data['handled']) != set(data['items']) or set(map(str, data['pending'])) & set(data['handled']):
        raise ValueError('Invalid delivery partition')

class EffectStore(StateStore):

    def load(self, identity):
        path = self.path_for(identity)
        if not path.exists():
            return EffectDelivery(identity)
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('identity') != identity.as_dict():
            raise ValueError('delivery identity mismatch')
        validate_delivery(data)
        base = self.parse({**data, 'schema': 9}, identity, path)
        return EffectDelivery(**base.__dict__, effects=deepcopy(data['effects']))
