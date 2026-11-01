; Project-authored M8 native transition controller. NESASM 3.01.
; Native addresses researched from Southbird's PRG1 disassembly; see docs.
; This file contains no original game data. The patcher verifies every hook.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0

Magic = $79A0
Version = $79A1
Phase = $79A2
Error = $79A3
Sequence = $79A4
Seen = $79A5
Command = $79A6
Destination = $79A7
Unlock = $79A8
Active = $79A9
Result = $79AA
TravelSeq = $79AB
TimerLo = $79AC
TimerHi = $79AD
Bound = $79AE
Session = $79B0
PointY = $79D0
PointX = $79D1
PointHi = $79D2
PointScroll = $79D3
PointScrollHi = $79D4
Expected1 = $79D5
Expected2 = $79D6
Sum1 = $79D7
Sum2 = $79D8
Global1 = $79D9
Global2 = $79DA
ReturnValue = $79EF

; Phases: 1 boot intro, 2 ready, 3 frozen source, 4 fade,
; 5 frozen destination, 6 intro, 7 frozen commit, FF fail-stop.
; Commands: 1 bind, 2 unlock, 3 travel, 4 source durable,
; 5 destination prepared, 6 commit durable. Sequence is published last.

 .bank 26
 .org $B600
Controller:
 CPX #0
 BNE NotDispatch
 JMP Dispatch
NotDispatch:
 CPX #1
 BNE NotPremap
 JMP Premap
NotPremap:
 CPX #2
 BNE NotReload
 JMP Reload
NotReload:
 CPX #3
 BNE NotInit
 JMP Init
NotInit:
 JMP Initialized

Fail:
 STA Error
 LDA #$FF
 STA Phase
 LDA #3
 STA Result
 RTS

ZeroInput:
 LDA #0
 STA $17
 STA $18
 RTS

Tick:
 INC TimerLo
 BNE TickCheck
 INC TimerHi
TickCheck:
 LDA TimerHi
 CMP #4
 BCC TickDone
 LDA #8
 JSR Fail
TickDone:
 RTS

ResetTimer:
 LDA #0
 STA TimerLo
 STA TimerHi
 RTS

; Each published sequence must be precisely previous+1, no wrap.
; Invalid commands consume their sequence and report rejection, never success.
Poll:
 LDA Sequence
 CMP Seen
 BEQ PollDone
 LDA Seen
 CMP #$FE
 BCS BadSequence
 CLC
 ADC #1
 CMP Sequence
 BNE BadSequence
 STA Seen
 LDA #2
 STA Result
 LDA Command
 CMP #1
 BNE NotBind
 LDA Bound
 BNE PollDone
 LDX #31
BindCompare:
 LDA Session,X
 CMP $9F1C,X
 BNE BadIdentity
 DEX
 BPL BindCompare
 LDA #1
 STA Bound
 STA Result
 RTS
BadIdentity:
 LDA #1
 JMP Fail
BadSequence:
 LDA #2
 JMP Fail
NotBind:
 LDA Bound
 BEQ PollDone
 LDA Command
 CMP #2
 BNE PollDone
 LDA Unlock
 ORA #2
 STA Unlock
 LDA #1
 STA Result
PollDone:
 RTS

; Cold initializer only. Later unrequested vanilla world initialization is
; fail-stopped before Map_Init destroys another world's state (airship/warp).
Init:
 LDA Magic
 CMP #$A8
 BEQ ExistingInit
 LDA $0727
 ORA $0726
 BNE InitBad
 LDA $072B
 CMP #1
 BNE InitBad
 LDA #$A8
 STA Magic
 LDA #1
 STA Version
 STA Phase
 STA Unlock
 LDA #0
 STA Active
 STA Bound
 STA Seen
 STA Sequence
 STA Error
 STA Result
 JSR ResetTimer
 RTS
ExistingInit:
 LDA Phase
 CMP #4
 BEQ InitReturn
InitBad:
 LDA #9
 JSR Fail
InitFrozen:
 JSR $96E5
 JMP InitFrozen
InitReturn:
 RTS

Dispatch:
 LDA Magic
 CMP #$A8
 BEQ DispatchValid
 RTS
DispatchValid:
 JSR Poll
 LDA Phase
 CMP #2
 BEQ DispatchReady
 RTS
DispatchReady:
 LDA Command
 CMP #3
 BEQ DispatchTravel
 RTS
DispatchTravel:
 LDA Result
 CMP #2
 BNE DispatchDone
 ; A rejected command may not be re-evaluated on a later map frame.
 LDA #0
 STA Command
 JSR Safe
 BCS DispatchDone
 LDA Destination
 CMP #2
 BCS DispatchDone
 CMP $0727
 BEQ DispatchDone
 CMP #1
 BNE RequestAllowed
 LDA Unlock
 AND #2
 BEQ DispatchDone
RequestAllowed:
 LDA Seen
 STA TravelSeq
 LDA $0727
 STA Active
 JSR Globals
 LDA Sum1
 STA Global1
 LDA Sum2
 STA Global2
 LDA #3
 STA Phase
 LDA #0
 STA Result
 JSR ResetTimer
SourceWait:
 JSR $96E5
 JSR ZeroInput
 JSR Tick
 LDA Phase
 CMP #$FF
 BEQ SourceWait
 JSR Poll
 LDA Command
 CMP #4
 BNE SourceWait
 LDA Result
 CMP #2
 BNE SourceWait
 LDA #0
 STA Command
 LDA #4
 STA Phase
 STA $0729
 LDA #1
 STA Result
DispatchDone:
 RTS

Reload:
 LDA Phase
 CMP #4
 BNE ReloadOrdinary
 LDA Destination
 STA $0727
 LDA #1
 RTS
ReloadOrdinary:
 LDA #0
 RTS

Initialized:
 LDA Phase
 CMP #4
 BEQ PrepareDestination
 RTS
PrepareDestination:
 LDA #5
 STA Phase
 JSR ResetTimer
DestinationWait:
 JSR WaitDisabled
 JSR ZeroInput
 JSR Tick
 LDA Phase
 CMP #$FF
 BEQ DestinationWait
 JSR Poll
 LDA Command
 CMP #5
 BNE DestinationWait
 LDA Result
 CMP #2
 BNE DestinationWait
 LDA #0
 STA Command
 JSR SnapshotSum
 LDA Sum1
 CMP Expected1
 BNE RestoreBad
 LDA Sum2
 CMP Expected2
 BNE RestoreBad
 JSR ValidatePoint
 BCS RestoreBad
 JSR ApplyPoint
 LDA #6
 STA Phase
 LDA #1
 STA Result
 JSR ResetTimer
 RTS
RestoreBad:
 LDA #4
 JSR Fail
 JMP DestinationWait

; UpdSel_Disable skips the vanilla VBlank_Tick update, but the NMI tail
; always increments Counter_1. Do not enable drawing of a partial map.
WaitDisabled:
 LDA $15
WaitCounter:
 CMP $15
 BEQ WaitCounter
 RTS

Premap:
 JSR Poll
 LDA Phase
 CMP #$FF
 BNE PremapRunning
 LDA #1
 RTS
PremapRunning:
 CMP #7
 BEQ CommitWait
 CMP #1
 BEQ Loading
 CMP #6
 BEQ Loading
 LDA #0
 RTS
Loading:
 JSR ZeroInput
 JSR Tick
 LDA Phase
 CMP #$FF
 BEQ SkipMap
 LDA $0729
 CMP #$0D
 BNE AllowMap
 LDA Bound
 BEQ SkipMap
 LDA Phase
 CMP #1
 BNE NeedCommit
 LDA #2
 STA Phase
 LDA #0
 STA Active
 JMP SkipMap
NeedCommit:
 JSR Globals
 LDA Sum1
 CMP Global1
 BNE GlobalBad
 LDA Sum2
 CMP Global2
 BNE GlobalBad
 LDA Destination
 CMP $0727
 BNE GlobalBad
 LDA #7
 STA Phase
 JSR ResetTimer
 JMP SkipMap
GlobalBad:
 LDA #5
 JSR Fail
 JMP SkipMap
CommitWait:
 JSR ZeroInput
 JSR Tick
 LDA Phase
 CMP #$FF
 BEQ SkipMap
 LDA Command
 CMP #6
 BNE SkipMap
 LDA Result
 CMP #2
 BNE SkipMap
 LDA #0
 STA Command
 LDA $0727
 STA Active
 LDA #2
 STA Phase
 LDA #1
 STA Result
SkipMap:
 LDA #1
 RTS
AllowMap:
 LDA #0
 RTS

; Accept only at normal dispatch, no pending movement/entry/pan/item effects.
Safe:
 LDA Bound
 BEQ Unsafe
 LDA $072B
 CMP #1
 BNE Unsafe
 LDA $0727
 CMP #2
 BCS Unsafe
 LDA $0729
 CMP #$0D
 BNE Unsafe
 LDA $0100
 CMP #$C0
 BNE Unsafe
 LDA $0728
 CMP #2
 BCS Unsafe
 LDA $0736
 CMP #100
 BCS Unsafe
 LDA $070A
 ORA $0726
 ORA $0014
 ORA $0020
 ORA $001E
 ORA $007B
 ORA $0017
 ORA $0018
 ORA $008B
 ORA $00C5
 ORA $00DA
 ORA $0376
 ORA $03E1
 ORA $03E6
 ORA $03ED
 ORA $05F2
 ORA $0710
 ORA $073C
 ORA $073E
 ORA $0745
 ORA $7955
 BNE Unsafe
 CLC
 RTS
Unsafe:
 SEC
 RTS

; Modulo-256 two-accumulator checksum; external snapshots also use SHA256.
SumByte:
 CLC
 ADC Sum1
 STA Sum1
 CLC
 ADC Sum2
 STA Sum2
 RTS
ClearSum:
 LDA #0
 STA Sum1
 STA Sum2
 RTS
Globals:
 JSR ClearSum
 LDA $0736
 JSR SumByte
 LDA $0746
 JSR SumByte
 ; Music-box duration and queued Starman remain global, as in vanilla.
 LDA $7F53
 JSR SumByte
 LDA $03F2
 JSR SumByte
 LDX #34
GlobalLoop:
 LDA $7D80,X
 JSR SumByte
 DEX
 BPL GlobalLoop
 RTS
SnapshotSum:
 JSR ClearSum
 LDX #0
CompletionSum:
 LDA $7D00,X
 JSR SumByte
 INX
 CPX #128
 BNE CompletionSum
 LDX #0
ObjectSum:
 LDA $7EEB,X
 JSR SumByte
 INX
 CPX #56
 BNE ObjectSum
 LDX #0
ItemSum:
 LDA $7956,X
 JSR SumByte
 INX
 CPX #13
 BNE ItemSum
 LDX #0
BonusSum:
 LDA $796B,X
 JSR SumByte
 INX
 CPX #3
 BNE BonusSum
 LDX #0
FlagSum:
 LDA $796F,X
 JSR SumByte
 INX
 CPX #4
 BNE FlagSum
 LDA $07E2
 JSR SumByte
 LDA $0742
 JSR SumByte
 LDA $7F2D
 JSR SumByte
 LDX #0
PointSum:
 LDA PointY,X
 JSR SumByte
 INX
 CPX #5
 BNE PointSum
 RTS

ValidatePoint:
 LDA PointY
 CMP #$20
 BCC BadPoint
 CMP #$A1
 BCS BadPoint
 AND #$0F
 BNE BadPoint
 LDA PointX
 AND #$0F
 BNE BadPoint
 LDA PointHi
 CMP #4
 BCS BadPoint
 LDA PointScrollHi
 CMP #4
 BCS BadPoint
 LDX #13
Collision:
 LDA $7F15,X
 BEQ NextObject
 LDA $7EEB,X
 CMP PointY
 BNE NextObject
 LDA $7EF9,X
 CMP PointX
 BNE NextObject
 LDA $7F07,X
 CMP PointHi
 BEQ BadPoint
NextObject:
 DEX
 BPL Collision
 CLC
 RTS
BadPoint:
 SEC
 RTS

ApplyPoint:
 LDA PointY
 STA $0075
 STA $7976
 STA $797E
 LDA PointX
 STA $0079
 STA $797A
 STA $7982
 LDA PointHi
 STA $0077
 STA $7978
 STA $7980
 LDA PointScroll
 STA $0722
 STA $7986
 LDA PointScrollHi
 STA $0724
 STA $7988
 LDA #1
 STA $007D
 STA $7993
 LDA #0
 STA $007B
 STA $0084
 STA $797C
 STA $7950
 STA $001E
 STA $0020
 STA $008B
 STA $00C5
 STA $00CC
 STA $00DA
 STA $0711
 STA $0713
 STA $0728
 STA $073C
 STA $073E
 STA $0745
 STA $7965
 STA $7966
 STA $7967
 STA $796E
 STA $7973
 STA $7974
 STA $7975
 LDX #14
ClearAnimation:
 STA $053C,X
 DEX
 BPL ClearAnimation
 RTS
ControllerEnd:

 .bank 30
 .org $9F60
DispatchStub:
 LDX #0
 JSR BankCall
 LDY $0729
 CPY #$0D
 RTS
PremapStub:
 LDX #1
 JSR BankCall
 CMP #0
 BEQ RunMap
 RTS
RunMap:
 JMP $C3C3
ShortStubsEnd:
 .org $9F90
InitializedStub:
 LDX #4
 JSR BankCall
 JMP $FD84
InitializedStubEnd:
 .org $9FB6
BankCall:
 LDA $0720
 PHA
 LDA #26
 STA $0720
 JSR $FFC2
 JSR Controller
 STA ReturnValue
 PLA
 STA $0720
 JSR $FFC2
 LDA ReturnValue
 RTS
ReloadStub:
 LDX #2
 JSR BankCall
 CMP #1
 BNE OrdinaryReload
 JMP $84A0
OrdinaryReload:
 JSR $FD84
 JMP $8581
InitStub:
 LDX #3
 JSR BankCall
 LDA #10
 STA $071F
 RTS
FixedEnd:
