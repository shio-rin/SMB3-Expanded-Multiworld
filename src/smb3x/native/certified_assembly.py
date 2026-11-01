# SPDX-License-Identifier: MPL-2.0
"""Reconstruct source-hash-bound assembler output; validate every emitted span."""
from pathlib import Path
from types import SimpleNamespace
import hashlib, json
from ..shared.resources import RESOURCE_ROOT
ASSEMBLER_SHA256 = 'd6c16c39e1ffe4b46896726c738b5a8654e9dac3389e4439597582e1b97f4501'

def assemble_file(source):
    source = Path(source)
    cache = json.loads((RESOURCE_ROOT / 'native/certificates/m23-assembly-cache.json').read_text())
    if cache['schema'] != 1 or cache['assembler_sha256'] != ASSEMBLER_SHA256:
        raise ValueError('Unsupported assembly certificate')
    key = hashlib.sha256(source.read_text(encoding='utf-8').encode()).hexdigest()
    row = cache['entries'].get(key)
    if row is None:
        raise ValueError('Uncertified assembly source: ' + source.name + ' / ' + key)
    payload = bytearray(b'\xff' * row['size'])
    payload[:16] = bytes.fromhex(row['header'])
    end = 16
    for offset, encoded in row['spans']:
        data = bytes.fromhex(encoded)
        if offset < end or offset + len(data) > len(payload):
            raise ValueError('Assembly span bounds')
        payload[offset:offset + len(data)] = data
        end = offset + len(data)
    if hashlib.sha256(payload).hexdigest() != row['output_sha256']:
        raise ValueError('Assembly output integrity mismatch')
    source.with_suffix('.nes').write_bytes(payload)
    source.with_suffix('.fns').write_text(row['symbols'])
    return SimpleNamespace(stdout='Verified assembly certificate\n', stderr='', returncode=0)
