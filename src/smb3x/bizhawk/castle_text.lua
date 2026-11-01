-- SPDX-License-Identifier: MPL-2.0
-- Hold A during pre-airship text: one native character per frame, no batching.
-- No mapper calls, script skips, input rewriting or post-victory/letter changes.
local M={}
function M.install(prg)
 assert(memory.hash_region(0,524288,'PRG ROM'):lower()==prg,'Castle ROM binding mismatch')
 local function r(a)return memory.read_u8(a,'System Bus')end
 event.onmemoryexecute(function()
  if r(0x720)==24 and r(0x5fd)~=0 and r(0x7f)==1 and r(0x17)>=128 then
   memory.write_u8(0x518,0,'System Bus')
  end
 end,0xa20a,'M251 pre-airship native character timer','System Bus')
end
return M
