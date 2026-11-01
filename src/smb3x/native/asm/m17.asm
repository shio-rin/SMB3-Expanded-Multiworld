; Project-authored M17 native transition controller. NESASM 3.01.
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
SequenceHi = $79F0
SeenHi = $79F1
TravelHi = $79F2
Published = $79F3
Accepted = $79F4
EndingPhase = $79F5
EndingVersion = $79F6
Hammers = $79F7
Stars = $79F8
PendingLo = $79F9
PendingHi = $79FA
ToolActive = $79FB
GrantHammers = $7997
GrantStars = $7998
GrantPendingLo = $7999
GrantPendingHi = $799A
; Southbird declares $7A73-$7ADF unused in gameplay. Presentation only;
; durable physical identities live in the seed/registry-bound client history.
GrantChecks = $7A80
CheckCounts = $7AA0
CheckTotal = $7AA8
StackFormat = $7AAC
StackMode = $7AAD
StackCounts = $7AB0
StackSerial = $7ACC
StackItem = $7BD0
StackTicket = $7BD1
StackPublish = $7BD5
StackAck = $7BD6
StackAckType = $7BDA
StackResult = $7BDB
StackPending = $7BDC
StackSlot = $7BDD
StackTemp = $7BDE
StackArg = $7BDF
StackAfter = $7BE0
StackReceiptSerial = $7BE2
StackBefore = $7BE6
StackBusy = $7BE8

; Phases: 1 boot intro, 2 ready, 3 frozen source, 4 fade,
; 5 frozen destination, 6 intro, 7 frozen commit, FF fail-stop.
; Commands: 1 bind, 2 unlock, 3 travel, 4 source durable,
; 5 destination prepared, 6 commit durable. Sequence is published last.

 .bank 26
 .org $B520
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
 CPX #5
 BNE EndingDispatch
 JMP AirshipReturn
EndingDispatch:
 JMP EndingReturn

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

; M17 unsigned 16-bit sequence, max FFFE, never reused. Host writes both
; sequence bytes then Published=1. ROM ignores incomplete publication.
Poll:
 LDA Published
 BNE PollPublished
 RTS
PollPublished:
 LDA #0
 STA Published
 LDA SeenHi
 CMP #$FF
 BNE PollIncrement
 LDA Seen
 CMP #$FE
 BCS BadSequence
PollIncrement:
 CLC
 LDA Seen
 ADC #1
 CMP Sequence
 BNE BadSequence
 LDA SeenHi
 LDX Sequence
 BNE PollHigh
 CLC
 ADC #1
PollHigh:
 CMP SequenceHi
 BNE BadSequence
 LDA SequenceHi
 STA SeenHi
 LDA Sequence
 STA Seen
 LDA Command
 STA Accepted
 LDA #2
 STA Result
 LDA Accepted
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
 LDA Accepted
 CMP #7
 BNE PollNotProgression
 LDX #8
 JMP BankCall
PollNotProgression:
 LDA Accepted
 CMP #2
 BNE PollDone
 LDA Phase
 CMP #2
 BNE PollDone
 LDX Destination
 CPX #8
 BCS PollDone
 LDA Unlock
 ORA WorldBits,X
 STA Unlock
 LDA #1
 STA Result
PollDone:
PollReturn:
 RTS

; Cold initializer only. Later unrequested vanilla world initialization is
; fail-stopped before Map_Init destroys another world's state (airship/warp).
Init:
 LDA Magic
 CMP #$AA
 BEQ ExistingInit
 LDA $0727
 ORA $0726
 BNE InitBad
 LDA $072B
 CMP #1
 BNE InitBad
 LDA #$AA
 STA Magic
 LDA #1
 STA Phase
 LDA #9
 STA Version
 LDA #1
 STA Unlock
 LDA #0
 STA Active
 STA Bound
 STA Seen
 STA Sequence
 STA SequenceHi
 STA SeenHi
 STA TravelSeq
 STA TravelHi
 STA Published
 STA Accepted
 STA Error
 STA Result
 STA EndingPhase
 STA EndingVersion
 STA Hammers
 STA Stars
 STA PendingLo
 STA PendingHi
 STA ToolActive
 LDX #8
ColdTracker:
 STA CheckCounts,X
 DEX
 BPL ColdTracker
 LDX #13
 JSR BankCall
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
 CMP #$AA
 BEQ DispatchValid
 RTS
DispatchValid:
 JSR Poll
 LDA Phase
 CMP #2
 BEQ DispatchReady
 RTS
DispatchReady:
 JSR Safe
 BCS StackTickSkip
 LDX #12
 JSR BankCall
StackTickSkip:
 JSR CastleGuard
 LDA MenuPart
 BPL DispatchMenuReady
 RTS
DispatchMenuReady:
 LDA MenuRequest
 BEQ HostRequest
 LDA #0
 STA MenuRequest
 JSR TravelLifetime
 BCC MenuSequence
 LDA #2
 JMP Fail
MenuSequence:
 LDA #0
 STA Reason
 JSR InternalSequence
 JMP RequestAllowed
HostRequest:
 LDA Accepted
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
 STA Accepted
 LDA #0
 STA Reason
 LDA SeenHi
 CMP #$FF
 BNE HostHasLifetime
 LDA Seen
 CMP #$FC
 BCC HostHasLifetime
 JMP DispatchDone
HostHasLifetime:
 JSR Safe
 BCC HostSafe
 JMP DispatchDone
HostSafe:
 LDA Destination
 CMP #8
 BCS DispatchDone
 CMP $0727
 BEQ DispatchDone
 TAX
 JSR AllowedWorld
 BEQ DispatchDone
RequestAllowed:
 LDA SeenHi
 STA TravelHi
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
 LDA Accepted
 CMP #4
 BNE SourceWait
 LDA Result
 CMP #2
 BNE SourceWait
 LDA #0
 STA Accepted
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
 LDA Accepted
 CMP #5
 BNE DestinationWait
 LDA Result
 CMP #2
 BNE DestinationWait
 LDA #0
 STA Accepted
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
 LDA Accepted
 CMP #6
 BNE SkipMap
 LDA Result
 CMP #2
 BNE SkipMap
 LDA #0
 STA Accepted
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
 CMP #8
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
 ORA $0597
 ORA $7973
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
 LDX #31
StackGlobalLoop:
 LDA StackCounts,X
 JSR SumByte
 DEX
 BPL StackGlobalLoop
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
 LDA $07BB
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
 LDX $0727
 CPX #8
 BCS BadPoint
 LDA PointHi
 CMP MapPages,X
 BCS BadPoint
 LDA PointScroll
 AND #$7F
 BNE BadPoint
 LDA PointScrollHi
 CMP MaxScrollHi,X
 BCC PointScrollOK
 BNE BadPoint
 LDA PointScroll
 BNE BadPoint
PointScrollOK:
 CPX #7
 BEQ PointFixedSection
 CPX #4
 BNE PointSectionOK
PointFixedSection:
 LDA PointScroll
 BNE BadPoint
 LDA PointScrollHi
 CMP PointHi
 BNE BadPoint
PointSectionOK:
 SEC
 LDA PointX
 SBC PointScroll
 LDA PointHi
 SBC PointScrollHi
 BNE BadPoint
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
 LDA MenuPart
 BMI MenuHold
 LDA ToolActive
 BEQ ToolIdle
 LDA $03ED
 BEQ ToolFinished
 JSR $A7C0
 JMP ToolHold
ToolFinished:
 LDA #0
 STA ToolActive
ToolHold:
 JSR ZeroInput
 LDA #1
 RTS
ToolIdle:
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
 CMP #2
 BEQ ProgressionRun
 CMP #0
 BNE MenuActive
 LDA $18
 AND #$10
 BEQ CheckWorldSelect
 JSR SafeContext
 BCS MenuNone
 JSR SequenceIdle
 BNE MenuNone
 LDA #2
 STA Menu
 LDA #0
 STA Selected
 STA MenuPart
ProgressionRun:
 LDX #7
 JSR BankCall
 CMP #2
 BNE ProgressionDone
 ; Deliberate virtual tool: same native adjacent-rock search/removal routine.
 LDA #1
 STA ToolActive
 JSR $A6BB
 LDA #1
ProgressionDone:
 RTS
CheckWorldSelect:
 LDA $18
 AND #$20
 BEQ MenuNone
 JSR SafeContext
 BCS MenuNone
 JSR SequenceIdle
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
 LDA $18
 AND #$0A
 BEQ MenuNext
 DEC Selected
 JMP MenuWrap
MenuNext:
 INC Selected
MenuWrap:
 LDA Selected
 CMP #$FF
 BNE MenuWrapHigh
 LDA #7
MenuWrapHigh:
 CMP #8
 BCC MenuSelected
 LDA #0
MenuSelected:
 STA Selected
MenuConfirm:
 LDA $18
 AND #$80
 BEQ MenuRender
 LDA Selected
 CMP $0727
 BEQ MenuClose
 TAX
 JSR AllowedWorld
 BEQ MenuRender
MenuGo:
 LDA $0300
 BNE MenuRender
 JSR SequenceIdle
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
 ; Restore one native HUD row per frame, with controller ownership retained.
 LDA #$80
 STA MenuPart
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
 LDX Selected
 JSR AllowedWorld
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
 LDX Selected
 JSR AllowedWorld
 BEQ MenuFinish
MenuClearD:
 LDA #$FE
 STA $0304
MenuFinish:
 LDX #17
 JSR BankCall
 INC MenuPart
 JMP MenuHold
MenuOpen:
 .db $C1,$B4,$B0,$B3,$C8
MenuOffsets:
 .db 0,14,28,42,56,70
MenuText:
 .db $2B,$22,$0A,$C6,$BE,$C1,$BB,$B3,$FE,$F1,$FE,$FE,$C3,$00
 .db $2B,$2C,$0A,$BE,$FE,$F1,$FE,$FE,$BB,$BE,$B2,$BA,$B4,$00
 .db $2B,$36,$0A,$B3,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$00
 .db $2B,$42,$0A,$B0,$C1,$C1,$BE,$C6,$C2,$FE,$B2,$B7,$BE,$00
 .db $2B,$4C,$0A,$BE,$C2,$B4,$FE,$B0,$FE,$B6,$BE,$FE,$B1,$00
 .db $2B,$56,$0A,$FE,$B2,$BB,$BE,$C2,$B4,$FE,$FE,$FE,$FE,$00
MenuStatus:
 LDA Menu
 BEQ MenuStatusClosed
 LDX #15
 JMP BankCall
MenuStatusClosed:
 LDA MenuPart
 BPL MenuStatusReleased
 LDA $0300
 BNE MenuStatusDone
 LDA MenuPart
 CMP #$84
 BCC MenuStatusRow
 BNE MenuStatusCards
 JSR $B0C4
 JSR $B108
 INC MenuPart
 JMP $B44A
MenuStatusCards:
 JSR $FCBF
 LDA #0
 STA MenuPart
 RTS
MenuStatusRow:
 LDX #16
 JMP BankCall
MenuStatusReleased:
 LDA Release
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
 CMP #7
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
 JSR SequenceIdle
 BNE AirshipBad
 JSR TravelLifetime
 BCS AirshipBad
 JSR InternalSequence
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
 ; King cleanup cleared low RAM. Publish a coherent frozen source camera for
 ; the castle fallback (especially W5 sky). PPU is disabled; reload renders it.
 LDA PointScroll
 STA $FD
 LDA PointScrollHi
 STA $12
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
; Called only by START at native THE END, before vanilla clears $6000-$7FFF.
EndingReturn:
 LDA EndingPhase
 CMP #3
 BEQ EndingReturnConfirmed
 JMP EndingReturnBad
EndingReturnConfirmed:
 LDA EndingVersion
 CMP #1
 BNE EndingReturnBad
 LDA Bound
 CMP #1
 BNE EndingReturnBad
 LDA Phase
 CMP #2
 BNE EndingReturnBad
 LDA $0727
 CMP #7
 BNE EndingReturnBad
 LDA $0726
 BNE EndingReturnBad
 LDA $072B
 CMP #1
 BNE EndingReturnBad
 JSR SequenceIdle
 BNE EndingReturnBad
 JSR TravelLifetime
 BCS EndingReturnBad
 JSR InternalSequence
 LDA #7
 STA Destination
 LDA #2
 STA Reason
 LDA #$70
 STA PointY
 LDA #$C0
 STA PointX
 LDA #3
 STA PointHi
 STA PointScrollHi
 LDA #0
 STA PointScroll
 JSR ApplyPoint
 LDA #0
 STA $FD
 STA $078D
 STA $16
 STA $2001
 LDA #3
 STA $12
 LDA #1
 STA $7955
 LDA #$A8
 STA $FF
 STA $2000
 JSR RequestAllowed
 RTS
EndingReturnBad:
 JMP AirshipBad
CastleGuard:
 ; Castle access is independent of the authentic ending receipt.
 LDA $0727
 CMP #7
 BNE OrdinaryCastleGuard
 LDA $9F3D
 CMP #2
 BNE CastleDone
 LDA Stars
 CMP $9F3E
 BCS CastleDone
 LDA $0729
 CMP #$10
 BNE CastleDone
 LDA $77
 CMP #3
 BNE CastleDone
 LDA $79
 CMP #$C0
 BNE CastleDone
 LDA $75
 CMP #$70
 BNE CastleDone
 LDA #$0D
 STA $0729
 LDA #0
 STA $20
 LDA #2
 STA Menu
 STA Selected
 RTS
OrdinaryCastleGuard:
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
 CPX #7
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
MapPages: .db 1,2,3,2,2,3,2,4
MaxScrollHi: .db 0,1,2,1,1,2,1,3
WorldBits: .db 1,2,4,8,16,32,64,128
CastleHi: .db 0,1,2,0,1,2,1
CastleX: .db $C0,$20,$90,$80,$20,$C0,$80
CastleY: .db $80,$60,$80,$60,$A0,$60,$90
; Z is set only if there is no partially published host command.
SequenceIdle:
 LDA Sequence
 EOR Seen
 BNE SequenceNotIdle
 LDA SequenceHi
 EOR SeenHi
 BNE SequenceNotIdle
 LDA Published
SequenceNotIdle:
 RTS
; Reserve request plus all three durable acknowledgments before starting.
TravelLifetime:
 LDA SeenHi
 CMP #$FF
 BNE LifetimeAvailable
 LDA Seen
 CMP #$FB
 RTS
LifetimeAvailable:
 CLC
 RTS
InternalSequence:
 INC Seen
 BNE InternalLow
 INC SeenHi
InternalLow:
 LDA SeenHi
 STA SequenceHi
 LDA Seen
 STA Sequence
 RTS
AllowedWorld:
 CPX #7
 BNE AllowedPass
 LDA $9F3D
 CMP #1
 BNE AllowedPass
 LDA Stars
 CMP $9F3E
 BCS AllowedPass
 LDA #0
 RTS
AllowedPass:
 LDA Unlock
 AND WorldBits,X
 RTS
HammerGate:
 LDA $9F3C
 BEQ HammerOriginal
 LDA ToolActive
 BEQ HammerDenied
 LDX $0727
 LDA Hammers
 AND WorldBits,X
 BEQ HammerDenied
HammerOriginal:
 LDA #3
 STA $00
 JMP $A6BF
HammerDenied:
 JMP $A687
HammerFinish:
 LDA ToolActive
 BNE HammerReusable
 JMP $A61B
HammerReusable:
 RTS
PoofFinish:
 LDA ToolActive
 BNE HammerReusable
 JMP $A426
; Inv_UseItem_ShiftOver entry wrapper. The native effect has succeeded.
StackDrawStub:
 LDX #11
 JSR BankCall
 LDA $03ED
 RTS
StackUseStub:
 LDX #14
 JMP BankCall
StackConsumeStub:
 LDX #10
 JSR BankCall
 CMP #1
 BEQ StackRetainSlot
 LDA #27
 STA $0E
 JMP $A61F
StackRetainSlot:
 JMP $A64B
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
 .org $9F98
EndingContinueStub:
 LDX #6
 JSR BankCall
 JMP $84A0
EndingContinueStubEnd:
 .org $9FB6
BankCall:
 LDA $0720
 PHA
 LDA #26
 CPX #7
 BCC BankSelected
 LDA #25
BankSelected:
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
 BNE RewardNotEnemy
 JMP EnemyReward
RewardNotEnemy:
 CMP #2
 BNE RewardRemoveDispatch
 JMP EnemyEntered
RewardRemoveDispatch:
 CMP #7
 BCC RewardOldDispatch
 JMP VisualDispatch
RewardOldDispatch:
 CMP #4
 BCC RewardRemoveNormal
 JMP EndingEvidence
RewardRemoveNormal:
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
 LDX #15
HouseMatch:
 LDA HouseHi,X
 CMP $7978
 BNE NextHouse
 LDA HouseWorld,X
 CMP $0727
 BNE NextHouse
 LDA HouseX,X
 CMP $797A
 BNE NextHouse
 LDA HouseY,X
 CMP $7976
 BNE NextHouse
 CPX #15
 BNE HouseEnabled
 LDA $9F3C
 BEQ OriginalHouse
HouseEnabled:
 LDA HouseBit,X
 ORA Receipts
 STA Receipts
 RTS
NextHouse:
 DEX
 BPL HouseMatch
OriginalHouse:
 LDA $9F3C
 BEQ OriginalHouseGrant
 LDA $79E2
 CMP #11
 BEQ SuppressedLegacyHammer
OriginalHouseGrant:
 LDY $79E4
 LDA StackMode
 BEQ OriginalHouseSlot
 LDA $79E2
 JMP $FD6C
OriginalHouseSlot:
 LDA $79E2
 STA $7D80,Y
 RTS
EnemyReward:
 JSR HandReward
 BCS PlantRewardDone
 JSR PlantReward
 BCS PlantRewardDone
 LDA $0727
 CMP #6
 BNE RoamingReward
 JMP OriginalEnemy
PlantRewardDone:
 RTS
RoamingReward:
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
 LDA $9F3C
 BEQ OriginalEnemyGrant
 LDA $79E2
 CMP #11
 BEQ SuppressedLegacyHammer
OriginalEnemyGrant:
 LDA $79E2
 JMP $FD6C
SuppressedLegacyHammer:
 RTS
; Hand traps share one native prize room, but retain distinct physical entries.
; Record the actual treasure insertion only; the monitor also requires the
; native successful-return map bit. Entry, grab and an ordinary exit cannot win.
HandReward:
 LDA Bound
 CMP #1
 BNE HandNotMatched
 LDA Phase
 CMP #2
 BNE HandNotMatched
 LDA $0727
 CMP #7
 BNE HandNotMatched
 LDA $0726
 BNE HandNotMatched
 LDA $072B
 CMP #1
 BNE HandNotMatched
 LDA $070A
 CMP #11
 BNE HandNotMatched
 LDA $0713
 CMP #1
 BNE HandNotMatched
 LDA $79E2
 CMP #3
 BNE HandNotMatched
 LDA $7978
 CMP #1
 BNE HandNotMatched
 LDA $7976
 CMP #$70
 BNE HandNotMatched
 LDA $7EB9
 CMP #$17
 BNE HandNotMatched
 LDA $7EBA
 CMP #$BE
 BNE HandNotMatched
 LDA $7EBB
 CMP #$CF
 BNE HandNotMatched
 LDA $7EBC
 CMP #$D0
 BNE HandNotMatched
 LDX #2
HandMatch:
 LDA HandX,X
 CMP $797A
 BEQ HandMatched
 DEX
 BPL HandMatch
HandNotMatched:
 CLC
 RTS
HandMatched:
 LDA HandBits,X
 ORA Receipts
 STA Receipts
 SEC
 RTS
HandX: .db $A0,$80,$60
HandBits: .db $20,$40,$80
; Stationary W7 Piranha objects use prize-room treasure then native slot deletion.
; Suppress only the authentic treasure insertion in the source-verified prize room.
PlantReward:
 LDA $0727
 CMP #6
 BNE PlantNotMatched
 LDA $0726
 BNE PlantNotMatched
 LDA $072B
 CMP #1
 BNE PlantNotMatched
 LDA $070A
 CMP #5
 BNE PlantNotMatched
 ; PRG026 junction sets return status 1; PRG005 treasure exit changes it to 0 later.
 LDA $0713
 CMP #1
 BNE PlantNotMatched
 LDX #1
PlantMatch:
 LDA PlantHi,X
 CMP $7978
 BNE PlantNext
 LDA PlantX,X
 CMP $797A
 BNE PlantNext
 LDA PlantY,X
 CMP $7976
 BNE PlantNext
 LDA PlantLayoutLo,X
 CMP $7EB9
 BNE PlantNext
 LDA PlantLayoutHi,X
 CMP $7EBA
 BNE PlantNext
 LDA PlantObjectsLo,X
 CMP $7EBB
 BNE PlantNext
 LDA PlantObjectsHi,X
 CMP $7EBC
 BNE PlantNext
 LDA PlantBit,X
 CMP $79E6
 BNE PlantNext
 LDA $79E7
 CMP #6
 BNE PlantNext
 LDA #1
 STA $79E8
 SEC
 RTS
PlantNext:
 DEX
 BPL PlantMatch
PlantNotMatched:
 CLC
 RTS
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
 STA $79E7
 LDX #20
EnemyMatch:
 LDA EnemyWorld,X
 CMP $0727
 BNE NextEnemy
 LDA EnemySlot,X
 CMP $79E4
 BNE NextEnemy
 TAY
 LDA EnemyType,X
 CMP $7F15,Y
 BNE NextEnemy
 STA $79EA
 LDA $7956,Y
 STA $79EB
 STY $79E9
 LDA EnemyBit,X
 STA $79E6
 JMP EntryDone
NextEnemy:
 DEX
 BPL EnemyMatch
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
 LDA $0727
 CMP #7
 BNE RemovalTreasureProof
 ; W8 military victories have no native inventory treasure. Their exact
 ; entered slot/type plus native successful operation7 deletion is the proof.
 LDA $0713
 ORA $070A
 BNE RewardDone
 JMP RemovalOperationProof
RemovalTreasureProof:
 LDA $79E8
 BEQ RewardDone
RemovalOperationProof:
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
 .db $00,$00,$01,$01,$03,$03,$03,$04,$04,$04,$05,$05,$06,$06,$06,$01
HouseHi:
 .db $00,$00,$00,$00,$00,$01,$01,$00,$01,$01,$00,$01,$00,$01,$01,$01
HouseX:
 .db $C0,$60,$E0,$60,$A0,$A0,$40,$60,$E0,$C0,$C0,$40,$90,$C0,$20,$80
HouseY:
 .db $40,$80,$20,$80,$40,$60,$A0,$20,$20,$A0,$20,$80,$50,$50,$90,$20
HouseBit:
 .db $02,$04,$02,$04,$02,$04,$10,$02,$04,$08,$02,$04,$02,$04,$08,$20
EnemyWorld:
 .db $00,$00,$01,$01,$02,$02,$03,$03,$03,$04,$04,$04,$05,$05,$05,$06,$06,$07,$07,$07,$07
EnemySlot:
 .db $02,$02,$02,$03,$02,$03,$02,$03,$04,$02,$03,$04,$02,$03,$04,$02,$03,$02,$03,$04,$05
EnemyType:
 .db $03,$0B,$04,$04,$03,$03,$05,$05,$05,$03,$03,$03,$03,$03,$03,$07,$07,$0E,$0D,$0F,$0E
EnemyBit:
 .db $08,$08,$08,$10,$40,$80,$20,$40,$80,$10,$20,$40,$10,$20,$40,$10,$20,$02,$04,$08,$10
PlantHi: .db 0,1
PlantX: .db 208,192
PlantY: .db 80,144
PlantBit: .db 16,32
PlantLayoutLo: .db 211,72
PlantLayoutHi: .db 190,190
PlantObjectsLo: .db 226,218
PlantObjectsHi: .db 208,208
; These paths are entered only from signature-verified native instructions.
; Preserve the intercepted stores even when the evidence guard rejects.
EndingEvidence:
 LDA $79E5
 CMP #4
 BNE EndingNotBowserStore
 LDA $79E2
 STA $7CF3
EndingNotBowserStore:
 LDA $79E5
 CMP #5
 BNE EndingGuard
 LDA $79E2
 STA $0100
EndingGuard:
 LDA Magic
 CMP #$AA
 BNE EndingEvidenceDone
 LDA Version
 CMP #9
 BNE EndingEvidenceDone
 LDA Bound
 CMP #1
 BNE EndingEvidenceDone
 LDA Phase
 CMP #2
 BNE EndingEvidenceDone
 LDA $0727
 CMP #7
 BNE EndingEvidenceDone
 LDA $0726
 BNE EndingEvidenceDone
 LDA $072B
 CMP #1
 BNE EndingEvidenceDone
 LDA $7978
 CMP #3
 BNE EndingEvidenceDone
 LDA $797A
 CMP #$C0
 BNE EndingEvidenceDone
 LDA $7976
 CMP #$70
 BNE EndingEvidenceDone
 LDA $79E5
 CMP #4
 BNE EndingRescue
 LDA EndingPhase
 BNE EndingEvidenceDone
 LDA #1
 STA EndingPhase
 STA EndingVersion
 RTS
EndingRescue:
 CMP #5
 BNE EndingExit
 LDA EndingPhase
 CMP #1
 BNE EndingEvidenceDone
 LDA $078D
 BEQ EndingEvidenceDone
 LDA $0713
 BNE EndingEvidenceDone
 INC EndingPhase
 RTS
EndingExit:
 LDA EndingPhase
 CMP #2
 BNE EndingEvidenceDone
 LDA $D5
 CMP #7
 BNE EndingEvidenceDone
 INC EndingPhase
EndingEvidenceDone:
 RTS
; M17 presentation predicate: no grants, receipts or completion writes.
; $7AA9 is transient visual selection, outside all authoritative snapshots.
VisualDispatch:
 JSR VisualMatch
 LDA #0
 ADC #0
 STA $7AA9
 LDA $79E5
 CMP #8
 BEQ VisualHouseDraw
 RTS
VisualHouseDraw:
 TSX
 LDA $0105,X
 TAX
 LDA $0669,X
 TAX
 LDY $79E4
 LDA $7AA9
 BEQ VisualHouseVanilla
 LDA #$AB
 STA $0201,Y
 LDA #$AD
 STA $0205,Y
 LDA #3
 STA $0202,Y
 STA $0206,Y
 RTS
VisualHouseVanilla:
 LDA VisualHouseLeft-1,X
 STA $0201,Y
 LDA VisualHouseRight-1,X
 STA $0205,Y
 LDA #3
 STA $0202,Y
 LDA VisualHouseAttrs-1,X
 STA $0206,Y
 RTS
; Original resident item pattern indices, independently checked against PRG002.
VisualHouseLeft: .db $85,$87,$9D,$81,$83,$8B,$B5,$91,$A9,$95,$99,$A1,$89
VisualHouseRight: .db $85,$87,$9F,$81,$83,$8B,$B7,$93,$A9,$97,$9B,$A3,$8D
VisualHouseAttrs: .db $43,$43,$03,$43,$43,$43,$03,$03,$43,$03,$03,$03,$03
VisualMatch:
 LDA $9F1B
 AND #3
 BEQ VisualNo
 CMP #2
 BNE VisualProduction
 LDA $7AAA ; dedicated offline ROM only: volatile presentation switch
 BEQ VisualNo
VisualProduction:
 LDA Bound
 CMP #1
 BNE VisualNo
 LDA Phase
 CMP #2
 BNE VisualNo
 LDA $0726
 BNE VisualNo
 LDA $072B
 CMP #1
 BNE VisualNo
 LDA $79E5
 CMP #8
 BNE VisualTreasure
 LDA $070A
 CMP #7
 BNE VisualNo
 LDX #15
VisualHouseMatch:
 LDA HouseWorld,X
 CMP $0727
 BNE VisualHouseNext
 LDA HouseHi,X
 CMP $7978
 BNE VisualHouseNext
 LDA HouseX,X
 CMP $797A
 BNE VisualHouseNext
 LDA HouseY,X
 CMP $7976
 BNE VisualHouseNext
 CPX #15
 BNE VisualYes
 LDA $9F3C
 BNE VisualYes
VisualNo:
 CLC
 RTS
VisualYes:
 SEC
 RTS
VisualHouseNext:
 DEX
 BPL VisualHouseMatch
 CLC
 RTS
VisualTreasure:
 LDA $0727
 CMP #7
 BEQ VisualHand
 CMP #6
 BEQ VisualPlant
 LDA $0713
 BNE VisualNo
 LDA $79E6
 BEQ VisualNo
 LDA $79E7
 CMP $0727
 BNE VisualNo
 LDA $1E
 CMP $79EA
 BNE VisualNo
 LDA $7963
 CMP $79EB
 BEQ VisualYes
 CLC
 RTS
VisualHand:
 LDA $0713
 CMP #1
 BNE VisualNo
 LDA $070A
 CMP #11
 BNE VisualNo
 LDA $7963
 CMP #3
 BNE VisualNo
 LDA $7978
 CMP #1
 BNE VisualNo
 LDA $7976
 CMP #$70
 BNE VisualNo
 LDA $7EB9
 CMP #$17
 BNE VisualNo
 LDA $7EBA
 CMP #$BE
 BNE VisualNo
 LDA $7EBB
 CMP #$CF
 BNE VisualNo
 LDA $7EBC
 CMP #$D0
 BNE VisualNo
 LDX #2
VisualHandLoop:
 LDA HandX,X
 CMP $797A
 BEQ VisualYes
 DEX
 BPL VisualHandLoop
 CLC
 RTS
VisualPlant:
 LDA $0713
 CMP #1
 BNE VisualPlantNo
 LDA $070A
 CMP #5
 BNE VisualPlantNo
 LDA $79E7
 CMP #6
 BNE VisualPlantNo
 LDX #1
VisualPlantLoop:
 LDA PlantHi,X
 CMP $7978
 BNE VisualPlantNext
 LDA PlantX,X
 CMP $797A
 BNE VisualPlantNext
 LDA PlantY,X
 CMP $7976
 BNE VisualPlantNext
 LDA PlantLayoutLo,X
 CMP $7EB9
 BNE VisualPlantNext
 LDA PlantLayoutHi,X
 CMP $7EBA
 BNE VisualPlantNext
 LDA PlantObjectsLo,X
 CMP $7EBB
 BNE VisualPlantNext
 LDA PlantObjectsHi,X
 CMP $7EBC
 BNE VisualPlantNext
 LDA PlantBit,X
 CMP $79E6
 BNE VisualPlantNext
 SEC
 RTS
VisualPlantNext:
 DEX
 BPL VisualPlantLoop
VisualPlantNo:
 CLC
 RTS
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
BowserDefeatStub:
 PHP
 PHA
 TXA
 PHA
 TYA
 PHA
 LDX #4
 JMP RewardCall
PeachRescueStub:
 PHP
 PHA
 TXA
 PHA
 TYA
 PHA
 LDX #5
 JMP RewardCall
EndingReceiptStub:
 PHP
 PHA
 TXA
 PHA
 TYA
 PHA
 LDX #6
 JMP RewardCall
EndingExitStub:
 JSR EndingReceiptStub
 JMP $BB7C
RewardStubsEnd:

; Source PRG025 ends with curtain palette data at D518; remainder is empty.
; MMC3 maps this bank at A000 for the bounded M17 extension (native origin C000).
 .bank 25
 .org $B520
ProgressionExtension:
 CPX #17
 BNE ExtensionNotSize
 JMP MenuTextSize
ExtensionNotSize:
 CPX #16
 BNE ExtensionNotRestore
 JMP MenuRestoreRow
ExtensionNotRestore:
 CPX #15
 BNE ExtensionNotBorder
 JMP MenuBorderDraw
ExtensionNotBorder:
 CPX #9
 BCC ProgressionOldEntry
 JMP StackDispatch
ProgressionOldEntry:
 CPX #8
 BEQ ProgressionSync
 JMP ProgressionUI
ProgressionSync:
 LDA Phase
 CMP #2
 BNE ProgressionRejected
 LDA GrantHammers
 AND #$D1
 BNE ProgressionRejected
 LDA $9F3C
 BNE GrantRegional
 LDA GrantHammers
 BNE ProgressionRejected
GrantRegional:
 LDA GrantHammers
 AND Hammers
 CMP Hammers
 BNE ProgressionRejected
 LDA GrantStars
 CMP Stars
 BCC ProgressionRejected
 CMP $9F3F
 BCC GrantCounts
 BNE ProgressionRejected
GrantCounts:
 LDX #7
GrantCheckValidate:
 TXA
 TAY
 LDA $9F3C
 BEQ GrantLegacyCheck
 TYA
 CLC
 ADC #8
 TAY
GrantLegacyCheck:
 LDA GrantChecks,X
 CMP ProgressionWorldTotals,Y
 BCC GrantCheckNext
 BNE ProgressionRejected
GrantCheckNext:
 DEX
 BPL GrantCheckValidate
 LDA #0
 STA CheckTotal
 LDX #7
GrantCheckCopy:
 LDA GrantChecks,X
 STA CheckCounts,X
 CLC
 ADC CheckTotal
 STA CheckTotal
 DEX
 BPL GrantCheckCopy
 LDA GrantHammers
 STA Hammers
 LDA GrantStars
 STA Stars
 LDA GrantPendingLo
 STA PendingLo
 LDA GrantPendingHi
 STA PendingHi
 LDA #1
 STA Result
ProgressionRejected:
 RTS
ProgressionUI:
 LDA $18
 AND #$40
 BEQ ProgressionMove
 JMP ProgressionClose
ProgressionMove:
 LDA $18
 AND #$0F
 BEQ ProgressionAction
 LDA $18
 AND #$0A
 BEQ ProgressionNext
 DEC Selected
 JMP ProgressionWrap
ProgressionNext:
 INC Selected
ProgressionWrap:
 LDA Selected
 CMP #$FF
 BNE ProgressionWrapHigh
 LDA #4
 BNE ProgressionWrapped
ProgressionWrapHigh:
 CMP #5
 BCC ProgressionWrapped
 LDA #0
ProgressionWrapped:
 STA Selected
ProgressionAction:
 LDA Selected
 CMP #1
 BNE ProgressionDraw
 LDA $18
 AND #$80
 BEQ ProgressionDraw
 LDA $9F3C
 BEQ ProgressionDraw
 LDX $0727
 LDA Hammers
 AND ProgressionBits,X
 BEQ ProgressionDraw
 LDA $0300
 BNE ProgressionDraw
 JSR ProgressionClose
 LDA #2
 RTS
ProgressionClose:
 LDA $0300
 BNE ProgressionDraw
 LDA #0
 STA Menu
 STA $17
 STA $18
 LDA #1
 STA Release
 LDA #$80
 STA MenuPart
 LDA #1
 RTS
ProgressionDraw:
 LDA $0300
 BNE ProgressionHold
 LDA MenuPart
 CMP #6
 BCC ProgressionPartOK
 LDA #0
 STA MenuPart
ProgressionPartOK:
 TAX
 LDA ProgressionPPULo,X
 STA $0302
 LDA #$2B
 STA $0301
 LDA #10
 STA $0303
 LDA Selected
 ASL A
 TAX
 LDA ProgressionTexts,X
 STA $00
 LDA ProgressionTexts+1,X
 STA $01
 LDA Selected
 CMP #1
 BNE ProgressionChooseStars
 LDA $9F3C
 BNE ProgressionTextReady
 LDA #LOW(ProgressionLegacyText)
 STA $00
 LDA #HIGH(ProgressionLegacyText)
 STA $01
 JMP ProgressionTextReady
ProgressionChooseStars:
 CMP #2
 BNE ProgressionTextReady
 LDA $9F3D
 ASL A
 TAX
 LDA ProgressionStarTexts,X
 STA $00
 LDA ProgressionStarTexts+1,X
 STA $01
ProgressionTextReady:
 LDX MenuPart
 LDY ProgressionOffsets,X
 LDX #0
ProgressionTextLoop:
 LDA [$00],Y
 STA $0304,X
 INY
 INX
 CPX #10
 BNE ProgressionTextLoop
 JSR ProgressionValues
 JSR MenuTextSize
 INC MenuPart
ProgressionHold:
 LDA #0
 STA $17
 STA $18
 LDA #1
 RTS
ProgressionValues:
 LDA Selected
 CMP #4
 BNE ProgressionOtherValues
 JMP TrackerValues
ProgressionOtherValues:
 LDA MenuPart
 CMP #4
 BNE ProgressionMainValues
 LDA Selected
 CMP #1
 BNE ProgressionExtraDone
 LDA $9F3C
 BEQ ProgressionExtraDone
 LDX #0
ProgressionHammerFlags:
 LDY ProgressionHammerWorlds,X
 LDA Hammers
 AND ProgressionBits,Y
 BEQ ProgressionHammerMissing
 TYA
 CLC
 ADC #$F1
 JMP ProgressionHammerFlagStore
ProgressionHammerMissing:
 LDA #$FE
ProgressionHammerFlagStore:
 STA $0305,X
 INX
 CPX #4
 BNE ProgressionHammerFlags
ProgressionExtraDone:
 RTS
ProgressionMainValues:
 LDA MenuPart
 CMP #3
 BEQ ProgressionValuesReady
 RTS
ProgressionValuesReady:
 LDA Selected
 BNE ProgressionNotPasses
 LDX #1
ProgressionPassLoop:
 LDA #$FE
 LDY Unlock
 TYA
 AND ProgressionBits,X
 BEQ ProgressionMissing
 TXA
 CLC
 ADC #$F1
 JMP ProgressionPassStore
ProgressionMissing:
 LDA #$FE
ProgressionPassStore:
 STA $0303,X
 INX
 CPX #8
 BNE ProgressionPassLoop
 RTS
ProgressionNotPasses:
 CMP #1
 BNE ProgressionNotHammer
 LDA $9F3C
 BEQ ProgressionValueDone
 LDA $0727
 CLC
 ADC #$F1
 STA $0305
 LDX $0727
 LDA Hammers
 AND ProgressionBits,X
 BEQ ProgressionValueDone
 LDA #$BE
 STA $0308
 LDA #$C6
 STA $0309
 LDA #$BD
 STA $030A
 LDA #$B4
 STA $030B
 LDA #$B3
 STA $030C
 LDA #$FE
 STA $030D
 RTS
ProgressionNotHammer:
 CMP #2
 BNE ProgressionPending
 LDA $9F3D
 BEQ ProgressionValueDone
 LDA Stars
 LDX #0
 JSR ProgressionDecimal
 LDA $9F3E
 LDX #4
 JMP ProgressionDecimal
ProgressionPending:
 LDA PendingHi
 BEQ ProgressionPendingLow
 LDA #$FF
ProgressionPendingLow:
 ORA PendingLo
 LDX #0
 JMP ProgressionDecimal
ProgressionValueDone:
 RTS
; Three digits, saturated at255 for display; delivery count itself is16-bit.
ProgressionDecimal:
 LDY #$F0
ProgressionHundreds:
 CMP #100
 BCC ProgressionHundredsDone
 SEC
 SBC #100
 INY
 BNE ProgressionHundreds
ProgressionHundredsDone:
 PHA
 TYA
 STA $0304,X
 PLA
 INX
 LDY #$F0
ProgressionTens:
 CMP #10
 BCC ProgressionTensDone
 SEC
 SBC #10
 INY
 BNE ProgressionTens
ProgressionTensDone:
 PHA
 TYA
 STA $0304,X
 PLA
 INX
 CLC
 ADC #$F0
 STA $0304,X
 RTS
ProgressionBits: .db 1,2,4,8,16,32,64,128
ProgressionHammerWorlds: .db 1,2,3,5
ProgressionPPULo: .db $22,$2C,$36,$42,$4C,$56
ProgressionOffsets: .db 0,10,20,30,40,50
ProgressionTexts:
 .dw ProgressionPassText,ProgressionHammerText,ProgressionStarText,ProgressionPendingText,ProgressionTrackerText
ProgressionStarTexts:
 .dw ProgressionStarOffText,ProgressionWorld8Text,ProgressionStarText
; Project-authored native status-panel text.
ProgressionPassText:
 .db $C6,$BE,$C1,$BB,$B3,$FE,$BF,$B0,$C2,$C2,$B4,$C2,$FE,$FE,$FE,$B1,$FE,$B2,$BB,$BE,$C2,$B4,$FE,$F1,$FE,$BE,$B5,$F5,$FE,$FE,$F2,$F3,$F4,$F5,$F6,$F7,$F8,$FE,$FE,$B0,$C1,$C1,$BE,$C6,$C2,$FE,$B2,$B7,$B0,$BD,$B6,$B4,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE
ProgressionHammerText:
 .db $C1,$B4,$B6,$B8,$BE,$BD,$B0,$BB,$FE,$B7,$B0,$BC,$BC,$B4,$C1,$FE,$B0,$FE,$C4,$C2,$B4,$FE,$FE,$F2,$FE,$BE,$B5,$F5,$FE,$FE,$C6,$F1,$FE,$FE,$BB,$BE,$B2,$BA,$B4,$B3,$FE,$F2,$F3,$F4,$F6,$FE,$BE,$C6,$BD,$FE,$B1,$FE,$B2,$BB,$BE,$C2,$B4,$FE,$FE,$FE,$FE
ProgressionStarText:
 .db $C2,$C3,$B0,$C1,$FE,$B6,$B0,$C3,$B4,$FE,$B1,$BE,$C6,$C2,$B4,$C1,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$F3,$FE,$BE,$B5,$F5,$FE,$FE,$F0,$F0,$F0,$FE,$F0,$F0,$F0,$FE,$C1,$B4,$C0,$C4,$B8,$C1,$B4,$B3,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE
ProgressionPendingText:
 .db $B8,$C3,$B4,$BC,$FE,$B3,$B4,$BB,$B8,$C5,$B4,$C1,$C8,$FE,$FE,$B1,$FE,$B2,$BB,$BE,$C2,$B4,$FE,$F4,$FE,$BE,$B5,$F5,$FE,$FE,$F0,$F0,$F0,$FE,$FE,$B0,$C1,$C1,$BE,$C6,$C2,$FE,$B2,$B7,$B0,$BD,$B6,$B4,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE

ProgressionLegacyText:
 .db $BB,$B4,$B6,$B0,$B2,$C8,$FE,$B7,$B0,$BC,$BC,$B4,$C1,$C2,$FE,$B1,$FE,$B2,$BB,$BE,$C2,$B4,$FE,$F2,$FE,$BE,$B5,$F5,$FE,$FE,$C4,$C2,$B4,$FE,$BD,$BE,$C1,$BC,$B0,$BB,$FE,$B8,$BD,$C5,$B4,$BD,$C3,$BE,$C1,$C8,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE
ProgressionStarOffText:
 .db $C2,$C3,$B0,$C1,$FE,$B7,$C4,$BD,$C3,$FE,$BE,$B5,$B5,$FE,$FE,$B1,$FE,$B2,$BB,$BE,$C2,$B4,$FE,$F3,$FE,$BE,$B5,$F5,$FE,$FE,$BD,$BE,$FE,$B5,$C1,$B0,$B6,$BC,$B4,$BD,$C3,$C2,$FE,$C1,$B4,$C0,$C4,$B8,$C1,$B4,$B3,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE
ProgressionWorld8Text:
 .db $C2,$C3,$B0,$C1,$FE,$B6,$B0,$C3,$B4,$FE,$C6,$BE,$C1,$BB,$B3,$FE,$F8,$FE,$FE,$FE,$FE,$FE,$FE,$F3,$FE,$BE,$B5,$F5,$FE,$FE,$F0,$F0,$F0,$FE,$F0,$F0,$F0,$FE,$C1,$B4,$C0,$C4,$B8,$C1,$B4,$B3,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE
TrackerValues:
 LDA MenuPart
 BNE TrackerNumbers
 LDA $0727
 CLC
 ADC #$F1
 STA $030B
 RTS
TrackerNumbers:
 CMP #3
 BNE TrackerOverall
 LDY $0727
 LDA CheckCounts,Y
 LDX #0
 JSR ProgressionDecimal
 LDY $0727
 JSR TrackerWorldTotal
 LDX #6
 JMP ProgressionDecimal
TrackerOverall:
 CMP #5
 BNE TrackerDone
 LDA CheckTotal
 LDX #0
 JSR ProgressionDecimal
 LDA $9F1A
 LDX #5
 JMP ProgressionDecimal
TrackerDone:
 RTS
TrackerWorldTotal:
 LDA $9F3C
 BEQ TrackerLegacyTotal
 TYA
 CLC
 ADC #8
 TAY
TrackerLegacyTotal:
 LDA ProgressionWorldTotals,Y
 RTS
ProgressionWorldTotals:
; @M17_TRACKER_TOTALS
ProgressionTrackerText:
 ; WORLD n / PHYSICAL / TOTAL; two three-digit count OF total pairs below.
 .db $FE,$C6,$BE,$C1,$BB,$B3,$FE,$F1,$FE,$FE,$BF,$B7,$C8,$C2,$B8,$B2,$B0,$BB,$FE,$FE,$C3,$BE,$C3,$B0,$BB,$FE,$FE,$FE,$FE,$FE
 .db $F0,$F0,$F0,$FE,$BE,$B5,$F0,$F0,$F0,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$FE,$F0,$F0,$F0,$BE,$B5,$F0,$F0,$F0,$FE,$FE

; Native inventory authority, storage v1. No host writes quantity or slot state.
StackDispatch:
 LDA #1
 STA StackBusy
 JSR StackOperation
 PHA
 LDA #0
 STA StackBusy
 PLA
 RTS
StackOperation:
 CPX #11
 BNE StackDispatchNotDraw
 JMP StackDraw
StackDispatchNotDraw:
 CPX #14
 BNE StackDispatchOld
 JMP StackUseGuard
StackDispatchOld:
 CPX #9
 BNE StackNotGrant
 JMP StackNativeGrant
StackNotGrant:
 CPX #10
 BNE StackNotConsume
 JMP StackConsume
StackNotConsume:
 CPX #12
 BNE StackCold
 JMP StackTick
StackCold:
 LDA #0
 LDX #31
StackClear:
 STA StackCounts,X
 STA StackItem,X
 DEX
 BPL StackClear
 LDA $9F1B
 AND #4
 STA StackMode
 LDA #1
 STA StackFormat
 RTS
StackUseGuard:
 LDA $7D80,Y
 STA StackTemp
 LDA StackMode
 BEQ StackUseReady
 LDA StackTemp
 BEQ StackUseReady
 CMP #14
 BCS StackUseBad
 ASL A
 TAX
 LDA StackCounts,X
 ORA StackCounts+1,X
 BEQ StackUseBad
 LDA StackTemp
 CMP #9
 BNE StackUseReady
 LDA $03F2
 CMP #$FF
 BNE StackUseReady
 ; Native INC queued Stars would wrap at255; reject before effect/consumption.
 LDA $04F6
 ORA #$80
 STA $04F6
 LDA #0
 RTS
StackUseBad:
 JSR StackFault
 LDA #0
 RTS
StackUseReady:
 LDA StackTemp
 RTS
StackFault:
 LDA #16
 STA Error
 LDA #$FF
 STA Phase
 LDA #3
 STA StackResult
 RTS
StackAdvance:
 LDA StackSerial
 AND StackSerial+1
 AND StackSerial+2
 AND StackSerial+3
 CMP #$FF
 BEQ StackFault
 INC StackSerial
 BNE StackAdvanceOK
 INC StackSerial+1
 BNE StackAdvanceOK
 INC StackSerial+2
 BNE StackAdvanceOK
 INC StackSerial+3
StackAdvanceOK:
 LDA #1
 RTS
; StackArg is independent of the AP staging fields.
StackAdd:
 LDA StackArg
 BEQ StackFault
 CMP #14
 BCS StackFault
 CMP #11
 BNE StackTypeOK
 LDA $9F3C
 BNE StackGrantDenied
StackTypeOK:
 LDA StackArg
 ASL A
 TAX
 LDA StackCounts,X
 AND StackCounts+1,X
 CMP #$FF
 BEQ StackFull
 LDA StackCounts,X
 ORA StackCounts+1,X
 BEQ StackCreate
 LDY #0
StackFind:
 LDA $7D80,Y
 CMP StackArg
 BEQ StackIncrement
 INY
 CPY #28
 BNE StackFind
 JMP StackFault
StackCreate:
 LDY #0
StackEmpty:
 LDA $7D80,Y
 BEQ StackNew
 CMP StackArg
 BEQ StackFault
 INY
 CPY #28
 BNE StackEmpty
 JMP StackFault
StackNew:
 STY StackSlot
 JSR StackAdvance
 CMP #1
 BNE StackAddDone
 LDY StackSlot
 LDA StackArg
 STA $7D80,Y
 JMP StackIncrementOnly
StackIncrement:
 JSR StackAdvance
 CMP #1
 BNE StackAddDone
StackIncrementOnly:
 INC StackCounts,X
 BNE StackAdded
 INC StackCounts+1,X
StackAdded:
 LDA #1
StackAddDone:
 RTS
StackFull:
 LDA #2
 RTS
StackGrantDenied:
 LDA #0
 RTS
StackNativeGrant:
 LDA StackMode
 BNE StackNativeActive
 ; Vanilla shared insertion, including original last-slot overwrite behavior.
 LDY $0726
 BEQ StackVanillaMario
 LDY #35
StackVanillaMario:
 LDX #27
StackVanillaFind:
 LDA $7D80,Y
 BEQ StackVanillaInsert
 INY
 DEX
 BNE StackVanillaFind
StackVanillaInsert:
 LDA StackArg
 STA $7D80,Y
 RTS
StackNativeActive:
 LDA $0726
 BNE StackGrantFault
 LDA $072B
 CMP #1
 BNE StackGrantFault
 LDA StackPending
 BNE StackGrantFault
 JSR StackAdd
 CMP #2
 BNE StackNativeDone
 JSR StackAdvance
 CMP #1
 BNE StackNativeDone
 LDA StackArg
 STA StackPending
StackNativeDone:
 RTS
StackGrantFault:
 JMP StackFault
StackConsume:
 LDA StackMode
 BNE StackConsumeActive
 LDA #0
 RTS
StackConsumeActive:
 LDA $03E7
 CLC
 ADC $03E9
 TAY
 CPY #28
 BCS StackGrantFault
 LDA $7D80,Y
 BEQ StackGrantFault
 CMP #14
 BCS StackGrantFault
 ASL A
 TAX
 LDA StackCounts,X
 ORA StackCounts+1,X
 BEQ StackGrantFault
 JSR StackAdvance
 CMP #1
 BNE StackKeep
 LDA StackCounts,X
 BNE StackSubtract
 DEC StackCounts+1,X
StackSubtract:
 DEC StackCounts,X
 LDA StackCounts,X
 ORA StackCounts+1,X
 BEQ StackRemove
StackKeep:
 LDA #1
 RTS
StackRemove:
 LDA #0
 RTS
StackTickEarlyDone:
 RTS
StackTick:
 LDA StackMode
 BEQ StackTickEarlyDone
 LDA Bound
 BEQ StackTickEarlyDone
 LDA Phase
 CMP #2
 BNE StackTickEarlyDone
 LDA StackPending
 BEQ StackAP
 STA StackArg
 JSR StackAdd
 CMP #1
 BNE StackAP
 LDA #0
 STA StackPending
StackAP:
 LDA StackPublish
 BEQ StackTickDone
 LDA #0
 STA StackPublish
 LDA StackTicket
 ORA StackTicket+1
 ORA StackTicket+2
 ORA StackTicket+3
 BEQ StackTicketBad
 LDX #3
StackTicketCompare:
 LDA StackTicket,X
 CMP StackAck,X
 BCC StackTicketBad
 BNE StackTicketNew
 DEX
 BPL StackTicketCompare
 LDA StackItem
 CMP StackAckType
 BNE StackTicketBad
 LDA #1
 STA StackResult
 RTS
StackTicketNew:
 LDA StackItem
 STA StackArg
 JSR StackAdd
 STA StackResult
 CMP #1
 BNE StackTickDone
 LDX #3
StackCommit:
 LDA StackTicket,X
 STA StackAck,X
 DEX
 BPL StackCommit
 LDA StackItem
 STA StackAckType
 ASL A
 TAX
 LDA StackCounts,X
 STA StackAfter
 SEC
 SBC #1
 STA StackBefore
 LDA StackCounts+1,X
 STA StackAfter+1
 SBC #0
 STA StackBefore+1
 LDX #3
StackReceiptCopy:
 LDA StackSerial,X
 STA StackReceiptSerial,X
 DEX
 BPL StackReceiptCopy
StackTickDone:
 RTS
StackTicketBad:
 JMP StackFault

 ; Original border art extends down one tile row while inventory is fully open.
; No CHR or OAM ownership changes. Idle-open row writes fit70 of107 queue bytes.
StackDrawEarlyDone:
 RTS
StackDraw:
 LDA StackMode
 BEQ StackDrawEarlyDone
 LDA $070A
 ORA $0300
 BNE StackDrawEarlyDone
 LDA $05F2
 BNE StackDrawOpen
 JMP StackDrawClear
StackDrawOpen:
 LDA $9F1B
 AND #3
 CMP #2
 BNE StackDrawProduction
 LDA $7AAE
 BNE StackDrawEarlyDone
StackDrawProduction:
 LDA $03E6
 CMP #4
 BNE StackDrawEarlyDone
 LDA $03ED
 ORA $DA
 ORA $18
 BNE StackDrawEarlyDone
 LDX #31
StackRowFill:
 LDA #$FC
 CPX #1
 BCC StackRowEdge
 CPX #30
 BCS StackRowEdge
 LDA #$FE
StackRowEdge:
 STA $0304,X
 LDA #$FC
 CPX #2
 BCC StackBorderEdge
 CPX #30
 BCS StackBorderEdge
 LDA #$A4
StackBorderEdge:
 STA $0327,X
 DEX
 BPL StackRowFill
 LDA #$A6
 STA $0305
 LDA #$A7
 STA $0322
 LDA #$A8
 STA $0328
 LDA #$A5
 STA $0345
 LDA #$2B
 STA $0301
 STA $0324
 LDA #$60
 STA $0302
 LDA #$80
 STA $0325
 LDA #32
 STA $0303
 STA $0326
 LDA #0
 STA $0347
 STA StackSlot
 LDA #70
 STA $0300
 LDX #12
 JMP StackDrawNext
StackDrawClear:
 ; Clear only alongside the light palette phase, not native 32-tile flip rows.
 ; Buffer capacity is not a vblank execution-time budget.
 LDA $03E6
 CMP #2
 BEQ StackDrawClearReady
 RTS
StackDrawClearReady:
 LDA #$2B
 STA $0301
 LDA #$80
 STA $0302
 LDA #$60 ; native repeat command:32 black tiles
 STA $0303
 LDA #$FC
 STA $0304
 LDA #0
 STA $0305
 LDA #4
 STA $0300
 RTS
StackDrawNext:
 LDA #$FE
 STA $0301,X
 STA $0302,X
 STA $0303,X
 LDA $05F2
 BEQ StackDrawAdvance
 LDA $03E7
 CLC
 ADC StackSlot
 TAY
 LDA $7D80,Y
 BEQ StackDrawAdvance
 ASL A
 TAY
 LDA StackCounts+1,Y
 BNE StackDrawLarge
 LDA StackCounts,Y
 CMP #100
 BCS StackDrawLarge
 ; One unit is shown as1; blank tens below10.
 LDY #$F0
StackDrawTens:
 CMP #10
 BCC StackDrawDigits
 SEC
 SBC #10
 INY
 BNE StackDrawTens
StackDrawDigits:
 ORA #$F0
 STA $0302,X
 CPY #$F0
 BEQ StackDrawAdvance
 TYA
 STA $0301,X
 JMP StackDrawAdvance
StackDrawLarge:
 LDA #$F9
 STA $0301,X
 STA $0302,X
 LDA #$9B ; original exclamation:99! means at least100; no CHR replacement
 STA $0303,X
StackDrawAdvance:
 INX
 INX
 INX
 INC StackSlot
 LDA StackSlot
 CMP #7
 BNE StackDrawNext
StackDrawDone:
 RTS
 ; Text has30-byte logical rows, with28 visible tiles between inset borders.
MenuTextSize:
 LDA #0
 STA $030E
 LDA #13
 STA $0300
 LDA MenuPart
 CMP #2
 BEQ MenuTextShort
 CMP #5
 BNE MenuTextSized
MenuTextShort:
 LDA #8
 STA $0303
 LDA #0
 STA $030C
 LDA #11
 STA $0300
MenuTextSized:
 RTS
 ; Original PRG030 Video_DoStatusBar commands, one32-tile row per frame.
 ; Fixed bank remains mapped at8000. Dynamic fields and cards follow separately.
MenuRestoreRow:
 LDA MenuPart
 AND #3
 TAX
 LDA MenuRestoreLengths,X
 STA $0300
 TAY
 LDA #0
 STA $0301,Y
 DEY
 LDA MenuRestoreEnds,X
 TAX
MenuRestoreCopy:
 LDA $811B,X
 STA $0301,Y
 DEX
 DEY
 BPL MenuRestoreCopy
 INC MenuPart
 RTS
MenuRestoreLengths: .db 24,35,35,24
MenuRestoreEnds: .db 23,58,93,117
 ; Bounded border fragments: at most38 PPU writes including text.
MenuBorderDraw:
 LDA MenuPart
 BEQ MenuBorderDone
 CMP #5
 BCS MenuBorderDone
 LDA $0300
 CMP #11
 BEQ MenuBorderReady
 CMP #13
 BNE MenuBorderDone
MenuBorderReady:
 TAY
 LDX MenuPart
 DEX
 CLC
 ADC MenuBorderLengths,X
 STA $0300
 LDA MenuBorderOffsets,X
 TAX
MenuBorderCopy:
 LDA MenuBorder,X
 STA $0301,Y
 INX
 INY
 CMP #0
 BNE MenuBorderCopy
MenuBorderDone:
 RTS
MenuBorderLengths: .db 4,4,16,8
MenuBorderOffsets: .db 0,5,10,27
MenuBorder:
 .db $2B,$02,$5C,$A1,$00
 .db $2B,$62,$5C,$A4,$00
 .db $2B,$01,$01,$A0,$2B,$1E,$01,$A2
 .db $2B,$61,$01,$A8,$2B,$7E,$01,$A5,$00
 .db $2B,$21,$C2,$A6,$2B,$3E,$C2,$A7,$00
ProgressionExtensionEnd:

; PRG003 source-declared empty tail after the final RotoDisc routine.
 .bank 3
 .org $BFC0
TreasureVisual:
 JSR TreasureVisualCall
 LDA $7AA9
 BEQ TreasureVisualVanilla
 LDA #0
 TAY
 STA $0669,X
 LDA #3
 JMP TreasureVisualAttribute
TreasureVisualVanilla:
 LDA $7963
 TAY
 STA $0669,X
 LDA #2
TreasureVisualAttribute:
 STA $7FE7,X
 JMP $A346
TreasureVisualCall:
 PHP
 PHA
 TXA
 PHA
 TYA
 PHA
 LDX #7
 JMP RewardCall
TreasureVisualEnd:
