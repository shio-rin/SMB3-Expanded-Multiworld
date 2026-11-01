-- SPDX-License-Identifier: MPL-2.0
-- M25 native mechanics port from narrowed accepted continuation. No persistence in callbacks.
-- Gameplay danger is intentional. Only native initialization/ownership is gated.
local M={}
function M.new(c,notify)
 local S=c.symbols
 local function r(a)return memory.read_u8(a,'System Bus')end
 local function w(a,v)memory.write_u8(a,v%256,'System Bus')end
 local function g(k)return r(assert(S[k],k))end
 local function p(k,v)w(assert(S[k],k),v)end
 assert(memory.hash_region(0,524288,'PRG ROM'):lower()==c.prg_sha256,'M25 native ROM mismatch')
 local active,pending,pending_area=nil,nil,nil
 local remote,suppress,assisted=false,false,false
 local remote_expires,alive_frames=0,0
 local remote_clock=0
 local death_armed=true
 local events={}
 local publishing=false
 local function allowed()return not c.allowed or c.allowed()end
 local function area()return r(0x70a)..':'..(r(0x7eb9)+256*r(0x7eba))end
 local function snapshot()
  return {air=g('Player_InAir'),water=g('Player_InWater'),slide=g('Player_Slide'),suit=g('Player_Suit'),fly=g('Player_FlyTime'),auto=g('Level_AScrlConfig'),vertical=g('Level_7Vertical'),x=g('Player_X')+256*g('Player_XHi'),y=g('Player_Y')+256*g('Player_YHi'),vx=g('Player_XVel'),area=area()}
 end
 local function note(kind,reason,effect)
  local e={frame=emu.framecount(),kind=kind,reason=reason,effect=effect or(active and active.kind or pending),context=snapshot()}
  -- CPU callbacks only append small in-memory observations. The ordinary Lua
  -- service loop drains them; diagnostics and durable work stay outside CPU hooks.
  events[#events+1]=e
 end
 local function gameplay()
  return allowed() and r(0x70a)>0 and r(0x70a)<=14 and r(0x70a)~=7 and g('Cine_ToadKing')==0 and r(0x79f5)==0 and r(S.Level_Objects+1)~=0x09 and r(S.Level_Objects+1)~=0xd5 and r(0xeb)>0 and r(0x376)==0 and r(0x79db)==0
   and g('Player_IsDying')==0 and g('Player_HaltGame')==0 and g('Player_HaltTick')==0
   and g('Level_PipeMove')==0 and g('Player_InPipe')==0 and g('LevelPartialInit')==0
   and g('Level_JctCtl')==0 and g('Player_EndLevel')==0 and g('Level_GetWandState')==0
   and g('Player_QueueSuit')==0 and g('Player_Grow')==0
 end
 local function free_slot()
  for i=5,0,-1 do if r(S.SpecialObj_ID+i)==0 then return i end end
 end
 local function can_start(kind)
  if not gameplay()or alive_frames<30 then return false end
  if(kind=='icy'or kind=='walking')and g('Player_InWater')~=0 then return false end
  if kind=='micro'then
   -- Genuine graphics/slot constraints; water releases attachment natively.
   return r(S.PatTable_BankSel+5)==0x4f and free_slot()~=nil and g('Player_InWater')==0
  end
  return kind=='icy'or kind=='walking'or kind=='small'or kind=='star'or kind=='mushroom'or kind=='death'
 end
 local function finish(reason)
  if active and active.slot and active.owned and active.area==area()then
   local i=active.slot
   if r(S.SpecialObj_ID+i)==6 then w(S.SpecialObj_Data+i,255);w(S.SpecialObj_YVel+i,224)end
  end
  note('completed',reason);active=nil
 end
 local api={}
 function api.area()return area()end
 function api.cancel(reason)
  if active then finish(reason)end
  if pending then local k=pending;pending=nil;note('canceled-before-activation',reason,k)end
 end
 function api.can_start(k)return can_start(k)end
 function api.gameplay()return gameplay()end
 function api.ended()return r(0x70a)==0 or g('Player_IsDying')~=0 or g('Player_EndLevel')~=0 end
 function api.state()return {active=active,pending=pending,events=events}end
 local function request(k)
  if not({icy=true,walking=true,small=true,micro=true,star=true,mushroom=true,death=true})[k]then return false end
  if active or pending then return false end
  pending=k;pending_area=area();note('queued','technical initialization guard only');return true
 end
 function api.request(k)
  if k=='death'then return false end
  return request(k)
 end
 function api.remote_death(deadline)
  if type(deadline)~='number' or (c.clock or os.time)()>=deadline then return false end
  if g('Player_IsDying')~=0 then note('canceled','already dying; coalesced remote event');return false end
  if active then finish('remote DeathLink supersedes temporary effect')end
  if pending then note('canceled-before-activation','DeathLink priority');pending=nil end
  remote=true;remote_expires=deadline;remote_clock=(c.clock or os.time)();return request('death')
 end
 function api.tick()
  if pending and pending~='death'and(area()~=pending_area or api.ended())then
   local k=pending;pending=nil;note('canceled-before-activation','retain unactivated indexed receipt',k)
  end
  if pending=='death'and remote and ((c.clock or os.time)()>=remote_expires or (c.clock or os.time)()<remote_clock) then note('canceled','20-second remote expiry');pending=nil;remote=false end
  if gameplay()then
   alive_frames=alive_frames+1
   if alive_frames>=30 then death_armed=true;suppress=false;assisted=false end
  else alive_frames=0 end
  if active then
   if api.ended()or area()~=active.area or g('LevelPartialInit')~=0 or g('Level_JctCtl')~=0 then finish('native stage/death/room boundary')
   elseif active.kind=='micro'and r(S.PatTable_BankSel+5)~=0x4f then finish('native CHR ownership changed; release actor')
   elseif active.kind=='micro'and(not active.owned or r(S.SpecialObj_ID+active.slot)~=6 or r(S.SpecialObj_Data+active.slot)>=128)then finish('native attachment release')
   elseif gameplay()then active.remaining=active.remaining-1;if active.remaining<=0 then finish('600 active gameplay frames elapsed')end end
  end
  local ready=events;events={}
  if notify then for _,e in ipairs(ready)do notify(e)end end
 end
 event.onmemoryexecute(function()
  if r(S.PAGE_A000)~=8 or not pending or not can_start(pending)then return end
  if pending=='death'and remote and ((c.clock or os.time)()>=remote_expires or (c.clock or os.time)()<remote_clock)then pending=nil;remote=false;note('canceled','original DeathLink deadline expired before CPU consumption','death');return end
  local k=pending;local slot=k=='micro'and free_slot()or nil
  active={kind=k,remaining=600,area=area(),slot=slot};pending=nil
  note('activated','native Player_Update; airborne/boss/autoscroll permitted')
  if k=='small'then
   if g('Player_Suit')~=0 then p('Player_QueueSuit',1);p('Player_Grow',0x2f);p('Player_FlyTime',0);p('Player_Power',0);p('Player_PMeterCnt',0);p('Player_RunFlag',0)
    finish('one-way native suit queue; no restoration')
   else finish('explicit consumed no-op: already Small')end
  elseif k=='mushroom'then
   if g('Player_Suit')==0 then p('Player_QueueSuit',2);p('Player_Grow',0x2f);finish('native Small-to-Super queue')
   else finish('explicit consumed no-op: stronger suit retained')end
  elseif k=='star'then
   if g('Level_PSwitchCnt')==0 then p('Sound_QMusic2',0x0a)end
   p('Player_StarInv',0xe0);finish('native bounded refresh to E0; native lifecycle owns expiry/music')
  elseif k=='micro'then
   publishing=true;active.owned=true
   for _,n in ipairs({'SpecialObj_Data','SpecialObj_Var1','SpecialObj_Var2','SpecialObj_Var3','SpecialObj_Timer','SpecialObj_XVel','SpecialObj_YVel','SpecialObj_XVelFrac','SpecialObj_YVelFrac'})do w(S[n]+slot,0)end
   w(S.SpecialObj_XLo+slot,g('Player_X')+4);w(S.SpecialObj_YLo+slot,g('Player_Y')+8);w(S.SpecialObj_YHi+slot,g('Player_YHi'));w(S.SpecialObj_ID+slot,6);publishing=false
  elseif k=='death'then
   suppress=true;assisted=not remote;alive_frames=0
   note('native-death-request',remote and'remote; suppress echo'or'developer-assisted')
   w(0x7c10,0xd1);active=nil;remote=false
  end
 end,S.Player_Update,'M25 native activation','System Bus')
 event.onmemoryexecute(function()
  if r(S.PAGE_A000)~=8 then return end
  if active and gameplay()then
   if active.kind=='walking'then
    -- Preserve lower uphill/native targets. No B masking, XVel or flight writes.
    p('Temp_Var14',math.min(g('Temp_Var14'),0x18))
   elseif active.kind=='icy'and g('Player_InAir')==0 and g('Player_InWater')==0 and g('Player_Slide')==0 then
    p('Player_Slippery',math.max(1,g('Player_Slippery')))
   end
  end
  if c.trace then c.trace(g('Player_Slippery'),g('Temp_Var14'))end
 end,0xab85,'M25 native target and traction','System Bus')
 event.onmemoryexecute(function()
  if r(S.PAGE_C000)~=0 or r(0x70a)==0 or r(0x70a)==7 or g('Player_IsDying')==0 or not death_armed then return end
  death_armed=false;alive_frames=0
  note(assisted and'assisted-death-observed'or suppress and'remote-death-observed'or'native-local-death','original Player_Die DAAE; trap deaths retain local origin')
 end,0xdaae,'M25 native death origin','System Bus')
 for slot=0,5 do
  event.onmemorywrite(function()
   if active and active.slot==slot and not publishing then active.owned=false end
  end,S.SpecialObj_ID+slot,'M25 Micro slot lifetime '..slot,'System Bus')
 end
 return api
end
return M
