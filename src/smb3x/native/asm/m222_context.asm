; Scoped content context through the existing fixed bank51 dispatcher.
; No new fixed-bank allocation, no new RAM, no physical-world writes.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 26
 .org $BFE0
M222SourceWorldY:
 PHA
 LDY #8
 JSR $E29F
 PLA
 RTS
M222SourceWorldYEnd:
 .bank 5
 .org $BFFB
M222PiranhaTimer:
 LDY #9
 JMP $E29F
 .org $C000
M222PiranhaTimerEnd:
 .bank 20
 .org $D700
M222Dispatch:
 CPY #8
 BNE M222NotSource
 JMP M222FindSourceWorld
M222NotSource:
 CPY #9
 BNE M222OriginalDispatch
 JSR M222FindSourceWorld
 CMP #0
 BNE M222NativeTimer
 LDA Objects_Timer,X
 CMP #$28
 BNE M222ZeroTimer
 LDA #$10
 RTS
M222ZeroTimer:
 LDA #0
 RTS
M222NativeTimer:
 LDA Objects_Timer,X
 RTS
M222OriginalDispatch:
 CPY #7
 BNE M222OriginalContinue
 JMP $C680
M222OriginalContinue:
 JMP $C007
M222FindSourceWorld:
 TXA
 PHA
 LDY World_Num
 LDA Level_Tileset
 BEQ M222ContextDone
 LDX $D6FF
 BEQ M222ContextDone
 DEX
M222ContextNext:
 TYA
 CMP $C880,X
 BNE M222ContextSkip
 LDA $7978
 CMP $C980,X
 BNE M222ContextSkip
 LDA $797A
 CMP $CA80,X
 BNE M222ContextSkip
 LDA $7976
 CMP $CB80,X
 BNE M222ContextSkip
 LDY $CC80,X
 JMP M222ContextDone
M222ContextSkip:
 DEX
 BPL M222ContextNext
M222ContextDone:
 PLA
 TAX
 TYA
 RTS
M222ContextEnd:
