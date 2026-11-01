# SPDX-License-Identifier: MPL-2.0
"""Audited expansion and explicit feature ownership. Not a stage-data loader."""
from dataclasses import dataclass
import json
import struct
import zlib
from .rom import _number, verify_base
BANK_SIZE = 8192
PRG_SIZE = 524288

@dataclass(frozen=True)
class Allocation:
    owner: str
    bank: int
    start: int
    size: int

class Registry:

    def __init__(self):
        self.rows = []

    def reserve(self, owner, bank, start, size):
        if type(bank) is not int or not 0 <= bank < 64 or (not 0 <= start < BANK_SIZE) or (not 0 < size <= BANK_SIZE - start):
            raise ValueError('Invalid bank allocation')
        for old in self.rows:
            if old.bank == bank and start < old.start + old.size and (old.start < start + size):
                raise ValueError(f'Allocation overlap: {owner}/{old.owner}')
        row = Allocation(owner, bank, start, size)
        self.rows.append(row)
        return row

def expand(source, patched):
    verify_base(source)
    if len(patched) != len(source) or patched[:16] != source[:16] or patched[262160:] != source[262160:]:
        raise ValueError('Expansion requires a source-verified 256 KiB PRG patch and unchanged CHR')
    header = bytearray(source[:16])
    header[4] = 32
    prg = bytearray(b'\xff' * PRG_SIZE)
    prg[:262144] = patched[16:262160]
    prg[62 * BANK_SIZE:] = prg[30 * BANK_SIZE:32 * BANK_SIZE]
    return header + prg + patched[262160:]

def make_bps(source, target, metadata):
    """BPS SourceRead/TargetRead with explicit differing-size bounds."""
    meta = json.dumps(metadata, sort_keys=True, separators=(',', ':')).encode()
    patch = bytearray(b'BPS1' + _number(len(source)) + _number(len(target)) + _number(len(meta)) + meta)
    pos = 0
    while pos < len(target):
        same = pos < len(source) and source[pos] == target[pos]
        end = pos + 1
        while end < len(target) and (end < len(source) and source[end] == target[end]) == same:
            end += 1
        patch += _number(end - pos - 1 << 2 | (0 if same else 1))
        if not same:
            patch += target[pos:end]
        pos = end
    patch += struct.pack('<II', zlib.crc32(source), zlib.crc32(target))
    patch += struct.pack('<I', zlib.crc32(patch))
    return bytes(patch)

def apply_bps(source, patch):
    if len(patch) < 19 or patch[:4] != b'BPS1' or zlib.crc32(patch[:-4]) != int.from_bytes(patch[-4:], 'little'):
        raise ValueError('BPS signature/checksum')
    if zlib.crc32(source) != int.from_bytes(patch[-12:-8], 'little'):
        raise ValueError('BPS source checksum')
    pos = 4

    def number():
        nonlocal pos
        value = 0
        shift = 1
        for _ in range(10):
            if pos >= len(patch) - 12:
                raise ValueError('Truncated BPS integer')
            b = patch[pos]
            pos += 1
            value += (b & 127) * shift
            if b & 128:
                return value
            shift <<= 7
            value += shift
        raise ValueError('Oversized BPS integer')
    if number() != len(source):
        raise ValueError('BPS source size')
    size = number()
    if size != 16 + PRG_SIZE + 131072:
        raise ValueError('target size')
    metadata_size = number()
    pos += metadata_size
    if pos > len(patch) - 12:
        raise ValueError('BPS metadata bounds')
    out = bytearray()
    while len(out) < size:
        command = number()
        count = (command >> 2) + 1
        mode = command & 3
        if len(out) + count > size:
            raise ValueError('BPS output overflow')
        if mode == 0:
            if len(out) + count > len(source):
                raise ValueError('BPS source read overflow')
            out += source[len(out):len(out) + count]
        elif mode == 1:
            if pos + count > len(patch) - 12:
                raise ValueError('BPS target read overflow')
            out += patch[pos:pos + count]
            pos += count
        else:
            raise ValueError('Unsupported BPS mode')
    if pos != len(patch) - 12 or zlib.crc32(out) != int.from_bytes(patch[-8:-4], 'little'):
        raise ValueError('BPS target checksum')
    return bytes(out)
