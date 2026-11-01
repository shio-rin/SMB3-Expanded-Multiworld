; Only a real native treasure-delay terminal can translate Big Tanks' success.
; Orb terminals use the separately guarded special-context hook.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 20
 .org $C600
M222MilitaryTreasure:
 INC Level_ExitToMap
 LDA #0
 STA Map_ReturnStatus
 TXA
 PHA
 LDA $1E
 BNE M222MilitaryCheckWorld
 JSR $C740
 JMP M222MilitaryDone
M222MilitaryCheckWorld:
 LDA World_Num
 CMP #7
 BEQ M222MilitaryWorld
 JMP M222MilitaryDone
M222MilitaryWorld:
 LDY $D300
 BNE M222MilitaryRows
 JMP M222MilitaryDone
M222MilitaryRows:
 DEY
M222MilitaryRow:
 LDA $79E9
 CMP $D320,Y
 BEQ M222MilitaryMatched
 DEY
 BPL M222MilitaryRow
 JMP M222MilitaryDone
M222MilitaryMatched:
 LDA $79AE
 CMP #1
 BNE M222MilitaryRejectEarly
 LDA $79A2
 CMP #2
 BNE M222MilitaryRejectEarly
 LDA $0726
 BNE M222MilitaryRejectEarly
 LDA $072B
 CMP #1
 BNE M222MilitaryRejectEarly
 LDA $79E7
 CMP #7
 BNE M222MilitaryRejectEarly
 LDA $79E6
 CMP $D4A0,Y
 BNE M222MilitaryReject
 LDA $1E
 CMP $D340,Y
 BNE M222MilitaryReject
 CMP $79EA
 BNE M222MilitaryReject
 LDX $79E9
 CMP $7F15,X
 BNE M222MilitaryReject
 JMP M222MilitaryPoint
M222MilitaryRejectEarly:
 JMP M222MilitaryReject
M222MilitaryPoint:
 LDA $7978
 CMP $D360,Y
 BNE M222MilitaryReject
 LDA $797A
 CMP $D380,Y
 BNE M222MilitaryReject
 LDA $7976
 CMP $D3A0,Y
 BNE M222MilitaryReject
 LDA Level_Tileset
 CMP #10
 BNE M222MilitaryReject
 LDA $7EB9
 CMP #$A0
 BNE M222MilitaryReject
 LDA $7EBA
 CMP #$BD
 BNE M222MilitaryReject
 LDA $7EBB
 CMP #$29
 BNE M222MilitaryReject
 LDA $7EBC
 CMP #$DA
 BNE M222MilitaryReject
 LDA Level_Event
 CMP #7
 BNE M222MilitaryReject
 LDA LevelEvent_Cnt
 BNE M222MilitaryReject
 LDA Level_TreasureItem
 CMP #9
 BNE M222MilitaryReject
 LDA $D3C0,Y
 CMP #1
 BNE M222MilitaryReject
 LDA $D3E0,Y
 STA Map_DoFortressFX
 JMP M222MilitaryDone
M222MilitaryReject:
 LDA #1
 STA Map_ReturnStatus
 LDA #0
 STA Map_DoFortressFX
M222MilitaryDone:
 PLA
 TAX
 LDA Map_ReturnStatus
 RTS
M222MilitaryEnd:
