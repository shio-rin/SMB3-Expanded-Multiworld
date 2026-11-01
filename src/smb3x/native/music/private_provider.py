# SPDX-License-Identifier: MPL-2.0
"""Separate private local asset format. Public rights validation is unchanged."""
from pathlib import Path
from zipfile import ZipFile,BadZipFile
import hashlib,json,argparse
from .compiler import payload
from ...planning.music import CATALOGUE as C
from ...shared.resources import RESOURCE_ROOT as ROOT
FORMAT='smb3-private-r3-pack-1'
NOTICE='User-local private playback only. Composition and arrangement redistribution rights remain unresolved. Not a public licence. Do not upload or share this pack or prepared ROM/BPS.'
def sha(b):return hashlib.sha256(b).hexdigest()
def manifest():return dict(format=FORMAT,catalogue_id=C['id'],compiler_version=C['compiler_version'],compiler_sha256=C['compiler_sha256'],private_only=True,public_redistribution_eligible=False,notice=NOTICE,
    scores={t['id']:t['score_sha256']for t in C['tracks']})
def check_compiler():
    if sha((Path(__file__).with_name('certified_compiler.py')).read_bytes().replace(b'\r\n',b'\n'))!=C['compiler_sha256']:raise ValueError('Private music compiler identity mismatch')
def create(research_root,target):
    from ...shared.archives import write_zip
    check_compiler();target=Path(target)
    if target.exists():raise ValueError('Choose a fresh private pack output')
    files={'pack.json':json.dumps(manifest(),sort_keys=True,separators=(',',':')).encode()}
    for t in C['tracks']:
        raw=(Path(research_root)/t['source_relative']).read_bytes()
        if sha(raw)!=t['score_sha256']:raise ValueError('Accepted score changed: '+t['id'])
        data,_,_=payload(json.loads(raw))
        if sha(data)!=t['payload_sha256']:raise ValueError('Native compilation changed: '+t['id'])
        files['scores/'+t['id']+'.json']=raw
    target.parent.mkdir(parents=True,exist_ok=True);write_zip(target,files)
    return dict(path=str(target.resolve()),sha256=sha(target.read_bytes()),catalogue_id=C['id'],tracks=len(C['tracks']),notice=NOTICE)
def load(path,selected):
    check_compiler()
    try:
        with ZipFile(path)as z:
            expected={'pack.json'}|{'scores/'+t['id']+'.json'for t in C['tracks']}
            if len(z.infolist())!=len(expected) or set(z.namelist())!=expected or any(i.file_size>2_000_000 for i in z.infolist()):raise ValueError('Invalid private music pack inventory')
            if json.loads(z.read('pack.json'))!=manifest():raise ValueError('Wrong private music pack/catalogue/compiler identity')
            scores={}
            for t in C['tracks']:
                raw=z.read('scores/'+t['id']+'.json')
                if sha(raw)!=t['score_sha256']:raise ValueError('Private score hash mismatch: '+t['id'])
                if t['id']in selected:
                    data,_,_=payload(json.loads(raw))
                    if sha(data)!=t['payload_sha256']:raise ValueError('Private native bank mismatch: '+t['id'])
                    scores[t['id']]=data
            if set(scores)!=set(selected):raise ValueError('Unknown selected private track')
            return scores
    except (OSError,KeyError,BadZipFile,ValueError) as e:raise ValueError('Custom music requires a separately supplied, compatible R3 .smb3music pack. No pack is included. Select the matching pack, then reopen the unchanged player file; preparation remains unfinished. Pack rejected: '+str(e))from e

def locate():
    from ...launcher.paths import home
    from ...shared.serialization import read
    from ...client.persistence.atomic import save_json as atomic
    import os
    settings_path=home()/'settings.json';settings=read(settings_path)if settings_path.exists()else{}
    override=os.environ.get('SMB3_PRIVATE_MUSIC_PACK')
    path=override or settings.get('private_music_pack')
    if path and not override:
        try:load(Path(path),[])
        except (ValueError,OSError):path=None
    if not path or not Path(path).is_file():
        from ...launcher.dialogs import select
        try:path=select('Select your private R3 music pack',[('SMB3 private music pack',('.smb3music',))])
        except ValueError as e:raise ValueError('Custom music needs the matching R3 .smb3music pack. Reopen this unchanged player file and select it; preparation remains unfinished.')from e
    load(Path(path),[])
    settings['private_music_pack']=str(Path(path).resolve());atomic(settings_path,settings)
    return Path(path)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--research-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(create(a.research_root,a.output),indent=2))
