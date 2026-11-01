; Research only. Slot-local Var10/11 are previous camera coordinates, Var14 is
; initialization marker. Native Sun never uses them; native slot preparation
; clears them on spawn/reuse. No new global or persistent RAM.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 5
 .org $AD69
HRSunEntry:
 LDY #10
 JSR $E29F
 JSR Object_CalcSpriteXY_NoHi
 JMP ObjNorm_Sun
HRSunEntryEnd:
 .org $BFC6
HRSunWait:
 LDY #12
 JSR $E29F
 CMP #2
 BEQ HRSunActivate
 LDA #0
 STA Objects_Frame,X
 RTS
HRSunActivate:
 JMP PRG005_ADF6
HRSunWaitEnd:
 .bank 20
 .org $C400
HRDispatch:
 CPY #10
 BNE HRNotCamera
 JMP HRCamera
HRNotCamera:
 CPY #11
 BNE HRNotReturn
 JMP HRReturn
HRNotReturn:
 CPY #12
 BNE HROldDispatch
 LDY #2
 JSR $C100
 CMP #0
 BNE HRDone
 LDA Objects_XHi,X
 CMP #5
 BNE HRPending
 LDA Objects_X,X
 CMP #176
 BCC HRPending
 LDA #2
 RTS
HRPending:
 LDA #1
HRDone:
 RTS
HROldDispatch:
 JMP HROldTarget

HRGate:
 LDA LevelJctBQ_Flag
 BNE HRNo
 LDY $CFFF
 BEQ HRNo
 DEY
HRGateLoop:
 LDA $D600,Y
 BPL HRGateNext
 LDA Level_Tileset
 CMP $D000,Y
 BNE HRGateNext
 LDA Level_LayPtrOrig_AddrL
 CMP $D100,Y
 BNE HRGateNext
 LDA Level_LayPtrOrig_AddrH
 CMP $D200,Y
 BNE HRGateNext
 LDA #1
 RTS
HRGateNext:
 DEY
 BPL HRGateLoop
HRNo:
 LDA #0
 RTS

HRCamera:
 JSR HRGate
 BEQ HRDone
 LDA Objects_State,X
 CMP #2
 BNE HRDone
 LDA Player_HaltGame
 BNE HRDone
 LDA Objects_Var14,X
 CMP #$A5
 BEQ HRDelta
 LDA #$A5
 STA Objects_Var14,X
 JSR HRAnchor
 JMP HRRemember
HRDelta:
 LDA Level_VertScroll
 SEC
 SBC Objects_Var10,X
 STA Temp_Var1
 LDA Level_VertScrollH
 SBC Objects_Var11,X
 STA Temp_Var2
 ; Dive/turn/return keep their world-space trajectory. Only waiting/orbiting
 ; states compensate gradual camera movement, never Player_Y or jump velocity.
 LDA Objects_Var7,X
 BEQ HRHover
 CMP #1
 BEQ HRHover
 CMP #4
 BEQ HRHover
 JSR HRReturnEdge
 JMP HRRemember
HRHover:
 LDA Temp_Var2
 BEQ HRPositive
 CMP #$FF
 BNE HRDiscontinuity
 LDA Temp_Var1
 CMP #$F8
 BCC HRDiscontinuity
 JMP HRShift
HRPositive:
 LDA Temp_Var1
 CMP #9
 BCS HRDiscontinuity
HRShift:
 LDA Objects_Y,X
 CLC
 ADC Temp_Var1
 STA Objects_Y,X
 LDA Objects_YHi,X
 ADC Temp_Var2
 STA Objects_YHi,X
 JMP HRRemember
HRDiscontinuity:
 ; A large discontinuity reinitializes at camera-top+33 in state0.
 ; Select the opposite horizontal margin below to avoid overlapping Mario.
 JSR HRAnchor
 ; Reinitialization only: choose the visible margin away from the player.
 ; Ordinary hover/attack motion never tracks Player_X or Player_Y.
 LDA Player_X
 SEC
 SBC Horz_Scroll
 STA Temp_Var1
 LDA Player_XHi
 SBC Horz_Scroll_Hi
 BNE HRLeftAnchor
 LDA Temp_Var1
 CMP #128
 BCS HRLeftAnchor
 LDA #192
 BNE HRChosenAnchor
HRLeftAnchor:
 LDA #32
HRChosenAnchor:
 CLC
 ADC Horz_Scroll
 STA Objects_X,X
 LDA Horz_Scroll_Hi
 ADC #0
 STA Objects_XHi,X
 LDA #0
 STA Objects_Var7,X
 STA Objects_XVel,X
 STA Objects_YVel,X
HRRemember:
 LDA Level_VertScroll
 STA Objects_Var10,X
 LDA Level_VertScrollH
 STA Objects_Var11,X
 RTS
HRAnchor:
 LDA Level_VertScroll
 CLC
 ADC #33
 STA Objects_Y,X
 LDA Level_VertScrollH
 ADC #0
 STA Objects_YHi,X
 RTS

HRReturnEdge:
 ; A camera-relative return can take longer than the native fixed-height arc.
 ; Stop native horizontal drift at a visible margin rather than deleting the
 ; sole added Sun. No player coordinate, chasing velocity, or sprite-only move.
 LDA Objects_Var7,X
 CMP #3
 BEQ HREdgeCheck
 CMP #6
 BNE HREdgeDone
HREdgeCheck:
 LDA Objects_X,X
 SEC
 SBC Horz_Scroll
 STA Temp_Var1
 LDA Objects_XHi,X
 SBC Horz_Scroll_Hi
 BMI HREdgeLeft
 BNE HREdgeRight
 LDA Temp_Var1
 CMP #32
 BCC HREdgeLeft
 CMP #193
 BCC HREdgeDone
HREdgeRight:
 LDA #192
 BNE HREdgeStore
HREdgeLeft:
 LDA #32
HREdgeStore:
 CLC
 ADC Horz_Scroll
 STA Objects_X,X
 LDA Horz_Scroll_Hi
 ADC #0
 STA Objects_XHi,X
 LDA #0
 STA Objects_XVel,X
HREdgeDone:
 RTS

HRReturn:
 JSR HRGate
 BNE HRCameraReturn
 ; Original encounters keep the exact low-byte threshold and clamp.
 LDA Objects_Y,X
 CMP #16
 BCS HRReturnNo
 LDA #16
 STA Objects_Y,X
 LDA #1
 RTS
HRCameraReturn:
 LDA Level_VertScroll
 CLC
 ADC #33
 STA Temp_Var1
 LDA Level_VertScrollH
 ADC #0
 STA Temp_Var2
 LDA Objects_YHi,X
 CMP Temp_Var2
 BCC HRReached
 BNE HRReturnNo
 LDA Objects_Y,X
 CMP Temp_Var1
 BCS HRReturnNo
HRReached:
 LDA Temp_Var1
 STA Objects_Y,X
 LDA Temp_Var2
 STA Objects_YHi,X
 LDA #1
 RTS
HRReturnNo:
 LDA #0
 RTS
HRSunEnd:
