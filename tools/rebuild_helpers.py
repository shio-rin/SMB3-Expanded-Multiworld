# SPDX-License-Identifier: MPL-2.0
"""Rebuild three source-only native cache records; never read an existing cache.

Local maintainer tool, not player preparation. The caller supplies the reviewed
source tree and their pinned assembler. Regeneration is not rights clearance.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,tempfile
ASSEMBLER_SHA256='d6c16c39e1ffe4b46896726c738b5a8654e9dac3389e4439597582e1b97f4501'
TARGETS={'palette':('src/smb3x/native/asm/m24_content.asm','src/smb3x/native/certificates/m241-palette-assembly.json'),
 'special':('src/smb3x/native/asm/m24_special_content.asm','src/smb3x/native/certificates/m24-special-palette-assembly.json'),
 'giant':('src/smb3x/native/asm/m26_giant.asm','src/smb3x/native/certificates/m26-giant-assembly.json')}
def sha(b):return hashlib.sha256(b).hexdigest()
def rebuild(root,assembler,output):
 root=Path(root).resolve();assembler=Path(assembler).resolve();output=Path(output).resolve()
 if output.exists():raise ValueError('Use a new output directory; previous evidence is retained')
 if sha(assembler.read_bytes())!=ASSEMBLER_SHA256:raise ValueError('Pinned assembler identity mismatch')
 # All inputs are explicit reviewed source. Do not load build tools that eagerly
 # import descriptors or caches, or fill gaps using original ROM/disassembly.
 symbols=json.loads((root/'src/smb3x/native/symbols/m20_symbols.json').read_bytes());results=[];pending=[]
 with tempfile.TemporaryDirectory()as tmp:
  tmp=Path(tmp)
  for kind,(source,target)in TARGETS.items():
   text=(root/source).read_text(encoding='utf-8');prelude=''
   if kind!='giant':
    sy=dict(symbols,Temp_Var1=0,Temp_Var2=1,LevelJctBQ_Flag=0x7eb6,Level_JctBackupTileset=0x7eb7)
    if kind=='special':sy['Map_EnterViaID']=0x1e
    prelude=''.join(f'{k} = ${v:04X}\n'for k,v in sy.items()if re.search(r'\b'+k+r'\b',text))
   folder=tmp/kind;folder.mkdir();asm=folder/'helper.asm';asm.write_text(prelude+text,encoding='utf-8',newline='\n')
   proc=subprocess.run([str(assembler),asm.name],cwd=folder,capture_output=True,text=True,check=True)
   if 'error'in(proc.stdout+proc.stderr).lower():raise ValueError('Assembly failed: '+kind)
   sy={k:int(v,16)for k,v in re.findall(r'^(\w+)\s*=\s*\$([\da-fA-F]+)',asm.with_suffix('.fns').read_text(),re.M)}
   blob=asm.with_suffix('.nes').read_bytes()
   if kind=='giant':
    lo=16+20*8192+0x380;hi=lo+sy['GiantFallback']+3-0xc380;code=blob[lo:hi]
    hook=blob[16+2*8192+0x3a2:16+2*8192+0x3aa]
    row=dict(assembler_sha256=ASSEMBLER_SHA256,code=code.hex(),code_sha256=sha(code),native_hook=hook.hex(),source_lf_sha256=sha(text.encode()))
   else:
    if sy['ContentExtension']!=0xc000 or sy['ContentExtensionEnd']>=0xc700:raise ValueError('Palette code allocation')
    code=blob[16+20*8192:16+20*8192+sy['ContentExtensionEnd']-0xc000]
    row=dict(input_sha256=sha((prelude+text).encode()),code=code.hex(),code_sha256=sha(code),symbols=sy)
   data=(json.dumps(row,indent=2,sort_keys=kind!='special')+'\n').encode()
   pending.append((target,data));results.append(dict(source=source,target=target,sha256=sha(data),code_sha256=sha(code),bytes=len(data),rom_input_used=False))
 output.mkdir(parents=True)
 for target,data in pending:
  path=output/target;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 return dict(assembler_sha256=ASSEMBLER_SHA256,inputs=['src/smb3x/native/symbols/m20_symbols.json']+[v[0]for v in TARGETS.values()],outputs=results,rights='Reconstruction completed; source, reference data and output rights still require review. No assembler or emitted iNES container is distributed.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--assembler',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=rebuild(a.source,a.assembler,a.output)
 print(json.dumps(result,indent=2))
