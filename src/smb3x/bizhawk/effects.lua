-- SPDX-License-Identifier: MPL-2.0
-- One indexed queue; selection once per entry, native clocks only.
-- Readiness holds native frames until the Python epoch commitment is durable.
local M={}
function M.new(io)
 local view={contract='m25-effects-1',prefix={},records={},last_entry=0}
 local serial=0;local inside=false;local snapshot=nil;local selected=nil
 local remaining=nil;local event=nil;local sequence=0;local area=nil;local native
 local terminal={completed=true,completed_noop=true,disposed_interrupted=true}
 local function emit(value)
  sequence=sequence+1;value.sequence=sequence;event=value
 end
 local function outcome(state,reason)
  if not selected then return end
  local r=view.records[tostring(selected)]
  emit({type='outcome',index=selected,entry=r.entry,token=r.token,state=state,reason=reason})
 end
 native=io.native(function(e)
  io.log('M25 NATIVE '..e.kind..' '..e.reason, 'Effects', e.kind=='remote-death-observed' and 'DeathLink: a shared death was applied.' or nil)
  if e.kind=='native-local-death'or e.kind=='remote-death-observed'or e.kind=='native-death-request'or e.kind=='canceled'then
   if io.death_event then io.death_event(e)end
  end
  if not selected or e.effect=='death'then return end
  if e.kind=='activated'then outcome('activated',e.reason)
  elseif e.kind=='completed'then
   outcome(e.reason:find('no%-op')and 'completed_noop' or
    (e.reason:find('boundary')or e.reason:find('supersedes'))and 'disposed_interrupted'or'completed',e.reason)
  elseif e.kind=='canceled-before-activation'then
   local r=view.records[tostring(selected)]
   outcome(r.state=='scheduled'and'queued'or'disposed_interrupted',e.reason)
  end
 end)
 local api={native=native}
 function api.export()return view end
 function api.event()return event end
 function api.safe()
  if event or native.state().active or native.state().pending then return false end
  for _,r in pairs(view.records)do if r.state=='committed'or r.state=='activated'then return false end end
  return true
 end
 function api.import(value)
  assert(value.contract=='m25-effects-1'and type(value.prefix)=='table'and type(value.records)=='table','Wrong effect contract')
  assert(not selected and not event,'Effect import requires frozen fresh controller')
  view=value;serial=value.last_entry;inside=false;snapshot=nil
 end
 function api.sync(value,ack)
  assert(value.contract==view.contract and value.last_entry>=view.last_entry,'Effect contract/entry regression')
  for i,row in ipairs(view.prefix)do assert(io.equal(row,value.prefix[i]),'Changed effect receipt prefix')end
  for i,r in pairs(view.records)do
   assert(value.records[i]and value.records[i].receipt==r.receipt,'Lost effect custody')
   if terminal[r.state]then assert(io.equal(r,value.records[i]),'Changed terminal effect')end
  end
  if ack then
   assert(event and event.sequence==ack,'Stale effect acknowledgement')
   local e=event
   if e.type=='select'then
    assert(value.last_entry==e.entry,'Entry persistence mismatch')
    if e.index~=false then
     selected=e.index;local r=value.records[tostring(selected)]
     assert(r.state=='scheduled'and r.entry==e.entry,'Schedule persistence mismatch')
     remaining=r.delay_frames;area=e.area
    end
   elseif e.type=='ready'then
    local r=value.records[tostring(selected)]
    assert(r.state=='committed'and r.entry==e.entry and type(r.token)=='string'and #r.token==64,'No durable native activation permission')
    assert(native.area()==e.area,'Area changed while commitment frozen')
    view=value;event=nil
    assert(native.request(r.kind),'Native activation owner changed while frozen')
    io.hold(false);return
   elseif e.type=='outcome'then
    local r=value.records[tostring(e.index)]
    assert(r.state==e.state and r.reason==e.reason,'Outcome not durably acknowledged')
    -- Display only durably acknowledged outcomes, never early trap scheduling.
    -- Native reasons/event payloads and DeathLink observation stay untouched.
    local names={walking='Walking Only Trap',icy='Icy Feet Trap',micro='Micro-Goomba Infestation',small='Forced Small Trap',star='Starman (Effect)',mushroom='Emergency Mushroom (Effect)'}
    local temporary=r.kind=='walking'or r.kind=='icy'or r.kind=='micro'
    local label=names[r.kind];local friendly=nil
    if label then
     if r.state=='activated'and temporary then friendly=label..' activated.'
     elseif r.state=='completed_noop'then friendly=label..': no change needed.'
     elseif r.state=='completed'then friendly=label..(temporary and ' ended.'or ' applied.')
     -- A committed request may stop before native activation. Do not
     -- reveal an unactivated trap, including with Trap Warning Hide.
     elseif r.state=='disposed_interrupted'and view.records[tostring(e.index)].state=='activated'then friendly=label..' interrupted.'end
    end
    io.log('M25 EFFECT ACK index='..e.index..' kind='..r.kind..' state='..r.state..' reason='..r.reason, 'Effects', friendly)
    if terminal[r.state]or r.state=='queued'then selected=nil;remaining=nil end
   else error('Unknown effect event')end
   event=nil;io.hold(false)
  end
  view=value
 end
 function api.tick()
  native.tick()
  if event and(event.type=='ready'or(event.type=='outcome'and event.state=='activated'))then io.hold(true);return end
  local level=io.read(0x70a)~=0
  if not level then
   if selected and view.records[tostring(selected)].state=='scheduled'and not event then outcome('queued','entry ended before commitment')end
   inside=false;snapshot=nil
  elseif not inside then
   inside=true;serial=math.max(serial,view.last_entry)+1;snapshot={}
   -- Snapshot exactly what was in custody at entry. Later arrivals wait.
   for i,r in pairs(view.records)do if r.state=='queued'then snapshot[#snapshot+1]=tonumber(i)end end
   table.sort(snapshot)
  end
  if event then return end
  if snapshot and not selected and native.can_start('small')then
   local index=false;local eligible={}
   for _,i in ipairs(snapshot)do
    local r=view.records[tostring(i)]
    if r and r.state=='queued'and native.can_start(r.kind)then eligible[#eligible+1]=i;if index==false then index=i end end
   end
   snapshot=nil;emit({type='select',entry=serial,index=index,eligible=eligible,area=native.area()});return
  end
  if selected and view.records[tostring(selected)].state=='scheduled'then
   -- A doorway changes room identity without ending the stage entry. Retain
   -- its selected receipt and remaining active-frame delay across that load.
   -- Death/exit still requeues, and each effect must qualify in the new room.
   if native.ended()then outcome('queued','native entry interrupted before commitment');return end
   if native.gameplay()then
    remaining=math.max(0,remaining-1)
    if remaining==0 and native.can_start(view.records[tostring(selected)].kind)then
     emit({type='ready',index=selected,entry=view.records[tostring(selected)].entry,area=native.area()})
     io.hold(true)
    end
   end
  end
 end
 return api
end
return M
