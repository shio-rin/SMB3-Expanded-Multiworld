# SPDX-License-Identifier: MPL-2.0
"""Check explicit package closure and source-bound native input certificates."""
from pathlib import Path
import ast,hashlib,json
from tools.build_apworld import ROOT,resource,contained
from tools.rebuild_assembly import inputs

def check(root=ROOT):
    root=Path(root).resolve()
    recipe=json.loads((root/'packaging/resources.json').read_bytes())
    for section in ('resources','outer'):
        for name,row in recipe[section].items():
            contained(root,name)
            data=resource(root,name,row)
            if name.endswith('.py'):
                ast.parse(data,filename=name)
            if Path(name).suffix.lower() in ('.nes','.state','.srm','.apsmb3x','.smb3music'):
                raise ValueError('Player/private binary in source recipe: '+name)
            if any(token in name for token in ('music_catalogue','historical-seeds','private_music_provider.json')):
                raise ValueError('Private metadata in public recipe: '+name)
    cache=json.loads((root/'src/smb3x/native/certificates/m23-assembly-cache.json').read_bytes())
    actual={hashlib.sha256(text.encode()).hexdigest() for _,text,_ in inputs(root)}
    if actual != set(cache['entries']):
        raise ValueError('Assembly authoring inputs differ from the thirteen reviewed certificates')
    expected={p.relative_to(root/'src/smb3x').as_posix() for p in (root/'src/smb3x').rglob('*')
              if p.is_file() and p.suffix in ('.py','.lua','.json','.asm')}
    if not expected <= set(recipe['resources']):
        raise ValueError('Current implementation missing from resource recipe: '+repr(sorted(expected-set(recipe['resources']))))
    return dict(resources=len(recipe['resources']),native_source_certificates=len(actual),syntax=True,private_assets_absent=True)

if __name__=='__main__':
    print(json.dumps(check(),indent=2))
