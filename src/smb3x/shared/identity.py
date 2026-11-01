# SPDX-License-Identifier: MPL-2.0
from dataclasses import dataclass
from hashlib import sha256
import json

@dataclass(frozen=True)
class Identity:
    seed: str
    team: int
    slot: int

    def __post_init__(self) -> None:
        if not self.seed or self.team < 0 or self.slot < 1:
            raise ValueError('A server seed, team, and player slot are required')

    @property
    def key(self) -> str:
        raw = json.dumps([self.seed, self.team, self.slot], separators=(',', ':'))
        return sha256(raw.encode('utf-8')).hexdigest()

    def as_dict(self) -> dict:
        return {'seed': self.seed, 'team': self.team, 'slot': self.slot}
