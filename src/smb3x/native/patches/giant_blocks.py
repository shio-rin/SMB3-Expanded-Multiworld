# SPDX-License-Identifier: MPL-2.0
"""Keep giant reward command14 in bank51, independent of special shuffle.

The shared E29F trampoline routes commands >=10 to bank52 when special shuffle
is installed. Command14 already belongs to bank52's special completion path.
The giant selector belongs to bank51. It uses ordinary reward command0 with
explicit controller-slot, actor-ID and native-bank guards before its lookup.
No shared command, collision code, source object or hazard table is changed.
"""
from hashlib import sha256
from pathlib import Path
import json
CONTRACT = 'm26-giant-bank-call-1'
ENTRY = 50048
OLD = bytes.fromhex('c00ef0034c00d7bda3008d0000bd88008d01002092c0c901f008aded00f003a91e60a90d60')
CODE = bytes.fromhex('c000d030e004d02cad2007c902d025bd7106c947d01e') + OLD[7:] + bytes.fromhex('4c00d7')
HOOK = bytes.fromhex('a00e209fe2eaeaea')

def install(target):
    from ...shared.resources import RESOURCE_ROOT as root
    cert = json.loads((root / 'native/certificates/m26-giant-assembly.json').read_bytes())
    if sha256((root / 'native/asm/m26_giant.asm').read_bytes().replace(b'\r\n', b'\n')).hexdigest() != cert['source_lf_sha256'] or CODE.hex() != cert['code'] or sha256(CODE).hexdigest() != cert['code_sha256']:
        raise ValueError('Giant authored assembly binding')
    rom = bytearray(target)
    edits = []
    if len(rom) != 786448:
        raise ValueError('giant correction requires PRG512/CHR256')
    before = OLD + b'\xff' * (len(CODE) - len(OLD))
    offset = 16 + 51 * 8192 + (ENTRY & 8191)
    if rom[offset:offset + len(CODE)] != before:
        raise ValueError('Giant selector allocation ownership')
    rom[offset:offset + len(CODE)] = CODE
    edits.append(dict(bank=51, address=ENTRY, offset=offset, before=before.hex(), after=CODE.hex()))
    offset = 16 + 2 * 8192 + 930
    if rom[offset:offset + len(HOOK)] != HOOK:
        raise ValueError('Giant reward hook ownership')
    after = bytes.fromhex('a000209fe2eaeaea')
    rom[offset:offset + len(HOOK)] = after
    edits.append(dict(bank=2, address=41890, offset=offset, before=HOOK.hex(), after=after.hex()))
    assert rom[524304:] == target[524304:]
    return (bytes(rom), dict(contract=CONTRACT, entry=ENTRY, code_sha256=sha256(CODE).hexdigest(), edits=edits, new_ram=0, new_chr=0))
