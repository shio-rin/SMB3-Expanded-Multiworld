; Exact native card terminal -> bound fortress-host effect. The native score,
; cards and lives sequence remains intact; no boss event is fabricated.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 20
 .org $C180
M222MixedCard:
 LDA #0
 STA Map_ReturnStatus
 INC Level_ExitToMap
 TXA
 PHA
 LDY $D500
 BNE M222MixedRows
 JMP M222MixedDone
M222MixedRows:
 DEY
M222MixedRow:
 LDA World_Num
 CMP $D520,Y
 BNE M222MixedNext
 LDA $7978
 CMP $D540,Y
 BNE M222MixedNext
 LDA $797A
 CMP $D560,Y
 BNE M222MixedNext
 LDA $7976
 CMP $D580,Y
 BEQ M222MixedMatched
M222MixedNext:
 DEY
 BPL M222MixedRow
 JMP M222MixedDone
M222MixedMatched:
 LDA $79AE
 CMP #1
 BNE M222MixedReject
 LDA $79A2
 CMP #2
 BNE M222MixedReject
 LDA $0726
 BNE M222MixedReject
 LDA $072B
 CMP #1
 BNE M222MixedReject
 LDA $1E
 BNE M222MixedReject
 LDA Level_Tileset
 CMP $D5A0,Y
 BNE M222MixedReject
 LDA $7EB9
 CMP $D5C0,Y
 BNE M222MixedReject
 LDA $7EBA
 CMP $D5E0,Y
 BNE M222MixedReject
 LDA $7EBB
 CMP $D620,Y
 BNE M222MixedReject
 LDA $7EBC
 CMP $D640,Y
 BNE M222MixedReject
 LDA Level_ObjectID,X
 CMP #$41
 BNE M222MixedReject
 LDA Objects_Timer,X
 BNE M222MixedReject
 LDA EndCard_Flag
 AND #$80
 BEQ M222MixedReject
 LDA $D600,Y
 STA Map_DoFortressFX
 JMP M222MixedDone
M222MixedReject:
 LDA #1
 STA Map_ReturnStatus
 LDA #0
 STA Map_DoFortressFX
M222MixedDone:
 PLA
 TAX
 ; Restore the native Y inventory offset used immediately after this hook.
 JSR Player_GetInventoryOffset
 TYA
 RTS
M222MixedEnd:
