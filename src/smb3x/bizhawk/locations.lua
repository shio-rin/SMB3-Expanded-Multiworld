-- SPDX-License-Identifier: MPL-2.0
-- M222 authentic native state/receipt monitor. No reward insertion callbacks.
local M={hooks={}}
local function hex(v) return tonumber(v:sub(3),16) end
function M.signature(rows)
    local parts={}
    for _,r in ipairs(rows) do
        local p=r.entry or {}; local ids={}
        for _,id in ipairs(r.object_ids or {}) do ids[#ids+1]=tostring(id) end
        parts[#parts+1]=table.concat({hex(r.id),r.world,r.stage,r.kind,r.signal,r.enabled and 1 or 0,
            hex(r.address),hex(r.bit),r.slot or -1,hex(p.x_hi or "0x00"),hex(p.x or "0x00"),
            hex(p.y or "0x00"),r.tileset or -1,r.terminal and 1 or 0,table.concat(ids,","),r.receipt_bit or 0},":")
    end
    return table.concat(parts,"|")
end
local function has(v,b) return math.floor(v/b)%2==1 end
function M.new(io,rows)
 local active,seen,prior={},{},{}
 local last_event="No completion observed"
 local function configure(ids)
  local expected={};local count=0
  for _,r in ipairs(rows) do if r.enabled and (not r.hammer_required or io.read(0x9F3C)==1) then expected[tonumber(r.id:sub(3),16)]=true;count=count+1 end end
  assert(#ids==count,"M222 location profile mismatch")
  local supplied={}
  for _,id in ipairs(ids) do assert(expected[id] and not supplied[id],"Invalid M222 location ID");supplied[id]=true end
  active=supplied
 end
 local function poll()
  if io.read(0x79A0)~=0xAA or io.read(0x79A1)~=9 or io.read(0x79A2)~=2 or io.read(0x79AE)~=1
   or io.read(0x070A)~=0 or io.read(0x0726)~=0 or io.read(0x072B)~=1 then return end
  for _,r in ipairs(rows) do
   local id=tonumber(r.id:sub(3),16)
   if active[id] and r.world==io.read(0x0727)+1 then
    local proof
    if r.kind=='bowser' then
     proof=io.read(0x79F6)==1 and io.read(0x79F5)>=1 and io.read(0x79F5)<=3
    elseif r.receipt_bit then
     proof=has(io.read(0x79E0),r.receipt_bit)
     if (r.kind=="plant" or r.kind=="military") then proof=proof and io.read(0x7F15+r.slot)==0 end
     if r.kind=="house" or r.kind=="hand" then proof=proof and has(io.read(tonumber(r.address:sub(3),16)),tonumber(r.bit:sub(3),16)) end
    else proof=has(io.read(tonumber(r.address:sub(3),16)),tonumber(r.bit:sub(3),16)) end
    if proof and not seen[id] then
     seen[id]=true
     last_event=r.name..(io.assisted and io.assisted() and " [developer-assisted session]" or "")
     io.log("LOCATION COMPLETE "..last_event.." id="..id.." native M222 receipt/state", "Checks", not prior[id] and r.name:gsub(" Clear$", "")..(r.kind=="house" and " opened." or " cleared.") or nil)
    end
   end
  end
 end
 return {configure=configure,poll=poll,rebaseline=function()end,onload=function()end,
  last_event=function()return last_event end,
  import_checks=function(ids)
   local next_prior={}
   for _,id in ipairs(ids)do assert(active[id] and not next_prior[id],'Invalid checkpoint physical ID');next_prior[id]=true end
   for id in pairs(prior)do assert(next_prior[id],'Physical checkpoint history rolled back')end
   prior=next_prior
  end,
  checks=function()
   local all={};for id in pairs(prior)do all[id]=true end;for id in pairs(seen)do all[id]=true end
   local out={};for id in pairs(all)do out[#out+1]=id end;table.sort(out);return out
  end}
end
return M
