; M26 giant command collision correction. Southbird native bank2/slot4 actor47.
; Authored executable bytes are guarded in tools/giant_patch_m26.py.
; No shared dispatcher change: Bros command14 retains bank52 ownership.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 2
 .org $A3A2
 LDY #0
 JSR $E29F
 NOP
 NOP
 NOP
 .bank 20
 .org $C380
 CPY #0
 BNE GiantFallback
 CPX #4
 BNE GiantFallback
 LDA $0720 ; PAGE_A000
 CMP #2
 BNE GiantFallback
 LDA $0671,X ; Level_ObjectID
 CMP #$47
 BNE GiantFallback
 LDA $00A3,X ; Objects_Y
 STA $0000
 LDA $0088,X ; Objects_YHi
 STA $0001
 JSR $C092 ; unchanged source-coordinate Poison lookup
 CMP #1
 BEQ GiantMushroom
 LDA $00ED ; Player_Suit
 BEQ GiantMushroom
 LDA #$1E
 RTS
GiantMushroom:
 LDA #$0D
 RTS
GiantFallback:
 JMP $D700
