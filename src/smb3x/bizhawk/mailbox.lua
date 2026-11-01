-- SPDX-License-Identifier: MPL-2.0
-- M222 transport only: no CPU redirects, transition execution hooks or heuristic
-- completion. ROM owns control. External restoration is permitted only in the
-- ROM's frozen destination phase, before command publication.
local M={hooks={}}
M.addresses={}
for _,r in ipairs({{0x7D00,128},{0x7EEB,56},{0x7956,13},{0x796B,3},{0x796F,4}}) do
    for a=r[1],r[1]+r[2]-1 do M.addresses[#M.addresses+1]=a end
end
for _,a in ipairs({0x07E2,0x0742,0x7F2D,0x07BB,0x79E0}) do M.addresses[#M.addresses+1]=a end
local zero={0x070A,0x0726,0x0014,0x0020,0x001E,0x007B,0x0017,0x0018,0x008B,
    0x00C5,0x00DA,0x0376,0x03E1,0x03E6,0x03ED,0x05F2,0x0710,0x073C,0x073E,0x0745,0x7955,0x0597,0x7973}
local function byte(v) return type(v)=="number" and v==math.floor(v) and v>=0 and v<=255 end
function M.new(io)
    local read,write=io.read,io.write
    local function counter(low,high) return read(low)+256*read(high) end
    local function sequence() return counter(0x79A4,0x79F0) end
    local function seen() return counter(0x79A5,0x79F1) end
    local function transaction() return counter(0x79AB,0x79F2) end
    local function valid_sequence(v) return type(v)=="number" and v==math.floor(v) and v>=1 and v<=65534 end
    local function idle() return read(0x79F3)==0 and sequence()==seen() end
    local s={session=nil,active=nil,boot_seen=false,phase="native",authorized=false,unlocked=false,unlock_mask=1,want_mask=1,
        blocked=false,last_frame=io.frame(),want_pass=false}
    local displayed_world=nil -- cosmetic deduplication, never native authority
    local desired={hammers=0,stars=0,pending=0,checks={0,0,0,0,0,0,0,0}}
    local progression={hammers=0,stars=0,pending=0,checks={0,0,0,0,0,0,0,0}}
    local function counts_ready()
        for i=1,8 do if read(0x7A9F+i)~=progression.checks[i] then return false end end
        return true
    end
    local function fail(reason)
        s.blocked=true;s.phase="blocked";s.authorized=false
        io.log("NATIVE M222 BLOCKED: "..reason.."; preserve ROM, journal and delivery history", "Checkpoint", "Game paused to protect your progress. Preserve this game and check the client and diagnostic log.")
        io.pause()
    end
    local function marker()
        local prefix="SMB3APP\0"
        for i=1,#prefix do assert(read(0x9F10+i-1)==prefix:byte(i),"Wrong patched ROM marker") end
        assert(read(0x9F18)==9,"Native ROM protocol mismatch")
        local key={}
        for i=0,31 do key[#key+1]=string.format("%02x",read(0x9F1C+i)) end
        return table.concat(key)
    end
    local function bind(key)
        assert(not s.blocked,"Native bridge blocked")
        assert(marker()==key,"Generated ROM seed/team/slot mismatch")
        assert(not s.session or s.session==key,"Native session changed")
        s.session=key
    end
    local function safe()
        if read(0x79DB)~=0 or read(0x79DD)~=0 or s.blocked or not s.authorized or read(0x79A2)~=2 or read(0x79AE)~=1 then return false end
        if read(0x0727)>7 or read(0x072B)~=1 or read(0x0729)~=13 or read(0x0100)~=0xC0
            or read(0x0728)>1 or read(0x0736)>99 then return false end
        for _,a in ipairs(zero) do if read(a)~=0 then return false end end
        return true
    end
    local function capture(phase)
        local data={}
        for _,a in ipairs(M.addresses) do data[#data+1]=read(a) end
        local p
        if phase==5 then
            p={read(0x7976),read(0x797A),read(0x7978),read(0x0722),read(0x0724)}
        else p={read(0x75),read(0x79),read(0x77),read(0xFD),read(0x12)} end
        return {data=data,point=p}
    end
    local function status()
        local p=read(0x79A0)==0xAA and read(0x79A2) or 0
        local result={session=s.session,phase=p,error=read(0x79A3),world=read(0x0727),active=read(0x79A9),
            seen=seen(),sequence=sequence(),transaction=transaction(),bound=read(0x79AE),
            reason=read(0x79E1),destination=read(0x79A7),result=read(0x79AA),unlock=read(0x79A8),
            ending_phase=read(0x79F5),ending_version=read(0x79F6)}
        if p==3 or p==5 or p==7 or (p==2 and safe()) then result.snapshot=capture(p) end
        return result
    end
    local function publish(op,serial)
        assert(not s.blocked and s.session,"Unbound/blocked native command")
        assert(valid_sequence(serial),"Native sequence exhausted")
        assert(idle() and serial==seen()+1,"Native command sequence race")
        s.blocked=true
        write(0x79A6,op);assert(read(0x79A6)==op,"Command readback failed")
        write(0x79A4,serial%256);write(0x79F0,math.floor(serial/256))
        assert(sequence()==serial,"Sequence readback failed")
        -- The explicit latch is the ONLY publication boundary; partial words
        -- cannot be interpreted as commands even when their low byte wraps.
        write(0x79F3,1);assert(read(0x79F3)==1,"Publication readback failed")
        s.blocked=false
    end
    local function action(a)
        assert(type(a)=="table" and valid_sequence(a.sequence) and byte(a.op),"Invalid native action")
        assert(not s.blocked and s.session and a.session==s.session,"Native action session mismatch/blocked")
        if a.sequence==sequence() then
            assert(a.op==read(0x79A6) or (a.sequence==seen() and read(0x79A6)==0),"Conflicting duplicate action")
            assert(a.transaction==transaction(),"Stale duplicate transaction")
            return -- lost reply: never repeat restore writes
        end
        assert(not s.blocked and s.session,"Native action while blocked/unbound")
        assert(read(0x79A2)==a.phase and transaction()==a.transaction,"Native phase/transaction changed")
        assert(idle() and a.sequence==seen()+1,"Native action out of order")
        local phases={[1]=1,[4]=3,[5]=5,[6]=7}
        assert(phases[a.op]==a.phase,"Invalid action for native phase")
        if a.op==1 then
            s.blocked=true
            for i=0,31 do
                local v=tonumber(s.session:sub(i*2+1,i*2+2),16)
                write(0x79B0+i,v);assert(read(0x79B0+i)==v,"Session readback failed")
            end
            s.blocked=false
        elseif a.op==5 then
            local data,p=a.snapshot.data,a.snapshot.point
            assert(type(data)=="table" and #data==209 and type(p)=="table" and #p==5,"Invalid restore size")
            for _,v in ipairs(data) do assert(byte(v),"Invalid restore byte") end
            for _,v in ipairs(p) do assert(byte(v),"Invalid position byte") end
            assert(p[1]>=0x20 and p[1]<=0xA0 and p[1]%16==0 and p[2]%16==0 and p[3]<=3 and p[5]<=3,"Invalid position")
            s.blocked=true
            for i,address in ipairs(M.addresses) do
                write(address,data[i]);assert(read(address)==data[i],"Restore readback failed")
            end
            local sum1,sum2=0,0
            for _,v in ipairs(data) do sum1=(sum1+v)%256;sum2=(sum2+sum1)%256 end
            for i,v in ipairs(p) do
                write(0x79CF+i,v);assert(read(0x79CF+i)==v,"Position readback failed")
                sum1=(sum1+v)%256;sum2=(sum2+sum1)%256
            end
            write(0x79D5,sum1);write(0x79D6,sum2)
            assert(read(0x79D5)==sum1 and read(0x79D6)==sum2,"Checksum readback failed")
            s.blocked=false
        end
        publish(a.op,a.sequence)
    end
    local function request(world)
        if seen()>=65531 then io.log("NATIVE travel rejected: command lifetime exhausted; preserve history", nil, "World travel unavailable. Preserve this game and check the client and diagnostic log.");return false end
        if not safe() or not idle() then io.log("NATIVE travel rejected: wait on a safe idle map", nil, "Wait on the overworld with menus closed before travelling.");return false end
        if (not byte(world) or world>7) or world==read(0x727) or (math.floor(read(0x79A8)/2^world)%2~=1) then
            io.log("NATIVE travel rejected: unavailable destination", nil, "That destination is unavailable.");return false
        end
        s.blocked=true;write(0x79A7,world);assert(read(0x79A7)==world,"Destination readback failed");s.blocked=false
        publish(3,seen()+1)
        return true
    end
    local function poll()
        if s.blocked then return end
        local now=io.frame()
        if now<s.last_frame then fail("frame rollback/reset");return end
        s.last_frame=now
        if read(0x79A0)==0xAA then
            assert(read(0x79A1)==9,"Mailbox protocol changed")
            local p=read(0x79A2)
            if p==255 then fail("ROM error "..read(0x79A3));return end
            if p~=s.last_phase then
                s.last_phase=p
                if p==2 then
                    local world=read(0x79A9)+1
                    io.log(string.format("NATIVE READY World %d transaction=%d",world,transaction()), nil, displayed_world~=world and string.format("World %d ready.",world) or nil)
                    displayed_world=world
                else io.log(string.format("NATIVE PHASE %d world=%d sequence=%d",p,read(0x727)+1,seen())) end
            end
            if read(0x79AA)==2 and s.last_rejection~=seen() then
                s.last_rejection=seen()
                io.log("NATIVE command rejected sequence="..s.last_rejection.."; no transition committed", nil, "A world action was refused. Check the client and diagnostic log.")
            end
            s.phase=p==2 and "idle" or "native"
            s.active=read(0x79A9);s.boot_seen=true;s.unlock_mask=read(0x79A8);s.unlocked=s.unlock_mask==s.want_mask
            if s.authorized and s.want_mask~=s.unlock_mask and p==2 and idle() and safe() then
                for world=1,7 do
                    if math.floor(s.want_mask/2^world)%2==1 and math.floor(s.unlock_mask/2^world)%2==0 then
                        s.blocked=true;write(0x79A7,world);assert(read(0x79A7)==world,"Unlock target readback");s.blocked=false
                        publish(2,seen()+1);break
                    end
                end
            end
            if s.authorized and p==2 and idle() and safe() and s.want_mask==s.unlock_mask and
                (read(0x79F7)~=progression.hammers or read(0x79F8)~=progression.stars or
                 read(0x79F9)+256*read(0x79FA)~=progression.pending or not counts_ready()) then
                s.blocked=true
                for i,v in ipairs({progression.hammers,progression.stars,progression.pending%256,math.floor(progression.pending/256)}) do
                    write(0x7996+i,v);assert(read(0x7996+i)==v,'Progression payload readback failed')
                end
                for i,v in ipairs(progression.checks) do
                    write(0x7A7F+i,v);assert(read(0x7A7F+i)==v,'Tracker payload readback failed')
                end
                s.blocked=false;publish(7,seen()+1)
            end
        elseif s.boot_seen then fail("ROM reset cleared native mailbox") end
    end
    local t={state=s,bind=bind,safe=safe,poll=poll,request=request,fail=fail,action=action,native_status=status,
        progression_ready=function()return read(0x79F7)==progression.hammers and read(0x79F8)==progression.stars end,
        grant_progression=function(v)
            assert(type(v)=='table' and byte(v.hammers) and byte(v.stars) and type(v.pending)=='number' and v.pending%1==0 and v.pending>=0 and v.pending<=65535,'Invalid permanent progression')
            assert(v.stars>=progression.stars and v.stars<=read(0x9F3F),'Star history/configuration mismatch')
            for w=0,7 do
                local bit=math.floor(v.hammers/2^w)%2
                assert(bit==0 or (read(0x9F3C)==1 and (w==1 or w==2 or w==3 or w==5)),'Unsupported regional permission')
                assert(math.floor(progression.hammers/2^w)%2==0 or bit==1,'Hammer history rolled back')
            end
            local counts=v.checks or {0,0,0,0,0,0,0,0}
            assert(type(counts)=='table' and #counts==8,'Invalid world check tracker')
            for i,n in ipairs(counts)do assert(byte(n) and n<=read(0x9F1A),'Check count exceeds enabled total')end
            progression={hammers=v.hammers,stars=v.stars,pending=v.pending,checks=counts}
            desired=v
        end,
        authorize=function(v) s.authorized=v==true end,grant_pass=function(mask)
            assert(byte(mask) and mask<=255 and mask%2==1,"Invalid supported unlock mask")
            for w=0,7 do if math.floor(s.want_mask/2^w)%2==1 then assert(math.floor(mask/2^w)%2==1,"Unlock history rolled back") end end
            s.want_mask=mask
        end,
        suspended=function() return s.blocked or not s.authorized or read(0x79A2)~=2 end,
        onload=function() fail("save-state loaded; automatic native reconciliation is unsupported") end,
        checkpoint=function() return nil end,
        status=function() io.log(string.format("NATIVE phase=%d error=%d world=%d committed=%d seq=%d/%d",
            read(0x79A2),read(0x79A3),read(0x727)+1,read(0x79A9)+1,sequence(),seen()), nil, read(0x79A3)~=0 and "Game error. Preserve this game and check the client and diagnostic log." or nil) end}
    local zero={0x070A,0x0726,0x0014,0x0020,0x001E,0x007B,0x0017,0x0018,0x008B,
        0x00C5,0x00DA,0x0376,0x03E1,0x03E6,0x03ED,0x05F2,0x0710,0x073C,0x073E,0x0745,0x7955,0x0597,0x7973,
        0x79DB,0x79DD,0x79F3,0x7BD5,0x7BDC,0x7BE8}
    t.checkpoint_safe=function()
        local r=io.read;local n=t.native_status()
        if t.state.blocked or not t.state.session or n.phase~=2 or n.bound~=1 or n.error~=0
            or n.sequence~=n.seen or n.world~=n.active or n.world>7
            or r(0x072B)~=1 or r(0x0729)~=13 or r(0x0100)~=0xC0 or r(0x0728)>1 or r(0x0736)>99 then return false end
        for _,a in ipairs(zero)do if r(a)~=0 then return false end end
        return true
    end
    local status=t.native_status
    t.checkpoint_status=function()
        assert(t.checkpoint_safe(),'Not a settled checkpoint overworld')
        local n=status();local data={}
        for _,a in ipairs(M.addresses)do data[#data+1]=io.read(a)end
        n.snapshot={data=data,point={io.read(0x75),io.read(0x79),io.read(0x77),io.read(0xFD),io.read(0x12)}}
        return n
    end
    t.progression_settled=function()
        if t.state.want_mask~=io.read(0x79A8) or not t.progression_ready()
            or io.read(0x79F9)+256*io.read(0x79FA)~=desired.pending then return false end
        for i=1,8 do if io.read(0x7A9F+i)~=desired.checks[i]then return false end end
        return true
    end
    t.export_controller=function()
        assert(not t.state.blocked and t.state.session,'Unbound/blocked checkpoint controller')
        return {schema=1,session=t.state.session,active=t.state.active,
            want_mask=t.state.want_mask,progression=desired}
    end
    t.import_controller=function(c)
        assert(not t.state.session and c.schema==1,'Controller import is one-use on a fresh controller')
        t.bind(c.session)
        local n=t.native_status()
        assert(n.phase==2 and n.bound==1 and n.error==0 and n.world==n.active
            and n.active==c.active and n.sequence==n.seen,'Checkpoint native controller mismatch')
        for i=0,31 do assert(io.read(0x79B0+i)==tonumber(c.session:sub(i*2+1,i*2+2),16),'Native bound session mismatch') end
        t.grant_pass(c.want_mask);t.grant_progression(c.progression)
        assert(n.unlock==c.want_mask,'Checkpoint unlock mirror mismatch')
        assert(t.progression_ready(),'Checkpoint permanent mirror mismatch')
        assert(io.read(0x79F9)+256*io.read(0x79FA)==c.progression.pending,'Checkpoint pending mirror mismatch')
        for i=1,8 do assert(io.read(0x7A9F+i)==c.progression.checks[i],'Checkpoint check count mirror mismatch')end
        t.state.active=n.active;t.state.boot_seen=true;t.state.unlock_mask=n.unlock
        t.state.unlocked=true;t.state.phase='idle';t.state.last_frame=io.frame()
        t.authorize(false)
    end
    return t
end
return M
