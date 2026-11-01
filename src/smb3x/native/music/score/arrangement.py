# SPDX-License-Identifier: MPL-2.0
"""Bounded section compiler; reuses R3's strict schema-1 event encoder unchanged."""
import hashlib
from .score import compile_song, require


def compile_arrangement(song):
    require(isinstance(song, dict) and type(song.get('schema')) is int, 'score object with integer schema required')
    if song.get('schema') == 1:
        blob, info = compile_song(song)
        for ch, events in info['timeline'].items():
            for i, event in enumerate(events):
                event['source_event'] = f'channels.{ch}[{i}]'
        return [(blob, info)], dict(title=song['title'], loop_section=0,
            intro_ticks=0, loop_ticks=info['ticks'], hurry_intro_ticks=0,
            hurry_loop_ticks=info['hurry_ticks'], sequence_bytes=len(blob),
            sha256=hashlib.sha256(blob).hexdigest())
    require(set(song) == {'schema', 'title', 'provenance', 'loop_section', 'sections'},
            'unknown/missing arrangement fields')
    require(type(song['schema']) is int and song['schema'] == 2, 'schema2 required')
    require(isinstance(song['title'], str) and bool(song['title'].strip()), 'title required')
    require(isinstance(song['provenance'], dict), 'provenance required')
    sections = song['sections']
    require(isinstance(sections, list) and 1 <= len(sections) <= 32, '1..32 sections required')
    loop = song['loop_section']
    require(type(loop) is int and 0 <= loop < len(sections), 'loop must name an existing section')
    compiled = []
    names = set()
    for i, section in enumerate(sections):
        require(isinstance(section, dict) and set(section) == {'id', 'tempo_row', 'channels'},
                f'section {i}: unknown/missing fields; ties and effects across boundaries unsupported')
        require(isinstance(section['id'], str) and section['id'] and section['id'] not in names,
                'unique section ID required')
        names.add(section['id'])
        # Every boundary is an explicit retrigger, never an inferred sustain/tie.
        block = dict(schema=1, title=song['title'], provenance=song['provenance'],
                     tempo_row=section['tempo_row'], loop=0, channels=section['channels'])
        require(type(section['tempo_row']) is int, 'integer tempo row required')
        require(isinstance(section['channels'], dict), 'channel object required')
        for events in section['channels'].values():
            require(isinstance(events, list) and all(isinstance(e, dict) for e in events), 'event objects required')
        blob, info = compile_song(block)
        info['section_id'] = section['id']
        for ch, events in info['timeline'].items():
            for j, event in enumerate(events):
                event['source_event'] = f'sections[{i}].channels.{ch}[{j}]'
        compiled.append((blob, info))
    def total(key, lo, hi):
        return sum(info[key] for _, info in compiled[lo:hi])
    return compiled, dict(title=song['title'], loop_section=loop,
        intro_ticks=total('ticks', 0, loop), loop_ticks=total('ticks', loop, len(sections)),
        hurry_intro_ticks=total('hurry_ticks', 0, loop),
        hurry_loop_ticks=total('hurry_ticks', loop, len(sections)),
        sequence_bytes=sum(len(b) for b, _ in compiled),
        sha256=hashlib.sha256(b''.join(b for b, _ in compiled)).hexdigest())


def plan_library(songs):
    """Three spare Set2B selectors, at most 36 seven-byte headers, no bank wrapping."""
    require(isinstance(songs, list) and 1 <= len(songs) <= 3, 'D0/E0/F0 only; 1..3 songs')
    plans = []
    cursor = 1  # native preincrement; index[0] is an unused sentinel
    for song in songs:
        blocks, report = compile_arrangement(song)
        require(cursor + len(blocks) <= 254, 'playlist end+2 would overflow')
        plans.append(dict(selector=0xd0 + 0x10 * len(plans), start=cursor,
                          end=cursor + len(blocks) - 1,
                          loop=cursor + report['loop_section'], blocks=blocks, report=report))
        cursor += len(blocks)
    require(sum(len(p['blocks']) for p in plans) <= 36, 'header offsets exceed byte range')
    return plans
