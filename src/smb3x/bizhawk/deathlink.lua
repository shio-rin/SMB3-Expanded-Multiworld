-- SPDX-License-Identifier: MPL-2.0
-- DeathLink is independent of the delayed indexed queue. No network/file I/O.
local M={}
function M.new(io)
 local view={contract='m25-deathlink-2',records={}}
 local events={};local sequence=0;local remote=nil
 local function sync(value)
  assert(value.contract=='m25-deathlink-2'and type(value.records)=='table','Invalid DeathLink controller')
  for k,r in pairs(view.records)do
   local n=assert(value.records[k],'Lost death dedup record')
   assert(n.direction==r.direction and n.received==r.received and n.deadline==r.deadline and n.run==r.run,'Changed death receipt/origin')
  end
  view=value
 end
 local api={}
 function api.import(value)
  assert(not remote and #events==0,'Death import requires fresh frozen lifetime')
  sync(value)
  assert(io.read(0x7c10)==0,'Pending native death request in map checkpoint')
 end
 function api.export()return view end
 function api.safe()return not remote and #events==0 and io.read(0x7c10)==0 end
 function api.observe(e)
  if e.kind~='native-local-death'and e.kind~='remote-death-observed'and not(e.kind=='canceled'and remote)then return end
  sequence=sequence+1
  events[#events+1]={sequence=sequence,kind=e.kind,reason=e.reason,remote_id=remote}
 end
 function api.control(q)
  sync(q.deathlink)
  if q.op=='DEATH_STATUS'then
   return {events=events,dying=io.read(0xf1)~=0,ready=io.enabled and io.allowed()and not remote and io.native.can_start('death')}
  elseif q.op=='DEATH_ACK'then
   assert(events[1]and events[1].sequence==q.event_sequence,'Stale death observation acknowledgement')
   if events[1].remote_id then remote=nil end
   table.remove(events,1);return {acknowledged=true}
  elseif q.op=='DEATH_APPLY'then
   assert(io.enabled,'DeathLink is disabled')
   local r=assert(view.records[q.id],'Remote death lacks durable custody')
   assert(r.direction=='incoming'and r.state=='committed'and r.received==q.received and r.deadline==q.deadline,'Remote death lacks exact commitment')
   local now=io.clock()*1000
   if remote or now<q.received or now>=q.deadline or not io.allowed()then return {accepted=false}end
   remote=q.id
   local accepted=io.native.remote_death(q.deadline/1000)
   if not accepted then remote=nil end
   return {accepted=accepted}
  end
  error('Unknown DeathLink command')
 end
 return api
end
return M
