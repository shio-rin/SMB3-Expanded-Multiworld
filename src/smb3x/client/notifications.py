# SPDX-License-Identifier: MPL-2.0
"""Best-effort cosmetic events. Never reads or writes the delivery journal."""
from collections import deque
from time import monotonic
from uuid import uuid4
import logging

class Notifications:

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.epoch = uuid4().hex
        self.serial = 0
        self.queue = deque(maxlen=256)
        self.checked = set()
        self.sent = set()
        self.received = set()
        self.first_items = True
        self.instance = None
        self.counts = {}
        self.examples = {}
        self.emitted = []

    def emit(self, text):
        if not self.enabled:
            return
        self.counts[text.split(':', 1)[0]] = self.counts.get(text.split(':', 1)[0], 0) + 1
        kind = text.split(':', 1)[0]
        self.examples.setdefault(kind, [])
        if len(self.examples[kind]) < 4:
            self.examples[kind].append(text)
        self.serial += 1
        event = {'id': self.epoch + ':' + str(self.serial), 'text': str(text)[:240]}
        self.queue.append((monotonic(), event))
        self.emitted = (self.emitted + [event['text']])[-256:]

    def confirmed(self, location, name):
        if location not in self.checked:
            self.checked.add(location)

    @property
    def initial_checked(self):
        return getattr(self, '_initial_checked', set())

    def applied(self, index, name, result):
        pass

    def connected(self, checked, known_count=0):
        self.checked = set(checked)
        self._initial_checked = set(checked)
        self.received.update(range(known_count))

    def emit_event(self, identity, text, count=1, **fields):
        if not self.enabled:
            return
        event = {'id': identity, 'text': str(text)[:240], 'count': count, **fields}
        self.emitted = (self.emitted + [event['text']])[-256:]
        if len(self.queue) >= 32 and self.queue[-1][1]['id'] not in getattr(self, '_inflight', set()):
            _, last = self.queue.pop()
            count += last.get('count', 1)
            event = {'id': identity, 'text': f'{count} additional AP item events; see client log', 'count': count}
        self.queue.append((0, event))

    def items(self, items, name, player):
        incoming = [(i, v) for i, v in enumerate(items) if i not in self.received]
        self.received.update((i for i, _ in incoming))
        for i, v in incoming:
            logging.getLogger('SMB3').info('AP received index=%s: %s from %s', i, name(v.item), player(v.player))
        if getattr(self, 'trap_warning', 'show') == 'hide':
            from .effects import SPECS
            incoming = [(i, v) for i, v in incoming if not (v.item in SPECS and SPECS[v.item][2])]
        if len(incoming) > 6:
            examples = '; '.join((name(v.item) + ' from ' + player(v.player) for _, v in incoming[:2]))
            self.emit_event('received-batch:' + str(incoming[0][0]) + ':' + str(incoming[-1][0]), f'Received {len(incoming)} items: {examples}; +{len(incoming) - 2} more', len(incoming))
        else:
            for i, v in incoming:
                self.emit_event('received:' + str(i), 'Received: ' + name(v.item) + ' from ' + player(v.player), kind='received', item=name(v.item), player=player(v.player))

    def send(self, item, recipient, own_slot, name, player):
        key = (item.player, item.location, item.item, recipient)
        if item.player != own_slot or recipient == own_slot or key in self.sent:
            return
        self.sent.add(key)
        if item.location in self.initial_checked:
            return
        logging.getLogger('SMB3').info('AP sent location=%s: %s to %s', item.location, name(item.item, recipient), player(recipient))
        self.emit_event('sent:' + ':'.join(map(str, key)), 'Sent: ' + name(item.item, recipient) + ' to ' + player(recipient), kind='sent', item=name(item.item, recipient), player=player(recipient))

    def batch(self, instance):
        self.instance = instance
        events = [event for _, event in list(self.queue)[:32]]
        self._inflight = {e['id'] for e in events}
        return events

    def acknowledge(self, events):
        ids = {e['id'] for e in events}
        self.queue = deque(((t, e) for t, e in self.queue if e['id'] not in ids))
        self._inflight = getattr(self, '_inflight', set()) - ids
