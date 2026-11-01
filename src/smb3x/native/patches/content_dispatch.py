# SPDX-License-Identifier: MPL-2.0
from ..certified_assembly import assemble_file
'Source-guarded content dispatch and background-only themed palette loader.'
from pathlib import Path
import json
import re
import subprocess
import tempfile
from ...planning.audio_allocation import THEMES as DEFAULT_THEMES
from ...shared.resources import RESOURCE_ROOT as ROOT

def install(rom, source, plan, registry, *, themes=None):
    THEMES = themes if themes is not None else DEFAULT_THEMES
    symbols = json.loads((ROOT / 'native/symbols/m20_symbols.json').read_text())
    text = (ROOT / 'native/asm/m20_content.asm').read_text()
    prelude = ''.join((f'{k} = ${v:04X}\n' for k, v in symbols.items() if re.search('\\b' + k + '\\b', text)))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'content.asm').write_text(prelude + text)
        run = assemble_file(tmp / 'content.asm')
        if 'error' in (run.stdout + run.stderr).lower():
            raise ValueError(run.stdout + run.stderr)
        local = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\dA-Fa-f]+)', (tmp / 'content.fns').read_text(), re.M)}
        data = (tmp / 'content.nes').read_bytes()

    def patch(bank, cpu, origin, old, new):
        off = 16 + bank * 8192 + cpu - origin
        if rom[off:off + len(old)] != old or len(old) != len(new):
            raise ValueError(f'Content source guard {bank}:{cpu:04x}')
        rom[off:off + len(new)] = new
        if bank in (30, 31):
            rom[off + 32 * 8192:off + 32 * 8192 + len(new)] = new
    for first, last, limit in [('ContentCall', 'ContentCallEnd', 57968), ('MusicContentCall', 'ContentWrappersEnd', 58048)]:
        lo = local[first]
        hi = local[last]
        if hi > limit:
            raise ValueError('Content fixed trampoline exceeds audited gap')
        off = 16 + 31 * 8192 + lo - 57344
        patch(31, lo, 57344, b'\xff' * (hi - lo), data[off:off + hi - lo])
    patch(30, 39117, 32768, bytes.fromhex('bdac97'), b' ' + local['MusicContentCall'].to_bytes(2, 'little'))
    patch(27, 47253, 40960, bytes.fromhex('adde7d'), b' ' + local['PaletteContentCall'].to_bytes(2, 'little'))
    bank = bytearray(b'\xff' * 8192)
    lo = local['ContentExtension']
    hi = local['ContentExtensionEnd']
    if not lo == 49152 < hi <= 50944:
        raise ValueError('Content extension exceeds allocation')
    bank[:hi - lo] = data[16 + 20 * 8192:16 + 20 * 8192 + hi - lo]
    bank[6144:] = source[16 + 29 * 8192 + 6144:16 + 30 * 8192]
    rows = plan['music']
    if len(rows) > 127:
        raise ValueError('Content lookup supports at most 127 unique areas')
    bank[2047] = len(rows)
    themes = {t['id']: i + 1 for i, t in enumerate(THEMES)}
    pal = {p['area']: p['theme'] for p in plan['palettes']}
    for i, row in enumerate(rows):
        for page, value in [(2048, row['tileset']), (2304, row['layout'] & 255), (2560, row['layout'] >> 8), (2816, row['selector'] if row['custom'] or row['reason'] == 'inherited-parent' else 0), (3072, themes.get(pal[row['id']], 0))]:
            bank[page + i] = value
    bank[3328:3584] = bytes(256)
    bank[3584:3592] = bytes(8)
    for t in THEMES:
        values = t['background']
        if len(values) != 16 or any((type(v) is not int or not 0 <= v < 64 or v % 16 == 13 for v in values)) or len({values[i] for i in (0, 4, 8, 12)}) != 1:
            raise ValueError('Unsafe theme palette')
        bank[3328 + themes[t['id']] * 16:3328 + themes[t['id']] * 16 + 16] = bytes(values)
    for world, theme in plan['map_themes'].items():
        bank[3584 + int(world) - 1] = themes[theme]
    registry.reserve('content-music-palette-lookup', 48, 0, 8192)
    rom[16 + 48 * 8192:16 + 49 * 8192] = bank
    return {'symbols': local, 'code_bytes': hi - lo, 'areas': len(rows), 'themes': themes, 'bank': 48}
