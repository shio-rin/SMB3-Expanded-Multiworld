# SPDX-License-Identifier: MPL-2.0
"""Guarded original Player_Die dispatcher, ported without research state/RPC."""
from hashlib import sha256
CONTRACT = 'm25-death-dispatch-1'
REQUEST = 31760

def install(original):
    rom = bytearray(original)
    off = 16 + 6636
    hook = 16 + 8 * 8192 + 1144
    if sha256(rom[off - 3:16 + 6677]).hexdigest() != '3e403d78d5cb0b680520a8edc8acab56a76d131358bf9a4e4ff7ebfed76be0b8' or rom[hook:hook + 3] != bytes.fromhex('20c2a4'):
        raise ValueError('death dispatcher source ownership mismatch')
    code = bytes.fromhex('ad107cc9d1d013a9008d107cad0a07f009a5f105ced003207cda4cc2a4')
    assert len(code) == 29
    rom[off:off + 29] = code
    rom[hook:hook + 3] = bytes.fromhex('20ecd9')
    return (bytes(rom), dict(contract=CONTRACT, request_ram=REQUEST, edits=[dict(bank=0, cpu=55788, offset=off, size=29), dict(bank=8, cpu=42104, offset=hook, size=3)]))
