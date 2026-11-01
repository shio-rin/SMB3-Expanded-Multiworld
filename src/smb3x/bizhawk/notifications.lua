-- SPDX-License-Identifier: MPL-2.0
-- Sole notification queue, active-visible timer and checkpoint status compositor.
local M={}
-- One composer owns the client surface. The retained renderer below supplies
-- only the read-only progression panel and native ending prompt, below headers.
-- Read-only subset of the audited native overworld witnesses. Deliberately
-- preserve the accepted B-inventory behavior. Custom menu owners and their
-- restoration/release phases suppress status until native ownership returns.
function M.status_scene(r)
 if r(0x79de)~=0 or r(0x79fb)~=0 or r(0x7ad0)~=0 or r(0x79db)~=0 or r(0x79df)~=0 or r(0x7ad9)~=0 or r(0x7ad8)~=0 then return false end
 if r(0x70A)~=0 or r(0x729)~=13 or r(0x100)~=0xC0 or r(0x728)>1
  or r(0x726)~=0 or r(0x72B)~=1 or r(0x727)>7
  or r(0x79A1)~=9 or r(0x79A2)~=2 or r(0x79AE)~=1 or r(0x79A9)~=r(0x727)then return false end
 for _,a in ipairs({0x14,0x1D,0x1E,0x20,0xC5,0xDA,0x3E1,0x3E6,
  0x710,0x711,0x73C,0x73E,0x745,0x7955,0x597,0x7973,0x79DD})do
  if r(a)~=0 then return false end
 end
 return true
end
local body_new=dofile((os.getenv('SMB3_AP_PROJECT') or '.')..'/bizhawk/presentation_body.lua').new
function M.new(io,options)
 options=options or {}
 local queue,current,remaining={},nil,0
 local seen,order={},{}
 local previous_time,previous_frame,previous_active=nil,nil,false
 local enabled=options.notifications~=false
 local header=0
 local map_frame,status_visible=nil,false
 local body_io={};for k,v in pairs(io)do body_io[k]=v end
 local function body_offset()return options.panel and options.panel.visible()and 0 or header end
 body_io.clear=function()end
 body_io.size=function()local w,h=io.size();return w,math.max(0,h-body_offset())end
 body_io.box=function(x,y,w,h,fg,bg,s)io.box(x,y+body_offset(),w,h,fg,bg,s)end
 body_io.text=function(x,y,line,fg,bg,size,s)io.text(x,y+body_offset(),line,fg,bg,size,s)end
 if io.paneltext then body_io.paneltext=function(x,y,line,scale,color)io.paneltext(x,y+body_offset(),line,scale,color)end end
 local body_options={};for k,v in pairs(options)do body_options[k]=v end;body_options.notifications=true
 local body=body_new(body_io,body_options)
 local function clean(s)return tostring(s or ''):gsub('[\r\n\t]',' '):gsub('[^ -~]','?')end
 local function short(s,n)s=clean(s);return #s<=n and s or s:sub(1,math.max(0,n-3))..'...'end
 local function wrapped(s,columns,limit)
  local lines={};s=clean(s)
  while #s>0 and #lines<limit do
   if #s<=columns then lines[#lines+1]=s;break end
   if #lines==limit-1 then lines[#lines+1]=short(s,columns);break end
   local cut=columns;for i=columns,math.max(1,columns-12),-1 do if s:sub(i,i)==' 'then cut=i;break end end
   lines[#lines+1]=s:sub(1,cut):gsub('%s+$','');s=s:sub(cut+1):gsub('^%s+','')
  end
  return lines
 end
 local function push(session,events)
  if session~=io.session or type(events)~='table'then return false end
  for i,e in ipairs(events)do
   if i>256 then break end
   if type(e)=='table'and type(e.id)=='string'and #e.id<=80 and type(e.text)=='string'and not seen[e.id]then
    seen[e.id]=true;order[#order+1]=e.id
    if #order>4096 then seen[table.remove(order,1)]=nil end
    if enabled then
     local event={text=clean(e.text):sub(1,240),kind=e.kind,item=e.item,player=e.player,count=math.max(1,math.min(100000,tonumber(e.count)or 1))}
     if #queue>=8 then
      local last=table.remove(queue);event.count=event.count+last.count
      event.text=event.count..' additional AP item events; see client log';event.kind=nil
     end
     queue[#queue+1]=event
    end
   end
  end
  return true
 end
 local function draw(info,active)
  info=info or {label='Connecting',saved='none'}
  local width,height=io.size();local ox,oy=0,0
  if io.viewport then ox,oy,width,height=io.viewport()end
  local font=width>=512 and 12 or(width>=220 and 10 or 8)
  local gap,margin,advance=8,4,math.ceil(font*.65)
  local right=math.max(48,math.floor(width*.38));local left=math.max(0,width-right-gap-2*margin)
  local columns=math.max(4,math.floor((left-8)/advance));local rc=math.max(4,math.floor((right-8)/advance))
  header=3*(font+3)+8
  io.clear('client')
  body.draw()
  local panel_visible=options.panel and options.panel.visible()
  local now=io.clock();local frame=io.frame()
  local visible=enabled and not panel_visible and width>=160 and height>=header+32
  -- A safety-held connection can occur before any map has been drawn. Keep
  -- this explanation independent of ordinary notice visibility/map status.
  if info.connection_waiting and width>=160 and height>=header then
   local wc=math.max(4,math.floor((width-2*margin-6)/advance))
   local lines=wrapped('Waiting for AP server. Game paused safely. Check room/address in client.',wc,4)
   for i,line in ipairs(lines)do io.toptext(ox+margin+3,oy+margin+2+(i-1)*(font+3),line,font)end
  end
  local running=active==true and visible and not(io.native_paused and io.native_paused())
  local dt=previous_time and now-previous_time or 0
  if current and running and previous_active and frame>(previous_frame or frame)and dt>=0 and dt<=.25 then remaining=remaining-dt end
  previous_time=now;previous_frame=frame;previous_active=running
  if current and remaining<=0 then current=nil end
  if not current and #queue>0 and running then current=table.remove(queue,1);remaining=5 end
  if current and visible then
   local lines
   if (current.kind=='received'or current.kind=='sent')and current.item and current.player then
    lines={current.kind=='received'and'Received:'or'Sent:',short(current.item,columns),
     (current.kind=='received'and'From: 'or'To: ')..short(current.player,columns-(current.kind=='received'and 6 or 4))}
   else lines=wrapped(current.text,columns,3)end
   for i,line in ipairs(lines)do io.toptext(ox+margin+3,oy+margin+2+(i-1)*(font+3),line,font)end
  end
  -- Hide on the first non-map witness, including pause and return transitions.
  -- Reappear after eight actual settled map frames. A locally verified cold
  -- checkpoint may already be paused on that exact map; it needs no new frames.
  local map=io.status_scene and io.status_scene()
  if not map or (map_frame and frame<map_frame)then map_frame=nil;status_visible=false end
  if map and not map_frame then map_frame=frame end
  status_visible=map==true and (status_visible or frame-map_frame>=8 or (info.label=='Resuming'and info.saved~='none'))
  if status_visible and width>=80 and height>=header then
   local lines=wrapped(info.label or'Checkpoint unknown',rc,2)
   lines[#lines+1]=info.failed and short('See log',rc)or short(info.saved=='none'and'No checkpoint'or('At '..tostring(info.saved)),rc)
   local x=width-margin-right
   for i,line in ipairs(lines)do io.toptext(ox+x+3,oy+margin+2+(i-1)*(font+3),line,font)end
  end
 end
 return {push=push,draw=draw,snapshot=body.snapshot,enabled=function()return enabled end,
  debug=function()return {queued=#queue,current=current,remaining=remaining,header=header,status_visible=status_visible}end,
  toggle=function()enabled=not enabled;return enabled end,close=function()body.close();io.clear('client')end}
end
function M.bizhawk(session,options)
 -- PRG031 StatusBarCHR_0000=$5C; uppercase tiles B0..C9, digits F0..F9.
 -- Read immutable CHR directly; never change MMC3 banks, PPU, or native palettes.
 local glyphs={}
 local punctuation={[':']={0,24,24,0,24,24,0,0},['/']={2,4,8,16,32,64,0,0},['-']={0,0,0,126,0,0,0,0}}
 local function glyph(c)
  if glyphs[c] then return glyphs[c] end
  local n=c:byte();local tile=n>=65 and n<=90 and n-65+0xB0 or (n>=48 and n<=57 and n-48+0xF0 or nil)
  local rows={}
  for y=0,7 do
   local bits=0
   if tile then
    local o=0x5C*1024+tile*16+y
    local lo=memory.read_u8(o,'CHR VROM');local hi=memory.read_u8(o+8,'CHR VROM')
    for x=0,7 do
     local value=math.floor(lo/2^x)%2+2*(math.floor(hi/2^x)%2)
     if value==(n>=48 and n<=57 and 2 or 0) then bits=bits+2^x end
    end
   elseif punctuation[c] then bits=punctuation[c][y+1] end
   rows[y+1]=bits
  end
  glyphs[c]=rows;return rows
 end
 local function paneltext(x,y,line,scale,color)
  for i=1,#line do
   local rows=glyph(line:sub(i,i))
   for row=0,7 do
    local col=0
    while col<8 do
     if math.floor(rows[row+1]/2^(7-col))%2==1 then
      local first=col;repeat col=col+1 until col==8 or math.floor(rows[row+1]/2^(7-col))%2==0
      gui.drawRectangle(x+(i-1)*8*scale+first*scale,y+row*scale,(col-first)*scale-1,scale-1,color or 0xFFFFFFFF,color or 0xFFFFFFFF,'client')
     else col=col+1 end
    end
   end
  end
 end
 local ready=false
 -- Read-only source-signature hook: this is presentation, never ending evidence.
 local hook=event.onmemoryexecute(function()
  if memory.read_u8(0xBCAE,'System Bus')==0x20 and memory.read_u8(0xBCAF,'System Bus')==6
   and memory.read_u8(0xBCB0,'System Bus')==0xA8 and memory.read_u8(0x79F5,'System Bus')==3 then ready=true end
 end,0xBCAE,'M222 THE END prompt','System Bus')
 event.onexit(function()if hook then event.unregisterbyid(hook) end end,'M222 prompt cleanup')
 return M.new({session=session,frame=emu.framecount,clock=assert(options.clock),clear=function(s)gui.clearGraphics(s)end,
  status_scene=function()return M.status_scene(function(a)return memory.read_u8(a,'System Bus')end)end,
  native_paused=function()
   local r=function(a)return memory.read_u8(a,'System Bus')end
   local tileset=r(0x70A)
   return r(0x376)==1 and tileset>=1 and tileset<=14 and tileset~=7
    and r(0x79A1)==9 and r(0x79AE)==1 and r(0x79A2)==2 and r(0x726)==0 and r(0x72B)==1
  end,
  continuation=function()
   if memory.read_u8(0x79A2,'System Bus')~=2 or memory.read_u8(0x0100,'System Bus')==0xC0 then ready=false end
   return ready
  end,
  paneltext=paneltext,
  box=function(x,y,w,h,fg,bg,surface)gui.drawRectangle(x,y,w,h,fg,bg,surface)end,
  size=function()return client.screenwidth(),client.screenheight()end,
  viewport=function()
   local first=client.transformPoint(0,0)
   local last=client.transformPoint(client.bufferwidth(),client.bufferheight())
   return first.x,first.y,math.max(0,last.x-first.x),math.max(0,last.y-first.y)
  end,
  toptext=function(x,y,line,size)
   local function draw(dx,dy,color)gui.drawText(x+dx,y+dy,line,color,0x00000000,size,'Consolas','bold','left','top','client')end
   draw(-1,0,0xFF101010);draw(1,0,0xFF101010);draw(0,-1,0xFF101010);draw(0,1,0xFF101010)
   draw(0,0,0xFFFFFFFF)
  end,
  text=function(x,y,line,fg,bg,size,surface)gui.drawText(x,y,line,fg,bg,size,'Consolas','bold','left','bottom',surface)end},options)
end
return M
