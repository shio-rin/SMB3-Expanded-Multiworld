-- SPDX-License-Identifier: MPL-2.0
-- M222 typed adapter. Native stack receipts are separate from in-level tools.
local M={}
function M.new(io,rows)
    local items={}
    for _,r in ipairs(rows) do items[tonumber(r.id:sub(3),16)]=r end
    local function owned(item,mask)
        local w=tonumber(item.name:match("^World (%d) Pass$"))
        if w then return math.floor(mask/2^(w-1))%2==1 end
        return io.permanent_ready and io.permanent_ready(item)==true
    end
    local function word(a) return io.read(a)+256*io.read(a+1) end
    local function dword(a) return word(a)+65536*word(a+2) end
    local function snapshot()
        if io.read(0x7AAC)~=1 or io.read(0x7BE8)~=0 then return nil end
        -- Native last-unit compaction follows the extension's decrement. Do not
        -- expose that transient representation between CPU/frame boundaries.
        if io.read(0x05F2)~=0 or io.read(0x03E6)~=0 or io.read(0x03ED)~=0 or io.read(0x00DA)~=0 then return nil end
        local mode=io.read(0x7AAD)
        assert(mode==0 or mode==4,'invalid native inventory mode')
        local q,slots,seen={},{},{}
        for t=1,13 do q[t]=word(0x7AB0+2*t) end
        local empty=false
        for i=0,27 do
            local t=io.read(0x7D80+i);assert(t>=0 and t<=13,'invalid native inventory type')
            slots[#slots+1]=t
            if mode==4 then
                if t==0 then empty=true else
                    assert(not empty and not seen[t] and q[t]>0,'native stack representation mismatch')
                    seen[t]=true
                end
            end
        end
        if mode==4 then for t=1,13 do assert((q[t]>0)==(seen[t]==true),'native quantity has no representative') end end
        return {format=1,mode=mode==4 and 'stacked' or 'vanilla',quantities=q,slots=slots,
            serial=dword(0x7ACC),ticket=dword(0x7BD6),item=io.read(0x7BDA),pending=io.read(0x7BDC),
            receipt_before=word(0x7BE6),receipt_after=word(0x7BE0),receipt_serial=dword(0x7BE2)}
    end
    local s={pending={},known={},results={},blocked=false,stable=0,full_index=nil}
    local function valid_index(v) return type(v)=="number" and v>=0 and v==math.floor(v) end
    local function sync(commands,handled,pass)
        assert(type(commands)=="table" and type(handled)=="table" and type(pass)=="number" and pass%2==1 and pass>=1 and pass<=255,"invalid typed delivery payload")
        -- Validate the whole packet before granting anything.
        local packet={}
        for _,c in ipairs(commands) do
            assert(type(c)=="table" and valid_index(c.index) and items[c.item],"unknown item/index")
            assert(not s.known[c.index] or s.known[c.index]==c.item,"item index changed type")
            assert(not packet[c.index] or packet[c.index]==c.item,"packet index changed type")
            assert(items[c.item].kind~="permanent" or owned(items[c.item],pass),"permanent item lacks server-derived unlock")
            packet[c.index]=c.item
        end
        for k,v in pairs(handled) do
            assert(valid_index(tonumber(k)) and (v=="applied" or v=="capped"),"invalid handled history")
            assert(not s.results[tonumber(k)] or s.results[tonumber(k)]==v,"conflicting handled result")
        end
        for k,v in pairs(handled) do s.results[tonumber(k)]=v end
        io.unlock(pass) -- monotonic, RAM-independent and not blocked by inventory
        for _,c in ipairs(commands) do
            if not s.known[c.index] then
                s.known[c.index]=c.item
                if not s.results[c.index] then
                    s.pending[#s.pending+1]={index=c.index,item=c.item}
                    io.log(string.format("AP ITEM QUEUED index=%d item=%s",c.index,items[c.item].name))
                end
            end
        end
        table.sort(s.pending,function(a,b) return a.index<b.index end)
        for i=#s.pending,1,-1 do
            local c=s.pending[i]
            if s.results[c.index] then table.remove(s.pending,i)
            elseif items[c.item].kind=="permanent" then
                assert(owned(items[c.item],pass),"permanent item lacks server-derived unlock")
                io.unlock(pass); s.results[c.index]="applied"; table.remove(s.pending,i)
                io.log("AP PERMANENT APPLIED index="..c.index.." item="..items[c.item].name, "Items", items[c.item].name.." received.")
            end
        end
    end
    local function process()
        if s.blocked then return end
        -- The checkpoint owner intentionally skips processing during play.
        -- A prior map's settled count cannot certify the first frame of a
        -- later return, when a native roaming collision can still take over.
        local frame=io.frame()
        if s.process_frame~=frame then
            if s.process_frame~=frame-1 then s.stable=0 end
            if io.safe() then s.stable=math.min(s.stable+1,30) else s.stable=0 end
            s.process_frame=frame
        elseif not io.safe() then s.stable=0 end
        if s.stable<30 or #s.pending==0 then return end
        local c=s.pending[1]; local item=items[c.item]
        if io.read(0x79A1)==9 then
            assert(io.read(0x7AAC)==1,'native stack storage format missing')
            assert(io.read(0x7AAD)==(math.floor(io.read(0x9F1B)/4)%2)*4,'native inventory mode differs from seed')
            if not snapshot() then return end
        end
        if item.kind=='inventory' and io.read(0x7AAD)==4 then
            local current=snapshot();if not current then return end
            local ticket=c.index+1
            assert(ticket<=4294967295,'native item ticket exhausted')
            if s.flight then
                assert(s.flight.index==c.index,'native delivery flight changed')
                if io.read(0x7BD5)~=0 then return end
                local result=io.read(0x7BDB)
                assert(result==1 or result==2,'native stack operation rejected')
                if result==2 then
                    s.flight=nil;s.full_index=c.index
                    return
                end
                assert(current.ticket==ticket and current.item==item.native,'native receipt ticket/type mismatch')
                assert(current.receipt_before==s.flight.before and current.receipt_after==s.flight.before+1
                    and current.receipt_serial>s.flight.serial and current.receipt_serial<=current.serial,'native increment receipt mismatch')
                s.results[c.index]='applied';table.remove(s.pending,1);s.flight=nil;s.full_index=nil
                io.log('AP STACK APPLIED index='..c.index..' item='..item.name..' quantity='..current.receipt_after, 'Items', item.name..' added to inventory.')
                return
            end
            if current.quantities[item.native]==65535 then
                if s.full_index~=c.index then io.log('AP STACK FULL: pending index='..c.index..' item='..item.name, 'Items', 'Inventory full: '..item.name..' is waiting. Use an item to make room.') end
                s.full_index=c.index;return
            end
            assert(io.read(0x7BD5)==0 and current.ticket<ticket,'uncertain or stale native stack request')
            s.blocked=true
            io.write(0x7BD0,item.native);assert(io.read(0x7BD0)==item.native,'stack item readback')
            for i=0,3 do
                local v=math.floor(ticket/256^i)%256
                io.write(0x7BD1+i,v);assert(io.read(0x7BD1+i)==v,'stack ticket readback')
            end
            io.write(0x7BDB,0);assert(io.read(0x7BDB)==0,'stack result clear readback')
            s.flight={index=c.index,before=current.quantities[item.native],serial=current.serial}
            io.write(0x7BD5,1);assert(io.read(0x7BD5)==1,'stack publication readback')
            s.blocked=false;return
        end
        local address,before,after,inventory
        if item.kind=="life" then
            address=0x0736; before=io.read(address)
            assert(before<=99,"invalid lives byte")
            if before==99 then
                s.results[c.index]="capped"; table.remove(s.pending,1)
                io.log("AP ITEM CAPPED index="..c.index.." item=1-Up lives=99", "Items", "1-Up received; lives are already at 99."); return
            end
            after=before+1
        else
            assert(item.kind=="inventory" and item.native and ((item.native>=1 and item.native<=9 and item.native~=7) or item.native==11),"unsupported native item")
            inventory={}
            for a=0x7D80,0x7D9B do
                local v=io.read(a); assert(v>=0 and v<=13,"invalid native inventory byte")
                inventory[#inventory+1]=v
                if not address and v==0 then address=a end
            end
            if not address then
                if s.full_index~=c.index then io.log("AP INVENTORY FULL: pending index="..c.index.." item="..item.name.."; free a slot normally", "Items", "Inventory full: "..item.name.." is waiting. Use an item to make room.") end
                s.full_index=c.index; return
            end
            before=0; after=item.native
        end
        -- A write exception is uncertain: stop, retain index, never retry in this instance.
        s.blocked=true
        io.write(address,after)
        assert(io.read(address)==after,"item write readback mismatch")
        s.blocked=false; s.full_index=nil
        s.results[c.index]="applied"; table.remove(s.pending,1)
        local extra=string.format("$%04X %d -> %d",address,before,after)
        if inventory then
            local values={}
            for a=0x7D80,0x7D9B do values[#values+1]=string.format("%02X",io.read(a)) end
            extra=extra.." inventory=["..table.concat(values," ").."]"
        end
        io.log(string.format("AP ITEM APPLIED index=%d item=%s %s frame=%d",c.index,item.name,extra,io.frame()), "Items", item.name.." received.")
    end
    local function acknowledgements()
        local a={}
        for i,v in pairs(s.results) do a[#a+1]={index=i,result=v} end
        table.sort(a,function(x,y) return x.index<y.index end)
        return a
    end
    return {sync=sync,process=process,acks=acknowledgements,state=s,snapshot=snapshot,
        onload=function() s.stable=0;s.process_frame=nil end}
end
return M
