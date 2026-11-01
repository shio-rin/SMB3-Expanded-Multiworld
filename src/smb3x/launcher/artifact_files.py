# SPDX-License-Identifier: MPL-2.0
"""Shared preparation helpers; existing-output refusal is unchanged."""
import hashlib, json

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fresh(path):
    path = path.resolve()
    if path.exists():
        raise ValueError('Output already exists. Choose a new folder; existing sessions are preserved.')
    path.mkdir(parents=True)
    return path

def dump(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write('\n')
