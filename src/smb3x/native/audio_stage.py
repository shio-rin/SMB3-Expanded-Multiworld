# SPDX-License-Identifier: MPL-2.0
from .certified_assembly import assemble_file
'Expand the native audio banks and install guarded music interfaces.'
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from ..shared.resources import RESOURCE_ROOT as ROOT
from ..shared.identity import Identity
from .rom import verify_base, digest
from .allocation import expand, make_bps, apply_bps, Registry
from ..native.music.score.arrangement import compile_arrangement
PATCH_VERSION = 'm20-native-1'

def assemble_audio():
    symbols = json.loads((ROOT / 'native/symbols/m20_symbols.json').read_text())
    source = (ROOT / 'native/asm/m20_audio.asm').read_text()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        prelude = ''.join((f'{name} = ${value:04X}\n' for name, value in symbols.items() if re.search('\\b' + name + '\\b', source)))
        (tmp / 'audio.asm').write_text(prelude + source)
        run = assemble_file(tmp / 'audio.asm')
        if 'error' in (run.stdout + run.stderr).lower() or not (tmp / 'audio.nes').exists():
            raise ValueError(run.stdout + run.stderr)
        local = {k: int(v, 16) for k, v in re.findall('^(\\w+)\\s*=\\s*\\$([\\dA-Fa-f]+)', (tmp / 'audio.fns').read_text(), re.M)}
        start = local['AudioExtension']
        end = local['AudioExtensionEnd']
        if start != 48663 or not start < end <= 49152:
            raise ValueError('Audio extension exceeds source-audited span')
        data = (tmp / 'audio.nes').read_bytes()
        off = 16 + 28 * 8192 + start - 40960
        if any((v != 255 for v in data[16:off] + data[off + end - start:])):
            raise ValueError('Unexpected audio assembly outside allocation')
        return (data[off:off + end - start], local, symbols)

def expand_audio(source, identity, patched, base, songs=(), *, audiovisual=None, pack=None, offline_fixture=False, **settings):
    verify_base(source)
    if offline_fixture and (not identity.seed.startswith('SMB3-M20-OFFLINE-FIXTURE-')):
        raise ValueError('Offline switch requires a dedicated fixture identity')
    if len(songs) > 16:
        raise ValueError('At most 16 allocated song banks')
    from ..planning.audio_allocation import validate
    av_settings = validate(audiovisual)
    cosmetics = dict(settings.get('cosmetics') or {})
    for kind in ('level', 'overworld'):
        if av_settings[kind + '_palette_style'] == 'constrained':
            cosmetics[kind + '_palette_shuffle'] = 'constrained'
    settings['cosmetics'] = cosmetics
    if pack is not None:
        from ..native.music.score.pack import verify_pack
        verify_pack(pack)
    av_plan = None
    if audiovisual is not None:
        from ..planning.audio_allocation import plan
        av_plan, songs = plan(identity.seed, base['level_shuffle'], pack, audiovisual, base['cosmetics'])
    expanded = expand(source, patched)
    ledger = Registry()
    for bank in (30, 62):
        marker = 16 + bank * 8192 + 7952
        if expanded[marker:marker + 8] != b'SMB3APK\x00':
            raise ValueError('marker source guard')
        expanded[marker:marker + 8] = b'SMB3APL\x00'
        if offline_fixture:
            expanded[marker + 11] = expanded[marker + 11] & ~3 | 2
    for bank in range(32):
        ledger.reserve('accepted-core', bank, 0, 8192)
    for bank in (62, 63):
        ledger.reserve('fixed-mirror', bank, 0, 8192)
    code, local, symbols = assemble_audio()
    code = bytearray(code)
    code[local['M20CustomLimit'] - local['AudioExtension']] = 208 + len(songs)
    code = bytes(code)

    def patch(bank, cpu, origin, expected, data):
        off = 16 + bank * 8192 + cpu - origin
        if expanded[off:off + len(expected)] != expected or len(expected) != len(data):
            raise ValueError(f'M20 source guard {bank}:{cpu:04x}')
        expanded[off:off + len(data)] = data
        if bank in (30, 31):
            mirror = off + 32 * 8192
            if expanded[mirror:mirror + len(expected)] != expected:
                raise ValueError('Fixed mirror guard')
            expanded[mirror:mirror + len(data)] = data
    off = 16 + 28 * 8192 + 7703
    assert source[off:off + 3] == bytes.fromhex('bdf799')
    patch(28, 48663, 40960, source[off:off + len(code)], code)
    for bank, origin, cpu, before, target in [(28, 40960, 41092, b' ' + symbols['Sound_PlayMusic'].to_bytes(2, 'little'), 'AudioTick'), (31, 57344, symbols['SndMus_QueueSet2B'], b'\x8d' + symbols['SndCur_Music2'].to_bytes(2, 'little'), 'QueueMusic'), (31, 57344, symbols['SndMus2B_LoadNext'], b'\xb9' + (symbols['Music_Set2B_IndexOffs'] - 1).to_bytes(2, 'little'), 'LoadCustomHeader'), (31, 57344, symbols['SndMus2A_LoadNext'], b'\xb9' + (symbols['Music_Set1_Set2A_IndexOffs'] - 1).to_bytes(2, 'little'), 'LoadEventHeader')]:
        patch(bank, cpu, origin, before, bytes([32 if target == 'AudioTick' else 76]) + local[target].to_bytes(2, 'little'))
    tracks = []
    for index, song in enumerate(songs):
        blocks, info = compile_arrangement(song)
        bank = 32 + index
        data = bytearray(b'\xff' * 8192)
        data[6144:] = source[16 + 29 * 8192 + 6144:16 + 30 * 8192]
        data[:3] = bytes([1, len(blocks), 1 + info['loop_section']])
        cursor = 512
        allocation = []
        for i, (blob, record) in enumerate(blocks):
            if cursor + len(blob) > 6144:
                raise ValueError(f"Song exceeds 5632-byte native sequence budget: {song['title']}")
            data[17 + i] = i * 7
            o = record['offsets']
            header = bytes([48]) + (49152 + cursor).to_bytes(2, 'little') + bytes([o['triangle'], o['pulse1'], o['noise'], 0])
            data[64 + 7 * i:71 + 7 * i] = header
            data[cursor:cursor + len(blob)] = blob
            allocation.append({**record, 'address': 49152 + cursor})
            cursor += len(blob)
        ledger.reserve('song:' + song['title'], bank, 0, 6144)
        ledger.reserve('original-dpcm-mirror', bank, 6144, 2048)
        expanded[16 + bank * 8192:16 + (bank + 1) * 8192] = data
        tracks.append({**info, 'selector': 208 + index, 'bank': bank, 'used_bytes': cursor, 'sequence_capacity': 5632, 'sections': allocation})
    content_extension = None
    if av_plan is not None:
        from .patches.content_dispatch import install
        content_extension = install(expanded, source, av_plan, ledger)
    target = bytes(expanded)
    assert target[16 + 524288:] == source[262160:]
    assert target[16 + 62 * 8192:16 + 64 * 8192] == target[16 + 30 * 8192:16 + 32 * 8192]
    config = {k: base[k] for k in ('identity', 'session', 'goal', 'progression', 'cosmetics', 'level_shuffle', 'classic_compiler_sha256', 'assembly')}
    config.update(patch_version=PATCH_VERSION, protocol=9, offline_fixture=bool(offline_fixture), architecture='mmc3-512k-fixed-mirror-c000-song-v1', audio={'tracks': tracks, 'extension_bytes': len(code), 'symbols': local}, allocation=[r.__dict__ for r in ledger.rows], m20_sources={__file__.replace('\\', '/').rsplit('/', 1)[-1]: digest(Path(__file__).read_bytes())['sha256']})
    config['m20_sources']['planning/data/music_primary_m20.json'] = digest((ROOT / 'planning/data/music_primary_m20.json').read_bytes())['sha256']
    config.update(audiovisual=av_plan, content_extension=content_extension, song_pack=pack)
    return (target, config)
