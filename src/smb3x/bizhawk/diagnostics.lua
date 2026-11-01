-- SPDX-License-Identifier: MPL-2.0
-- Cosmetic diagnostics only. Never participates in grants or checkpoint authority.
local M={}
-- Producers explicitly opt into player presentation. Never infer audience from
-- diagnostic text: the original record may also be a protocol/debugging contract.
function M.display(category,text)
 return '[SMB3X'..(category and ' / '..category or '')..'] '..text
end
function M.new(options)
 local console=assert(options.console)
 local limit=options.max_bytes or 1048576
 local file,size,disabled=nil,0,false
 local function warning(reason)
  if disabled then return end;disabled=true
  if file then pcall(function()file:close()end);file=nil end
  pcall(console,M.display(nil,'Diagnostic log unavailable. Technical details will appear here; keep them for support. '..tostring(reason)))
 end
 local function open()
  file=assert(io.open(options.path,'ab'));size=assert(file:seek('end'))
 end
 local function rotate()
  assert(file:close());file=nil
  local old=options.path..'.3';local f=io.open(old,'rb')
  if f then f:close();assert(os.remove(old))end
  for i=2,0,-1 do
   local src=i==0 and options.path or options.path..'.'..i
   local found=io.open(src,'rb')
   if found then found:close();assert(os.rename(src,options.path..'.'..(i+1)))end
  end
  open()
 end
 local ok,err=pcall(open);if not ok then warning(err)end
 local function log(...)
  local values={};for i=1,select('#',...)do values[i]=tostring(select(i,...))end
  local text=table.concat(values,'	')
  if not disabled then
   local success,reason=pcall(function()
    local line=os.date('!%Y-%m-%dT%H:%M:%SZ')..' '..text..'\n'
    if size>0 and size+#line>limit then rotate()end
    assert(file:write(line));assert(file:flush());size=size+#line
   end)
   if not success then warning(reason)end
  end
  if options.verbose==true or disabled then pcall(console,M.display('Diagnostics',text))end
 end
 local function close()if file then local f=file;file=nil;local ok,err=pcall(function()assert(f:close())end);if not ok then warning(err)end end end
 -- Only the original first argument enters the diagnostic log. Presentation
 -- arguments never contaminate serialized/technical producer records.
 local function event(raw,category,text)
  log(raw)
  if text then pcall(console,M.display(category,text))end
 end
 return {log=log,event=event,close=close}
end
return M
