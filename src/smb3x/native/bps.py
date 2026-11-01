# SPDX-License-Identifier: MPL-2.0
"""Strict BPS decoder; accepted decoder stays unchanged."""
import zlib
from .allocation import make_bps

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
    if size not in (655376, 786448):
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
    if out[:4] != b'NES\x1a' or out[4] != 32 or out[5] not in (16, 32) or (len(out) != 16 + 524288 + out[5] * 8192):
        raise ValueError('target header')
    if out[6:16] != source[6:16]:
        raise ValueError('mapper/header mismatch')
    return bytes(out)
