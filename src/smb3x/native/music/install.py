# SPDX-License-Identifier: MPL-2.0
"""Install hash-certified R3 banks using unchanged native dispatch."""
import hashlib

def install(rom, source, base, selection, pack_path=None, payloads=None):
    rows = selection['selected']
    if not rows:
        return None
    from ..music.private_provider import load, C
    if selection['catalogue_id'] != C['id'] or not 1 <= len(rows) <= 16:
        raise ValueError('R3 selection identity')
    if payloads is None:
        if pack_path is None:
            raise ValueError('Custom music requires a validated private R3 .smb3music pack')
        payloads = load(pack_path, [r['id'] for r in rows])
    if set(payloads) != {r['id'] for r in rows}:
        raise ValueError('Private native payload inventory')
    catalogue = {t['id']: t for t in C['tracks']}
    before = bytes(rom)
    mirror = source[16 + 29 * 8192 + 6144:16 + 30 * 8192]
    for i, row in enumerate(rows):
        t = catalogue[row['id']]
        data = payloads[row['id']]
        if row['bank'] != 32 + i or row['selector'] != 208 + i or len(data) != 6144 or (hashlib.sha256(data).hexdigest() != t['payload_sha256']) or (row['payload_sha256'] != t['payload_sha256']):
            raise ValueError('Unapproved private native music bank')
        off = 16 + (32 + i) * 8192
        if rom[off:off + 6144] != b'\xff' * 6144:
            raise ValueError('Occupied native music bank')
        rom[off:off + 8192] = data + mirror
    limit = 16 + 28 * 8192 + base['audio']['symbols']['M20CustomLimit'] - 40960
    if rom[limit] != 208:
        raise ValueError('Native custom selector source guard')
    rom[limit] = 208 + len(rows)
    start = 16 + 48 * 8192
    count = rom[start + 2047]
    lookup = {(rom[start + 2048 + i], rom[start + 2304 + i] + 256 * rom[start + 2560 + i]): i for i in range(count)}
    for row in selection['music']:
        key = (row['tileset'], row['layout'])
        if key not in lookup:
            raise ValueError('Unregistered custom music area: ' + row['id'])
        i = lookup[key]
        if rom[start + 2816 + i] != 0:
            raise ValueError('Existing music selector overwritten')
        rom[start + 2816 + i] = row['selector']
    if rom[start + 6144:start + 8192] != before[start + 6144:start + 8192]:
        raise ValueError('Content DPCM mirror changed')
    return dict(version='m244-r3-banks-1', catalogue_id=C['id'], compiler_sha256=C['compiler_sha256'], bank_hashes={r['id']: hashlib.sha256(rom[16 + r['bank'] * 8192:16 + (r['bank'] + 1) * 8192]).hexdigest() for r in rows}, event_fallback='unchanged native SMB3 overrides', custom_slots=len(rows), dpcm_sha256=hashlib.sha256(mirror).hexdigest())
