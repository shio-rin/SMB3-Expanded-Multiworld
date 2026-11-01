; Presentation reads authoritative native permissions and physical counters only.
UiValues:
 LDA UiRow
 BNE UiValueInterior
 RTS
UiValueInterior:
 CLC
 ADC #1
 CMP UiHeight
 BNE UiValueInteriorReady
 RTS
UiValueInteriorReady:
 LDA Menu
 CMP #1
 BNE UiValuesProgression
 JMP UiTravelValues
UiValuesProgression:
 LDA UiRow
 CMP #1
 BNE UiValuesBody
 JSR UiTitleValues
UiValuesBody:
 LDA UiPage
 BEQ UiPassValues
 CMP #1
 BNE UiValuesNotHammer
 JMP UiHammerValues
UiValuesNotHammer:
 CMP #2
 BNE UiValuesChecks
 JMP UiStarValues
UiValuesChecks:
 JMP UiCheckValues
UiValueDone:
 RTS
UiPassValues:
 LDA UiRow
 CMP #2
 BEQ UiCurrentWorld
 CMP #4
 BEQ UiOwnership
 CMP #6
 BEQ UiTotalFraction
 CMP #7
 BNE UiValueDone
 LDA UiError
 CMP #1
 BNE UiValueDone
 JSR UiBlankLine
 LDX #MsgNoView
 LDY #1
 JMP UiPutText
UiCurrentWorld:
 LDX $0727
 INX
 LDA UiDigits,X
 STA $742F
 LDA $0727
 LDY #17
 JMP UiName
UiOwnership:
 LDX #0
 LDY #2
UiOwnershipLoop:
 LDA $79A8
 AND UiWorldBits,X
 BEQ UiOwnershipMissing
 LDA #GlyphOwned
 JMP UiOwnershipStore
UiOwnershipMissing:
 LDA #GlyphX
UiOwnershipStore:
 STA $7420,Y
 INX
 INY
 INY
 INY
 CPX #8
 BCC UiOwnershipLoop
 RTS
UiTotalFraction:
 LDA $7AA8
 LDY #18
 JSR UiNumber
 LDA $9F1A
 LDY #22
 JMP UiNumber

UiHammerValues:
 LDA $9F3C
 BNE UiHammerRegional
 JSR UiBlankLine
 LDX UiRow
 DEX
 LDA UiLegacyMessages,X
 TAX
 LDY #1
 JSR UiPutText
 LDA UiRow
 CMP #1
 BEQ UiLegacyTitlePage
 JMP UiHammerDone
UiLegacyTitlePage:
 JMP UiTitleValues
UiLegacyMessages: .db MsgLegacyTitle,MsgLegacyLine,MsgLegacyBack,MsgFooter
UiHammerRegional:
 LDA UiRow
 CMP #1
 BEQ UiHammerHeader
 CMP #2
 BEQ UiHammerFirstPair
 CMP #3
 BNE UiHammerNotSecondPair
 JMP UiHammerSecondPair
UiHammerNotSecondPair:
 CMP #4
 BEQ UiHammerActionHint
 JMP UiHammerDone
UiHammerActionHint:
 JSR UiToolAllowed
 BEQ UiHammerNoAction
 LDX #MsgTryRock
 LDA UiError
 CMP #3
 BNE UiHammerHint
 LDX #MsgBusy
 JMP UiHammerHint
UiHammerNoAction:
 LDX #MsgFooter
 LDA UiError
 CMP #2
 BNE UiHammerHint
 LDX #MsgMissing
UiHammerHint:
 TXA
 PHA
 JSR UiBlankLine
 PLA
 TAX
 LDY #1
 JMP UiPutText
UiHammerHeader:
 JSR UiBlankLine
 LDA #GlyphW
 STA $7421
 LDX $0727
 INX
 LDA UiDigits,X
 STA $7422
 LDX $0727
 LDA UiWorldBits,X
 AND #$2E
 BEQ UiHammerNonRegion
 LDA $0727
 LDY #4
 JSR UiName
 JSR UiToolAllowed
 BEQ UiHammerHeaderMissing
 LDX #MsgOwned
 JMP UiHammerHeaderState
UiHammerHeaderMissing:
 LDX #MsgMissingWord
UiHammerHeaderState:
 LDY #12
 JSR UiPutText
 JMP UiTitleValues
UiHammerNonRegion:
 LDX #MsgNoRegion
 LDY #4
 JSR UiPutText
 JMP UiTitleValues
UiHammerFirstPair:
 LDA #2
 LDY #8
 JSR UiHammerMark
 LDA #4
 LDY #24
 JMP UiHammerMark
UiHammerSecondPair:
 LDA #8
 LDY #8
 JSR UiHammerMark
 LDA #32
 LDY #24
UiHammerMark:
 AND $79F7
 BEQ UiHammerMarkMissing
 LDA #GlyphOwned
 BNE UiHammerMarkStore
UiHammerMarkMissing:
 LDA #GlyphX
UiHammerMarkStore:
 STA $7420,Y
UiHammerDone:
 RTS

UiStarValues:
 LDA UiRow
 CMP #2
 BEQ UiStarFraction
 CMP #3
 BEQ UiStarGateLabel
 CMP #4
 BEQ UiStarThreshold
 CMP #5
 BEQ UiStarPassLabel
 RTS
UiStarFraction:
 LDA $79F8
 LDY #18
 JSR UiNumber
 LDA $9F3E
 LDY #22
 JMP UiNumber
UiStarGateLabel:
 LDX #MsgStarTravel
 LDA $9F3D
 CMP #1
 BEQ UiStarText
 LDX #MsgStarBowser
 BNE UiStarText
UiStarThreshold:
 LDX #MsgStarMissing
 LDA $79F8
 CMP $9F3E
 BCC UiStarText
 LDX #MsgStarReady
 BNE UiStarText
UiStarPassLabel:
 LDX #MsgPassNeeded
 LDA $9F3D
 CMP #1
 BEQ UiStarText
 LDX #MsgBowserOnly
UiStarText:
 TXA
 PHA
 JSR UiBlankLine
 PLA
 TAX
 LDY #1
 JMP UiPutText

UiCheckValues:
 LDA UiRow
 CMP #2
 BNE UiCheckCounts
 JMP UiCurrentWorld
UiCheckCounts:
 CMP #4
 BEQ UiCheckCurrent
 CMP #5
 BEQ UiCheckTotal
 RTS
UiCheckCurrent:
 LDX $0727
 LDA $7AA0,X
 LDY #18
 JSR UiNumber
 LDX $0727
 LDA UiTotals,X
 LDY #24
 JMP UiNumber
UiCheckTotal:
 LDA $7AA8
 LDY #18
 JSR UiNumber
 LDA $9F1A
 LDY #24
 JMP UiNumber

UiTravelValues:
 LDA UiRow
 CMP #1
 BEQ UiTravelCurrent
 CMP #2
 BEQ UiTravelCursor
 CMP #3
 BNE UiTravelNotOwnership
 JMP UiOwnership
UiTravelNotOwnership:
 CMP #4
 BEQ UiTravelDescription
 CMP #5
 BEQ UiTravelHint
 RTS
UiTravelCurrent:
 LDX $0727
 INX
 LDA UiDigits,X
 STA $7437
 RTS
UiTravelCursor:
 LDA $79DC
 ASL A
 CLC
 ADC $79DC
 TAX
 LDA #GlyphArrow
 STA $7421,X
 RTS
UiTravelDescription:
 LDX $79DC
 INX
 LDA UiDigits,X
 STA $7427
 LDA $79DC
 LDY #9
 JSR UiName
 LDX $79DC
 LDA $79A8
 AND UiWorldBits,X
 BEQ UiTravelDescriptionMissing
 LDX #MsgOwned
 JMP UiTravelDescriptionText
UiTravelDescriptionMissing:
 LDX #MsgMissingWord
UiTravelDescriptionText:
 LDY #19
 JMP UiPutText
UiTravelHint:
 JSR UiBlankLine
 LDA UiError
 CMP #3
 BEQ UiTravelBusyHint
 LDA $79DC
 CMP $0727
 BEQ UiTravelCurrentHint
 TAX
 LDA $79A8
 AND UiWorldBits,X
 BEQ UiTravelMissingHint
 JSR UiAllowed
 BEQ UiTravelStarHint
 JSR UiIdle
 BNE UiTravelBusyHint
 LDX #MsgTravelMap
 LDA UiParent
 BEQ UiTravelPutHint
 LDX #MsgTravelParent
 BNE UiTravelPutHint
UiTravelCurrentHint:
 LDX #MsgCurrentMap
 LDA UiParent
 BEQ UiTravelPutHint
 LDX #MsgCurrentParent
 BNE UiTravelPutHint
UiTravelMissingHint:
 LDX #MsgPassMissing
 BNE UiTravelPutHint
UiTravelBusyHint:
 LDX #MsgBusy
UiTravelPutHint:
 LDY #1
 JMP UiPutText
UiTravelStarHint:
 LDX #MsgStarGate
 LDY #1
 JSR UiPutText
 JMP UiStarFraction

UiTitleValues:
 LDA UiPage
 CLC
 ADC #1
 CMP #4
 BNE UiTitleDigit
 LDX $9F3D
 BNE UiTitleDigit
 SEC
 SBC #1
UiTitleDigit:
 TAX
 LDA UiDigits,X
 STA $7437
 LDX UiPageCount
 LDA UiDigits,X
 STA $7439
 LDA #GlyphSlash
 STA $7438
 RTS
UiBlankLine:
 LDA #GlyphBlank
 LDX #26
UiBlankLoop:
 STA $7420,X
 DEX
 BNE UiBlankLoop
 RTS
UiPutText:
 STY UiValueColumn
 LDA UiMessagesLo,X
 STA $00
 LDA UiMessagesHi,X
 STA $01
 LDY #0
UiPutLoop:
 LDA [$00],Y
 BEQ UiPutDone
 LDX UiValueColumn
 CPX #27
 BCS UiPutDone
 STA $7420,X
 INC UiValueColumn
 INY
 BNE UiPutLoop
UiPutDone:
 RTS
UiName:
 ASL A
 ASL A
 ASL A
 TAX
 LDA #8
 STA UiValueMask
UiNameLoop:
 LDA UiNames,X
 STA $7420,Y
 INX
 INY
 DEC UiValueMask
 BNE UiNameLoop
 RTS
UiNumber:
 STA UiValue
 LDA #GlyphBlank
 STA $7420,Y
 STA $7421,Y
 LDA UiValue
 LDX #0
UiHundreds:
 CMP #100
 BCC UiHundredsDone
 SEC
 SBC #100
 INX
 BNE UiHundreds
UiHundredsDone:
 STA UiValue
 CPX #0
 BEQ UiTensBegin
 LDA UiDigits,X
 STA $7420,Y
UiTensBegin:
 LDA UiValue
 LDX #0
UiTens:
 CMP #10
 BCC UiTensDone
 SEC
 SBC #10
 INX
 BNE UiTens
UiTensDone:
 STA UiValue
 CPX #0
 BNE UiTensVisible
 LDA $7420,Y
 CMP #GlyphBlank
 BEQ UiUnits
UiTensVisible:
 LDA UiDigits,X
 STA $7421,Y
UiUnits:
 LDX UiValue
 LDA UiDigits,X
 STA $7422,Y
 RTS
; @VALUES_DATA
