; M24.5 bounded native panel proof. Project-authored NESASM source.
; Cache $7000-$7217 is volatile map-only tile-memory scratch: original maps
; use at most four $1B0-byte pages below $6800. Never persistent authority.
 .inesprg 32
 .ineschr 0
 .inesmap 4
 .inesmir 0
Menu = $79DB
Release = $79DD
MenuPart = $79DF
UiState = $7AD0
UiRow = $7AD1
UiPage = $7AD2
UiAnchor = $7AD3
UiHeight = $7AD4
UiAttrRows = $7AD5
UiTotalRows = $7AD6
UiCamera = $7AD7
UiPending = $7AD8
UiGoal = $7AD9
UiParent = $7ADA
UiError = $7ADB
UiDestination = $7ADC
UiGoalPage = $7ADD
UiPageCount = $7ADE
UiBank = $7ADF
UiFlag = $7BE9
UiLo = $7BEA
UiHi = $7BEB
UiCount = $7BEC
UiCacheLo = $7BED
UiCacheHi = $7BEE
UiMask = $7BEF
UiTileY = $7BF0
UiTileX = $7BF1
UiColumn = $7BF2
UiAccum = $7BF3
UiFirstCount = $7BF4
UiBufferOffset = $7BF5
UiStartMeta = $7BF6
UiAttrColumn = $7BF7
UiAttrRow = $7BF8
UiAttrCount = $7BF9
UiTop = $7BFA
UiBottom = $7BFB
UiValue = $7BFC
UiValueColumn = $7BFD
UiValueMask = $7BFE

; @NATIVE_CONSTANTS
 .bank 26
 .org NativeMenuControl
UiControlHook:
 LDA $79FB
 BEQ UiControlIdle
 LDA $03ED
 BEQ UiToolFinished
 JSR $A7C0
 JMP UiControlConsume
UiToolFinished:
 LDA #0
 STA $79FB
 LDA #1
 STA Release
 JMP UiControlConsume
UiControlIdle:
 LDA #53
 STA UiBank
 LDX #7
 JSR NativeBankCall
 PHA
 LDA #25
 STA UiBank
 PLA
 CMP #2
 BNE UiControlReturn
 LDA #1
 STA $79FB
 JSR $A6BB
UiControlConsume:
 LDA #0
 STA $17
 STA $18
 LDA #1
UiControlReturn:
 RTS
UiControlHookEnd:
 .org NativeMenuStatus
UiStatusHook:
 LDA Menu
 ORA MenuPart
 BNE UiStatusOwned
 LDA Release
 BNE UiStatusDone
 JMP $B44A
UiStatusOwned:
 JSR UiCull
UiStatusDone:
 RTS
UiStatusHookEnd:

; Main-thread helpers replace retired menu drawing code. NMI is untouched.
 .org NativeMenuRender
UiHelpers:
UiColdInit:
 LDA #0
 STA UiState
 STA UiFlag
 STA UiPending
 STA UiGoal
 STA UiParent
 LDA #25
 STA UiBank
 LDX #13
 JMP NativeBankCall
; Cull only sprites intersecting the solid window. No OAM slots are added.
; Map_DrawPlayer has already run when MenuStatus reaches this routine.
UiCull:
 LDX #0
UiCullLoop:
 LDA $0200,X
 CMP UiTop
 BCC UiCullNext
 CMP UiBottom
 BCS UiCullNext
 LDA $0203,X
 CMP #9
 BCC UiCullNext
 CMP #240
 BCS UiCullNext
 LDA #$F8
 STA $0200,X
UiCullNext:
 INX
 INX
 INX
 INX
 BNE UiCullLoop
 RTS
UiHelpersEnd:

 .bank 53
 .org $B520
UiEntry:
 JMP UiControl
 .db "M245-UI-RC3"
UiEntryEnd:
 .org $A000
UiControl:
 LDA UiState
 BNE UiOwned
 LDA Release
 BEQ UiOpenCheck
 LDA $17
 BNE UiHold
 LDA #0
 STA Release
 JMP UiHold
UiOpenCheck:
 LDA $18
 AND #$30
 BEQ UiNone
 JSR UiSafe
 BCS UiNone
 LDA $FD
 AND #$0F
 BNE UiNone
 LDA #2
 LDX $18
 TXA
 AND #$10
 BNE UiOpenStart
 LDA #1
 JMP UiOpenMode
UiOpenStart:
 LDA #2
UiOpenMode:
 STA Menu
 LDA $0727
 STA $79DC
 LDA #0
 STA UiPage
 STA UiParent
 STA UiGoal
 STA UiPending
 STA UiError
 JSR UiConfigure
UiBegin:
 LDA #1
 STA UiState
 STA Release
 LDA #$80
 STA MenuPart
 LDA #0
 STA UiRow
 STA UiFlag
UiOwned:
 JSR UiChr
 LDA $0300
 BNE UiHold
 LDA UiState
 CMP #1
 BEQ UiCapture
 CMP #2
 BEQ UiDraw
 CMP #4
 BNE UiNotRestore
 JMP UiRestore
UiNotRestore:
 JMP UiLive
UiNone:
 LDA #0
 RTS
UiHold:
 LDA #0
 STA $17
 STA $18
 LDA #1
 RTS

UiCapture:
 JSR UiDescriptor
 JSR UiMapSnapshot
 INC UiRow
 LDA UiRow
 CMP UiTotalRows
 BCC UiCaptureDone
 LDA #0
 STA UiRow
 LDA #2
 STA UiState
UiCaptureDone:
 JMP UiHold

UiDraw:
 JSR UiDescriptor
 LDA UiRow
 CMP UiHeight
 BCS UiDrawAttribute
 LDX UiPage
 LDA Menu
 CMP #1
 BNE UiDrawCategory
 LDX #4
UiDrawCategory:
 LDA UiPageBases,X
 CLC
 ADC UiRow
 TAX
UiDrawPointer:
 LDA UiRowsLo,X
 STA $00
 LDA UiRowsHi,X
 STA $01
 LDY #0
UiComposeLoop:
 LDA [$00],Y
 STA $7420,Y
 INY
 CPY #28
 BCC UiComposeLoop
 JSR UiValues
 LDA #$20
 STA $00
 LDA #$74
 STA $01
 JMP UiWrite
UiDrawAttribute:
 LDA UiCacheLo
 STA $00
 LDA UiCacheHi
 STA $01
 JMP UiWrite
UiRestore:
 JSR UiDescriptor
 LDA UiCacheLo
 STA $00
 LDA UiCacheHi
 STA $01
UiWrite:
 LDA UiHi
 STA $0301
 LDA UiLo
 STA $0302
 LDA UiFirstCount
 STA $0303
 LDY #0
 LDA #3
 STA UiBufferOffset
UiWriteLoop:
 LDA [$00],Y
 LDX UiState
 CPX #2
 BNE UiWriteByte
 LDX UiRow
 CPX UiHeight
 BCC UiWriteByte
 ; Own only the interior 2x2 quadrants. Preserve native edge colors.
 JSR UiAttributeMask
UiMaskY:
 STA UiMask
 LDA UiStartMeta
 AND #1
 BEQ UiMaskDone
 CPY #0
 BNE UiMaskRight
 LDA UiMask
 AND #$CC
 STA UiMask
UiMaskRight:
 TYA
 CLC
 ADC #1
 CMP UiAttrCount
 BNE UiMaskDone
 LDA UiMask
 AND #$33
 STA UiMask
UiMaskDone:
 LDA UiMask
 EOR #$FF
 AND [$00],Y
UiWriteByte:
 LDX UiBufferOffset
 STA $0301,X
 INC UiBufferOffset
 INY
 CPY UiFirstCount
 BNE UiWriteContinue
 CPY UiCount
 BEQ UiWriteContinue
 ; A screen-anchored row may cross the horizontal nametable boundary.
 LDX UiBufferOffset
 LDA UiHi
 EOR #4
 STA $0301,X
 LDA UiLo
 AND #$E0
 CPY #28
 BEQ UiWriteSecondLow
 LDA UiRow
 CMP UiHeight
 BCC UiWriteSecondPattern
 LDA UiLo
 AND #$F8
 JMP UiWriteSecondLow
UiWriteSecondPattern:
 LDA UiLo
 AND #$E0
UiWriteSecondLow:
 STA $0302,X
 LDA UiCount
 SEC
 SBC UiFirstCount
 STA $0303,X
 INX
 INX
 INX
 STX UiBufferOffset
UiWriteContinue:
 CPY UiCount
 BEQ UiWriteLoopDone
 JMP UiWriteLoop
UiWriteLoopDone:
 LDA #0
 LDX UiBufferOffset
 STA $0301,X
 TXA
 STA $0300
 INC UiRow
 LDA UiRow
 CMP UiTotalRows
 BCC UiWriteDone
 LDA UiState
 CMP #4
 BEQ UiRestored
 LDA #3
 STA UiState
 LDA #0
 STA MenuPart
UiWriteDone:
 JMP UiHold
UiRestored:
 ; Wait for the final queued row to reach NMI before releasing ownership.
 LDA #5
 STA UiState
 JMP UiHold

UiLive:
 JMP UiLiveImpl
UiCacheLow: .db $00,$1C,$38,$54,$70,$8C,$A8,$C4,$E0,$FC,$00,$08,$10
UiCacheHigh: .db $70,$70,$70,$70,$70,$70,$70,$70,$70,$70,$72,$72,$72

UiChr:
 LDX #3
UiChrFind:
 LDA UiOriginalChr,X
 CMP $0719
 BEQ UiChrFound
 DEX
 BPL UiChrFind
 LDX #0
UiChrFound:
 LDA UiOriginalChr,X
 STA UiFlag
 LDA UiMenuChr,X
 STA $0719
 LDA #$E8
 STA $071A
 RTS
UiOriginalChr: .db $14,$70,$72,$74
UiMenuChr: .db $E0,$E2,$E4,$E6

; Reconstruct the covered native map rectangle from its authoritative tiles.
; No $2007 reads: DMC DMA cannot skip bytes from a presentation snapshot.
UiMapSnapshot:
 LDA UiRow
 CMP UiHeight
 BCC UiMapSnapshotPatterns
 JMP UiMapAttributes
UiMapSnapshotPatterns:
 CLC
 ADC UiAnchor
 LSR A
 SEC
 SBC #1
 STA UiTileY
 LDA #0
 STA UiColumn
UiMapPatternLoop:
 LDA UiColumn
 LSR A
 CLC
 ADC UiStartMeta
 STA UiTileX
 JSR UiMapTile
 TAX
 LDA UiRow
 AND #1
 BNE UiMapPatternLower
 LDA UiColumn
 AND #1
 BNE UiMapPatternUpperRight
 LDA $B600,X
 JMP UiMapPatternStore
UiMapPatternUpperRight:
 LDA $B800,X
 JMP UiMapPatternStore
UiMapPatternLower:
 LDA UiColumn
 AND #1
 BNE UiMapPatternLowerRight
 LDA $B700,X
 JMP UiMapPatternStore
UiMapPatternLowerRight:
 LDA $B900,X
UiMapPatternStore:
 ; World8 section2 preserves the native48x48 light window. Darkness covers
 ; nametable rows4..22; borders and attributes retain their ordinary owners.
 PHA
 LDA $0598
 BEQ UiMapPatternLit
 LDA UiRow
 CLC
 ADC UiAnchor
 CMP #4
 BCC UiMapPatternLit
 CMP #23
 BCS UiMapPatternLit
 ASL A
 ASL A
 ASL A
 CLC
 ADC #16
 SEC
 SBC $75
 CMP #48
 BCS UiMapPatternDark
 LDA UiColumn
 AND #1
 ASL A
 ASL A
 ASL A
 STA $02
 LDA UiTileX
 ASL A
 ASL A
 ASL A
 ASL A
 ORA $02
 CLC
 ADC #16
 SEC
 SBC $79
 CMP #48
 BCC UiMapPatternLit
UiMapPatternDark:
 PLA
 LDA #$FF
 JMP UiMapPatternReady
UiMapPatternLit:
 PLA
UiMapPatternReady:
 LDY UiColumn
 STA $7400,Y
 INC UiColumn
 LDA UiColumn
 CMP #28
 BCS UiMapPatternsDone
 JMP UiMapPatternLoop
UiMapPatternsDone:
 JMP UiMapCopy
UiMapAttributes:
 SEC
 SBC UiHeight
 CLC
 ADC UiAttrRow
 ASL A
 SEC
 SBC #1
 STA UiTileY
 LDA #0
 STA UiColumn
UiMapAttributeLoop:
 LDA UiColumn
 ASL A
 STA UiTileX
 LDA UiStartMeta
 AND #$FE
 CLC
 ADC UiTileX
 STA UiTileX
 JSR UiMapTile
 AND #$C0
 LSR A
 LSR A
 LSR A
 LSR A
 LSR A
 LSR A
 STA UiAccum
 INC UiTileX
 JSR UiMapTile
 AND #$C0
 LSR A
 LSR A
 LSR A
 LSR A
 ORA UiAccum
 STA UiAccum
 INC UiTileY
 DEC UiTileX
 JSR UiMapTile
 AND #$C0
 LSR A
 LSR A
 ORA UiAccum
 STA UiAccum
 INC UiTileX
 JSR UiMapTile
 AND #$C0
 ORA UiAccum
 DEC UiTileY
 LDY UiColumn
 PHA
 LDA UiStartMeta
 AND #1
 BNE UiMapAttributeBorder
 PLA
 JMP UiMapAttributeStore
UiMapAttributeBorder:
 PLA
 CPY #0
 BNE UiMapAttributeRight
 AND #$CC
 ORA #$11
UiMapAttributeRight:
 STA UiAccum
 TYA
 CLC
 ADC #1
 CMP UiAttrCount
 BEQ UiMapAttributeForceRight
 LDA UiAccum
 JMP UiMapAttributeStore
UiMapAttributeForceRight:
 LDA UiAccum
 AND #$33
 ORA #$44
UiMapAttributeStore:
 STA $7400,Y
 INC UiColumn
 LDA UiColumn
 CMP UiAttrCount
 BCS UiMapCopy
 JMP UiMapAttributeLoop
UiMapCopy:
 LDA UiCacheLo
 STA $00
 LDA UiCacheHi
 STA $01
 LDY #0
UiMapCopyLoop:
 LDA $7400,Y
 STA [$00],Y
 INY
 CPY UiCount
 BNE UiMapCopyLoop
 RTS
UiMapTile:
 LDA UiTileX
 LSR A
 LSR A
 LSR A
 LSR A
 ASL A
 TAX
 LDA $8000,X
 STA $00
 LDA $8001,X
 CLC
 ADC #1
 STA $01
 LDA UiTileY
 ASL A
 ASL A
 ASL A
 ASL A
 STA $02
 LDA UiTileX
 AND #$0F
 ORA $02
 TAY
 LDA [$00],Y
 RTS

; Exact SafeContext fields and idle sequence copied from the accepted controller.
UiSafe:
 LDA $79AE
 BNE UiSafeBound
 JMP UiUnsafe
UiSafeBound:
 LDA $072B
 CMP #1
 BEQ UiSafeSinglePlayer
 JMP UiUnsafe
UiSafeSinglePlayer:
 LDA $0727
 CMP #8
 BCC UiSafeWorld
 JMP UiUnsafe
UiSafeWorld:
 LDA $0729
 CMP #$0D
 BNE UiUnsafe
 LDA $0100
 CMP #$C0
 BNE UiUnsafe
 LDA $0728
 CMP #2
 BCS UiUnsafe
 LDA $0736
 CMP #100
 BCS UiUnsafe
 LDA $79A2
 CMP #2
 BNE UiUnsafe
 LDA $0598
 BEQ UiSafeDarkReady
 CMP #7
 BCC UiUnsafe
UiSafeDarkReady:
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
 ORA $79F3
 BNE UiUnsafe
 LDA $79A4
 CMP $79A5
 BNE UiUnsafe
 LDA $79F0
 CMP $79F1
 BNE UiUnsafe
 CLC
 RTS
UiUnsafe:
 SEC
 RTS
UiCodeEnd:
; @CONTROLS
; @GEOMETRY
; @VALUES
UiAllCodeEnd:
 .org $BA00
; @UI_ROWS
UiRowsEnd:
