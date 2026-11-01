# SPDX-License-Identifier: MPL-2.0
"""Accepted restoration-only PRG028 helper; no score, SFX or RAM redesign."""
from pathlib import Path
import hashlib, json
from ...shared.resources import RESOURCE_ROOT as ROOT
CONTRACT = 'm244-sfx-resume-1'
SOURCE_COMMIT = '46f62083af057307038d391eac2e94f0ff85fea0'
HELPER_SHA256 = '2ffe28ab930ea4dd1e8258bf664eefbfd45fab8ac8ce6b5db9a569991a5d824d'

def install(rom, source, base):
    row = json.loads((ROOT / 'native/certificates/m25-foundation-sfx-native.json').read_bytes())
    if row['contract'] != CONTRACT or row['source_commit'] != SOURCE_COMMIT:
        raise ValueError('Unknown restoration-only source contract')
    if hashlib.sha256((ROOT / 'native/asm/m244_sfx_resume.asm').read_bytes().replace(b'\r\n', b'\n')).hexdigest() != row['source_sha256']:
        raise ValueError('Restoration authored-source binding mismatch')
    if any((base['audio']['symbols'].get(k) != v for k, v in row['audio_symbols'].items())):
        raise ValueError('Restoration native dispatcher symbols changed')
    code = bytes.fromhex(row['code'])
    if len(code) != 171 or hashlib.sha256(code).hexdigest() != HELPER_SHA256 or row['code_sha256'] != HELPER_SHA256:
        raise ValueError('Restoration compiled helper integrity')
    if row['symbols']['ResumePulse1'] != 48843 or row['symbols']['ResumePulse2'] != 48856:
        raise ValueError('Restoration hook entry identity')
    before = bytes(rom)
    start = 16 + 28 * 8192 + 7883
    if rom[start:start + 171] != source[start:start + 171] or hashlib.sha256(source[start:start + 171]).hexdigest() != row['expected_helper_sha256']:
        raise ValueError('Restoration helper source/ownership guard')
    edits = []
    for cpu, label in ((41824, 'ResumePulse1'), (42041, 'ResumePulse2')):
        off = 16 + 28 * 8192 + cpu - 40960
        if rom[off:off + 3] != bytes.fromhex('8e1540'):
            raise ValueError('Restoration native stop-hook guard')
        target = row['symbols'][label]
        rom[off:off + 3] = b' ' + target.to_bytes(2, 'little')
        edits.append(dict(bank=28, cpu=cpu, size=3, offset=off, name=label))
    rom[start:start + 171] = code
    edits.append(dict(bank=28, cpu=48843, size=171, offset=start, name='restoration helper'))
    allowed = {e['offset'] + i for e in edits for i in range(e['size'])}
    if len(rom) != len(before) or any((i not in allowed for i, (a, b) in enumerate(zip(before, rom)) if a != b)):
        raise ValueError('Restoration escaped its accepted byte ranges')
    return dict(contract=CONTRACT, source_commit=SOURCE_COMMIT, helper_sha256=row['code_sha256'], helper_bytes=171, edits=edits, new_ram=0, pulse_swapping=False, score_payloads_changed=False)
