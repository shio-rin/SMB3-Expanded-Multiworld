# SPDX-License-Identifier: MPL-2.0
"""Compile versioned by-type plans into exact native host/content bindings."""
from .fortress import install as install_special
from .bros import install as install_bros
from .military import install as install_military
from .mixed_fortresses import install as install_mixed

def bindings(plan, records):
    result = dict(context=[], orbs=[], bros=[], military=[], table_edits=[])
    for kind, assignments in plan['pools'].items():
        if kind not in ('fortresses', 'bros', 'military'):
            raise ValueError('Uncertified special pool')
        for a in assignments:
            c = records[a['assigned_content']]
            p = records[a['original_content']]
            if c['pool'] != kind or p['pool'] != kind or a['physical_location_id'] != p['physical_location_id']:
                raise ValueError('Special host/content category mismatch')
            entry = {k: c[k] for k in ('tileset', 'layout', 'objects')}
            if entry != a['native_entry']:
                raise ValueError('Special native entry differs from source')
            e = p['physical_entry']
            host = dict(world=p['original_world'] - 1, hi=int(e['x_hi'], 16), x=int(e['x'], 16), y=int(e['y'], 16))
            if kind == 'bros':
                result['bros'].append(dict(world=host['world'], slot=p['slot'], host_type=p['physical_object_type'], battle_type=c['physical_object_type'], **entry, prize=p['source_prize'], receipt=int(p['physical_clear']['receipt_bit'])))
                continue
            result['context'].append(dict(**host, source_world=c['original_world'] - 1))
            for key, value in dict(ByRowType=bytes([int(p['original_table_bytes']['ByRowType'], 16) & 240 | c['tileset']]), LevelLayout=c['layout'].to_bytes(2, 'little'), ObjSets=c['objects'].to_bytes(2, 'little')).items():
                result['table_edits'].append(dict(offset=p['table_sites'][key], before=p['original_table_bytes'][key], after=value.hex()))
            effects = p['native_effect_indices']
            if len(effects) > 1:
                raise ValueError('Ambiguous host map effect')
            effect = effects[0] if effects else 0
            bosses = [n for n in c['content_graph']['nodes'] if any((e['name'] in ('OBJ_BOOMBOOMJUMP', 'OBJ_BOOMBOOMFLY') for e in n['enemy']['records']))]
            if len(bosses) > 1 or (kind == 'fortresses' and (len(bosses) != 1 or not effect)):
                raise ValueError('Ambiguous source terminal or fortress host effect')
            if bosses:
                result['orbs'].append(dict(**host, tileset=bosses[0]['tileset'], layout=bosses[0]['layout'], objects=bosses[0]['objects'], effect=effect, secret=c['content_id'] == 'smb3-prg1-w1-fortress'))
            if kind == 'military':
                result['military'].append(dict(slot=p['slot'], host_type=p['physical_object_type'], hi=host['hi'], x=host['x'], y=host['y'], treasure=c['stage'] == 'big-tanks', effect=effect, receipt=int(p['physical_clear']['receipt_bit'])))
    return result

def install(target, source, rows):
    rom = bytearray(target)
    for e in rows['table_edits']:
        before = bytes.fromhex(e['before'])
        after = bytes.fromhex(e['after'])
        o = e['offset']
        if len(before) != len(after) or rom[o:o + len(before)] != before:
            raise ValueError('Special physical source table guard')
        rom[o:o + len(after)] = after
    result = dict(orbs=install_special(rom, source, rows['orbs']), bros=install_bros(rom, source, rows['bros']), military=install_military(rom, source, rows['military']), mixed=install_mixed(rom, source, rows.get('mixed', [])), physical_table_edits=rows['table_edits'])
    target[:] = rom
    return result

def add_mixed(rows, assignments, records, contract):
    allowed = {r['content_id'] for r in contract['ordinary_donors'] if r['cross_type_candidate']}
    rows['mixed'] = []
    for a in assignments:
        c, p = (records[a['assigned_content']], records[a['original_content']])
        source_fort = c.get('pool') == 'fortresses'
        host_fort = p.get('pool') == 'fortresses'
        if not source_fort and (not host_fort):
            continue
        e = p['physical_entry']
        host = dict(world=p['original_world'] - 1, hi=int(e['x_hi'], 16), x=int(e['x'], 16), y=int(e['y'], 16))
        effect = p['native_effect_indices'][0] if host_fort else 0
        if source_fort:
            bosses = [n for n in c['content_graph']['nodes'] if any((e['name'] in ('OBJ_BOOMBOOMJUMP', 'OBJ_BOOMBOOMFLY') for e in n['enemy']['records']))]
            if len(bosses) != 1:
                raise ValueError('Mixed fortress terminal ambiguity')
            rows['orbs'].append(dict(**host, **{k: bosses[0][k] for k in ('tileset', 'layout', 'objects')}, effect=effect, secret=c['content_id'] == 'smb3-prg1-w1-fortress'))
        else:
            if c['content_id'] not in allowed:
                raise ValueError('Uncertified mixed ordinary terminal')
            rows['mixed'].append(dict(**host, **{k: c[k] for k in ('tileset', 'layout', 'objects')}, effect=effect))
