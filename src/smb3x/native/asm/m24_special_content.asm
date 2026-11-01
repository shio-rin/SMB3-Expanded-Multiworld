; Experimental special palette loader. M24 plus guarded native-airship fallback.
; No persistent RAM. Temporary pointer is saved/restored on the stack.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
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
 ; BQ visits retain the parent's Orig pointer and backup tileset. Resolve a
 ; separately authored bonus selection through that immutable parent identity.
 LDA LevelJctBQ_Flag
 BEQ OrdinaryPalette
 JSR FindBQParent
 BCC PaletteDone
 LDA $CF00,X
 JMP SelectPalette
OrdinaryPalette:
 JSR FindContent
 BCC AirshipFallback
 LDA $CC00,X
 JMP SelectPalette
AirshipFallback:
 ; Native MO_Airship overrides the active pointer after Orig was captured.
 ; No parent latch: type2 selects its fixed world deck, only on a lookup miss.
 LDA Level_Tileset
 CMP #10
 BNE PaletteDone
 LDA Map_EnterViaID
 CMP #2
 BNE PaletteDone
 LDX World_Num
 CPX #7
 BCS PaletteDone
 LDA $CE10,X
 JMP SelectPalette
MapPalette:
 LDX World_Num
 CPX #8
 BCS PaletteDone
 LDA $CE00,X
SelectPalette:
 BEQ PaletteDone
 CMP $CE08
 BCS PaletteDone
 TAY
 LDA <Temp_Var1
 PHA
 LDA <Temp_Var2
 PHA
 LDA $CE20,Y
 STA <Temp_Var1
 LDA $CE60,Y
 STA <Temp_Var2
 LDY #0
PaletteCopy:
 LDA [Temp_Var1],Y
 STA Pal_Data,Y
 INY
 CPY #16
 BNE PaletteCopy
 PLA
 STA <Temp_Var2
 PLA
 STA <Temp_Var1
PaletteDone:
 LDA Pal_Data
 RTS
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
 CPX #$FF
 BNE FindNext
ContentNotFound:
 CLC
 RTS
FindBQParent:
 LDX $C7FF
 BEQ ContentNotFound
 DEX
FindBQNext:
 LDA Level_JctBackupTileset
 CMP $C800,X
 BNE FindBQSkip
 LDA Level_LayPtrOrig_AddrL
 CMP $C900,X
 BNE FindBQSkip
 LDA Level_LayPtrOrig_AddrH
 CMP $CA00,X
 BNE FindBQSkip
 SEC
 RTS
FindBQSkip:
 DEX
 CPX #$FF
 BNE FindBQNext
 CLC
 RTS
ContentExtensionEnd:
