# SPDX-License-Identifier: MPL-2.0
"""Strict PRG1 validation and deterministic BPS1 delta patches (no source ROM)."""
from __future__ import annotations
import hashlib
import json
import struct
import zlib
from dataclasses import dataclass
PAYLOAD_SHA1 = 'BB894D104C796F69BA16587EB66C0275F5C2FC02'
PAYLOAD_CRC = 778240493
HEADER = bytes.fromhex('4E45531A101040000000000000000000')

def digest(data: bytes) -> dict:
    return {'sha1': hashlib.sha1(data).hexdigest().upper(), 'sha256': hashlib.sha256(data).hexdigest(), 'crc32': f'{zlib.crc32(data):08X}', 'size': len(data)}

def verify_base(data: bytes) -> bytes:
    if len(data) != 393232 or data[:16] != HEADER:
        raise ValueError('Expected canonical iNES1 PRG1: mapper 4, 256K PRG/128K CHR, no trainer/battery/trailer')
    payload = data[16:]
    if hashlib.sha1(payload).hexdigest().upper() != PAYLOAD_SHA1 or zlib.crc32(payload) != PAYLOAD_CRC:
        raise ValueError('Incorrect SMB3 USA PRG1 revision/payload')
    return payload

def prg_offset(bank: int, cpu: int, origin: int) -> int:
    if not (0 <= bank < 32 and origin in (32768, 40960, 49152, 57344) and (origin <= cpu < origin + 8192)):
        raise ValueError('Invalid 8K bank/CPU mapping')
    return 16 + bank * 8192 + cpu - origin

@dataclass(frozen=True)
class Edit:
    offset: int
    before: bytes
    after: bytes
    name: str

def apply_edits(source: bytes, edits: list[Edit]) -> bytes:
    verify_base(source)
    output = bytearray(source)
    end = 16
    for edit in sorted(edits, key=lambda e: e.offset):
        if not edit.before or len(edit.before) != len(edit.after):
            raise ValueError('Patch must be nonempty and size preserving')
        if edit.offset < end or edit.offset + len(edit.after) > 16 + 262144:
            raise ValueError('Overlapping/out-of-PRG patch')
        end = edit.offset + len(edit.after)
        if source[edit.offset:end] != edit.before:
            raise ValueError(f'Unexpected patch-site bytes: {edit.name}')
        output[edit.offset:end] = edit.after
    return bytes(output)

def _number(value: int) -> bytes:
    result = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        if value == 0:
            result.append(byte | 128)
            return bytes(result)
        result.append(byte)
        value -= 1

def make_bps(source: bytes, target: bytes, metadata: dict) -> bytes:
    if len(source) != len(target):
        raise ValueError('patches are size preserving')
    meta = json.dumps(metadata, sort_keys=True, separators=(',', ':')).encode()
    patch = bytearray(b'BPS1' + _number(len(source)) + _number(len(target)) + _number(len(meta)) + meta)
    pos = 0
    while pos < len(target):
        same = source[pos] == target[pos]
        end = pos + 1
        while end < len(target) and (source[end] == target[end]) == same:
            end += 1
        patch.extend(_number(end - pos - 1 << 2 | (0 if same else 1)))
        if not same:
            patch.extend(target[pos:end])
        pos = end
    patch.extend(struct.pack('<II', zlib.crc32(source), zlib.crc32(target)))
    patch.extend(struct.pack('<I', zlib.crc32(patch)))
    return bytes(patch)

def apply_bps(source: bytes, patch: bytes) -> bytes:
    """Read the deliberately restricted SourceRead/TargetRead BPS we emit."""
    if len(patch) < 19 or patch[:4] != b'BPS1' or zlib.crc32(patch[:-4]) != struct.unpack('<I', patch[-4:])[0]:
        raise ValueError('Invalid BPS signature/checksum')
    if zlib.crc32(source) != struct.unpack('<I', patch[-12:-8])[0]:
        raise ValueError('BPS source checksum mismatch')
    pos = 4

    def number():
        nonlocal pos
        value, shift = (0, 1)
        for _ in range(10):
            if pos >= len(patch) - 12:
                raise ValueError('Truncated BPS')
            byte = patch[pos]
            pos += 1
            value += (byte & 127) * shift
            if byte & 128:
                return value
            shift <<= 7
            value += shift
        raise ValueError('Oversized BPS integer')
    if number() != len(source):
        raise ValueError('BPS source size mismatch')
    size = number()
    if size != len(source):
        raise ValueError('BPS output must preserve size')
    metadata_size = number()
    pos += metadata_size
    if pos > len(patch) - 12:
        raise ValueError('Truncated metadata')
    out = bytearray()
    while len(out) < size:
        command = number()
        count, mode = ((command >> 2) + 1, command & 3)
        if len(out) + count > size:
            raise ValueError('BPS output overflow')
        if mode == 0:
            out.extend(source[len(out):len(out) + count])
        elif mode == 1:
            if pos + count > len(patch) - 12:
                raise ValueError('Truncated target data')
            out.extend(patch[pos:pos + count])
            pos += count
        else:
            raise ValueError('Unsupported BPS copy mode')
    if pos != len(patch) - 12 or zlib.crc32(out) != struct.unpack('<I', patch[-8:-4])[0]:
        raise ValueError('BPS target checksum/trailing data mismatch')
    return bytes(out)
