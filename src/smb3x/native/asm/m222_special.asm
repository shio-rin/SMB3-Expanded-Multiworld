; Bounded original special-content context. PRG52 is mapped only through the
; accepted fixed trampoline, extended by relocating the four-byte external
; render lookup from E2B8 to its verified adjacent E2BC..E2BF slack.
; No physical World_Num change and no new persistent RAM.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 31
 .org $E29F
M222BankCall:
 LDA PAGE_C000
 PHA
 ; Commands0..9 remain in51. Commands10..12 use52.
 CPY #10
 LDA #51
 ADC #0
 STA PAGE_C000
 JSR PRGROM_Change_C000
 JSR $C000
 TAY
 PLA
 STA PAGE_C000
 JSR PRGROM_Change_C000
 TYA
 RTS
M222BankCallEnd:
 .bank 3
 .org $BFED
M222OrbEffect:
 LDY #10
 JMP $E29F
M222OrbEffectEnd:
 .bank 20
 .org $C000
M222SpecialDispatch:
 CPY #10
 BNE M222NotOrb
 JMP M222ResolveOrb
M222NotOrb:
 CPY #11
 BNE M222NotTense
 ; Nested call restores52 before returning here.
 LDY #8
 JSR $E29F
 CMP #0
 BNE M222LateTense
 LDA #$30
 RTS
M222LateTense:
 LDA #$18
 RTS
M222NotTense:
 CPY #12
 BNE M222NotSpeed
 LDY #8
 JSR $E29F
 CMP #0
 BNE M222LateSpeed
 LDA #$18
 BNE M222SpeedDirection
M222LateSpeed:
 LDA #$20
M222SpeedDirection:
 LDY Temp_Var16
 BEQ M222SpeedReady
 EOR #$FF
 CLC
 ADC #1
M222SpeedReady:
 RTS
M222NotSpeed:
 CPY #13
 BNE M222NotSecret
 JMP M222SecretTreasure
M222NotSecret:
 CPY #14
 BCC M222UnknownSpecial
 JMP $C300
M222UnknownSpecial:
 LDA #0
 RTS

M222ResolveOrb:
 ; The hook runs only at the native orb timer1 terminal, after its real hit
 ; and score conversion. A configured host must match its assigned boss area.
 TXA
 PHA
 LDA $79AE
 CMP #1
 BNE M222RejectOrb
 LDA $79A2
 CMP #2
 BNE M222RejectOrb
 LDA $0726
 BNE M222RejectOrb
 LDA $072B
 CMP #1
 BNE M222RejectOrb
 LDY $C7FF
 BEQ M222NativeOrb
 DEY
M222OrbRow:
 LDA World_Num
 CMP $C800,Y
 BNE M222OrbNext
 LDA $7978
 CMP $C900,Y
 BNE M222OrbNext
 LDA $797A
 CMP $CA00,Y
 BNE M222OrbNext
 LDA $7976
 CMP $CB00,Y
 BNE M222OrbNext
 LDA Level_Tileset
 CMP $CC00,Y
 BNE M222RejectOrb
 LDA $7EB9
 CMP $CD00,Y
 BNE M222RejectOrb
 LDA $7EBA
 CMP $CE00,Y
 BNE M222RejectOrb
 JSR M222OrbObjects
 BCC M222RejectOrb
 LDA Level_ObjectID,X
 CMP #$4A
 BNE M222RejectOrb
 LDA Objects_Timer,X
 CMP #1
 BNE M222RejectOrb
 LDA Objects_Var5,X
 BEQ M222RejectOrb
 LDA $CF00,Y
 JMP M222StoreOrb
M222OrbNext:
 DEY
 BPL M222OrbRow
M222NativeOrb:
 LDA Objects_Var4,X
 JMP M222StoreOrb
M222RejectOrb:
 ; Fail closed: native return may continue, but no host clear or map effect.
 LDA #1
 STA Map_ReturnStatus
 LDA #0
M222StoreOrb:
 STA Map_DoFortressFX
 PLA
 TAX
 LDA Map_DoFortressFX
 RTS
M222SecretTreasure:
 ; Invoked solely by the accepted Whistle reward-suppression hook. Bind the
 ; actual hidden area and assigned source; do not turn a room departure into
 ; a completion event. Native chest handling still owns exit and map return.
 LDA $79AE
 CMP #1
 BEQ M222SecretBound
 RTS
M222SecretBound:
 LDA $79A2
 CMP #2
 BNE M222SecretDone
 LDA $0726
 BNE M222SecretDone
 LDA $072B
 CMP #1
 BNE M222SecretDone
 LDA $79E2
 CMP #12
 BNE M222SecretDone
 LDA Level_Tileset
 CMP #2
 BNE M222SecretDone
 LDA $7EB9
 CMP #$2A
 BNE M222SecretDone
 LDA $7EBA
 CMP #$AA
 BNE M222SecretDone
 JSR M222SecretObjects
 BCC M222SecretDone
 LDY $C7FF
 BEQ M222SecretLegacy
 DEY
M222SecretRow:
 LDA World_Num
 CMP $C800,Y
 BNE M222SecretNext
 LDA $7978
 CMP $C900,Y
 BNE M222SecretNext
 LDA $797A
 CMP $CA00,Y
 BNE M222SecretNext
 LDA $7976
 CMP $CB00,Y
 BNE M222SecretNext
 LDA $D000,Y
 BEQ M222SecretDone
 LDA $CF00,Y
 STA Map_DoFortressFX
 RTS
M222SecretNext:
 DEY
 BPL M222SecretRow
M222SecretLegacy:
 LDA World_Num
 ORA $7978
 BNE M222SecretDone
 LDA $797A
 CMP #$60
 BNE M222SecretDone
 LDA $7976
 CMP #$60
 BNE M222SecretDone
 LDA #1
 STA Map_DoFortressFX
M222SecretDone:
 RTS
M222SpecialEnd:
 .org $C700
M222OrbObjects:
 LDA $7EBB
 CMP $D680,Y
 BNE M222WrongObjects
 LDA $7EBC
 CMP $D700,Y
 BNE M222WrongObjects
 SEC
 RTS
M222WrongObjects:
 CLC
 RTS
M222SecretObjects:
 LDA $7EBB
 CMP #$51
 BNE M222WrongObjects
 LDA $7EBC
 CMP #$D3
 BNE M222WrongObjects
 SEC
 RTS
M222ObjectsEnd:
 .org $C740
M222SecretTerminal:
 LDY $C7FF
 BEQ M222SecretTerminalDone
 DEY
M222SecretTerminalRow:
 LDA World_Num
 CMP $C800,Y
 BNE M222SecretTerminalNext
 LDA $7978
 CMP $C900,Y
 BNE M222SecretTerminalNext
 LDA $797A
 CMP $CA00,Y
 BNE M222SecretTerminalNext
 LDA $7976
 CMP $CB00,Y
 BEQ M222SecretTerminalMatched
M222SecretTerminalNext:
 DEY
 BPL M222SecretTerminalRow
M222SecretTerminalDone:
 RTS
M222SecretTerminalMatched:
 LDA $D000,Y
 CMP #1
 BNE M222SecretTerminalReject
 LDA $79AE
 CMP #1
 BNE M222SecretTerminalReject
 LDA $79A2
 CMP #2
 BNE M222SecretTerminalReject
 LDA $0726
 BNE M222SecretTerminalReject
 LDA $072B
 CMP #1
 BNE M222SecretTerminalReject
 LDA Level_Tileset
 CMP #2
 BNE M222SecretTerminalReject
 LDA $7EB9
 CMP #$2A
 BNE M222SecretTerminalReject
 LDA $7EBA
 CMP #$AA
 BNE M222SecretTerminalReject
 JSR M222SecretObjects
 BCC M222SecretTerminalReject
 LDA $0566
 CMP #7
 BNE M222SecretTerminalReject
 LDA $7CF1
 BNE M222SecretTerminalReject
 LDA $7963
 CMP #12
 BNE M222SecretTerminalReject
 LDA $CF00,Y
 STA Map_DoFortressFX
 RTS
M222SecretTerminalReject:
 LDA #1
 STA Map_ReturnStatus
 LDA #0
 STA Map_DoFortressFX
 RTS
M222SecretTerminalEnd:
