# SPDX-License-Identifier: MPL-2.0
"""Source-bound project-authored UI code; normal player builds need no assembler."""
from pathlib import Path
import hashlib, json, os, re, subprocess
from ..shared.resources import RESOURCE_ROOT as ROOT
ASSEMBLER = 'd6c16c39e1ffe4b46896726c738b5a8654e9dac3389e4439597582e1b97f4501'

def compile_ui(text):
    key = hashlib.sha256(text.encode()).hexdigest()
    path = ROOT / 'native/certificates/m245-menu-native.json'
    cached = json.loads(path.read_text()) if path.exists() else None
    if cached and cached['source_text_sha256'] == key:
        if cached['schema'] != 1 or cached['assembler_sha256'] != ASSEMBLER:
            raise ValueError('Unsupported UI compiled contract')
        data = bytearray(b'\xff' * cached['size'])
        data[:16] = bytes.fromhex(cached['header'])
        end = 16
        for offset, value in cached['spans']:
            value = bytes.fromhex(value)
            if offset < end or offset + len(value) > len(data):
                raise ValueError('UI compiled span bounds')
            data[offset:offset + len(value)] = value
            end = offset + len(value)
        if hashlib.sha256(data).hexdigest() != cached['output_sha256']:
            raise ValueError('UI compiled integrity')
        return (bytes(data), cached['symbols'], key)
    raise ValueError('Uncertified UI source; regenerate and review its native certificate before building')
