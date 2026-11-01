; Content identity lookup. No physical completion or progression state is written.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 31
 .org $E241
ContentCall:
 LDA PAGE_C000
 PHA
 LDA #48
 STA PAGE_C000
 JSR PRGROM_Change_C000
 JSR $C000
 TAY
 PLA
 STA PAGE_C000
 JSR PRGROM_Change_C000
 TYA
 RTS
ContentCallEnd:
 .org $E270
MusicContentCall:
 SEC
 JMP ContentCall
PaletteContentCall:
 CLC
 JMP ContentCall
ContentWrappersEnd:
; Assemble into an unused output bank; builder relocates this payload to bank48.
 .bank 20
 .org $C000
ContentExtension:
 BCC PaletteContent
 LDA GamePlay_BGM,X
 PHA
 JSR FindContent
 BCC MusicFallback
 LDA $CB00,X
 BEQ MusicFallback
 TAY
 PLA
 TYA
 RTS
MusicFallback:
 PLA
 RTS
PaletteContent:
 LDA Level_Tileset
 BEQ MapPalette
 JSR FindContent
 BCC PaletteDone
 LDA $CC00,X
 BEQ PaletteDone
 ASL A
 ASL A
 ASL A
 ASL A
 TAY
 LDX #0
PaletteCopy:
 LDA $CD00,Y
 STA Pal_Data,X
 INY
 INX
 CPX #16
 BNE PaletteCopy
PaletteDone:
 LDA Pal_Data
 RTS
MapPalette:
 LDX World_Num
 LDA $CE00,X
 BEQ PaletteDone
 ASL A
 ASL A
 ASL A
 ASL A
 TAY
 LDX #0
 BEQ PaletteCopy
FindContent:
 LDX $C7FF
 BEQ ContentNotFound
 DEX
FindNext:
 LDA Level_Tileset
 CMP $C800,X
 BNE FindSkip
 LDA Level_LayPtrOrig_AddrL
 CMP $C900,X
 BNE FindSkip
 LDA Level_LayPtrOrig_AddrH
 CMP $CA00,X
 BNE FindSkip
 SEC
 RTS
FindSkip:
 DEX
 BPL FindNext
ContentNotFound:
 CLC
 RTS
ContentExtensionEnd:
