# SPDX-License-Identifier: MPL-2.0
"""Propose source/output hash changes, then apply an explicitly reviewed proposal.

This updates ordinary text resources only. Native certificates and generated
binary data require their own reproducible generator and independent comparison.
Nothing is accepted simply because a new hash can be calculated.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'packaging/resources.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def propose():
    raw = RECIPE.read_bytes().replace(b'\r\n', b'\n')
    recipe = json.loads(raw)
    changes = []
    for section in ('resources', 'outer'):
        for name, row in sorted(recipe[section].items()):
            source = (ROOT / row['source']).resolve()
            if not source.is_relative_to(ROOT) or not source.is_file():
                raise ValueError('Invalid source: ' + row['source'])
            data = source.read_bytes().replace(b'\r\n', b'\n')
            source_hash = digest(data)
            for substitution in row.get('path_substitutions', []):
                old, new = substitution['before'].encode(), substitution['after'].encode()
                if data.count(old) != substitution['count']:
                    raise ValueError('Reviewed substitution no longer matches: ' + name)
                data = data.replace(old, new)
            if row['transform'] == 'crlf':
                data = data.replace(b'\n', b'\r\n')
            elif row['transform'] == 'managed-config':
                settings = json.loads(data)
                settings['PathEntries']['LastRomPath'] = '.'
                settings['UpdateAutoCheckEnabled'] = False
                data = encoded(settings)
            elif row['transform'] != 'lf':
                raise ValueError('Unknown transformation: ' + name)
            hashes = dict(source_lf_sha256=source_hash, output_sha256=digest(data))
            old = {k: row.get(k) for k in hashes}
            if old != hashes:
                protected = any(token in row['source'] for token in
                    ('assembly-cache', 'palette-assembly', 'interface-assembly', 'certificates/'))
                changes.append(dict(section=section, resource=name, source=row['source'],
                                    old=old, new=hashes, native_certificate=protected,
                                    native_authoring=row['source'].endswith('.asm'),
                                    requires_native_verification=protected or row['source'].endswith('.asm')))
    return dict(schema=1, recipe_sha256=digest(raw), changes=changes)


def apply(proposal):
    current = propose()
    if proposal != current:
        raise ValueError('Source or recipe changed since review; generate a new proposal')
    if any(row['native_certificate'] for row in proposal['changes']):
        raise ValueError('Native certificate change requires generator verification; this tool cannot approve it')
    recipe = json.loads(RECIPE.read_bytes())
    for row in proposal['changes']:
        recipe[row['section']][row['resource']].update(row['new'])
    RECIPE.write_bytes(encoded(recipe))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--propose', type=Path)
    group.add_argument('--apply', type=Path)
    args = parser.parse_args()
    if args.propose:
        if args.propose.exists():
            raise ValueError('Choose a new proposal path')
        args.propose.write_bytes(encoded(propose()))
    else:
        apply(json.loads(args.apply.read_bytes()))
