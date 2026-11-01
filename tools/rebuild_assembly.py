# SPDX-License-Identifier: MPL-2.0
"""Rebuild thirteen certified assembly records from explicit source.

Packaging uses the checked-in certificate; optional regeneration requires the
pinned, separately acquired NESASM executable. Rights gates remain in NOTICE.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,tempfile
ASM_SHA='d6c16c39e1ffe4b46896726c738b5a8654e9dac3389e4439597582e1b97f4501'
def sha(b):return hashlib.sha256(b).hexdigest()
def inputs(root):
 root=Path(root);rows=json.loads((root/'src/smb3x/planning/data/locations_m191.json').read_bytes());totals=[]
 for regional in (False,True):
  enabled=[r for r in rows if r['enabled']and(not r.get('hammer_required')or regional)]
  totals.extend(sum(r['world']==w for r in enabled)for w in range(1,9))
 result=[('m191.asm',(root/'src/smb3x/native/asm/m191.asm').read_text().replace('; @M19.1_TRACKER_TOTALS',' .db '+','.join(map(str,totals))),['src/smb3x/native/asm/m191.asm','src/smb3x/planning/data/locations_m191.json'])]
 for name,src,sym in [('audio','m20_audio','m20'),('content','m20_content','m20'),('loader','m22_loader','m221'),('context','m222_context','m222'),('special','m222_special','m222_special'),('bros','m222_bros','m222_bros'),('military','m222_military','m222_military'),('mixed','m222_mixed','m222_mixed')]:
  text=(root/f'src/smb3x/native/asm/{src}.asm').read_text();symbols=json.loads((root/f'src/smb3x/native/symbols/{sym}_symbols.json').read_bytes());pre=''.join(f'{k} = ${v:04X}\n'for k,v in symbols.items()if re.search(r'\b'+k+r'\b',text));result.append((name+'.asm',pre+text,[f'src/smb3x/native/asm/{src}.asm',f'src/smb3x/native/symbols/{sym}_symbols.json']))
 descriptor=root/'src/smb3x/planning/data/contents_m22.json';doc=json.loads(descriptor.read_bytes());area=next(c for c in doc['contents']if c['content_id']=='classic/smw/yoshis-island-2')['areas'][0]
 text=(root/'src/smb3x/native/asm/m221_poison.asm').read_text();symbols=json.loads((root/'src/smb3x/native/symbols/m221_symbols.json').read_bytes());pre=''.join(f'{k} = ${v:04X}\n'for k,v in symbols.items()if re.search(r'\b'+k+r'\b',text))
 if area['id']!='classic/smw/yoshis-island-2/main'or area['tileset']!=3:raise ValueError('Legacy descriptor identity')
 for desert in (0,1):
  for plains in (0,1):result.append(('poison.asm',pre+f'M221SmwLayout = ${area["layout"]:04X}\nM221SunDesertEnabled = {desert}\nM221SunPlainsEnabled = {plains}\n'+text,['src/smb3x/native/asm/m221_poison.asm','src/smb3x/native/symbols/m221_symbols.json','src/smb3x/planning/data/contents_m22.json']))
 return result
def assemble(assembler,folder,name,text):
 folder.mkdir();path=folder/name;path.write_text(text,encoding='utf-8',newline='\n');p=subprocess.run([str(assembler),name],cwd=folder,capture_output=True,text=True,check=True)
 if 'error'in(p.stdout+p.stderr).lower():raise ValueError('Assembly failed: '+name)
 blob=path.with_suffix('.nes').read_bytes();spans=[];i=16
 while i<len(blob):
  if blob[i]==255:i+=1;continue
  end=i+1
  while end<len(blob)and blob[end]!=255:end+=1
  spans.append([i,blob[i:end].hex()]);i=end
 return dict(name=name,size=len(blob),header=blob[:16].hex(),spans=spans,symbols=path.with_suffix('.fns').read_text(),output_sha256=sha(blob))
def rebuild(source,assembler,output):
 source=Path(source).resolve();assembler=Path(assembler).resolve();output=Path(output).resolve()
 if output.exists():raise ValueError('Choose a fresh output directory')
 if sha(assembler.read_bytes())!=ASM_SHA:raise ValueError('Assembler identity')
 entries={};provenance=[];counterfactual=[]
 with tempfile.TemporaryDirectory()as tmp:
  tmp=Path(tmp)
  for i,(name,text,dependencies)in enumerate(inputs(source)):
   key=sha(text.encode());entries[key]=assemble(assembler,tmp/str(i),name,text);provenance.append(dict(name=name,input_sha256=key,dependencies=dependencies,output_sha256=entries[key]['output_sha256']))
 data=(json.dumps(dict(schema=1,assembler_sha256=ASM_SHA,entries=entries),sort_keys=True,separators=(',',':'))+'\n').encode()
 output.mkdir(parents=True);(output/'assembly-cache.json').write_bytes(data)
 return dict(entries=len(entries),sha256=sha(data),inputs=provenance,rom_input_used=False,existing_cache_used_as_input=False,explicit_descriptor_required=True,descriptor_sha256=sha((source/'src/smb3x/planning/data/contents_m22.json').read_bytes()))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--assembler',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(rebuild(a.source,a.assembler,a.output),indent=2))
