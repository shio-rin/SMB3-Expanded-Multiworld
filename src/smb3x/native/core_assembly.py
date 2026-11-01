# SPDX-License-Identifier: MPL-2.0
from .certified_assembly import assemble_file
'Assemble only project-authored code; extract explicitly bounded bank spans.'
from pathlib import Path
import re
import json
import subprocess
from .rom import Edit, prg_offset
from ..shared.resources import RESOURCE_ROOT as ROOT
SPANS = [(3, 40960, 'TreasureVisual', 'TreasureVisualEnd', 49088, 49152), (27, 40960, 'RewardCode', 'RewardCodeEnd', 47561, 49152), (25, 40960, 'ProgressionExtension', 'ProgressionExtensionEnd', 46368, 49152), (31, 57344, 'RewardStubs', 'RewardStubsEnd', 59665, 59776), (26, 40960, 'Controller', 'ControllerEnd', 46368, 49152), (30, 32768, 'DispatchStub', 'ShortStubsEnd', 40800, 40830), (30, 32768, 'InitializedStub', 'InitializedStubEnd', 40848, 40856), (30, 32768, 'EndingContinueStub', 'EndingContinueStubEnd', 40856, 40864), (30, 32768, 'BankCall', 'FixedEnd', 40886, 40960)]

def _assemble(directory) -> tuple[list[Edit], dict]:
    out = Path(directory)
    source = ROOT / 'native/asm/m191.asm'
    rows = json.loads((ROOT / 'planning/data/locations_m191.json').read_text())
    totals = []
    for regional in (False, True):
        enabled = [r for r in rows if r['enabled'] and (not r.get('hammer_required') or regional)]
        totals.extend((sum((r['world'] == w for r in enabled)) for w in range(1, 9)))
    (out / 'm191.asm').write_text(source.read_text().replace('; @M19.1_TRACKER_TOTALS', ' .db ' + ','.join(map(str, totals))))
    for name in ('m191.nes', 'm191.fns'):
        (out / name).unlink(missing_ok=True)
    result = assemble_file(out / 'm191.asm')
    if 'error' in (result.stdout + result.stderr).lower() or not (out / 'm191.nes').exists():
        raise ValueError('Assembly failed:\n' + result.stdout + result.stderr)
    symbols = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([0-9A-Fa-f]+)', (out / 'm191.fns').read_text(), re.M)}
    data = (out / 'm191.nes').read_bytes()
    edits, used = ([], set())
    for bank, origin, start, end, lower, upper in SPANS:
        lo, hi = (symbols[start], symbols[end])
        if lo != lower or not lo < hi <= upper:
            raise ValueError(f'Assembly exceeds allocation: {start} ${lo:04X}-${hi:04X}')
        offset = prg_offset(bank, lo, origin)
        edits.append(Edit(offset, b'\xff' * (hi - lo), data[offset:offset + hi - lo], start))
        used.update(range(offset, offset + hi - lo))
    if any((v != 255 and i not in used for i, v in enumerate(data[16:], 16))):
        raise ValueError('Assembler emitted outside declared spans')

    def hook(cpu, before, target, jump=False, suffix=b''):
        code = bytes([76 if jump else 32]) + symbols[target].to_bytes(2, 'little') + suffix
        original = bytes.fromhex(before)
        if len(original) != len(code):
            raise ValueError('Hook instruction boundary mismatch')
        edits.append(Edit(prg_offset(30, cpu, 32768), original, code, target + ' hook'))
    hook(34610, 'AC2907C00D', 'DispatchStub', suffix=b'\xea\xea')
    hook(34589, '20C3C3', 'PremapStub')
    hook(34174, '2084FD', 'ReloadStub', jump=True)
    hook(33952, 'A90A8D1F07', 'InitStub', suffix=b'\xea\xea')
    hook(34007, '2084FD', 'InitializedStub')
    hook(34607, '204AB4', 'MenuStatus')
    hook(37009, 'EE27074CA084', 'AirshipStub', jump=True, suffix=b'\xea\xea\xea')
    hook(36854, '8D0001', 'PeachRescueStub')
    for bank, cpu, before, target in [(1, 48844, '8DF37C', 'BowserDefeatStub')]:
        edits.append(Edit(prg_offset(bank, cpu, 40960), bytes.fromhex(before), b' ' + symbols[target].to_bytes(2, 'little'), target + ' hook'))
    for cpu, before, target, suffix in [(47276, '4C7CBB', 'EndingExitStub', b''), (48319, 'A9008D0120', 'EndingContinueStub', b'\xea\xea')]:
        edits.append(Edit(prg_offset(24, cpu, 40960), bytes.fromhex(before), b'L' + symbols[target].to_bytes(2, 'little') + suffix, target + ' hook'))
    for bank, origin, cpu, before, name in [(2, 40960, 46429, '99807D', 'HouseStub'), (3, 40960, 41764, '206CFD', 'TreasureStub'), (11, 40960, 46821, 'B95679', 'EnteredStub'), (11, 40960, 43959, '99157F', 'RemovedStub')]:
        edits.append(Edit(prg_offset(bank, cpu, origin), bytes.fromhex(before), b' ' + symbols[name].to_bytes(2, 'little'), name + ' hook'))
    edits.append(Edit(prg_offset(26, 42683, 40960), bytes.fromhex('A9038500'), b'L' + symbols['HammerGate'].to_bytes(2, 'little') + b'\xea', 'Regional Hammer activation guard'))
    edits.append(Edit(prg_offset(26, 42843, 40960), bytes.fromhex('4C1BA6'), b'L' + symbols['HammerFinish'].to_bytes(2, 'little'), 'Reusable Hammer native completion'))
    edits.append(Edit(prg_offset(26, 43080, 40960), bytes.fromhex('4C26A4'), b'L' + symbols['PoofFinish'].to_bytes(2, 'little'), 'Virtual tool animation completion'))
    edits.append(Edit(prg_offset(26, 42848, 40960), bytes.fromhex('AC2607'), bytes.fromhex('4C87A6'), 'Whistle use denied before consumption/wind'))
    edits.append(Edit(prg_offset(3, 41786, 40960), bytes.fromhex('AD6379A89D6906A9029DE77F'), b'L' + symbols['TreasureVisual'].to_bytes(2, 'little') + b'\xea' * 9, 'Scoped treasure display'))
    before = bytes.fromhex('BD6906AABDB1B4990102BDBEB4990502A903990202BD CBB4990602'.replace(' ', ''))
    code = bytes.fromhex('2080B54C95B508488A489848A2084C') + symbols['RewardCall'].to_bytes(2, 'little')
    edits.append(Edit(prg_offset(2, 46458, 40960), before, code + b'\xea' * (len(before) - len(code)), 'Scoped house flight display'))
    edits.append(Edit(prg_offset(26, 42298, 40960), bytes.fromhex('B9807D'), b' ' + symbols['StackUseStub'].to_bytes(2, 'little'), 'Validate quantity before native effect'))
    edits.append(Edit(prg_offset(26, 41072, 40960), bytes.fromhex('ADED03'), b' ' + symbols['StackDrawStub'].to_bytes(2, 'little'), 'Bounded native inventory count row'))
    edits.append(Edit(prg_offset(31, 64876, 57344), bytes.fromhex('48AC2607F002A023A21BB9807DF004C8CAD0F76899807D60'), bytes.fromhex('8DDF7BA2094C') + symbols['BankCall'].to_bytes(2, 'little') + b'\xea' * 16, 'Native grant gateway'))
    edits.append(Edit(prg_offset(26, 42523, 40960), bytes.fromhex('A91B850E'), b'L' + symbols['StackConsumeStub'].to_bytes(2, 'little') + b'\xea', 'Native successful consumption'))
    edits.append(Edit(prg_offset(27, 41463, 40960), bytes.fromhex('99807D'), bytes.fromhex('206CFD'), 'King letter grant through native stack gateway'))
    return (edits, symbols)

def assemble():
    import tempfile
    with tempfile.TemporaryDirectory(prefix='smb3x-assembly-') as directory:
        return _assemble(directory)
