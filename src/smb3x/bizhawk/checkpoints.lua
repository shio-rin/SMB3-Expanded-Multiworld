-- SPDX-License-Identifier: MPL-2.0
-- M23.3 automatic ordinary-thread freeze. No state API in input/memory callbacks.
local M={}
local function equal(a,b)
 if type(a)~=type(b)then return false end
 if type(a)~='table'then return a==b end
 for k,v in pairs(a)do if not equal(v,b[k])then return false end end
 for k in pairs(b)do if a[k]==nil then return false end end
 return true
end
M.equal=equal
function M.new(io)
 local travel,delivery,monitor=io.travel,io.delivery,io.monitor
 local effects=io.effects
 local deathlink=io.deathlink
 local clock=io.clock or os.clock
 local state={policy='reason-aware-1',mode=io.resume and 'restoring' or 'booting',requested=false,stable=0,last_contact=os.time(),load=nil,verified=false,
  quit=false,reason='initial safe checkpoint',saved_signature=nil,awaiting_ack=false,batch_count=0,ui=false,previous={},dirty=false,exposed=false,
  start_pause_pending=io.resume and io.start_paused==true,message='Connecting - initial progress will save on the overworld'}
 local neutral={A=false,B=false,Start=false,Select=false,Up=false,Down=false,Left=false,Right=false,Power=false,Reset=false}
 local function read(path)local f=assert(_G.io.open(path,'rb'));local v=f:read('*a');f:close();return io.json.decode(v)end
 local function status(text,category,friendly)state.message=text;state.message_until=os.time()+3;io.log('M23.3 '..text,category,friendly)end
 local function failed(reason)
  state.mode='failed';state.message='Checkpoint inconsistent: '..tostring(reason)..'; original files preserved'
  travel.authorize(false);io.pause();io.log(state.message, "Checkpoint", "Game paused to protect your save. Preserve this game and check the client and diagnostic log.")
 end
 local function frozen()return state.effect_hold==true or state.mode=='frozen' or state.mode=='restoring' or state.mode=='closed' or state.mode=='failed' or state.mode=='suspended' or state.mode=='connecting' end
 local function retained()
  return {frame=io.frame(),ram=io.hash(0,2048,'System Bus'),wram=io.hash(0x6000,8192,'System Bus')}
 end
 local function disconnected()
  if state.mode=='closed'or state.mode=='failed'or state.mode=='suspended'then return end
  state.suspension={mode=state.mode,frame=state.frame,authorized=travel.state.authorized,paused=client.ispaused(),
   witness=retained(),challenge=tostring({})..':'..os.time()..':'..os.clock()}
  state.mode='suspended';state.frame=io.frame();travel.authorize(false);io.pause()
  status('Connection suspended - waiting for the same client', 'Network', 'Connection suspended; waiting for the same client.')
 end
 local function recover(challenge)
  assert(state.mode=='suspended'and state.suspension,'No recoverable transport suspension')
  local saved=state.suspension
  assert(saved.challenge==challenge,'Stale suspension challenge')
  assert(equal(retained(),saved.witness),'Native state changed during transport suspension')
  assert(not travel.state.blocked and not delivery.state.blocked,'Uncertain controller cannot resume')
  state.mode=saved.mode;state.frame=saved.frame;state.suspension=nil
  state.last_contact=os.time();travel.authorize(saved.authorized)
  if not saved.paused and not frozen()then io.unpause()end
  status('Client reconnected - retained session verified', 'Network', 'Client reconnected; your game was verified.')
 end
 local function safe()
  return (not deathlink or deathlink.safe()) and (not effects or effects.safe()) and travel.checkpoint_safe() and travel.progression_settled() and not delivery.state.blocked and not delivery.state.flight
    and delivery.snapshot()~=nil and (not io.panel or not io.panel.visible())
 end
 local function map_gate()
  return io.read(0x70A)==0 and io.read(0x729)==13 and io.read(0x79A2)==2 and io.read(0x79AE)==1
   and io.read(0x79DB)==0 and io.read(0x3ED)==0 and io.read(0x5F2)==0
 end
 local function batch_ready()
  return not state.awaiting_ack and not delivery.state.flight and(state.saved_signature==nil or state.batch_count>=32
    or #delivery.state.pending==0 or delivery.state.full_index~=nil)
 end
 local function signature()
  if not travel.checkpoint_safe()then return nil end
  local n=travel.checkpoint_status();local a={n.world,n.transaction,n.ending_phase,io.read(0x736)}
  for _,v in ipairs(n.snapshot.data)do a[#a+1]=v end
  for p=0x7D80,0x7DA2 do a[#a+1]=io.read(p)end
  for p=0x7AAC,0x7ACF do a[#a+1]=io.read(p)end
  for p=0x79F7,0x79FA do a[#a+1]=io.read(p)end
  for _,v in ipairs(monitor.checks())do a[#a+1]=v end
  for _,v in ipairs(delivery.acks())do a[#a+1]=v.index;a[#a+1]=v.result end
  return table.concat(a,':')
 end
 local function point_signature()
  if not travel.checkpoint_safe()then return nil end
  return table.concat(travel.checkpoint_status().snapshot.point,':')
 end
 local function inventory_value()
  local a={}
  -- Vanilla consumption does not advance the Stacked serial. Its real bag
  -- slots must also be observed; menu selection/cursor bytes are excluded.
  for p=0x7D80,0x7D9B do a[#a+1]=io.read(p)end
  for p=0x7AB2,0x7ACF do a[#a+1]=io.read(p)end
  return table.concat(a,':')
 end
 local function quiesce(reason)
  if frozen()then return end
  if not state.gate_started then state.gate_started=clock();state.gate_frame=io.frame()end
  state.requested=true;state.reason=reason or state.reason;state.mode='quiescing';state.stable=0
  status(state.quit and 'Saving and quitting - settling native work' or 'Saving automatically - settling native work', 'Checkpoint', state.quit and 'Saving before closing. Please wait.' or 'Saving progress...')
 end
 local function witness()
  assert(safe(),'Native checkpoint is not quiescent')
  return {schema=1,session=io.build.session,frame=io.frame(),native=travel.checkpoint_status(),inventory=delivery.snapshot(),
   ram={io.hash(0,2048,'System Bus'),io.hash(0x6000,8192,'System Bus')},
   prg=io.hash(0,524288,'PRG ROM'),chr=io.hash(0,262144,'CHR VROM'),
   frozen=true,publication={mailbox=io.read(0x79F3),stack=io.read(0x7BD5),pending=io.read(0x7BDC),write=io.read(0x7BE8)}}
 end
 local function delivery_export(d)
  assert(not delivery.state.blocked and not delivery.state.flight,'Uncertain/in-flight delivery cannot be saved')
  local results={};for k,v in pairs(delivery.state.results)do results[tostring(k)]=v end
  assert(equal(results,d.handled),'Lua results not durably acknowledged by Python')
  for _,c in ipairs(delivery.state.pending)do
   assert(d.items[tostring(c.index)]==c.item,'Lua/Python pending item mismatch')
   assert(not d.handled[tostring(c.index)],'Lua pending item was already handled')
  end
  -- Any Python-only pending command has never been issued. Frozen Lua cannot
  -- execute it. Save the full typed prefix rather than losing buffered entries.
  return {items=d.items,handled=d.handled,pending=d.pending}
 end
 local function controller(d,physical)
  return {schema=effects and 2 or 1,effects=effects and effects.export()or nil,deathlink=deathlink and deathlink.export()or nil,session=io.build.session,travel=travel.export_controller(),delivery=delivery_export(d),physical_checks=physical,
   flight=false,unissued=true}
 end
 local function import(c)
  assert(c.schema==(effects and 2 or 1) and c.session==io.build.session and c.flight==false and c.unissued==true,'Invalid cold controller')
  travel.import_controller(c.travel)
  if effects then effects.import(c.effects);deathlink.import(c.deathlink)end
  local s=delivery.state;assert(next(s.results)==nil and next(s.known)==nil and #s.pending==0,'Delivery import requires a fresh controller')
  for k,v in pairs(c.delivery.items)do s.known[tonumber(k)]=v end
  for k,v in pairs(c.delivery.handled)do s.results[tonumber(k)]=v end
  for _,i in ipairs(c.delivery.pending)do assert(not s.results[i] and s.known[i],'Invalid imported pending command');s.pending[#s.pending+1]={index=i,item=s.known[i]}end
  s.stable=0;s.flight=nil;s.full_index=nil
  monitor.import_checks(c.physical_checks)
 end
 local function managed_load(path,marker)
  assert(not state.load,'Reentrant state load forbidden')
  userdata.set('smb3.m233.generation',false)
  state.load={path=path,marker=marker,callback=false}
  local ok=savestate.load(path)
  local done=state.load;state.load=nil
  assert(ok==true and done and done.callback,'Native load/callback did not succeed exactly once')
  assert(userdata.get('smb3.m233.generation')==marker,'Native generation marker mismatch')
 end
 local function onload(name)
  if not state.load or state.load.callback or name~='native.State' or not frozen()then failed('Unmanaged/repeated state load');return end
  state.load.callback=true
  if userdata.get('smb3.m233.generation')~=state.load.marker then failed('Loaded userdata generation mismatch')end
 end
 local function request()
  if state.mode~='playing' and state.mode~='quiescing'then return end
  state.quit=true;state.ui=false;state.requested=true
  if not safe()then status('Waiting for safe overworld - close menus and settle', 'Checkpoint', 'Waiting to save. Return to the overworld and close menus.');return end
  quiesce('player Save and Quit')
 end
 local function tick()
  if (travel.state.blocked or delivery.state.blocked) and state.mode~='failed'then failed('Native controller blocked; no frames or player input released')end
  if state.mode=='booting'and io.read(0x79A0)==0xAA and io.read(0x79A2)==1 and io.read(0x79AE)==0 and io.read(0x79F3)==0 then
   state.mode='connecting';state.frame=io.frame();io.pause();status('Waiting for server - new game remains paused', 'Network', 'Waiting for the AP server. Your new game is safely paused.')
  end
  if state.mode=='connecting'and io.read(0x79F3)==1 and io.read(0x79A6)==1 then
   -- Only the existing validated same-instance journal bind action publishes
   -- this latch. STATUS/replay-wait cannot release native timeout frames.
   assert(io.frame()==state.frame,'Native frame advanced during initial binding wait')
   state.mode='booting';state.frame=nil;io.unpause();status('Connecting - validating native session', 'Network', 'Server history received; starting your game.')
  end
  if not frozen()then
  local sig=signature()
   -- Menus and map coordinates alone are not durable progress. Preserve the
   -- full native checkpoint at real returns/mutations; never reconstruct RAM.
   -- Observe consumption even before its inventory animation/menu has settled,
   -- so an interrupted unsaved use still requires the existing loss warning.
   if state.mode=='playing'and(io.read(0x70A)~=0 or(io.read(0x7BE8)==0 and state.saved_inventory and inventory_value()~=state.saved_inventory))then
    state.exposed=true;state.dirty=true;state.reason='unsaved native gameplay or inventory mutation'
   end
   if sig and sig~=state.saved_signature and state.mode=='playing'then
    state.dirty=true;state.reason='native world, inventory, reward or completion changed'
    delivery.state.full_index=nil -- Normal inventory use may have freed capacity.
   end
   if (state.mode=='booting' or state.mode=='playing' or state.mode=='synchronizing') and safe()
     and (state.saved_signature==nil or state.requested or state.dirty or state.awaiting_ack
       or(state.mode=='synchronizing'and(#delivery.state.pending==0 or delivery.state.full_index~=nil)))then quiesce(state.reason)end
  end
  if state.mode=='quiescing' or state.mode=='synchronizing'then if safe()then state.stable=state.stable+1 else state.stable=0 end end
  if frozen()then
   if state.frame and io.frame()~=state.frame and state.mode~='failed'then failed('Native frame advanced while frozen')end
   io.pause();joypad.set(neutral,1);joypad.set(neutral,2)
  end
  if not frozen() and travel.state.authorized and os.time()-state.last_contact>5 then
   disconnected()
  end
 end
 local function control(q)
  assert(q.session==io.build.session and q.run==io.run and q.token==io.token,'Checkpoint run/control token mismatch')
  state.last_contact=os.time()
  if q.op=='STATUS'then
   return {mode=state.mode,message=state.message,requested=state.requested,stable=state.stable,frame=io.frame(),dirty=state.dirty,reason=state.reason,quit=state.quit}
  elseif q.op=='SAVE_FAILED'then
   assert(frozen(),'Failure display requires frozen native ownership')
   state.save_error=true;return {displayed=true}
  elseif q.op=='WAIT_SERVER'then
   disconnected();status('Waiting for server - retained session paused', 'Network', 'Waiting for the AP server. Your game is safely paused.')
   return {waiting=true,mode=state.mode}
  elseif q.op=='ACK_RESULTS'then
   assert(not frozen()and state.awaiting_ack,'No quarantined native outcome awaits acknowledgement')
   delivery_export(q.delivery) -- Every result must already exist in durable Python state.
   state.awaiting_ack=false;state.batch_count=state.batch_count+1;state.stable=0
   return {acknowledged=true,batch_count=state.batch_count}
  elseif q.op=='QUIESCE'then request();return {mode=state.mode,stable=state.stable}
  elseif q.op=='FREEZE'then
   if state.mode~='quiescing' or state.stable<30 or not safe()or not batch_ready()then return {waiting=true,mode=state.mode}end
   state.freeze_started=clock();state.mode='frozen';io.pause();joypad.set(neutral,1);joypad.set(neutral,2)
   state.frame=io.frame();state.baseline=witness();status('Saving — native frames frozen')
   return {mode=state.mode,witness=state.baseline,acks=delivery.acks(),checks=monitor.checks(),timing={
    settlement_seconds=state.freeze_started-(state.gate_started or state.freeze_started),
    settlement_frames=io.frame()-(state.gate_frame or io.frame()),reason=state.reason}}
  elseif q.op=='CAPTURE'then
   local started=clock();local timing={}
   assert(state.mode=='frozen' and io.frame()==state.frame,'Capture lost freeze ownership')
   assert(equal(witness(),state.baseline),'Native state changed after freeze')
   local c=controller(q.delivery,q.physical_checks)
   monitor.import_checks(q.physical_checks)
   userdata.set('smb3.m233.generation',q.marker)
   timing.export_witness_seconds=clock()-started;local step=clock()
   savestate.save(q.path)
   timing.state_save_seconds=clock()-step;step=clock()
   managed_load(q.path,q.marker)
   timing.exact_load_seconds=clock()-step;step=clock()
   assert(state.mode=='frozen','Managed verification load failed')
   local after=witness();assert(equal(after,state.baseline),'Self-load witness differs')
   state.verified=true;state.marker=q.marker;status('Verifying save — exact native load passed')
   timing.loaded_witness_seconds=clock()-step
   return {verified=true,witness=after,controller=c,marker=q.marker,timing=timing}
  elseif q.op=='CLOSE'then
   assert(state.mode=='frozen' and state.verified and state.marker==q.marker and io.frame()==state.frame,'Unverified save cannot close')
   state.last_checkpoint=q.published_at or state.last_checkpoint
   state.mode='closed';travel.authorize(false);io.pause();status('Progress saved', 'Checkpoint', 'Progress saved.')
   return {closed=true,frame=io.frame()}
  elseif q.op=='THAW'then
   assert(state.mode=='frozen' and state.verified and state.marker==q.marker and io.frame()==state.frame,'Unverified autosave cannot release input')
   assert(type(q.epoch_token)=='string'and #q.epoch_token==32 and q.epoch_token~=state.epoch_token,'Fresh durable epoch token required')
   state.last_checkpoint=q.published_at or state.last_checkpoint;state.saved_notice_until=clock()+3
   state.epoch_token=q.epoch_token;state.saved_signature=signature();state.saved_point=point_signature();state.saved_inventory=inventory_value();state.saved_at=os.time()
   state.dirty=false;state.exposed=false;state.awaiting_ack=false;state.batch_count=0
   state.requested=false;state.stable=0;state.frame=nil;state.verified=false;state.reason='safe change';state.last_contact=os.time()
   state.mode=(#delivery.state.pending>0 and delivery.state.full_index==nil)and 'synchronizing'or'playing'
   if state.mode=='playing'and io.resume and not state.restore_notice and type(io.restored_at)=='number'then
    state.restore_notice=true;status('Restored checkpoint '..os.date('%Y-%m-%d %H:%M:%S',math.floor(io.restored_at)), 'Checkpoint', 'Saved progress restored.')
   else status(state.mode=='playing'and 'Saved automatically'or 'Receiving offline items - input remains gated', state.mode=='playing'and 'Checkpoint'or 'Items', state.mode=='playing'and 'Progress saved.'or 'Receiving offline items. Please wait.')end
   if state.mode=='playing'and state.start_pause_pending then
    state.start_pause_pending=false;io.pause();status('Restored paused - unpause BizHawk to continue', 'Checkpoint', 'Progress restored. Unpause BizHawk to continue.')
   else io.unpause()end
   local timing={frozen_seconds=clock()-(state.freeze_started or clock()),
    gated_seconds=clock()-(state.gate_started or clock())}
   state.gate_started=nil;state.gate_frame=nil
   return {playing=state.mode=='playing',pending=#delivery.state.pending,timing=timing}
  elseif q.op=='RESUME_READY'then
   assert(state.mode=='restoring' and state.verified,'Cold restore not locally verified')
   return {witness=witness(),mode=state.mode}
  elseif q.op=='RECONCILE_EFFECTS'then
   assert(effects and state.mode=='restoring'and state.verified and not state.reconciled,'Effect reconciliation requires one-use frozen restore')
   assert(equal(witness(),state.baseline),'Native state changed before disposition import')
   effects.import(q.effects);deathlink.import(q.deathlink)
   local s=delivery.state;s.known={};s.results={};s.pending={}
   for k,v in pairs(q.delivery.items)do s.known[tonumber(k)]=v end
   for k,v in pairs(q.delivery.handled)do s.results[tonumber(k)]=v end
   for _,i in ipairs(q.delivery.pending)do assert(s.known[i]and not s.results[i],'Invalid reconciliation pending');s.pending[#s.pending+1]={index=i,item=s.known[i]}end
   state.reconciled=true;return {effects=effects.export()}
  elseif q.op:sub(1,6)=='DEATH_'then
   assert(deathlink and state.mode~='restoring'and state.mode~='failed','DeathLink unavailable during restore/failure')
   return deathlink.control(q)
  elseif q.op=='EFFECTS'then
   assert(effects and state.mode~='restoring'and state.mode~='failed','Effects unavailable during restore/failure')
   effects.sync(q.effects,q.acknowledgement)
   return {effects=effects.export(),event=effects.event()}
  elseif q.op=='ACTIVATE'then
   assert(not effects or state.reconciled,'Effect overlay must reconcile before native activation')
   assert(state.mode=='restoring' and state.verified and not state.activated,'Stale/duplicate activation')
   assert(equal(witness(),state.baseline),'Cold native state changed before AP validation')
   state.activated=true;state.mode='synchronizing';state.stable=0;state.last_contact=os.time();state.frame=nil;travel.authorize(false)
   state.saved_signature=signature();state.requested=true;state.reason='resume synchronization checkpoint'
   status('Receiving offline items — player input remains gated', 'Items', 'Receiving offline items. Please wait.');io.unpause();return {active=true}
  end
  error('Unknown checkpoint command')
 end
 local function bootstrap()
  if not io.resume then return end
  io.pause();joypad.set(neutral,1);joypad.set(neutral,2)
  status('Validating resume — player input gated', 'Checkpoint', 'Restoring your saved game. Please wait.')
  local c=read(io.resume..'/controller.json');local expected=read(io.resume..'/witness.json')
  managed_load(io.resume..'/native.State',io.marker)
  assert(state.mode=='restoring','Bootstrap state load failed')
  import(c)
  state.baseline=witness();state.frame=io.frame()
  assert(equal(state.baseline,expected),'Cold-process native/controller witness mismatch')
  state.verified=true;state.last_checkpoint=io.restored_at;status('Waiting for server — restored state remains paused', 'Network', 'Waiting for the AP server. Your restored game is safely paused.')
 end
 event.oninputpoll(function()
  if state.mode=='playing'and map_gate()then
   -- Gate at the first eligible input poll, before a held direction/A can
   -- leave the safe return. State API and file I/O remain ordinary-thread only.
   local sig=signature()
   if sig and sig~=state.saved_signature then
    state.dirty=true;state.requested=true
    if not state.gate_started then state.gate_started=clock();state.gate_frame=io.frame()end
   end
  end
  if state.requested or (state.mode~='playing'and not(state.mode=='booting'and not map_gate()))then
   joypad.set(neutral,1);joypad.set(neutral,2)
  end
 end,'M233 mandatory automatic checkpoint input gate')
 local function process_delivery()
  if frozen()or state.ui then return end
  -- The initial stable map itself must be recoverable before the first native
  -- consumable issuance. A killed first grant then has a real matching State.
  if state.saved_signature==nil then return end
  if state.awaiting_ack and not delivery.state.flight then return end
  if state.batch_count>=32 and not delivery.state.flight then return end
  if #delivery.state.pending>0 and delivery.state.full_index==nil and map_gate()and state.mode=='playing'then quiesce('AP item delivery')end
  local count=#delivery.acks()
  if state.mode~='playing'or delivery.state.flight then delivery.process()end
  if #delivery.acks()>count then state.awaiting_ack=true;state.dirty=true;state.requested=true;state.stable=0;state.reason='durable AP item outcome' end
 end
 local function prepare_sync(commands)
  local unseen=false;for _,c in ipairs(commands)do if not delivery.state.known[c.index]then unseen=true end end
  if #commands>0 and(delivery.state.full_index==nil or unseen)and map_gate()and state.mode=='playing'then
   state.ui=false -- A newly arrived grant must settle before offering Quit again.
   quiesce('AP item delivery')
  end
 end
 local function presentation()
  local label
  if state.mode=='failed'or state.save_error then label='Save failed'
  elseif state.mode=='frozen'then label='Saving'
  elseif state.mode=='restoring'then label='Resuming'
  elseif state.mode=='suspended'or state.mode=='connecting'then label='Connection pending'
  elseif state.mode=='booting'then label='Connecting'
  elseif state.mode=='quiescing'or state.mode=='synchronizing'or state.requested or state.awaiting_ack or delivery.state.flight
    or io.read(0x79A2)~=2 or io.read(0x79F3)~=0 then label='Save pending'
  elseif state.dirty or state.exposed then label='Unsaved progress'
  elseif #delivery.state.pending>0 then label='Items pending: '..#delivery.state.pending
  elseif state.mode=='closed'then label='Progress saved'
  elseif clock()<(state.saved_notice_until or 0)and point_signature()==state.saved_point then label='Progress saved'
  else label='Last checkpoint'end
  local saved=type(state.last_checkpoint)=='number'and os.date('%H:%M',math.floor(state.last_checkpoint))or 'none'
  return {label=label,saved=saved,failed=state.mode=='failed'or state.save_error==true,
   connection_waiting=state.mode=='connecting'or state.mode=='suspended'or(state.mode=='restoring'and state.verified)}
 end
 return {effect_hold=function(hold)
   if hold and not state.effect_hold then
    assert(state.mode=='playing','Effect activation outside playable controller ownership')
    state.effect_hold=true;state.frame=io.frame();io.pause()
   elseif not hold and state.effect_hold then
    assert(state.frame==io.frame(),'Effect gate lost native frame ownership')
    state.effect_hold=false;state.frame=nil;io.unpause()
   end
  end,state=state,frozen=frozen,safe=safe,tick=tick,control=control,onload=onload,bootstrap=bootstrap,request=request,
  recover=recover,
  suspension=function()return state.suspension and {challenge=state.suspension.challenge,frame=state.frame,mode=state.suspension.mode}end,
  waiting_for_bind=function()return state.mode=='connecting'end,
  prepare_sync=prepare_sync,presentation=presentation,disconnected=disconnected,batch_ready=batch_ready,
  user_pause=function()
   state.last_contact=os.time()
   state.message='Paused - unpause BizHawk to continue';state.message_until=os.time()+1
  end,
  contact=function()state.last_contact=os.time()end,fail=failed,
  process_delivery=process_delivery}
end
return M
