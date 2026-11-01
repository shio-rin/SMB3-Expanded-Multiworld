# SPDX-License-Identifier: MPL-2.0
"""Actual Lua file logger in disposable directories; no native state or gameplay."""
from pathlib import Path
import tempfile,unittest
from lupa import LuaRuntime
ROOT=Path(__file__).resolve().parents[1]
class LoggerTests(unittest.TestCase):
 def create(self,path,verbose=False,limit=1048576):
  lua=LuaRuntime(unpack_returned_tuples=True)
  lua.globals().module=lua.execute((ROOT/'src/smb3x/bizhawk/diagnostics.lua').read_text())
  lua.globals().path=str(path);lua.globals().verbose=verbose;lua.globals().limit=limit
  lua.execute('console={};logger=module.new({path=path,verbose=verbose,max_bytes=limit,console=function(s)console[#console+1]=s end})')
  return lua
 def test_explicit_audience_complete_file_and_verbose(self):
  with tempfile.TemporaryDirectory()as folder:
   for verbose in (False,True):
    path=Path(folder)/str(verbose);lua=self.create(path,verbose)
    lua.execute("logger.event('SMB3 bridge started',nil,'Ready.');for i=1,40 do logger.event('NATIVE PHASE '..i);logger.event('M23.3 Saving automatically')end;logger.event('NATIVE M222 BLOCKED: diagnostic','Checkpoint','Game paused.');logger.close()")
    self.assertEqual(lua.eval('#console'),84 if verbose else 2)
    self.assertEqual(lua.eval('console[1]'), '[SMB3X / Diagnostics] SMB3 bridge started' if verbose else '[SMB3X] Ready.')
    self.assertEqual(len(path.read_text().splitlines()),82)
 def test_unknown_diagnostics_do_not_guess_audience_and_errors_opt_in(self):
  with tempfile.TemporaryDirectory()as folder:
   path=Path(folder)/'lua.log';lua=self.create(path)
   lua.execute("logger.event('M25 NATIVE native-local-death original Player_Die DAAE; trap deaths retain local origin');logger.event('new developer debug trace');logger.event('NATIVE phase=255 error=8','Checkpoint','Game error. Check diagnostic log.');logger.close()")
   self.assertEqual(lua.eval('#console'),1)
   self.assertEqual(lua.eval('console[1]'),'[SMB3X / Checkpoint] Game error. Check diagnostic log.')
   self.assertEqual(len(path.read_text().splitlines()),3)
 def test_bounded_rotation_preserves_newest_complete_records(self):
  with tempfile.TemporaryDirectory()as folder:
   path=Path(folder)/'lua.log';lua=self.create(path,limit=512)
   lua.execute("for i=1,100 do logger.log('NATIVE PHASE '..i)end;logger.close()")
   files=list(Path(folder).iterdir());self.assertEqual(len(files),4)
   self.assertTrue(all(p.stat().st_size<=512 for p in files))
   lines=path.read_text().splitlines();self.assertTrue(lines[-1].endswith('NATIVE PHASE 100'))
 def test_unavailable_log_is_nonfatal_and_warns_once(self):
  with tempfile.TemporaryDirectory()as folder:
   lua=self.create(Path(folder)/'missing'/'lua.log')
   lua.execute("logger.log('M23.3 Saving automatically');logger.log('NATIVE PHASE 2');logger.log('Checkpoint inconsistent: test');logger.close()")
   self.assertEqual(lua.eval('#console'),4)
   self.assertIn('Diagnostic log unavailable',lua.eval('console[1]'))
   self.assertIn('inconsistent',lua.eval('console[4]'))
if __name__=='__main__':unittest.main()
