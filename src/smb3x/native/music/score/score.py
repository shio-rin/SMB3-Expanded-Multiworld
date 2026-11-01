# SPDX-License-Identifier: MPL-2.0
"""Fail-closed original R3 score compiler, independent of MusConv code."""
import json,struct,hashlib
CHANNELS=('pulse2','pulse1','triangle','noise')
DURATIONS=(6,6,8,8,12,18,16,16,24,36,48,72,96,4,2,22)
HURRY=(5,5,7,6,10,15,13,14,20,30,40,60,80,3,1,19)
def require(ok,message):
 if not ok:raise ValueError(message)
def compile_song(song):
 require(set(song)=={'schema','title','provenance','tempo_row','loop','channels'},'unknown/missing score fields')
 require(song['schema']==1 and song['tempo_row']==0x30 and song['loop']==0,'only schema1, row30, whole-song loop supported')
 require(isinstance(song['title'],str) and isinstance(song['provenance'],dict),'title/provenance required')
 require(set(song['channels'])==set(CHANNELS),'four monophonic channels required')
 blob=bytearray();offsets={};timeline={};totals=[];fast=[]
 for ch in CHANNELS:
  offsets[ch]=len(blob);time=0;quick=0;timeline[ch]=[]
  events=song['channels'][ch];require(isinstance(events,list) and 0<len(events)<=100,'event count out of bounds')
  for i,e in enumerate(events):
   require(set(e)=={'note','ticks','instrument','effects'},f'{ch}:{i}: unknown/missing event fields')
   require(type(e['ticks']) is int and e['ticks'] in DURATIONS,f'{ch}:{i}: duration not exactly representable')
   require(e['effects']==[],f'{ch}:{i}: unsupported effect')
   instrument=e['instrument'];require(type(instrument) is int and instrument in (0,1,2,3,4,5,7),f'{ch}:{i}: unsupported/coupled timbre')
   if ch in ('triangle','noise'):require(instrument==0,f'{ch}: no instruments')
   n=e['note'];require(n is None or type(n) is int,f'{ch}: note must be integer or null')
   if ch=='noise':
    require(n in (None,2,4,6),f'{ch}: unsupported noise preset');code=1 if n is None else n
   else:
    low=25 if ch=='triangle' else 37
    require(n is None or low<=n<=low+60,f'{ch}: pitch outside safe native range')
    code=126 if n is None else 2*(n-(24 if ch=='triangle' else 36))
   idx=DURATIONS.index(e['ticks']);command=(0x80+16*instrument if ch.startswith('pulse') else 0x80)|idx
   require(command!=255,'FF is an effect, not a duration')
   blob.extend([command,code]);timeline[ch].append(dict(tick=time,note=n,code=code,instrument=instrument,duration=e['ticks']))
   time+=e['ticks'];quick+=HURRY[idx]
  if ch in ('pulse2','noise'):blob.append(0)
  totals.append(time);fast.append(quick)
 require(len(set(totals))==1,'channels end at different times')
 require(len(set(fast))==1,'channels desynchronize in hurry mode')
 require(len(blob)<=256 and all(v<256 for v in offsets.values()),'segment exceeds 256-byte native index window')
 return bytes(blob),dict(offsets=offsets,ticks=totals[0],hurry_ticks=fast[0],timeline=timeline,sha256=hashlib.sha256(blob).hexdigest(),size=len(blob))

def vlq(n):
 require(type(n) is int and 0<=n<0x10000000,'invalid VLQ');a=[n&127];n>>=7
 while n:a.insert(0,128|(n&127));n>>=7
 return bytes(a)
def export_midi(song):
 compile_song(song)
 # 24 PPQ and 400000 us/quarter = one score tick per nominal 60 Hz frame.
 tracks=[b'\0\xff\x51\x03\x06\x1a\x80\0\xff\x06\x04LOOP\0\xff\x2f\0']
 for c,ch in enumerate(CHANNELS):
  data=bytearray(b'\0\xff\x03'+bytes([len(ch)])+ch.encode());pending=0;channel=9 if ch=='noise' else c;current_instrument=0
  for e in song['channels'][ch]:
   if e['note'] is None:
    # Preserve a leading/rest-only program change without changing existing exports.
    if e['instrument']!=current_instrument:
     data+=vlq(pending)+bytes([0xc0|channel,e['instrument']]);pending=0;current_instrument=e['instrument']
    pending+=e['ticks'];continue
   note={2:42,4:38,6:46}[e['note']] if ch=='noise' else e['note']
   data+=vlq(pending)+bytes([0xc0|channel,e['instrument']])+b'\0'+bytes([0x90|channel,note,100])
   data+=vlq(e['ticks'])+bytes([0x80|channel,note,0]);pending=0;current_instrument=e['instrument']
  data+=vlq(pending)+b'\xff\x2f\0';tracks.append(bytes(data))
 return b'MThd'+struct.pack('>IHHH',6,1,len(tracks),24)+b''.join(b'MTrk'+struct.pack('>I',len(t))+t for t in tracks)

def import_midi(data,provenance):
 """Strict SMF1 subset. Track names are explicit channel bindings; no silent quantization."""
 require(len(data)<=1000000 and data[:4]==b'MThd','invalid/oversized SMF')
 require(len(data)>=14 and struct.unpack('>I',data[4:8])[0]==6,'invalid MIDI header')
 fmt,count,ppq=struct.unpack('>HHH',data[8:14]);require(fmt==1 and count==5 and 0<ppq<0x8000,'SMF1 requires conductor + four named tracks, PPQ timing')
 pos=14;parsed=[]
 for tr in range(count):
  require(data[pos:pos+4]==b'MTrk' and pos+8<=len(data),'missing MIDI track');size=int.from_bytes(data[pos+4:pos+8],'big');pos+=8
  end=pos+size;require(end<=len(data),'truncated MIDI track');t=0;running=None;events=[];ended=False
  def take(n):
   nonlocal pos
   require(pos+n<=end,'truncated MIDI event');v=data[pos:pos+n];pos+=n;return v
  def var():
   v=0
   for _ in range(4):
    b=take(1)[0];v=(v<<7)|(b&127)
    if b<128:return v
   raise ValueError('overlong MIDI VLQ')
  while pos<end:
   t+=var();status=take(1)[0]
   if status<128:
    require(running is not None,'invalid running status');pos-=1;status=running
   if status==255:
    running=None;kind=take(1)[0];payload=take(var());events.append((t,'meta',kind,payload))
    if kind==47:require(not payload and pos==end,'bad end-of-track');ended=True
   else:
    require(status>>4 in (8,9,12),'unsupported MIDI controller, bend, SysEx or pressure')
    running=status;payload=take(1 if status>>4==12 else 2);require(all(v<128 for v in payload),'invalid MIDI data byte');events.append((t,status>>4,status&15,payload))
  require(ended,'missing end-of-track');parsed.append(events)
 require(pos==len(data),'trailing MIDI bytes')
 conductor=parsed[0];tempos=[e for e in conductor if e[1:3]==('meta',81)]
 require(len(tempos)==1 and tempos[0][0]==0 and tempos[0][3]==bytes.fromhex('061a80'),'only constant 150 BPM supported')
 require(all(e[1]=='meta' and e[2] in (3,6,47,81,88,89) for e in conductor),'invalid conductor event')
 loops=[e for e in conductor if e[1:3]==('meta',6)];require(len(loops)==1 and loops[0][0]==0 and loops[0][3]==b'LOOP','conductor LOOP marker required at zero')
 channels={}
 for tr,events in enumerate(parsed[1:]):
  names=[e[3].decode('ascii') for e in events if e[1:3]==('meta',3)]
  require(len(names)==1 and names[0] in CHANNELS and names[0] not in channels,'unique native track name required');ch=names[0]
  out=[];active=None;last=0;inst=0
  def tick(t):
   require(t*24%ppq==0,'MIDI timing not exactly on native tick grid');return t*24//ppq
  def event(n,d,i):
   if d:out.append(dict(note=n,ticks=d,instrument=i,effects=[]))
  for time,kind,chan,payload in events:
   time=tick(time)
   if kind=='meta':
    require(chan in (3,47),'unsupported channel metadata')
    if chan==47:require(active is None,'unterminated note');event(None,time-last,inst);last=time
    continue
   require(chan==(9 if ch=='noise' else CHANNELS.index(ch)),'unexpected MIDI channel')
   if kind==12:require(active is None,'instrument change during note');event(None,time-last,inst);last=time;inst=payload[0];continue
   n=payload[0];on=kind==9 and payload[1]>0
   if on:
    require(active is None,'polyphonic overlap');event(None,time-last,inst);active=(n,time,inst)
   else:
    require(active is not None and active[0]==n,'unmatched note off');require(time>active[1],'zero-length note');note={42:2,38:4,46:6}.get(n) if ch=='noise' else n
    require(ch!='noise' or note is not None,'unsupported percussion pitch');event(note,time-active[1],active[2]);active=None;last=time
  channels[ch]=out
 song=dict(schema=1,title='Imported original R3 score',provenance=provenance,tempo_row=48,loop=0,channels=channels)
 compile_song(song);return song

if __name__=='__main__':
 import argparse
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 song=import_midi(a.input.read_bytes(),{'source':str(a.input),'rights':'author must supply'}) if a.input.suffix=='.mid' else json.loads(a.input.read_text())
 blob,info=compile_song(song);a.output.mkdir(parents=True,exist_ok=False)
 (a.output/'sequence.bin').write_bytes(blob);(a.output/'events.json').write_text(json.dumps(song,indent=2));(a.output/'diagnostics.json').write_text(json.dumps(info,indent=2))
 (a.output/'sequence.asm').write_text('; Original R3 sequence, pulse2/pulse1/triangle/noise\n .db '+','.join('$%02X'%v for v in blob)+'\n')
 (a.output/'editable.mid').write_bytes(export_midi(song));print(info['sha256'],info['size'])
