# SPDX-License-Identifier: MPL-2.0
"""Standalone deterministic release construction from the checked-in recipe.

Python standard library and Git only. No ROM, private music, ignored generated
history, historical APWorld archive, assembler or installed AP is a build input.
"""
from pathlib import Path,PurePosixPath
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
import argparse,hashlib,json,os,subprocess,sys,zlib
ROOT=Path(__file__).resolve().parents[1]
RECIPE='packaging/resources.json'

def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()

def contained(root,name):
    if (not isinstance(name,str) or '\\' in name or ':' in name
        or PurePosixPath(name).is_absolute() or any(x in ('','.','..')for x in name.split('/'))):
        raise ValueError('Unsafe resource path: '+str(name))
    p=(root/name).resolve()
    if not p.is_relative_to(root.resolve()):raise ValueError('Resource escapes checkout: '+name)
    return p

def resource(root,name,row):
    p=contained(root,row['source']);data=p.read_bytes().replace(b'\r\n',b'\n')
    if sha(data)!=row['source_lf_sha256']:raise ValueError('Canonical source changed: '+name)
    for substitution in row.get('path_substitutions',[]):
        before=substitution['before'].encode();after=substitution['after'].encode()
        if data.count(before)!=substitution['count']:raise ValueError('Path normalization source changed: '+name)
        data=data.replace(before,after)
    mode=row['transform']
    if mode=='crlf':data=data.replace(b'\n',b'\r\n')
    elif mode=='managed-config':
        settings=json.loads(data);settings['PathEntries']['LastRomPath']='.';settings['UpdateAutoCheckEnabled']=False
        data=(json.dumps(settings,indent=2,sort_keys=True)+'\n').encode()
    elif mode!='lf':raise ValueError('Unknown resource transform: '+mode)
    if sha(data)!=row['output_sha256']:raise ValueError('Transformed resource changed: '+name)
    return data

def source_commit(root):
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=root,text=True).strip():
        raise ValueError('Commit tracked source changes before building a release')
    return commit

def package(target,root=ROOT):
    root=Path(root).resolve();target=Path(target).resolve()
    if target.exists():raise ValueError('Choose a new sealed output path; existing artifacts are retained')
    recipe_bytes=contained(root,RECIPE).read_bytes().replace(b'\r\n',b'\n');recipe=json.loads(recipe_bytes)
    if recipe['schema']!=1:raise ValueError('Unsupported source recipe')
    commit=source_commit(root)
    tracked=set(subprocess.check_output(['git','ls-files'],cwd=root,text=True).splitlines())
    resources={}
    for name,row in sorted(recipe['resources'].items()):
        contained(root,name)
        if row['source']not in tracked:raise ValueError('Resource source is not checked in: '+name)
        resources[name]=resource(root,name,row)
    inventory=canonical({n:sha(b)for n,b in resources.items()})
    files={'smb3x/resources/'+n:b for n,b in resources.items()}
    files['smb3x/resources.json']=inventory
    for name,row in recipe['outer'].items():
        contained(root,name)
        if row['source']not in tracked:raise ValueError('Outer resource source is not checked in: '+name)
        files[name]=resource(root,name,row)
    files['archipelago.json']=json.dumps(recipe['apworld'],sort_keys=True).encode()
    files['smb3x/build-source.json']=canonical(dict(source_commit=commit,recipe_sha256=sha(recipe_bytes),
        source_recipe=RECIPE,release=recipe['release'],runtime=recipe['runtime'],resource_id=sha(inventory)))
    target.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(target,'x',compression=ZIP_DEFLATED,compresslevel=9)as archive:
        for name,data in sorted(files.items()):
            info=ZipInfo(name,(2026,10,30,0,0,0));info.compress_type=ZIP_DEFLATED
            info.create_system=3;info.external_attr=0o100644<<16
            archive.writestr(info,data,compresslevel=9)
    result=dict(archive_sha256=sha(target.read_bytes()),resource_manifest_sha256=sha(inventory),
        source_commit=commit,recipe_sha256=sha(recipe_bytes),version=recipe['apworld']['world_version'],
        release=recipe['release'],runtime=recipe['runtime'],resources=len(resources),members=len(files),
        python=sys.version,zlib=zlib.ZLIB_RUNTIME_VERSION,
        member_sha256={n:sha(b)for n,b in sorted(files.items())})
    target.with_suffix('.build.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items()if k!='member_sha256'},indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);package(p.parse_args().output)
