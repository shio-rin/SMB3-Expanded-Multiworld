-- SPDX-License-Identifier: MPL-2.0
-- Read-only progression panel and ending prompt; no notification queue.
local M={}
function M.new(io,options)
 options=options or {}
 local enabled=options.notifications~=false
 local font=({small=12,normal=16,large=20})[options.notification_size or 'normal'] or 16
 local panel=options.panel
 local function clear() io.clear('client') end
 local function reset() clear() end
 -- Clears our prior launcher lifetime, including a stopped script's last frame.
 local ok=pcall(clear)
 if not ok then enabled=false end
 local function draw()
  if not enabled then if panel then panel.update();panel.hide() end;return end
  local success=pcall(function()
   -- Repaint ownership each frame: removes expired/shorter text and resized frames.
   clear()
   if panel then
    panel.update()
    local lines=panel.lines()
    if lines then
     local width,height=io.size()
     if io.paneltext and width>=220 and height>=160 then
      -- Native eight-pixel glyphs, integer scale, four existing pages.
      local scale=math.max(1,math.floor(math.min(width/256,height/160)))
      local longest=0;for _,line in ipairs(lines)do longest=math.max(longest,#line)end
      local w=math.min(width-12*scale,longest*8*scale+16*scale)
      local h=(#lines*10+16)*scale
      io.box(5*scale,7*scale,w,h,0xFFF8B8A8,0xFF000000,'client')
      io.box(7*scale,9*scale,w-4*scale,h-4*scale,0xFFB4ECF4,0xFF000000,'client')
      io.box(12*scale,14*scale,w-15*scale,9*scale,0xFFB4ECF4,0xFFB4ECF4,'client')
      for i,line in ipairs(lines)do io.paneltext(13*scale,(15+(i-1)*10)*scale,line,scale,i==1 and 0xFF000000 or 0xFFFFFFFF)end
     else
      local size=math.max(8,math.min(16,math.floor((width-12)/17)))
      local columns=math.max(4,math.floor((width-12)/math.ceil(size*0.65)))
      if io.box then
       local h=math.min(height-12,(#lines+1)*(size+4)+12)
       io.box(3,10,width-6,h,0xFF000000,0xFFFFFFFF,'client')
       io.box(6,13,width-12,h-6,0xFF000000,0xFFB4ECF4,'client')
      end
      for i,line in ipairs(lines)do
       if #line>columns then line=line:sub(1,columns-3)..'...' end
       io.text(10,12+i*(size+4),line,0xFF000000,0xFFB4ECF4,size,'client')
      end
     end
     return
    end
   end
   local prompt=io.continuation and io.continuation()
   if not prompt then return end
   local width,height=io.size()
   if width<font*4+8 or height<font+6 then return end
   -- Conservative advance for a fixed-width font, with edge/outline margin.
   local columns=math.max(4,math.floor((width-12)/math.ceil(font*0.65)))
   local line='THE END - Press Start to Continue'
   if #line>columns then line=line:sub(1,columns-3)..'...' end
   io.text(2,height-2,line,0xFFFFFFFF,0xE0000000,font,'client')
  end)
  if not success then enabled=false;pcall(reset) end
 end
 return {draw=draw,snapshot=function(session,v)return panel and panel.publish(session,v) or false end,enabled=function()return enabled end,
  toggle=function()enabled=not enabled;if panel then panel.hide() end;if not pcall(reset) then enabled=false end;return enabled end,
  close=function()enabled=false;if panel then panel.close()end;pcall(reset)end}
end
return M
