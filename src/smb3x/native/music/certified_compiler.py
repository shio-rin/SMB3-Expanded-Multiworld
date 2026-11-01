# SPDX-License-Identifier: MPL-2.0
"""M24.4 strict native compiler, adapted from accepted R3 encoders.
No quantization, transcription, octave changes, or authoring operations.
Legacy schema1/2 encoding remains byte-identical.
"""
from copy import deepcopy
from fractions import Fraction
from fractions import Fraction as F
import hashlib
from tools.music_m20.arrangement import compile_arrangement as compile_legacy
from tools.music_m20.score import DURATIONS, CHANNELS, require
VERSION='m244-native-music-1'
ROWS = (
 (8,8,11,10,16,24,21,22,32,48,64,96,128,1,31,0),
 (7,8,10,10,15,22,20,20,30,45,60,90,120,5,0,0),
 (7,7,9,10,14,21,19,18,28,42,56,84,112,1,4,0),
 (6,6,8,8,12,18,16,16,24,36,48,72,96,4,2,22),
 (5,5,7,6,10,15,13,14,20,30,40,60,80,3,1,19),
 (4,5,6,6,9,13,12,12,18,27,36,54,72,30,3,0),
 (4,4,5,6,8,12,11,10,16,24,32,48,64,0,0,0),
 (3,4,5,4,7,10,9,10,14,21,28,42,56,11,0,0),
 (3,3,4,4,6,9,8,8,12,18,24,36,48,2,0,0),
)
# Avoid row80's 50% hurry increase. Every note is additionally checked below.
MODES={f'row{row:02x}':row for row in range(0,0x80,0x10)}


def compile_tempo(score):
    require(set(score)=={'schema','title','provenance','tempo_mode','notation_quarter','loop_section','sections'}
            and score['schema']==3,'research schema3 fields required')
    require(score['tempo_mode'] in MODES,'unsupported verified tempo mode')
    quarter=score['notation_quarter']
    require(type(quarter) is int and quarter in (12,18,24,36,48),'notation quarter must be 12, 18, 24, 36 or 48')
    row=MODES[score['tempo_mode']];normal,fast=ROWS[row//16],ROWS[row//16+1]
    legacy={k:deepcopy(score[k]) for k in ('title','provenance','loop_section','sections')};legacy['schema']=2
    blocks,base=compile_legacy(legacy)
    result=[]
    for blob,record in blocks:
        record=deepcopy(record);totals=[];quick=[]
        for ch,events in record['timeline'].items():
            at=0;hurry_at=0
            for e in events:
                duration=e['duration'];index=DURATIONS.index(duration)
                a,b=normal[index],fast[index]
                require(a>0 and b>0 and Fraction(a,duration)==Fraction(normal[8],24)
                        and Fraction(b,duration)==Fraction(fast[8],24),
                        f'{score["tempo_mode"]}: duration {duration} changes rhythmic proportions in normal/hurry')
                e.update(notation_tick=e['tick'],notation_duration=duration,tick=at,hurry_tick=hurry_at,
                         duration=a,hurry_duration=b,duration_index=index)
                at+=a;hurry_at+=b
            totals.append(at);quick.append(hurry_at)
        require(len(set(totals))==len(set(quick))==1,'normal/hurry channel drift')
        record.update(ticks=totals[0],hurry_ticks=quick[0],tempo_row=row)
        result.append((blob,record))
    loop=score['loop_section']
    total=lambda key,lo,hi:sum(v[key] for _,v in result[lo:hi])
    summary={**base,'intro_ticks':total('ticks',0,loop),'loop_ticks':total('ticks',loop,len(result)),
             'hurry_intro_ticks':total('hurry_ticks',0,loop),'hurry_loop_ticks':total('hurry_ticks',loop,len(result)),
             'tempo_row':row,'tempo_mode':score['tempo_mode'],'notation_quarter':quarter,
             'nominal_bpm':3600/(normal[8]*quarter/24),'hurry_nominal_bpm':3600/(fast[8]*quarter/24),
             'hurry_ratio':normal[8]/fast[8],'format':'r3-tempo-1',
             'compatibility':'native M20 engine headers; schema3 not accepted by m20-score-1 pack compiler'}
    require(summary['sequence_bytes']<=5632,'song bank capacity exceeded')
    return result,summary


def clocks(mode,quarter=24):
    require(mode in MODES and type(quarter) is int and quarter in (12,18,24,36,48),'verified mode/notation quarter required')
    row=MODES[mode]//16;a,b=ROWS[row],ROWS[row+1]
    q=(F(a[8]*quarter,24),F(b[8]*quarter,24))
    return a,b,q
def block(channels,mode,quarter):
    require(set(channels)==set(CHANNELS),'four channels required')
    a,b,q=clocks(mode,quarter);blob=bytearray();offsets={};timeline={};totals=[]
    for ch in CHANNELS:
        events=channels[ch];require(isinstance(events,list) and 0<len(events)<=100,'bounded nonempty channel required')
        offsets[ch]=len(blob);timeline[ch]=[];t=u=0
        for e in events:
            require(set(e)=={'note','duration_index','instrument','effects'} and e['effects']==[],'strict native index event required')
            i=e['duration_index'];inst=e['instrument'];n=e['note']
            require(type(i) is int and 0<=i<16 and a[i]>0 and b[i]>0,'unsafe native duration index')
            require(type(inst) is int and inst in (0,1,2,3,4,5,7),'unsupported timbre')
            require(ch.startswith('pulse') or inst==0,'triangle/noise instrument must be zero')
            require(n is None or type(n) is int,'integer pitch required')
            if ch=='noise':require(n in (None,2,4,6),'invalid noise preset');code=1 if n is None else n
            else:
                low=25 if ch=='triangle' else 37;require(n is None or low<=n<=low+60,'pitch outside safe native range')
                code=126 if n is None else 2*(n-(24 if ch=='triangle' else 36))
            command=(128+16*inst if ch.startswith('pulse') else 128)|i;require(command!=255,'FF is an effect')
            blob.extend((command,code));timeline[ch].append(dict(tick=t,hurry_tick=u,note=n,code=code,instrument=inst,
                duration=a[i],hurry_duration=b[i],duration_index=i,notation_tick=float(F(t)*24/q[0]),notation_duration=float(F(a[i])*24/q[0])))
            t+=a[i];u+=b[i]
        if ch in ('pulse2','noise'):blob.append(0)
        totals.append((t,u))
    require(len(set(totals))==1,'normal/hurry channel drift')
    require(len(blob)<=256 and all(v<256 for v in offsets.values()),'segment exceeds 256-byte native index window')
    return bytes(blob),dict(offsets=offsets,timeline=timeline,ticks=totals[0][0],hurry_ticks=totals[0][1],size=len(blob),sha256=hashlib.sha256(blob).hexdigest())

def compile_phase(score):
    require(isinstance(score,dict) and set(score)=={'schema','title','provenance','tempo_mode','notation_quarter','loop_section','sections'} and type(score['schema']) is int and score['schema']==4,'research schema4 required')
    require(isinstance(score['title'],str) and score['title'] and isinstance(score['provenance'],dict),'title/provenance required')
    sections=score['sections'];loop=score['loop_section'];mode=score['tempo_mode'];quarter=score['notation_quarter']
    require(isinstance(sections,list) and 1<=len(sections)<=32 and type(loop) is int and 0<=loop<len(sections),'bounded section loop required')
    blocks=[];ids=set();_,_,q=clocks(mode,quarter)
    for s in sections:
        require(set(s)=={'id','channels'} and isinstance(s['id'],str) and s['id'] and s['id'] not in ids,'unique strict section required');ids.add(s['id'])
        blob,report=block(s['channels'],mode,quarter);report['section_id']=s['id'];blocks.append((blob,report))
    info=dict(title=score['title'],loop_section=loop,sequence_bytes=sum(len(b) for b,_ in blocks),
        sha256=hashlib.sha256(b''.join(b for b,_ in blocks)).hexdigest(),tempo_mode=mode,tempo_row=MODES[mode],
        notation_quarter=quarter,timeline_quarter=24,normal_quarter_frames=str(q[0]),hurry_quarter_frames=str(q[1]),
        nominal_bpm=float(3600/q[0]),hurry_nominal_bpm=float(3600/q[1]),hurry_ratio=float(q[0]/q[1]),
        format='r3-native-phase-1',compatibility='native M20 headers; explicit index schema4 is not an accepted production score/pack')
    for kind,part in [('intro',blocks[:loop]),('loop',blocks[loop:])]:
        n=sum(r['ticks'] for _,r in part);h=sum(r['hurry_ticks'] for _,r in part)
        require(F(n)/q[0]==F(h)/q[1],'phrase normal/hurry beat totals differ')
        info[kind+'_ticks']=n;info['hurry_'+kind+'_ticks']=h;info[kind+'_beats']=str(F(n)/q[0])
    require(info['sequence_bytes']<=5632,'song bank capacity exceeded')
    return blocks,info


def compile_score(score):
    require(isinstance(score,dict) and type(score.get('schema')) is int,'integer schema required')
    if score['schema'] in (1,2):return compile_legacy(score)
    if score['schema']==3:return compile_tempo(score)
    if score['schema']==4:return compile_phase(score)
    raise ValueError('Unsupported score schema')

def payload(score):
    blocks,info=compile_score(score)
    data=bytearray(b'\xff'*0x1800)
    data[:3]=bytes([1,len(blocks),1+info['loop_section']]);cursor=0x200
    for i,(blob,record) in enumerate(blocks):
        require(cursor+len(blob)<=0x1800,'native bank overflow')
        data[0x11+i]=i*7;o=record['offsets']
        row=info.get('tempo_row',48)
        data[0x40+7*i:0x47+7*i]=bytes([row])+(0xc000+cursor).to_bytes(2,'little')+bytes([o['triangle'],o['pulse1'],o['noise'],0])
        data[cursor:cursor+len(blob)]=blob;cursor+=len(blob)
    return bytes(data),blocks,info
