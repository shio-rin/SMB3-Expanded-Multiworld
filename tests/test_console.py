# SPDX-License-Identifier: MPL-2.0
"""Exercise production Lua producers and real logger; RAM/native fixtures are disclosed."""
from pathlib import Path
import tempfile,unittest,json
from lupa import LuaRuntime
from tests import test_effect_queue as queue_fixture
from tests import test_autosave_policy as checkpoint_fixture
ROOT=Path(__file__).resolve().parents[1]
class ConsolePaths(unittest.TestCase):
 def logger(self,lua,folder):
  lua.globals().logger_module=lua.execute((ROOT/'src/smb3x/bizhawk/diagnostics.lua').read_text())
  lua.globals().path=str(Path(folder)/'raw.log')
  lua.execute("console={};logger=logger_module.new({path=path,console=function(s)console[#console+1]=s end})")
 def test_all_check_types_local_only_once_with_exact_raw_identifiers(self):
  lua=LuaRuntime(unpack_returned_tuples=True)
  with tempfile.TemporaryDirectory()as d:
   self.logger(lua,d)
   # The inherited M7 signature helper is the only dependency of this producer.
   lua.execute("dofile=function()return {signature=function()return 'signature'end}end")
   lua.globals().module=lua.execute((ROOT/'src/smb3x/bizhawk/locations.lua').read_text())
   rows=json.loads((ROOT/'src/smb3x/planning/data/locations_m242.json').read_text())
   for row in rows:
    if row['world']!=1 or not row['enabled']:continue
    lua.globals().row=lua.table_from(row)
    lua.execute("""mem={[0x79A0]=0xAA,[0x79A1]=9,[0x79A2]=2,[0x79AE]=1,[0x72B]=1,[0x9F3C]=1};id=tonumber(row.id:sub(3),16)
     mem[tonumber(row.address:sub(3),16)]=tonumber(row.bit:sub(3),16);mem[0x79E0]=row.receipt_bit or 0
     local io={read=function(a)return mem[a]or 0 end,log=logger.event};m=module.new(io,{row});m.configure({id});m.poll();m.poll()""")
   lua.execute('logger.close()')
   output=list(lua.globals().console.values());raw=Path(d,'raw.log').read_text()
   self.assertEqual(len(output),len([r for r in rows if r['world']==1 and r['enabled']]))
   self.assertIn('[SMB3X / Checks] World 1-1 cleared.',output)
   self.assertIn('[SMB3X / Checks] World 1 Toad House 1 Chest opened.',output)
   self.assertIn('id=1397568257 native M222 receipt/state',raw)
   self.assertTrue(all('id='not in v and 'native'not in v and 'server'not in v for v in output))
 def test_restored_check_keeps_raw_evidence_without_new_console_event(self):
  lua=LuaRuntime(unpack_returned_tuples=True)
  with tempfile.TemporaryDirectory()as d:
   self.logger(lua,d)
   lua.execute("dofile=function()return {signature=function()return 's'end}end")
   base=lua.execute((ROOT/'src/smb3x/bizhawk/locations.lua').read_text());lua.globals().base_module=base
   lua.execute('dofile=function()return base_module end')
   module=lua.execute((ROOT/'src/smb3x/bizhawk/locations.lua').read_text());lua.globals().module=module
   row=json.loads((ROOT/'src/smb3x/planning/data/locations_m242.json').read_text())[0];lua.globals().row=lua.table_from(row)
   lua.execute("""mem={[0x79A0]=0xAA,[0x79A1]=9,[0x79A2]=2,[0x79AE]=1,[0x72B]=1,[0x9F3C]=1};id=tonumber(row.id:sub(3),16)
    mem[tonumber(row.address:sub(3),16)]=tonumber(row.bit:sub(3),16)
    m=module.new({read=function(a)return mem[a]or 0 end,log=logger.event},{row});m.configure({id});m.import_checks({id});m.poll();m.poll();logger.close()""")
   self.assertEqual(lua.eval('#console'),0);self.assertEqual(lua.eval('#m.checks()'),1)
   self.assertIn('LOCATION COMPLETE World 1-1 Clear id=',Path(d,'raw.log').read_text())
 def test_native_death_and_remote_event_audiences(self):
  q=queue_fixture.QueueTests();q.setUp();lua=q.lua
  with tempfile.TemporaryDirectory()as d:
   self.logger(lua,d);lua.execute('fixture.log=logger.event')
   lua.execute("observe({kind='native-local-death',effect='death',reason='original Player_Die DAAE; trap deaths retain local origin'});observe({kind='queued',effect='walking',reason='internal callback'});observe({kind='remote-death-observed',effect='death',reason='original Player_Die DAAE'})")
   lua.execute('logger.close()')
   self.assertEqual(list(lua.globals().console.values()),['[SMB3X / Effects] DeathLink: a shared death was applied.'])
   self.assertIn('native-local-death original Player_Die DAAE; trap deaths retain local origin',Path(d,'raw.log').read_text())
 def test_durable_effect_presentation_no_early_hidden_traps(self):
  for kind in ('walking','icy','micro','small','star','mushroom'):
   q=queue_fixture.QueueTests();q.setUp();lua=q.lua
   with tempfile.TemporaryDirectory()as d:
    self.logger(lua,d);lua.execute('fixture.log=logger.event;compatible.micro=true')
    q.push(0,kind);q.schedule(q.select(),1)
    self.assertEqual(lua.eval('#console'),0)
    q.step();e=q.q.event();q.value['records']['0'].update(state='committed',token='a'*64);q.sync(e['sequence'])
    for native_kind,reason,expected in [('activated','Player_Update','activated'),('completed','native duration ended','completed')]:
     lua.globals().observe(lua.table_from(dict(kind=native_kind,effect=kind,reason=reason)))
     e=q.q.event();self.assertEqual(e['state'],expected)
     q.value['records']['0'].update(state=e['state'],reason=e['reason']);q.sync(e['sequence'])
    lua.execute('logger.close()');out=list(lua.globals().console.values())
    self.assertEqual(len(out),2 if kind in ('walking','icy','micro')else 1)
    self.assertTrue(all('index='not in s and 'NATIVE'not in s for s in out))
    self.assertIn('M25 NATIVE activated Player_Update',Path(d,'raw.log').read_text())
 def test_pre_activation_interruption_does_not_reveal_hidden_trap(self):
  for activated in (False,True):
   q=queue_fixture.QueueTests();q.setUp();lua=q.lua
   with tempfile.TemporaryDirectory()as d:
    self.logger(lua,d);lua.execute('fixture.log=logger.event')
    q.push(0,'walking');q.schedule(q.select(),1);q.step();e=q.q.event()
    q.value['records']['0'].update(state='committed',token='a'*64);q.sync(e['sequence'])
    if activated:
     lua.globals().observe(lua.table_from(dict(kind='activated',effect='walking',reason='native Player_Update')))
     e=q.q.event();q.value['records']['0'].update(state=e['state'],reason=e['reason']);q.sync(e['sequence'])
    lua.globals().observe(lua.table_from(dict(kind='canceled-before-activation',effect='walking',reason='native boundary')))
    e=q.q.event();self.assertEqual(e['state'],'disposed_interrupted')
    q.value['records']['0'].update(state=e['state'],reason=e['reason']);q.sync(e['sequence']);lua.execute('logger.close()')
    out=list(lua.globals().console.values());self.assertEqual(len(out),2 if activated else 0)
    if activated:self.assertTrue(out[-1].endswith('interrupted.'))
    self.assertIn('state=disposed_interrupted',Path(d,'raw.log').read_text())
 def test_inventory_grants_capped_lives_and_capacity_warning(self):
  for scenario in ('permanent','life','capped','inventory','full'):
   lua=LuaRuntime(unpack_returned_tuples=True)
   with tempfile.TemporaryDirectory()as d:
    self.logger(lua,d)
    lua.globals().module=lua.execute((ROOT/'src/smb3x/bizhawk/delivery.lua').read_text())
    lua.globals().scenario=scenario
    lua.execute("""mem={[0x736]=scenario=='capped'and 99 or 4};local permanent=scenario=='permanent';local life=scenario=='life'or scenario=='capped'
     if scenario=='full'then for a=0x7D80,0x7D9B do mem[a]=1 end end
     local row={id='0x1',kind=permanent and 'permanent'or life and 'life'or 'inventory',name=permanent and 'World 2 Pass'or life and '1-Up'or 'Super Leaf',native=3}
     d=module.new({read=function(a)return mem[a]or 0 end,write=function(a,v)mem[a]=v end,log=logger.event,frame=function()return 123 end,safe=function()return true end,unlock=function()end},{row})
     d.sync({{index=0,item=1}},{},3);for i=1,45 do d.process()end;logger.close()""")
    out=list(lua.globals().console.values());self.assertEqual(len(out),1)
    self.assertTrue(out[0].startswith('[SMB3X / Items]'))
    self.assertNotIn('index=',out[0]);self.assertNotIn('$',out[0]);self.assertIn('AP ITEM QUEUED index=0',Path(d,'raw.log').read_text())
    if scenario=='full':self.assertIn('is waiting',out[0]);self.assertEqual(lua.eval('#d.state.pending'),1)
    elif scenario=='capped':self.assertIn('99',out[0]);self.assertEqual(lua.eval('mem[0x736]'),99)
    elif scenario=='life':self.assertEqual(lua.eval('mem[0x736]'),5)
 def test_travel_warnings_and_blocked_controller_remain_visible(self):
  lua=LuaRuntime(unpack_returned_tuples=True)
  with tempfile.TemporaryDirectory()as d:
   self.logger(lua,d);lua.globals().module=lua.execute((ROOT/'src/smb3x/bizhawk/mailbox.lua').read_text())
   lua.execute("""mem={};local io={read=function(a)return mem[a]or 0 end,write=function(a,v)mem[a]=v end,log=logger.event,frame=function()return 100 end,pause=function()paused=true end}
    m=module.new(io);assert(not m.request(1));m.fail('frame rollback/reset');logger.close()""")
   out=list(lua.globals().console.values());self.assertEqual(len(out),2)
   self.assertIn('menus closed',out[0]);self.assertIn('protect your progress',out[1]);self.assertTrue(lua.eval('paused'))
   self.assertIn('NATIVE M222 BLOCKED: frame rollback/reset',Path(d,'raw.log').read_text())
 def test_checkpoint_connection_and_fatal_errors_still_visible(self):
  c=checkpoint_fixture.AutosavePolicyTests();c.setUp();lua=c.lua
  with tempfile.TemporaryDirectory()as d:
   self.logger(lua,d);lua.execute("args.log=logger.event;args.hash=function()return 'fixture'end;c.disconnected();c.fail('invalid exact native state');logger.close()")
   out=list(lua.globals().console.values());self.assertEqual(len(out),2)
   self.assertIn('Connection suspended',out[0]);self.assertIn('protect your save',out[1]);self.assertIn('diagnostic log',out[1])
   self.assertIn('Checkpoint inconsistent: invalid exact native state; original files preserved',Path(d,'raw.log').read_text())
if __name__=='__main__':unittest.main()
