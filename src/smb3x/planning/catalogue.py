# SPDX-License-Identifier: MPL-2.0
"""Verified descriptor ancestry, independent of historical shuffle algorithms."""
from pathlib import Path
import hashlib, json
from ..shared.resources import DATA as ROOT

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def catalogue(version):
    raw = (ROOT / 'contents_m18.json').read_bytes()
    base = json.loads(raw)
    contents = {r['content_id']: r for r in base['contents']}
    if version == 'm18':
        return dict(CONTENTS=contents, REGISTRY=base, REGISTRY_HASH=hashlib.sha256(raw).hexdigest(), canonical=canonical)
    child = (ROOT / ('contents_' + version + '.json')).read_bytes()
    doc = json.loads(child)
    if doc['parent_sha256'] != hashlib.sha256(raw).hexdigest():
        raise ValueError('Content descriptor parent identity mismatch: ' + version)
    contents.update({r['content_id']: r for r in doc['contents']})
    return dict(CONTENTS=contents, REGISTRY=doc, REGISTRY_HASH=hashlib.sha256(child).hexdigest(), canonical=canonical)
