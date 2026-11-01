# SPDX-License-Identifier: MPL-2.0
"""Local pack validation: provenance claims and technical checks remain separate."""
from pathlib import Path
import hashlib
import json
import re
from .arrangement import compile_arrangement
from .score import import_midi, require

VERSION='m20-score-1'
CAPABILITIES=['ntsc-row30','sections32','four-monophonic-channels','native-events','no-custom-dpcm']
CONTEXTS={'plains','athletic','underground','water','desert','ice','castle','dark'}

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def fingerprint(value):return hashlib.sha256(canonical(value)).hexdigest()

def load_pack(path, *, development=False):
    path=Path(path).resolve();raw=path.read_bytes();pack=json.loads(raw)
    require(set(pack)=={'schema','id','version','tracks'},'pack requires schema/id/version/tracks only')
    require(pack['schema']==1 and isinstance(pack['version'],str),'unsupported pack version')
    require(isinstance(pack['id'],str) and re.fullmatch('[a-z0-9][a-z0-9._-]{0,63}',pack['id']),'invalid pack id')
    require(isinstance(pack['tracks'],list) and len(pack['tracks'])<=1024,'invalid pack track list')
    tracks=[];ids=set();sources={}
    for t in pack['tracks']:
        require(set(t)=={'id','title','family','melody','contexts','source','format','provenance','review','enabled'},'unknown/missing track metadata')
        require(isinstance(t['id'],str) and re.fullmatch('[a-z0-9][a-z0-9._-]{0,63}',t['id']) and t['id'] not in ids,'invalid/duplicate stable track id');ids.add(t['id'])
        require(type(t['enabled']) is bool,'enabled must be boolean')
        require(t['family'] in ('mario-classics','nes-classics','local','development'),'unsupported family')
        require(isinstance(t['contexts'],list) and t['contexts'] and set(t['contexts'])<=CONTEXTS,'explicit supported contexts required')
        require(isinstance(t['title'],str) and t['title'].strip() and isinstance(t['melody'],str) and t['melody'],'title/melody identity required')
        rights=t['provenance']
        require(isinstance(rights,dict) and set(rights)=={'author','composition','arrangement','distribution','evidence'},'complete provenance fields required')
        require(all(isinstance(v,str) and v.strip() for v in rights.values()),'nonempty rights metadata required')
        require(rights['distribution'] in ('unresolved','private-only','cleared'),'unsupported distribution status')
        require(t['review'] in ('pending','reviewed'),'invalid listening review status')
        if not t['enabled']:continue
        if t['family']=='development':require(development,'development fixtures require explicit opt-in')
        else:
            require(rights['composition']!='unresolved' and rights['arrangement']!='unresolved','composition and arrangement rights must be established')
            require(rights['distribution']=='cleared' or development and rights['distribution']=='private-only','uncleared pack requires private development mode')
        source=(path.parent/t['source']).resolve()
        require(source.is_relative_to(path.parent),'source must stay within pack directory')
        payload=source.read_bytes();fmt=t['format'];sources[t['source']]=payload.hex()
        if fmt=='json':score=json.loads(payload)
        elif fmt=='smf1':
            score=import_midi(payload,rights);score['title']=t['title']
        elif fmt=='native-verified':
            native=json.loads(payload)
            require(set(native)=={'score','sections_hex','converter'},'verified native source must carry editable certification score')
            require(native['converter']==VERSION,'native converter version mismatch')
            score=native['score'];blocks,_=compile_arrangement(score)
            require(native['sections_hex']==[b.hex() for b,_ in blocks],'precompiled bytes differ from independently compiled score')
        else:raise ValueError('Supported inputs: JSON, strict SMF1, verified native; no direct FMS/FTM support')
        blocks,report=compile_arrangement(score)
        require(report['sequence_bytes']<=5632,'track exceeds native bank sequence capacity')
        tracks.append({**t,'score':score,'conversion':{**report,'section_count':len(blocks),'section_sizes':[len(b) for b,_ in blocks],
            'converter':VERSION,'tempo_row':48,'capabilities':CAPABILITIES,'input_sha256':hashlib.sha256(payload).hexdigest(),
            'technical_certification':'conversion-passed; native pack playback review required','listening_review':t['review']},
            'storage_bytes':8192,'sequence_bytes':report['sequence_bytes']})
    return {'id':pack['id'],'version':pack['version'],'tracks':tracks,'sha256':fingerprint({'metadata':pack,'inputs':[t['conversion']['input_sha256'] for t in tracks]}),
            'snapshot':{'metadata':pack,'sources':sources,'development':development}}

def verify_pack(pack):
    """Revalidate embedded source bytes, provenance and compiled report independently."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix='smb3-m20-pack-') as tmp:
        root=Path(tmp);snapshot=pack['snapshot']
        for name,data in snapshot['sources'].items():
            target=(root/name).resolve()
            require(target.is_relative_to(root),'snapshot source escapes pack directory')
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(bytes.fromhex(data))
        (root/'pack.json').write_text(json.dumps(snapshot['metadata']))
        actual=load_pack(root/'pack.json',development=snapshot['development'])
        require(actual==pack,'embedded pack source/compilation identity mismatch')
        return actual

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('pack',type=Path);p.add_argument('--development',action='store_true');a=p.parse_args()
    result=load_pack(a.pack,development=a.development)
    print(json.dumps({**result,'tracks':[{k:v for k,v in t.items() if k!='score'} for t in result['tracks']]},indent=2))
