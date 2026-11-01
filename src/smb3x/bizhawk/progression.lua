-- SPDX-License-Identifier: MPL-2.0
-- M24.5 read-only status. Native pause remains the sole gameplay pause owner.
local M={}
function M.new(io,expected)
 local visible,page,held=false,1,{}
 local value,last=nil,-100000
 local pages={'checks','passes','hammers'}
 if expected.gate~='off'then pages[#pages+1]='stars'end
 local names={'GRASS','DESERT','WATER','GIANT','SKY','ICE','PIPE','DARK'}
 local function integer(n,max)return type(n)=='number'and n==math.floor(n)and n>=0 and n<=max end
 local function valid(v)
  if type(v)~='table'or v.version~=1 or v.session~=expected.session or v.rom~=expected.rom then return false end
  if type(v.connected)~='boolean'or v.gate~=expected.gate or v.hammer_mode~=expected.hammer_mode or v.required~=expected.required then return false end
  if not integer(v.unlock_mask,255)or v.unlock_mask%2~=1 or not integer(v.hammers,46)or v.hammers%2~=0 or math.floor(v.hammers/16)%2~=0 or not integer(v.stars,255)or not integer(v.pending,65535)then return false end
  if type(v.checks)~='table'or type(v.totals)~='table'or #v.checks~=8 or #v.totals~=8 then return false end
  for w=1,8 do if v.totals[w]~=expected.totals[w]or not integer(v.checks[w],v.totals[w])then return false end end
  return true
 end
 local function publish(session,v)
  if session~=expected.session or not valid(v)then value=nil;return false end
  value={};for k,x in pairs(v)do if type(x)=='table'then value[k]={};for i,n in ipairs(x)do value[k][i]=n end else value[k]=x end end
  last=io.frame();return true
 end
 local function update()
  local buttons=io.buttons()or {};local edges={}
  for k,v in pairs(buttons)do if v and not held[k]then edges[k]=true end end
  held={};for k,v in pairs(buttons)do held[k]=v end
  if not io.eligible()or edges.Start or buttons.Start then visible=false
  elseif edges.Select then visible=not visible;if visible then page=1 end
  elseif visible and edges.B then visible=false
  elseif visible then
   if edges.Right then page=page%#pages+1
   elseif edges.Left then page=(page+#pages-2)%#pages+1 end
  end
 end
 local function has(mask,w)return math.floor(mask/2^(w-1))%2==1 end
 local function lines()
  if not visible then return nil end
  local category=pages[page]
  local title=({checks='ITEM CHECKS',passes='WORLD PASSES',hammers='REGIONAL HAMMERS',stars='STAR HUNT'})[category]
  local out={string.format('%-22s%d/%d',title,page,#pages),'PAUSED - READ ONLY'}
  local w=io.world()
  if not value or not integer(w,8)or w<1 then out[#out+1]='STATUS UNAVAILABLE'
  else
   if category=='checks'then
    local done,total=0,0;for i=1,8 do done=done+value.checks[i];total=total+value.totals[i]end
    out[#out+1]='PHYSICAL WORLD '..w..' '..names[w]
    out[#out+1]='               DONE TOTAL'
    out[#out+1]=string.format('CURRENT WORLD  %3d   %3d',value.checks[w],value.totals[w])
    out[#out+1]=string.format('ALL WORLDS     %3d   %3d',done,total)
    out[#out+1]='PHYSICAL REWARDS ONLY'
   elseif category=='passes'then
    for i=1,8 do out[#out+1]=string.format('%d %-7s %-7s%s',i,names[i],has(value.unlock_mask,i)and 'OWNED'or 'MISSING',i==w and ' HERE'or '')end
   elseif category=='hammers'then
    out[#out+1]='PHYSICAL WORLD '..w..' '..names[w]
    if value.hammer_mode=='regional'then
     for _,i in ipairs({2,3,4,6})do out[#out+1]=string.format('%-6s W%d  %s',names[i],i,has(value.hammers,i)and 'OWNED'or 'MISSING')end
     out[#out+1]='USE TOOLS ON MAP'
    else out[#out+1]='LEGACY INVENTORY HAMMERS';out[#out+1]='USE FROM MAP INVENTORY'end
   elseif category=='stars'then
    out[#out+1]=string.format('STAR FRAGMENTS  %3d/%3d',value.stars,value.required)
    out[#out+1]=value.gate=='world_8'and 'GATE WORLD 8 TRAVEL'or 'GATE BOWSER CASTLE'
    out[#out+1]=value.stars>=value.required and 'STAR THRESHOLD MET'or 'STAR THRESHOLD NOT MET'
    if value.gate=='world_8'then out[#out+1]=has(value.unlock_mask,8)and 'WORLD 8 PASS OWNED'or 'WORLD 8 PASS MISSING'end
   end
   out[#out+1]=value.offline and 'DISPOSABLE FIXTURE DATA'or ((not value.connected or io.frame()-last>180)and 'LAST CONFIRMED - STALE'or 'LAST CONFIRMED STATUS')
   out[#out+1]='UPDATES ON MAP'
  end
  out[#out+1]='LR PAGE  B/SELECT HIDE'
  out[#out+1]='START RESUMES'
  return out
 end
 return {publish=publish,update=update,lines=lines,close=function()visible=false;value=nil end,
  hide=function()visible=false end,visible=function()return visible end}
end
function M.bizhawk(build,rows)
 local function read(a)return memory.read_u8(a,'System Bus')end
 local last=-1000
 local id=event.onmemoryexecute(function()
  if read(0x8E79)==0xAD and read(0x8E7A)==0x76 and read(0x8E7B)==3 and read(0x376)==1 then last=emu.framecount() end
 end,0x8E79,'M222 read-only native pause observer','System Bus')
 local totals={0,0,0,0,0,0,0,0}
 for _,r in ipairs(rows)do if r.enabled and (not r.hammer_required or build.progression.hammer_mode=='regional')then totals[r.world]=totals[r.world]+1 end end
 local panel=M.new({frame=emu.framecount,buttons=function()return joypad and joypad.get(1) or {}end,
  world=function()return read(0x727)+1 end,
  eligible=function()
   local tileset=read(0x70A)
   return emu.framecount()-last<=2 and read(0x376)==1 and read(0x79A1)==9 and read(0x79AE)==1 and read(0x79A2)==2
    and read(0x726)==0 and read(0x72B)==1 and read(0x727)<8 and tileset>=1 and tileset<=14 and tileset~=7
    and read(0x14)==0 and read(0x3DE)==0 and read(0xCF)==0
  end}, {session=build.session,rom=build.output.sha256,totals=totals,gate=build.progression.star_hunt_mode,
    hammer_mode=build.progression.hammer_mode,required=build.progression.star_hunt_mode=='off' and 0 or build.progression.star_fragments_required})
 event.onexit(function()panel.close();if id then event.unregisterbyid(id)end end,'M222 pause cleanup')
 event.onloadstate(panel.close,'M222 pause state-load cleanup')
 return panel
end
return M
