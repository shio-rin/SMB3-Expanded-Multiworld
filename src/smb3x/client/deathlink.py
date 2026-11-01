# SPDX-License-Identifier: MPL-2.0
"""Small DeathLink records owned by the existing checkpoint epoch/controller."""
from copy import deepcopy
import math
from .effects import digest
CONTRACT = 'm25-deathlink-2'
FINAL = {'applied', 'expired', 'coalesced', 'disposed_interrupted', 'published', 'send_uncertain'}

def empty():
    return dict(contract=CONTRACT, records={})

def payload(value, now):
    if not isinstance(value, dict):
        return None
    stamp = value.get('time')
    source = value.get('source')
    cause = value.get('cause', '')
    if type(stamp) not in (int, float) or not now - 20 <= stamp <= now + 5 or (not math.isfinite(stamp)):
        return None
    if not isinstance(source, str) or not source.strip() or len(source) > 128:
        return None
    if not isinstance(cause, str) or len(cause) > 512 or any((ord(c) < 32 for c in source + cause)):
        return None
    return dict(time=float(stamp), source=source, cause=cause)

def event_id(data):
    return digest([data['time'], data['source']])

def validate(value):
    if not isinstance(value, dict) or set(value) != {'contract', 'records'} or value['contract'] != CONTRACT or (not isinstance(value['records'], dict)):
        raise ValueError('Unknown managed DeathLink contract')
    for key, r in value['records'].items():
        if not isinstance(key, str) or len(key) != 64 or any((c not in '0123456789abcdef' for c in key)):
            raise ValueError('Invalid death identity')
        if not isinstance(r, dict) or set(r) != {'direction', 'state', 'received', 'deadline', 'network_id', 'run', 'reason'}:
            raise ValueError('Incomplete death record')
        if r['direction'] not in ('incoming', 'outgoing') or r['state'] not in FINAL | {'queued', 'committed', 'send_intent'}:
            raise ValueError('Invalid death disposition')
        if any((type(r[k]) is not int for k in ('received', 'deadline'))) or not 0 <= r['deadline'] - r['received'] <= 20000:
            raise ValueError('Invalid original receipt deadline')
        if not isinstance(r['run'], str) or len(r['run']) != 32 or any((c not in '0123456789abcdef' for c in r['run'])) or (not isinstance(r['reason'], str)):
            raise ValueError('Missing death run/origin')
        if r['network_id'] is not None and (not isinstance(r['network_id'], str) or len(r['network_id']) != 64 or any((c not in '0123456789abcdef' for c in r['network_id']))):
            raise ValueError('Invalid network death identity')
        if r['direction'] == 'incoming':
            if r['network_id'] != key or r['state'] not in {'queued', 'committed', 'applied', 'expired', 'coalesced', 'disposed_interrupted'}:
                raise ValueError('Contradictory incoming DeathLink origin/disposition')
        elif r['state'] not in {'send_intent', 'published', 'send_uncertain', 'disposed_interrupted'} or r['deadline'] != r['received']:
            raise ValueError('Contradictory outgoing DeathLink disposition/deadline')
        elif r['state'] == 'published' and r['network_id'] is None:
            raise ValueError('Published DeathLink lacks a network identity')
    return value

def extends(old, new):
    validate(old)
    validate(new)
    for key, r in old['records'].items():
        if key not in new['records']:
            raise ValueError('Lost DeathLink dedup record')
        n = new['records'][key]
        if any((n[k] != r[k] for k in ('direction', 'received', 'deadline', 'run'))):
            raise ValueError('DeathLink origin/deadline changed')
        if r['network_id'] is not None and n['network_id'] != r['network_id']:
            raise ValueError('DeathLink packet identity changed')
        if r['state'] in FINAL and n != r:
            raise ValueError('Terminal DeathLink changed')
        if r['state'] == 'committed' and n['state'] not in FINAL | {'committed'}:
            raise ValueError('Remote death rearmed')
    return new

def recovered(value):
    result = deepcopy(validate(value))
    for r in result['records'].values():
        if r['state'] not in FINAL:
            r.update(state='disposed_interrupted', reason='new native lifetime: old death intent never replayed')
    return result
