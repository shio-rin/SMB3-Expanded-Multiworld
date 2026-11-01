# SPDX-License-Identifier: MPL-2.0
"""An indexed receipt records what the server sent and what native code acknowledged.
Pending receipt ownership is durable before a grant is requested; receiving an item
is not proof that it has reached inventory."""

from __future__ import annotations
from ...shared.identity import Identity
from dataclasses import dataclass, field
from hashlib import sha256
import json
import os
from pathlib import Path
from ...shared.items import ITEMS, PASS_ID, PASS_WORLDS, HAMMER_WORLDS, STAR_ID


@dataclass
class DeliveryState:
    identity: Identity
    pending: list[int] = field(default_factory=list)
    handled: dict[int, str] = field(default_factory=dict)
    items: dict[int, int] = field(default_factory=dict)
    travel: dict | None = None
    registry: str | None = None
    physical_checks: set[int] = field(default_factory=set)
    confirmed_physical: set[int] = field(default_factory=set)

    def observe_checks(self, observed, server_checked, enabled):
        enabled = set(enabled)
        observed = set(observed)
        if (observed | self.physical_checks | self.confirmed_physical) - enabled:
            raise ValueError('Physical tracker contains a disabled or unknown location')
        before = (set(self.physical_checks), set(self.confirmed_physical))
        self.physical_checks.update(observed)
        self.confirmed_physical.update(self.physical_checks & set(server_checked))
        return before != (self.physical_checks, self.confirmed_physical)

    def check_counts(self):
        from ...shared.location_signals import BY_ID

        return [sum((BY_ID[i]['world'] == w for i in self.confirmed_physical)) for w in range(1, 9)]

    def bind_registry(self, registry: str, *, require_bound_history: bool = False) -> None:
        if self.registry is not None and self.registry != registry:
            raise ValueError('Delivery history location registry mismatch; use a fresh seed')
        if (
            require_bound_history
            and self.registry is None
            and (
                self.items
                or self.pending
                or self.handled
                or self.travel
                or self.physical_checks
                or self.confirmed_physical
            )
        ):
            raise ValueError('Unbound older session history; use a fresh seed')
        self.registry = registry

    @property
    def world2_pass(self) -> bool:
        return PASS_ID in self.items.values()

    @property
    def unlock_mask(self) -> int:
        return 1 | sum(
            (1 << world - 1 for item, world in PASS_WORLDS.items() if item in self.items.values())
        )

    def observe_items(self, entries: list[tuple[int, int]]) -> bool:
        """Validate the whole packet before mutating indexed item ownership."""
        packet = {}
        for index, item in entries:
            if type(index) is not int or index < 0 or item not in ITEMS:
                raise ValueError('Unsupported server item/index')
            if index in packet and packet[index] != item:
                raise ValueError('Conflicting item within server delivery packet')
            if index in self.items and self.items[index] != item:
                raise ValueError('Conflicting item at a server delivery index')
            packet[index] = item
        changed = False
        for index, item in entries:
            if type(index) is not int or index < 0 or item not in ITEMS:
                raise ValueError('Unsupported server item/index')
            if index in self.items and self.items[index] != item:
                raise ValueError('Conflicting item at a server delivery index')
            if index not in self.items:
                self.items[index] = item
                changed = True
        return self.observe_indices([i for i, _ in entries]) or changed

    @property
    def progression(self):
        return dict(
            hammers=sum(
                (
                    1 << world - 1
                    for item, world in HAMMER_WORLDS.items()
                    if item in self.items.values()
                )
            ),
            stars=sum((item == STAR_ID for item in self.items.values())),
            pending=len(self.pending),
        )

    def commands(self) -> list[dict]:
        return [{'index': i, 'item': self.items[i]} for i in self.pending]

    def observe_indices(self, indices: list[int]) -> bool:
        """Queue only new server delivery indices in their canonical order."""
        before = self.pending.copy()
        for index in indices:
            if index < 0:
                raise ValueError('Negative item delivery index')
            if index not in self.handled and index not in self.pending:
                self.pending.append(index)
        self.pending.sort()
        return self.pending != before

    def acknowledge(self, index: int, result: str) -> bool:
        """Mark a native result once; the caller must persist before releasing its barrier."""
        if result not in ('applied', 'capped'):
            raise ValueError('Unrecognized delivery result')
        if index in self.handled:
            if self.handled[index] != result:
                raise ValueError('Conflicting result for a handled item')
            return False
        if index not in self.pending:
            raise ValueError('Acknowledgement for an item that was not queued')
        self.pending.remove(index)
        self.handled[index] = result
        return True

    def as_dict(self) -> dict:
        return {
            'schema': 9,
            'identity': self.identity.as_dict(),
            'pending': self.pending,
            'handled': {str(k): v for k, v in sorted(self.handled.items())},
            'items': {str(k): v for k, v in sorted(self.items.items())},
            'travel': self.travel,
            'registry': self.registry,
            'physical_checks': sorted(self.physical_checks),
            'confirmed_physical': sorted(self.confirmed_physical),
        }


class StateStore:

    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def path_for(self, identity: Identity) -> Path:
        return self.directory / f'{identity.key}.json'

    def load(self, identity: Identity) -> DeliveryState:
        path = self.path_for(identity)
        if not path.exists():
            return DeliveryState(identity)
        data = json.loads(path.read_text(encoding='utf-8'))
        return self.parse(data, identity, path)

    @staticmethod
    def parse(data, identity, path='<memory>'):
        if data.get('schema') != 9 or data.get('identity') != identity.as_dict():
            raise ValueError(f'State identity/schema mismatch: {path}')
        pending = data['pending']
        handled = {int(k): v for k, v in data['handled'].items()}
        if (
            not isinstance(pending, list)
            or any((type(i) is not int or i < 0 for i in pending))
            or pending != sorted(set(pending))
            or set(pending) & set(handled)
            or any((v not in ('applied', 'capped') for v in handled.values()))
        ):
            raise ValueError(f'Invalid delivery state: {path}')
        items = {int(k): v for k, v in data.get('items', {}).items()}
        if any((i < 0 or type(v) is not int or v not in ITEMS for i, v in items.items())):
            raise ValueError('Invalid item history')
        travel = data.get('travel')
        if travel is not None and (
            not isinstance(travel, dict) or travel.get('session') != identity.key
        ):
            raise ValueError('Travel checkpoint identity mismatch')
        registry = data.get('registry')
        if registry is not None and (not isinstance(registry, str) or len(registry) != 64):
            raise ValueError('Invalid location registry binding')
        physical = data.get('physical_checks', [])
        confirmed = data.get('confirmed_physical', [])
        from ...shared.location_signals import BY_ID

        if any(
            (
                not isinstance(v, list)
                or any((type(i) is not int or i not in BY_ID for i in v))
                or v != sorted(set(v))
                for v in (physical, confirmed)
            )
        ) or not set(confirmed) <= set(physical):
            raise ValueError('Invalid physical check tracker')
        return DeliveryState(
            identity, pending, handled, items, travel, registry, set(physical), set(confirmed)
        )

    def save(self, state: DeliveryState) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.path_for(state.identity)
        from .atomic import save_json

        save_json(target, state.as_dict())


def new_location_checks(
    observed: set[int], missing: set[int], supported: set[int] | frozenset[int]
) -> set[int]:
    """Server missing locations decide which observed game clears are reportable."""
    unknown = observed - supported
    if unknown:
        raise ValueError(f'Unknown location IDs from BizHawk: {sorted(unknown)}')
    return observed & missing
