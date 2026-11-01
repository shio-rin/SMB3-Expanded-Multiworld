# SPDX-License-Identifier: MPL-2.0
"""Explicit menu certificate reconstruction. Never edits the production recipe."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ASSEMBLER = 'd6c16c39e1ffe4b46896726c738b5a8654e9dac3389e4439597582e1b97f4501'

def assemble_menu(text, assembler):
    assembler = Path(assembler).resolve()
    if hashlib.sha256(assembler.read_bytes()).hexdigest() != ASSEMBLER:
        raise ValueError('UI assembler identity')
    key = hashlib.sha256(text.encode()).hexdigest()
    with tempfile.TemporaryDirectory() as folder:
        asm = Path(folder) / 'menu.asm'
        asm.write_text(text, encoding='utf-8', newline='\n')
        result = subprocess.run([str(assembler), asm.name], cwd=folder, capture_output=True, text=True, check=True)
        if 'error' in (result.stdout + result.stderr).lower():
            raise ValueError(result.stdout + result.stderr)
        data = asm.with_suffix('.nes').read_bytes()
        sy = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\da-fA-F]+)', asm.with_suffix('.fns').read_text(), re.M)}
        declarations = ((26, 'UiControlHook', 'UiControlHookEnd'), (26, 'UiStatusHook', 'UiStatusHookEnd'), (26, 'UiHelpers', 'UiHelpersEnd'), (53, 'UiControl', 'UiAllCodeEnd'), (53, 'UiEntry', 'UiEntryEnd'), (53, 'UiRowsLo', 'UiRowsEnd'))
        spans = []
        owned = set()
        for bank, start, end in declarations:
            a, b = (sy[start], sy[end])
            if not 40960 <= a < b <= 49152:
                raise ValueError('UI emitted span')
            offset = 16 + bank * 8192 + a - 40960
            spans.append([offset, data[offset:offset + b - a].hex()])
            owned.update(range(offset, offset + b - a))
        if any((v != 255 and i not in owned for i, v in enumerate(data[16:], 16))):
            raise ValueError('UI assembler emitted outside reviewed spans')
        record = dict(schema=1, source_text_sha256=key, assembler_sha256=ASSEMBLER, size=len(data), header=data[:16].hex(), spans=sorted(spans), symbols=sy, output_sha256=hashlib.sha256(data).hexdigest(), contains='project-authored code and text only; no source-ROM metatiles or graphics')
    return (json.dumps(record,sort_keys=True,separators=(",",":"))+"\n").encode()
