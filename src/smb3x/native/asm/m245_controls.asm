; Explicit owners and stable categories:0 Passes,1 Hammers,2 Stars,3 Checks.
UiLiveImpl:
 LDA UiState
 CMP #5
 BNE UiLiveRelease2
 LDA #$16
 STA $071A
 LDA UiFlag
 STA $0719
 LDA #0
 STA UiState
 STA Menu
 STA MenuPart
 LDA #1
 STA Release
 LDA UiGoal
 BEQ UiClosedAction
 STA Menu
 LDA #0
 STA UiGoal
 LDA UiGoalPage
 STA UiPage
 JSR UiConfigure
 JMP UiBegin
UiClosedAction:
 LDA UiPending
 PHA
 LDA #0
 STA UiPending
 PLA
 CMP #2
 BEQ UiClosedTool
 CMP #1
 BNE UiCloseDone
 ; Restoration spans frames. Revalidate immediately before native dispatch.
 JSR UiSafe
 BCS UiCloseDone
 JSR UiIdle
 BNE UiCloseDone
 LDX UiDestination
 JSR UiAllowed
 BEQ UiCloseDone
 LDA UiDestination
 STA $79A7
 LDA #1
 STA $79DE
UiCloseDone:
 JMP UiHold
UiClosedTool:
 JSR UiSafe
 BCS UiCloseDone
 JSR UiToolAllowed
 BEQ UiCloseDone
 LDA #0
 STA $17
 STA $18
 LDA #2
 RTS
UiLiveRelease2:
 LDA Release
 BEQ UiButtons
 LDA $17
 BNE UiButtonsHeld
 LDA #0
 STA Release
UiButtonsHeld:
 JMP UiHold
UiButtons:
 LDA $18
 AND #$10
 BEQ UiCheckBack
 JMP UiCloseAll
UiCheckBack:
 LDA $18
 AND #$40
 BEQ UiCheckMove
 JMP UiBack
UiCheckMove:
 LDA $18
 AND #3
 BNE UiMove
 JMP UiAction
UiMove:
 LDA #0
 STA UiError
 LDA Menu
 CMP #1
 BEQ UiTravelMove
UiPageMove:
 LDA $18
 AND #2
 BEQ UiPageNext
 DEC UiPage
 JMP UiPageWrap
UiPageNext:
 INC UiPage
UiPageWrap:
 LDA UiPage
 CMP #$FF
 BNE UiPageHigh
 LDA #3
UiPageHigh:
 CMP #4
 BCC UiPageVisible
 LDA #0
UiPageVisible:
 STA UiPage
 CMP #2
 BNE UiCategoryReady
 LDA $9F3D
 BEQ UiPageMove
UiCategoryReady:
 LDA UiPage
 CMP #1
 BEQ UiCategoryGeometry
 LDA UiHeight
 CMP #10
 BNE UiCategoryGeometry
 JMP UiRedraw
UiCategoryGeometry:
 LDA UiPage
 STA UiGoalPage
 LDA #2
 STA UiGoal
 JMP UiClose2
UiTravelMove:
 LDA $18
 AND #2
 BEQ UiTravelNext
 DEC $79DC
 JMP UiTravelWrap
UiTravelNext:
 INC $79DC
UiTravelWrap:
 LDA $79DC
 CMP #$FF
 BNE UiTravelHigh
 LDA #7
UiTravelHigh:
 CMP #8
 BCC UiTravelChosen
 LDA #0
UiTravelChosen:
 STA $79DC
 JMP UiRedraw
UiAction:
 LDA $18
 AND #$80
 BNE UiActionPressed
 JMP UiHold
UiActionPressed:
 LDA Menu
 CMP #1
 BEQ UiTravelAction
 LDA UiPage
 BEQ UiEnterTravel
 CMP #1
 BNE UiActionNoop
 JSR UiToolAllowed
 BEQ UiDenied
 JSR UiIdle
 BNE UiBusy
 LDA #2
 STA UiPending
 JMP UiClose2
UiActionNoop:
 JMP UiHold
UiEnterTravel:
 LDA #2
 STA UiParent
 LDA #1
 STA UiGoal
 LDA #0
 STA UiGoalPage
 LDA $0727
 STA $79DC
 JMP UiClose2
UiTravelAction:
 LDA $79DC
 CMP $0727
 BNE UiTravelOther
 JMP UiCloseAll
UiTravelOther:
 TAX
 JSR UiAllowed
 BEQ UiDenied
 JSR UiSafe
 BCS UiBusy
 LDA $79DC
 STA UiDestination
 LDA #1
 STA UiPending
 JMP UiClose2
UiDenied:
 LDA #2
 STA UiError
 JMP UiRedraw
UiBusy:
 LDA #3
 STA UiError
 JMP UiRedraw
UiBack:
 LDA Menu
 CMP #1
 BNE UiCloseAll
 LDA UiParent
 CMP #2
 BNE UiCloseAll
 STA UiGoal
 LDA #0
 STA UiGoalPage
 STA UiParent
 JMP UiClose2
UiCloseAll:
 LDA #0
 STA UiGoal
 STA UiPending
 STA UiParent
 JMP UiClose2
UiRedraw:
 LDA #2
 STA UiState
 LDA #0
 STA UiRow
 LDA #1
 STA Release
 LDA #$80
 STA MenuPart
 JMP UiHold
UiClose2:
 LDA #4
 STA UiState
 LDA #0
 STA UiRow
 LDA #$80
 STA MenuPart
 JMP UiHold
UiIdle:
 LDA $79F3
 BNE UiIdleDone
 LDA $79A4
 CMP $79A5
 BNE UiIdleDone
 LDA $79F0
 CMP $79F1
UiIdleDone:
 RTS
UiAllowed:
 ; Exact World8-only gate. Bowser gate does not restrict travel.
 CPX #7
 BNE UiAllowedPass
 LDA $9F3D
 CMP #1
 BNE UiAllowedPass
 LDA $79F8
 CMP $9F3E
 BCC UiNotAllowed
UiAllowedPass:
 LDA $79A8
 AND UiWorldBits,X
 RTS
UiNotAllowed:
 LDA #0
 RTS
UiToolAllowed:
 LDA $9F3C
 BEQ UiNotAllowed
 LDX $0727
 LDA $79F7
 AND UiWorldBits,X
 RTS
UiWorldBits: .db 1,2,4,8,16,32,64,128
