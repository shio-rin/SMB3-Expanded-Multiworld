# SPDX-License-Identifier: MPL-2.0
"""Reconstruct the menu cache from proposed source, without ROM or old cache.

Uses the existing source generator and declared-span encoder unchanged. Temporary
M191 assembly supplies only symbols; its container is never an output artifact.
This establishes reproduction, not permission to redistribute native adaptations.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,runpy,shutil,subprocess,tempfile
ASSEMBLER_SHA256='d6c16c39e1ffe4b46896726c738b5a8654e9dac3389e4439597582e1b97f4501'
def sha(b):return hashlib.sha256(b).hexdigest()
def rebuild(source,assembler,output):
 source=Path(source).resolve();assembler=Path(assembler).resolve();output=Path(output).resolve()
 if output.exists():raise ValueError('Use a new retained output directory')
 if sha(assembler.read_bytes())!=ASSEMBLER_SHA256:raise ValueError('Assembler identity')
 with tempfile.TemporaryDirectory()as tmp:
  tmp=Path(tmp);asm=tmp/'m191.asm'
  rows=json.loads((source/'src/smb3x/planning/data/locations_m191.json').read_bytes());totals=[]
  for regional in (False,True):
   enabled=[r for r in rows if r['enabled']and(not r.get('hammer_required')or regional)]
   totals.extend(sum(r['world']==w for r in enabled)for w in range(1,9))
  text=(source/'src/smb3x/native/asm/m191.asm').read_text();marker='; @M19.1_TRACKER_TOTALS'
  if text.count(marker)!=1:raise ValueError('Tracker source contract')
  asm.write_text(text.replace(marker,' .db '+','.join(map(str,totals))),encoding='utf-8')
  proc=subprocess.run([str(assembler),asm.name],cwd=tmp,capture_output=True,text=True,check=True)
  if 'error'in(proc.stdout+proc.stderr).lower():raise ValueError('M191 symbol assembly failed')
  symbols={k:int(v,16)for k,v in re.findall(r'^(\w+)\s*=\s*\$([\da-fA-F]+)',asm.with_suffix('.fns').read_text(),re.M)}
  if source != Path(__file__).resolve().parents[1]:raise ValueError('Run this tool from the source checkout being rebuilt')
  from smb3x.native.patches.interface import tile
  from smb3x.native import interface_text as p
  pre='\n'.join(f'{k} = ${v:04X}'for k,v in dict(NativeMenuControl=symbols['MenuControl'],NativeMenuStatus=symbols['MenuStatus'],NativeMenuRender=symbols['MenuRender'],NativeBankCall=symbols['BankCall'],GlyphOwned=tile('Y'),GlyphX=tile('-'),GlyphBlank=tile(' '),GlyphW=tile('W'),GlyphArrow=tile('>'),GlyphSlash=tile('/')).items())
  text=(source/'src/smb3x/native/asm/m245_menu.asm').read_text().replace('; @NATIVE_CONSTANTS',pre).replace('; @UI_ROWS',p.rows(tile))
  for name in ('controls','geometry','values'):text=text.replace('; @'+name.upper(),(source/f'src/smb3x/native/asm/m245_{name}.asm').read_text())
  text=text.replace('; @VALUES_DATA',p.values_data(tile,None,None))
  from tools.menu_certificate import assemble_menu
  raw=assemble_menu(text,assembler)
 output.mkdir(parents=True);dst=output/'src/smb3x/native/certificates/m245-menu-native.json';dst.parent.mkdir(parents=True);dst.write_bytes(raw)
 return dict(target='src/smb3x/native/certificates/m245-menu-native.json',sha256=sha(raw),source_text_sha256=sha(text.encode()),bytes=len(raw),rom_input_used=False,old_cache_read=False,assembler_sha256=ASSEMBLER_SHA256,rights='Reconstruction completed; rights implications still need review')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--assembler',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(rebuild(a.source,a.assembler,a.output),indent=2))
