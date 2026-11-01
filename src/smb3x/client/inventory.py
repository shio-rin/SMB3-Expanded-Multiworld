# SPDX-License-Identifier: MPL-2.0
"""inventory witnesses. Native RAM is authoritative; never restore balances."""
from copy import deepcopy
from hashlib import sha256
import json
FORMAT = 1
MAX_QUANTITY = 65535
MAX_TICKET = 4294967295
TYPES = frozenset(range(1, 14))
AP_TYPES = frozenset((1, 2, 3, 4, 5, 6, 8, 9, 11))

def validate(snapshot, mode, *, regional=False):
    fields = {'format', 'mode', 'quantities', 'slots', 'serial', 'ticket', 'item', 'pending', 'receipt_before', 'receipt_after', 'receipt_serial'}
    if not isinstance(snapshot, dict) or set(snapshot) != fields:
        raise ValueError('Invalid native inventory witness fields')
    if snapshot['format'] != FORMAT or snapshot['mode'] != mode or mode not in ('vanilla', 'stacked'):
        raise ValueError('Native inventory format/mode mismatch')
    quantities, slots = (snapshot['quantities'], snapshot['slots'])
    if not isinstance(quantities, list) or len(quantities) != 13 or any((type(q) is not int or not 0 <= q <= MAX_QUANTITY for q in quantities)):
        raise ValueError('Invalid native quantities')
    if not isinstance(slots, list) or len(slots) != 28 or any((type(t) is not int or t not in TYPES | {0} for t in slots)):
        raise ValueError('Invalid native inventory slots')
    for field in ('serial', 'ticket', 'receipt_serial'):
        if type(snapshot[field]) is not int or not 0 <= snapshot[field] <= MAX_TICKET:
            raise ValueError('Invalid native inventory serial/ticket')
    if type(snapshot['item']) is not int or snapshot['item'] not in AP_TYPES | {0} or bool(snapshot['ticket']) != bool(snapshot['item']):
        raise ValueError('Invalid native receipt')
    if type(snapshot['pending']) is not int or snapshot['pending'] not in TYPES | {0}:
        raise ValueError('Invalid native grant pending type')
    for field in ('receipt_before', 'receipt_after'):
        if type(snapshot[field]) is not int or not 0 <= snapshot[field] <= MAX_QUANTITY:
            raise ValueError('Invalid native quantity receipt')
    if snapshot['ticket']:
        if snapshot['receipt_after'] != snapshot['receipt_before'] + 1 or not 0 < snapshot['receipt_serial'] <= snapshot['serial']:
            raise ValueError('Native receipt does not establish one increment')
    elif snapshot['receipt_before'] or snapshot['receipt_after'] or snapshot['receipt_serial']:
        raise ValueError('Quantity receipt lacks AP ticket')
    if mode == 'stacked':
        owned = [t for t in slots if t]
        if len(owned) != len(set(owned)) or slots != owned + [0] * (28 - len(owned)):
            raise ValueError('Duplicate or noncompact native stack representatives')
        if set(owned) != {i + 1 for i, q in enumerate(quantities) if q}:
            raise ValueError('Native quantity/representative disagreement')
        if regional and (quantities[10] or snapshot['pending'] == 11):
            raise ValueError('Consumable Hammer in regional inventory')
    elif any(quantities) or any((snapshot[k] for k in ('serial', 'ticket', 'item', 'pending', 'receipt_before', 'receipt_after', 'receipt_serial'))):
        raise ValueError('Stack authority present in vanilla mode')
    return deepcopy(snapshot)

def seal(snapshot):
    return {'snapshot': deepcopy(snapshot), 'sha256': sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}

def reconcile(previous, current, mode, *, regional=False):
    current = validate(current, mode, regional=regional)
    if previous is not None:
        if not isinstance(previous, dict) or set(previous) != {'snapshot', 'sha256'} or seal(previous['snapshot']) != previous:
            raise ValueError('Inventory witness seal mismatch')
        old = validate(previous['snapshot'], mode, regional=regional)
        if current['serial'] < old['serial'] or current['ticket'] < old['ticket']:
            raise ValueError('Native inventory rollback; preserve history')
        if mode == 'stacked' and current['serial'] == old['serial'] and (current != old):
            raise ValueError('Native inventory changed without mutation receipt')
        if current['ticket'] > old['ticket'] and current['receipt_serial'] <= old['serial']:
            raise ValueError('AP receipt did not advance native mutation serial')
        if current['ticket'] == old['ticket'] and current['item'] != old['item']:
            raise ValueError('Conflicting native inventory receipt type')
    return seal(current)
