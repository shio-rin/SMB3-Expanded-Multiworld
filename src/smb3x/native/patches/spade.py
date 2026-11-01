# SPDX-License-Identifier: MPL-2.0
"""Static Spade's NMI must restore its C000 caller after the shared sound tick.

Southbird PRG022:$CF9D calls Sound_Engine_Begin from bank22. The accepted
dispatcher selects bank29 at C000 even for native music. Unlike the ordinary
fixed-bank NMI path, Spade returns directly into C000 before restoring it.
The wrapper lives in PRG028's source-declared unused tail and changes no music.
"""
CALL_OFFSET = 16 + 22 * 8192 + 3997
WRAPPER_OFFSET = 16 + 28 * 8192 + 8118
WRAPPER = bytes.fromhex('2000A020D1FF60')
MAP_OFFSET = 16 + 28 * 8192 + 7729
MAP_ORIGINAL = bytes.fromhex('48A9468D0080688D018060')
SAFE_MAP_OFFSET = 16 + 28 * 8192 + 8125
SAFE_MAP = bytes.fromhex('48A9468D21078D0080688D018060')

def install(rom, source):
    if source[CALL_OFFSET:CALL_OFFSET + 3] != bytes.fromhex('2000A0') or rom[CALL_OFFSET:CALL_OFFSET + 3] != bytes.fromhex('2000A0'):
        raise ValueError('Static Spade original sound-call guard')
    if source[WRAPPER_OFFSET:WRAPPER_OFFSET + len(WRAPPER)] != b'\xff' * len(WRAPPER) or rom[WRAPPER_OFFSET:WRAPPER_OFFSET + len(WRAPPER)] != b'\xff' * len(WRAPPER):
        raise ValueError('Static Spade unused bank28 tail guard')
    rom[CALL_OFFSET:CALL_OFFSET + 3] = bytes.fromhex('20B6BF')
    rom[WRAPPER_OFFSET:WRAPPER_OFFSET + len(WRAPPER)] = WRAPPER
    if rom[MAP_OFFSET:MAP_OFFSET + len(MAP_ORIGINAL)] != MAP_ORIGINAL:
        raise ValueError('Shared dispatcher bank-selection guard')
    if source[SAFE_MAP_OFFSET:SAFE_MAP_OFFSET + len(SAFE_MAP)] != b'\xff' * len(SAFE_MAP) or rom[SAFE_MAP_OFFSET:SAFE_MAP_OFFSET + len(SAFE_MAP)] != b'\xff' * len(SAFE_MAP):
        raise ValueError('Safe mapper tail guard')
    rom[MAP_OFFSET:MAP_OFFSET + len(MAP_ORIGINAL)] = bytes.fromhex('4CBDBF') + b'\xea' * (len(MAP_ORIGINAL) - 3)
    rom[SAFE_MAP_OFFSET:SAFE_MAP_OFFSET + len(SAFE_MAP)] = SAFE_MAP
    return {'version': 'm232-static-spade-1', 'call': {'bank': 22, 'cpu': 'CF9D', 'size': 3}, 'wrapper': {'bank': 28, 'cpu': 'BFB6', 'size': len(WRAPPER)}, 'irq_safe_mapper': {'bank': 28, 'cpu': 'BFBD', 'size': len(SAFE_MAP)}, 'ram_bytes': 0}
