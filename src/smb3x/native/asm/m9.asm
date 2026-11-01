; Project-authored M9 native transition controller. NESASM 3.01.
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
Menu = $79DB
Selected = $79DC
Release = $79DD
MenuRequest = $79DE
MenuPart = $79DF
Receipts = $79E0
Reason = $79E1
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
 CPX #4
 BNE NotInitialized
 JMP Initialized
NotInitialized:
 JMP AirshipReturn

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
 CMP #$A9
 BEQ ExistingInit
 LDA $0727
 ORA $0726
 BNE InitBad
 LDA $072B
 CMP #1
 BNE InitBad
 LDA #$A9
 STA Magic
 LDA #1
 STA Phase
 LDA #2
 STA Version
 LDA #1
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
 LDA #0
 STA Receipts
 RTS

Dispatch:
 LDA Magic
 CMP #$A9
 BEQ DispatchValid
 RTS
DispatchValid:
 JSR Poll
 LDA Phase
 CMP #2
 BEQ DispatchReady
 RTS
DispatchReady:
 JSR CastleGuard
 LDA MenuRequest
 BEQ HostRequest
 LDA #0
 STA MenuRequest
 LDA Seen
 CMP #$FB
 BCC MenuSequence
 LDA #2
 JMP Fail
MenuSequence:
 LDA #0
 STA Reason
 INC Seen
 LDA Seen
 STA Sequence
 JMP RequestAllowed
HostRequest:
 LDA Command
 CMP #3
 BEQ DispatchTravel
 RTS
DispatchTravel:
 LDA Result
 CMP #2
 BEQ DispatchPending
 RTS
DispatchPending:
 ; A rejected command may not be re-evaluated on a later map frame.
 LDA #0
 STA Command
 LDA #0
 STA Reason
 LDA Seen
 CMP #$FC
 BCC HostHasLifetime
 JMP DispatchDone
HostHasLifetime:
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
 LDA Reason
 BEQ SourceVBlank
 JSR WaitDisabled
 JMP SourceTick
SourceVBlank:
 JSR $96E5
SourceTick:
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
 JSR MenuControl
 RTS
Loading:
 JSR ZeroInput
 JSR Tick
 LDA Phase
 CMP #$FF
 BNE LoadingAlive
 JMP SkipMap
LoadingAlive:
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
 STA Release
SkipMap:
 LDA #1
 RTS
AllowMap:
 LDA #0
 RTS

; Accept only at normal dispatch, no pending movement/entry/pan/item effects.
Safe:
 LDA $17
 ORA $18
 BNE Unsafe
SafeContext:
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
 LDA Receipts
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
 STA $79E6
 STA $79E8
 STA $7973
 STA $7974
 STA $7975
 LDX #14
ClearAnimation:
 STA $053C,X
 DEX
 BPL ClearAnimation
 RTS

; Controller input is owned before Map_DoMap, including automatic entry.
MenuControl:
 LDA Release
 BEQ MenuCheck
 LDA $17
 BNE MenuHold
 LDA #0
 STA Release
MenuHold:
 JSR ZeroInput
 LDA #1
 RTS
MenuCheck:
 LDA Menu
 BNE MenuActive
 LDA $18
 AND #$20
 BEQ MenuNone
 JSR SafeContext
 BCS MenuNone
 LDA Sequence
 CMP Seen
 BNE MenuNone
 LDA #1
 STA Menu
 LDA $0727
 STA Selected
 JMP MenuRender
MenuNone:
 LDA #0
 RTS
MenuActive:
 LDA $18
 AND #$40
 BNE MenuClose
 LDA $18
 AND #$0F
 BEQ MenuConfirm
 LDA Selected
 EOR #1
 STA Selected
MenuConfirm:
 LDA $18
 AND #$80
 BEQ MenuRender
 LDA Selected
 CMP $0727
 BEQ MenuClose
 CMP #1
 BNE MenuGo
 LDA Unlock
 AND #2
 BEQ MenuRender
MenuGo:
 LDA $0300
 BNE MenuRender
 LDA Sequence
 CMP Seen
 BNE MenuRender
 LDA Selected
 STA Destination
 LDA #1
 STA MenuRequest
MenuClose:
 LDA $0300
 BNE MenuRender
 LDA #0
 STA Menu
 LDA #1
 STA Release
 ; Restore the native status panel through its normal static queue.
 LDA #2
 STA $5E
 JMP MenuHold
MenuRender:
 LDA $0300
 BEQ MenuBufferFree
 JMP MenuHold
MenuBufferFree:
 LDA MenuPart
 CMP #6
 BCC MenuPartOK
 LDA #0
 STA MenuPart
MenuPartOK:
 TAX
 LDA MenuOffsets,X
 TAX
 LDY #0
MenuDrawLoop:
 LDA MenuText,X
 STA $0301,Y
 INX
 INY
 CPY #14
 BNE MenuDrawLoop
 LDA MenuPart
 BNE MenuNotFirst
 LDA $0727
 CLC
 ADC #$F1
 STA $030A
MenuNotFirst:
 LDA MenuPart
 CMP #1
 BNE MenuDrawDone
 LDA Selected
 CLC
 ADC #$F1
 STA $0306
 LDA Selected
 BEQ MenuUnlocked
 LDA Unlock
 AND #2
 BEQ MenuDrawDone
MenuUnlocked:
 LDX #4
MenuOpenText:
 LDA MenuOpen,X
 STA $0309,X
 DEX
 BPL MenuOpenText
MenuDrawDone:
 LDA MenuPart
 CMP #2
 BNE MenuFinish
 LDA Selected
 BEQ MenuClearD
 LDA Unlock
 AND #2
 BEQ MenuFinish
MenuClearD:
 LDA #$FE
 STA $0304
MenuFinish:
 INC MenuPart
 LDA #13
 STA $0300
 JMP MenuHold
MenuOpen:
 .db $BE,$BF,$B4,$BD,$FE
MenuOffsets:
 .db 0,14,28,42,56,70
MenuText:
 .db $2B,$21,$0A,$C6,$BE,$C1,$BB,$B3,$FE,$F1,$FE,$FE,$C3,$00
 .db $2B,$2B,$0A,$BE,$FE,$F1,$FE,$FE,$BB,$BE,$B2,$BA,$B4,$00
 .db $2B,$35,$0A,$B3,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$00
 .db $2B,$41,$0A,$B0,$C1,$C1,$BE,$C6,$C2,$FE,$B2,$B7,$BE,$00
 .db $2B,$4B,$0A,$BE,$C2,$B4,$FE,$B0,$FE,$B6,$BE,$FE,$B1,$00
 .db $2B,$55,$0A,$FE,$B2,$B0,$BD,$B2,$B4,$BB,$FE,$FE,$FE,$00
MenuStatus:
 LDA Menu
 ORA Release
 BNE MenuStatusDone
 JMP $B44A
MenuStatusDone:
 RTS
; Called only after the native king/letter sequence and score cleanup.
AirshipReturn:
 LDA Bound
 BNE AirshipBound
 JMP AirshipBad
AirshipBound:
 LDA Phase
 CMP #2
 BEQ AirshipPhaseReady
 JMP AirshipBad
AirshipPhaseReady:
 LDA $0727
 CMP #2
 BCS AirshipBad
 STA Destination
 LDA $0726
 BNE AirshipBad
 LDA $072B
 CMP #1
 BNE AirshipBad
 LDA Receipts
 AND #1
 BNE AirshipBad
 LDA Sequence
 CMP Seen
 BNE AirshipBad
 LDA Seen
 CMP #$FA
 BCS AirshipBad
 INC Seen
 LDA Seen
 STA Sequence
 LDA Receipts
 ORA #1
 STA Receipts
 LDA #1
 STA Reason
 ; PRG011 reserves slot 1 for the airship. Vanilla next-world init normally
 ; discards it; same-world return must retire it before sealing the source.
 LDA #0
 STA $7F16
 ; Low RAM was cleared. The completed castle is now free of its airship;
 ; use it as the validated fallback when START contains a bonus object.
 LDX $0727
 LDA CastleY,X
 STA PointY
 LDA CastleX,X
 STA PointX
 LDA CastleHi,X
 STA PointHi
 STA PointScrollHi
 LDA #0
 STA PointScroll
 JSR ApplyPoint
 ; Native king cleanup clears PPU_CTL1_Copy/NMI enable. Restore only the
 ; interrupt clock while display/update work is disabled for the source hold.
 LDA #0
 STA $16
 STA $2001
 LDA #1
 STA $7955
 LDA #$A8
 STA $FF
 STA $2000
 JSR RequestAllowed
 RTS
AirshipBad:
 LDA #10
 JSR Fail
AirshipHalt:
 JSR $96E5
 JMP AirshipHalt
CastleGuard:
 LDA Receipts
 AND #1
 BEQ CastleDone
 LDA $0729
 CMP #$10
 BNE CastleDone
 LDA $070A
 BNE CastleDone
 ; World_Map_Tile is scratch after drawing; match source-backed castle position.
 LDX $0727
 CPX #2
 BCS CastleDone
 LDA $77
 CMP CastleHi,X
 BNE CastleDone
 LDA $79
 CMP CastleX,X
 BNE CastleDone
 LDA $75
 CMP CastleY,X
 BNE CastleDone
 LDA #$0D
 STA $0729
 LDA #0
 STA $20
CastleDone:
 RTS
CastleHi: .db 0,1
CastleX: .db $C0,$20
CastleY: .db $80,$60
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
 JMP $CF29
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
AirshipStub:
 LDX #5
 JSR BankCall
 JMP $84A0
FixedEnd:

; Source-reviewed PRG027 tail after B9C8, separate from king/letter code.
 .bank 27
 .org $BA00
RewardCode:
 STX $79E5
 TSX
 LDA $0104,X
 STA $79E4
 LDA $0106,X
 STA $79E2
 LDA $79E5
 BEQ HouseReward
 CMP #1
 BEQ EnemyReward
 CMP #2
 BEQ EnemyEntered
 JMP EnemyRemoved
HouseReward:
 LDA $0726
 BNE OriginalHouse
 LDA $072B
 CMP #1
 BNE OriginalHouse
 LDA $070A
 CMP #7
 BNE OriginalHouse
 LDA $7978
 BNE OriginalHouse
 LDX #3
HouseMatch:
 LDA HouseWorld,X
 CMP $0727
 BNE NextHouse
 LDA HouseX,X
 CMP $797A
 BNE NextHouse
 LDA HouseY,X
 CMP $7976
 BNE NextHouse
 LDA HouseBit,X
 ORA Receipts
 STA Receipts
 RTS
NextHouse:
 DEX
 BPL HouseMatch
OriginalHouse:
 LDY $79E4
 LDA $79E2
 STA $7D80,Y
 RTS
EnemyReward:
 LDA $1E
 CMP $79EA
 BNE OriginalEnemy
 LDA $7963
 CMP $79EB
 BNE OriginalEnemy
 CMP $79E2
 BNE OriginalEnemy
 LDA $79E6
 BEQ OriginalEnemy
 LDA $79E7
 CMP $0727
 BNE OriginalEnemy
 LDA $0713
 BNE OriginalEnemy
 LDA #1
 STA $79E8
 RTS
OriginalEnemy:
 LDA $79E2
 JMP $FD6C
EnemyEntered:
 LDA #0
 STA $79E6
 STA $79E8
 LDA $0726
 BNE EntryDone
 LDA $072B
 CMP #1
 BNE EntryDone
 LDA $0727
 CMP #2
 BCS EntryDone
 STA $79E7
 LDY $79E4
 CPY #2
 BCC EntryDone
 CPY #4
 BCS EntryDone
 STA $79E9
 LDA $7F15,Y
 LDX $0727
 BNE W2Encounter
 CPY #2
 BNE EntryDone
 CMP #3
 BEQ EncounterValid
 CMP #11
 BNE EntryDone
 BEQ EncounterValid
W2Encounter:
 CMP #4
 BNE EntryDone
EncounterValid:
 STA $79EA
 LDA $7956,Y
 STA $79EB
 STY $79E9
 LDA #8
 CPY #2
 BEQ EncounterBit
 LDA #16
EncounterBit:
 STA $79E6
EntryDone:
 LDY $79E4
 LDA $7956,Y
 TSX
 STA $0106,X
 RTS
EnemyRemoved:
 LDY $79E4
 LDA $79E2
 STA $7F15,Y
 BNE RewardDone
 LDA $79E8
 BEQ RewardDone
 LDA $0729
 CMP #7
 BNE RewardDone
 LDA $0727
 CMP $79E7
 BNE RewardDone
 CPY $79E9
 BNE RewardDone
 LDA Receipts
 ORA $79E6
 STA Receipts
 LDA #0
 STA $79E6
 STA $79E8
RewardDone:
 RTS
HouseWorld:
 .db 0,0,1,1
HouseX:
 .db $C0,$60,$E0,$60
HouseY:
 .db $40,$80,$20,$80
HouseBit:
 .db 2,4,2,4
RewardCodeEnd:

; PRG031 source-declared DMC alignment gap E911-E97F. No sample moved.
 .bank 31
 .org $E911
RewardStubs:
HouseStub:
 PHP
 PHA
 TXA
 PHA
 TYA
 PHA
 LDX #0
 JMP RewardCall
TreasureStub:
 PHP
 PHA
 TXA
 PHA
 TYA
 PHA
 LDX #1
 JMP RewardCall
EnteredStub:
 PHP
 PHA
 TXA
 PHA
 TYA
 PHA
 LDX #2
 JMP RewardCall
RemovedStub:
 PHP
 PHA
 TXA
 PHA
 TYA
 PHA
 LDX #3
RewardCall:
 LDA $0720
 PHA
 LDA #27
 STA $0720
 JSR $FFC2
 JSR RewardCode
 PLA
 STA $0720
 JSR $FFC2
 PLA
 TAY
 PLA
 TAX
 PLA
 PLP
 RTS
RewardStubsEnd:
