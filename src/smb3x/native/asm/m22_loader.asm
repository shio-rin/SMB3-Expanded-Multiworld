; Virtual layout $8600..$9FFF maps to copied native generator/data banks.
; This hook runs before the native PRGROM_Change_Both2; no mapper writes here.
; Original content pointer remains virtual for junctions and audiovisual lookup.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 31
 .org $E25A
M21RenderBank:
 LDA Level_LayPtrOrig_AddrH
 CMP #$86
 BCC M21OriginalRenderBank
 CMP #$A0
 BCS M21OriginalRenderBank
 CPY #3
 BEQ M21ReturnHills
 CPY #14
 BNE M21OriginalRenderBank
 JMP M21ReturnUnder
M21RenderBankEnd:
 .org $E279
M21TerrainBank:
 LDA <Level_LayPtr_AddrH
 CMP #$86
 BCC M21OriginalBank
 CMP #$A0
 BCS M21OriginalBank
 CPY #3
 BEQ M21HillsBank
 CPY #14
 BNE M21OriginalBank
 CLC
 ADC #$20
 STA <Level_LayPtr_AddrH
M21ReturnUnder:
 LDA #50
 RTS
M21HillsBank:
 CLC
 ADC #$20
 STA <Level_LayPtr_AddrH
M21ReturnHills:
 LDA #49
 RTS
M21OriginalBank:
 LDA PAGE_A000_ByTileset,Y
 RTS
M21TerrainBankEnd:
 .org $E2B8
M21OriginalRenderBank:
 LDA TileLayoutPage_ByTileset,Y
 RTS
M21OriginalRenderBankEnd:
 .bank 16
 .org $A580
M21Backdrop:
 ; External-only generator76: noncolliding tile0D rectangle. Width<=128.
 LDY #0
 LDA [Level_LayPtr_AddrL],Y
 STA Temp_Var3
 INC Level_LayPtr_AddrL
 BNE M21BackdropRead
 INC Level_LayPtr_AddrH
M21BackdropRead:
 LDA LL_ShapeDef
 AND #15
 STA Temp_Var4
 LDA Map_Tile_AddrL
 STA Temp_Var1
 LDA Map_Tile_AddrH
 STA Temp_Var2
M21BackdropRow:
 LDY TileAddr_Off
 LDX Temp_Var3
M21BackdropColumn:
 LDA #$0D
 STA [Map_Tile_AddrL],Y
 JSR LoadLevel_NextColumn
 DEX
 BPL M21BackdropColumn
 LDA Temp_Var1
 STA Map_Tile_AddrL
 LDA TileAddr_Off
 CLC
 ADC #16
 STA TileAddr_Off
 LDA Temp_Var2
 ADC #0
 STA Temp_Var2
 STA Map_Tile_AddrH
 DEC Temp_Var4
 BPL M21BackdropRow
 RTS
M21BackdropEnd:
