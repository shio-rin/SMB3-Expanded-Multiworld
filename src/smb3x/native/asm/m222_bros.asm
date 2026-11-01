; Complete battle content follows a bound physical world/encounter slot.
; Map_EnterViaID and map-object type remain physical and unchanged.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 12
 .org $BDC0
M222BrosPrepareStub:
 LDY #14
 JSR $E29F
 JMP MO_Unused
M222BrosPrepareStubEnd:
 .bank 4
 .org $BE56
M222BrosEnemyStub:
 LDY #15
 JMP $E29F
M222BrosEnemyStubEnd:
 .bank 20
 .org $C300
M222BrosDispatch:
 CPY #18
 BNE M222BrosNotCard
 JMP $C180
M222BrosNotCard:
 CPY #17
 BNE M222BrosCommand
 JMP $C600
M222BrosCommand:
 TXA
 PHA
 CPY #14
 BNE M222BrosNotPrepare
 JSR M222BrosFind
 BCS M222BrosPrepareMatched
 JMP M222BrosDone
M222BrosPrepareMatched:
 LDA $D1A0,Y
 STA Level_Tileset
 LDA $D1C0,Y
 STA Level_LayPtr_AddrL
 STA Level_LayPtrOrig_AddrL
 LDA $D1E0,Y
 STA Level_LayPtr_AddrH
 STA Level_LayPtrOrig_AddrH
 LDA $D200,Y
 STA Level_ObjPtr_AddrL
 STA Level_ObjPtrOrig_AddrL
 LDA $D220,Y
 STA Level_ObjPtr_AddrH
 STA Level_ObjPtrOrig_AddrH
 JMP M222BrosDone
M222BrosNotPrepare:
 CPY #15
 BNE M222BrosNotEnemy
 JSR M222BrosFind
 BCC M222BrosNativeEnemy
 JSR M222BrosActive
 BCC M222BrosNativeEnemy
 LDA $D180,Y
 TAY
 JMP M222BrosEnemyValue
M222BrosNativeEnemy:
 LDY Map_EnterViaID
M222BrosEnemyValue:
 LDA BattleEnemy_ByEnterID,Y
 JMP M222BrosDone
M222BrosNotEnemy:
 CPY #16
 BNE M222BrosNo
 ; A genuine transformed Coin Ship uses its accepted narrow proof, regardless
 ; of the untransformed battle assignment. No assigned battle overrides it.
 LDA Map_EnterViaID
 CMP #11
 BEQ M222BrosNativePrize
 JSR M222BrosFindRow
 BCC M222BrosNativePrize
 JSR M222BrosStrict
 BCC M222BrosNo
 JSR M222BrosActive
 BCC M222BrosNo
 LDA Map_ReturnStatus
 BNE M222BrosNo
 SEC
 JMP M222BrosDone
M222BrosNativePrize:
 LDA Map_ReturnStatus
 BEQ M222BrosYes
 CMP #1
 BNE M222BrosNo
 LDA Map_EnterViaID
 CMP #11
 BNE M222BrosNo
 LDA $7EB9
 CMP #$B8
 BNE M222BrosNo
 LDA $7EBA
 CMP #$BC
 BNE M222BrosNo
 LDA $7EBB
 CMP #$0F
 BNE M222BrosNo
 LDA $7EBC
 CMP #$DA
 BNE M222BrosNo
M222BrosYes:
 SEC
 BCS M222BrosDone
M222BrosNo:
 CLC
M222BrosDone:
 TAY
 PLA
 TAX
 TYA
 RTS

M222BrosFind:
 JSR M222BrosFindRow
 BCC M222BrosFindDone
 JMP M222BrosStrict
M222BrosFindRow:
 LDY $D100
 BEQ M222BrosNotFound
 DEY
M222BrosRow:
 LDA World_Num
 CMP $D120,Y
 BNE M222BrosNext
 LDA $79E9
 CMP $D140,Y
 BEQ M222BrosRowFound
M222BrosNext:
 DEY
 BPL M222BrosRow
M222BrosNotFound:
 CLC
 RTS
M222BrosRowFound:
 SEC
M222BrosFindDone:
 RTS
M222BrosStrict:
 LDA $79AE
 CMP #1
 BNE M222BrosNotFound
 LDA $79A2
 CMP #2
 BNE M222BrosNotFound
 LDA $0726
 BNE M222BrosNotFound
 LDA $072B
 CMP #1
 BNE M222BrosNotFound
 LDA $79E7
 CMP $D120,Y
 BNE M222BrosNotFound
 LDA $79E6
 CMP $D260,Y
 BNE M222BrosNotFound
 LDA Map_EnterViaID
 CMP $D160,Y
 BNE M222BrosNotFound
 LDA $79EA
 CMP $D160,Y
 BNE M222BrosNotFound
 LDX $79E9
 LDA $7F15,X
 CMP $D160,Y
 BNE M222BrosNotFound
 LDA $79EB
 CMP $D240,Y
 BNE M222BrosNotFound
 LDA $7956,X
 CMP $D240,Y
 BNE M222BrosNotFound
 SEC
 RTS
M222BrosActive:
 LDA Level_Event
 CMP #7
 BNE M222BrosActiveNo
 LDA Level_Tileset
 CMP $D1A0,Y
 BNE M222BrosActiveNo
 LDA $7EB9
 CMP $D1C0,Y
 BNE M222BrosActiveNo
 LDA $7EBA
 CMP $D1E0,Y
 BNE M222BrosActiveNo
 LDA $7EBB
 CMP $D200,Y
 BNE M222BrosActiveNo
 LDA $7EBC
 CMP $D220,Y
 BNE M222BrosActiveNo
 SEC
 RTS
M222BrosActiveNo:
 CLC
 RTS
M222BrosEnd:
