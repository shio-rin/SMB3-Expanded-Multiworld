; M21 ordinary-block poison. No new RAM; sprite attribute bit2 is ignored by
; the NES PPU and belongs to all eight slots. NEVER use Objects_Var3+5: that
; address belongs to SpecialObj_YHi[0], not the power-up slot.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 1
 .org $BFB0
M21MushroomInit:
 JSR Mushroom_SetFall
 CPX #5
 BNE M21InitDone
 LDA Level_ObjectID,X
 CMP #$0D
 BNE M21InitDone
 LDY #1
 JSR M21HazardCall
 BEQ M21InitDone
 LDA #7
 STA Objects_SprAttr,X
M21InitDone:
 RTS
M21MushroomHit:
 LDA Objects_SprAttr,X
 AND #4
 BEQ M21OrdinaryHit
 LDA #0
 STA Objects_State,X
 JMP Player_GetHurt
M21OrdinaryHit:
 LDA #1
 STA Temp_Var1
 JMP PRG001_A897
M21PoisonInitEnd:
 .org $B81A
M21ChoosePowerup:
 CPY #2
 BEQ M21Eligible
 CPY #3
 BEQ M21Eligible
 CPY #5
 BNE M21OrdinaryPowerup
M21Eligible:
 TYA
 PHA
 LDY #0
 JSR M21HazardCall
 CMP #1
 PLA
 TAY
 BCC M21OrdinaryPowerup
 LDA #$0D
 RTS
M21OrdinaryPowerup:
 LDA Bouncer_PUp,Y
 RTS
M21PoisonChooseEnd:
 .bank 5
 .org $BFC6
M21SunWait:
 LDY #2
 JSR M21HazardCall
 CMP #2
 BEQ M21SunActivate
 CMP #1
 BEQ M21SunPending
 ; No matching seeded encounter: preserve the original page-five test.
 LDA #0
 STA Objects_Frame,X
 JMP Sun_WaitFarEnough+5
M21SunPending:
 LDA #0
 STA Objects_Frame,X
 RTS
M21SunActivate:
 JMP PRG005_ADF6
M21SunInit:
 LDY #3
 JSR M21HazardCall
 RTS
M21SunWaitEnd:
 .org $BFEA
M221SunEdge:
 ; Frame1 allocates two additional edge sprites outside Object_SprRAM.
 ; Remap those at their native draw sites, preserving their random OAM slots.
 LDA PatTable_BankSel+4
 CMP #136
 BNE M221SunEdgeNative
 LDA #$A1
 BNE M221SunEdgeStore
M221SunEdgeNative:
 LDA #$91
M221SunEdgeStore:
 STA Sprite_RAM+1,Y
 RTS
M221SunEdgeEnd:
 .bank 7
 .org $BFE5
M21DrawFinish:
 JSR Gameplay_UpdateAndDrawMisc
 LDY #4
 JMP M21HazardCall
M21DrawFinishEnd:
 .bank 31
 .org $E29F
M21HazardCall:
 LDA PAGE_C000
 PHA
 LDA #51
 STA PAGE_C000
 JSR PRGROM_Change_C000
 JSR $C000
 TAY
 PLA
 STA PAGE_C000
 JSR PRGROM_Change_C000
 TYA
 RTS
M21HazardCallEnd:
 .org $FF2A
M221SelectCollision:
 ; Original initializer supplies Y=0/1. Preserve A and native bank state.
 PHA
 STY Level_SlopeEn
 LDY #6
 JSR M21HazardCall
 PLA
 LDY Level_SlopeEn
 RTS
M221SelectCollisionEnd:
 .org $FF38
M221SpriteBank:
 ; Five-byte selector in the last original reset-padding bytes. The banked
 ; helper reloads the native request and restores Y; caller overwrites A.
 LDY #7
 JMP M21HazardCall
M221SpriteBankEnd:
 .bank 20
 .org $C000
M21HazardLookup:
 CPY #7
 BNE M221NotSpriteBank
 JMP M221SetSpriteBank
M221NotSpriteBank:
 CPY #6
 BNE M221NotCollision
 JMP M221FlatCollision
M221NotCollision:
 CPY #5
 BNE M221NotEnemyCopy
 JMP M221InsertSun
M221NotEnemyCopy:
 CPY #4
 BNE M21LookupOrdinary
 JMP M21PoisonGraphics
M21LookupOrdinary:
 CPY #2
 BCC M21PoisonLookup
 JMP M21SunLookup
M21PoisonLookup:
 ; Y=0 is ordinary upward block reveal; Y=1 is slot5 mushroom init.
 CPY #1
 BEQ M21InitCoordinates
 CPX #6
 BCC M21NoPoison
 LDA Objects_Var2,X
 BEQ M21NoPoison
 LDA Objects_Y,X
 STA Temp_Var1
 LDA Objects_YHi,X
 STA Temp_Var2
 JMP M21LookupCoordinates
M21InitCoordinates:
 LDA Objects_Y,X
 CLC
 ADC #1
 STA Temp_Var1
 LDA Objects_YHi,X
 ADC #0
 STA Temp_Var2
M21LookupCoordinates:
 LDY $C7FF
 BEQ M21NoPoison
 DEY
M21PoisonNext:
 LDA Level_Tileset
 CMP $C800,Y
 BNE M21PoisonSkip
 LDA Level_LayPtrOrig_AddrL
 CMP $C900,Y
 BNE M21PoisonSkip
 LDA Level_LayPtrOrig_AddrH
 CMP $CA00,Y
 BNE M21PoisonSkip
 LDA Objects_X,X
 CMP $CB00,Y
 BNE M21PoisonSkip
 LDA Objects_XHi,X
 CMP $CC00,Y
 BNE M21PoisonSkip
 LDA Temp_Var1
 CMP $CD00,Y
 BNE M21PoisonSkip
 LDA Temp_Var2
 CMP $CE00,Y
 BNE M21PoisonSkip
 LDA #1
 RTS
M21PoisonSkip:
 DEY
 BPL M21PoisonNext
M21NoPoison:
 LDA #0
 RTS
M21HazardLookupEnd:
 .org $C100
M21SunLookup:
 STY Temp_Var3
 LDY $CFFF
 BEQ M21SunNative
 DEY
M21SunNext:
 LDA Level_Tileset
 CMP $D000,Y
 BNE M21SunSkip
 LDA Level_LayPtrOrig_AddrL
 CMP $D100,Y
 BNE M21SunSkip
 LDA Level_LayPtrOrig_AddrH
 CMP $D200,Y
 BNE M21SunSkip
 LDA Temp_Var3
 CMP #3
 BEQ M21SunPosition
 LDA Player_XHi
 CMP $D300,Y
 BCC M21SunNotYet
 BNE M21SunReady
 LDA Player_X
 CMP $D400,Y
 BCC M21SunNotYet
M21SunReady:
 LDA #2
 RTS
M21SunNotYet:
 LDA #1
 RTS
M21SunSkip:
 DEY
 BPL M21SunNext
M21SunNative:
 LDA #0
 RTS
M21SunPosition:
 ; Native original Sun starts near the left of the camera. A late enemy-list
 ; insertion starts at its right edge and is deleted before its first attack.
 ; Restore the original safe screen-relative origin only for seeded areas.
 LDA Horz_Scroll
 CLC
 ADC #32
 STA Objects_X,X
 LDA Horz_Scroll_Hi
 ADC #0
 STA Objects_XHi,X
 LDA #0
 RTS
M21SunLookupEnd:
 .org $C200
M21PoisonGraphics:
 TXA
 PHA
 TYA
 PHA
 JSR M221SunGraphics
 PLA
 TAY
 PLA
 TAX
 ; Runs in the main thread AFTER all object, score and projectile drawing.
 ; The gameplay entry resets common sprites to bank4 each frame. No NMI work.
 LDA PatTable_BankSel+3
 CMP #4
 BNE M21GraphicsDone
 LDA Objects_SprAttr+5
 AND #4
 BEQ M21GraphicsDone
 ; Reuse native common-page mushroom51 and its mirrored draw unchanged.
 ; Objects_SprAttr low bits3 select existing amber/pink palette; bit2 remains
 ; the collision marker ignored by PPU. No CHR switch or palette writes.
M21GraphicsDone:
 RTS
M21PoisonGraphicsEnd:

 ; Only original, explicitly reviewed horizontal outdoor identities reach here.
 ; Keep native source pointers and reciprocal junction identities unchanged.
 .org $C300
M221InsertSun:
 LDY $CFFF
 BEQ M221InsertDone
 DEY
M221InsertLookup:
 LDA $D600,Y
 BEQ M221InsertSkip
 LDA Level_Tileset
 CMP $D000,Y
 BNE M221InsertSkip
 LDA Level_LayPtrOrig_AddrL
 CMP $D100,Y
 BNE M221InsertSkip
 LDA Level_LayPtrOrig_AddrH
 CMP $D200,Y
 BNE M221InsertSkip
 LDA $D500,Y
 STA Temp_Var2
 LDX #1
M221CheckList:
 LDA Level_Objects,X
 CMP #$FF
 BEQ M221ListEnd
 CMP #$AF
 BEQ M221InsertDone
 INX
 INX
 INX
 CPX #142
 BCC M221CheckList
 RTS
M221InsertSkip:
 DEY
 BPL M221InsertLookup
M221InsertDone:
 RTS
M221ListEnd:
 STX Temp_Var4
 LDY #1
M221FindPosition:
 CPY Temp_Var4
 BEQ M221PositionFound
 LDA Level_Objects+1,Y
 CMP Temp_Var2
 BCS M221PositionFound
 INY
 INY
 INY
 BNE M221FindPosition
M221PositionFound:
 STY Temp_Var1
 LDY Temp_Var4
M221ShiftList:
 LDA Level_Objects,Y
 STA Level_Objects+3,Y
 DEY
 CPY Temp_Var1
 BCS M221ShiftList
 LDY Temp_Var1
 LDA #$AF
 STA Level_Objects,Y
 LDA Temp_Var2
 STA Level_Objects+1,Y
 LDA #17
 STA Level_Objects+2,Y
 RTS
 .org $C600
M221FlatCollision:
 ; Use native flat floor/wall/ceiling attributes for this slope-free content.
 ; Match loaded identity, never a physical world/entrance or player appearance.
 LDA Level_Tileset
 CMP #3
 BNE M221CollisionDone
 LDA Level_LayPtrOrig_AddrL
 CMP #LOW(M221SmwLayout)
 BNE M221CollisionDone
 LDA Level_LayPtrOrig_AddrH
 CMP #HIGH(M221SmwLayout)
 BNE M221CollisionDone
 LDA #0
 STA Level_SlopeEn
M221CollisionDone:
 LDA Level_SlopeEn
 RTS
 .org $C640
M221SunArea:
 LDA Level_Tileset
 CMP #9
 BNE M221SunAreaPlains
 LDA #M221SunDesertEnabled
 BEQ M221SunAreaNo
 LDA Level_LayPtrOrig_AddrL
 CMP #$3A
 BNE M221SunAreaNo
 LDA Level_LayPtrOrig_AddrH
 CMP #$B7
 BNE M221SunAreaNo
 BEQ M221SunAreaYes
M221SunAreaPlains:
 CMP #1
 BNE M221SunAreaNo
 LDA #M221SunPlainsEnabled
 BEQ M221SunAreaNo
 LDA Level_LayPtrOrig_AddrL
 CMP #$BC
 BNE M221SunAreaNo
 LDA Level_LayPtrOrig_AddrH
 CMP #$B8
 BNE M221SunAreaNo
M221SunAreaYes:
 LDA #136
 RTS
M221SunAreaNo:
 LDA #0
 RTS
 .org $C680
M221SetSpriteBank:
 LDY ObjGroupRel_Idx
 LDA ObjectGroup_PatTableSel,Y
 AND #$7F
 CPX #0
 BNE M221SetSpriteStore
 CMP #10
 BEQ M221SetSpriteLookup
 CMP #50
 BNE M221SetSpriteStore
M221SetSpriteLookup:
 PHA
 JSR M221SunArea
 CMP #136
 PLA
 BCC M221SetSpriteStore
 LDA #136
M221SetSpriteStore:
 STA PatTable_BankSel+4,X
 TYA
 RTS
 .org $C700
M221SunGraphics:
 ; Only the reviewed original2-5/3-7 identities. CHR136 copies bank10 and
 ; moves Sun90..9B to A0..AB, unused by their Chomp/Spike object sets.
 LDA Level_Tileset
 CMP #9
 BNE M221SunTryPlains
 LDA Level_LayPtrOrig_AddrL
 CMP #$3A
 BNE M221SunGraphicsDone
 LDA Level_LayPtrOrig_AddrH
 CMP #$B7
 BNE M221SunGraphicsDone
 BEQ M221SunGraphicsArea
M221SunTryPlains:
 CMP #1
 BNE M221SunGraphicsDone
 LDA Level_LayPtrOrig_AddrL
 CMP #$BC
 BNE M221SunGraphicsDone
 LDA Level_LayPtrOrig_AddrH
 CMP #$B8
 BNE M221SunGraphicsDone
M221SunGraphicsArea:
 LDA PatTable_BankSel+4
 CMP #136
 BEQ M221SunGraphicsSlots
 JMP M221SunGraphicsDone
M221SunGraphicsSlots:
 LDX #4
M221SunGraphicsNext:
 LDA Objects_State,X
 BEQ M221SunGraphicsSkip
 LDA Level_ObjectID,X
 CMP #$AF
 BEQ M221SunGraphicsFound
M221SunGraphicsSkip:
 DEX
 BPL M221SunGraphicsNext
M221SunGraphicsDone:
 RTS
M221SunGraphicsFound:
 LDY Object_SprRAM,X
 LDX #6
M221SunGraphicsSprite:
 LDA Sprite_RAM+1,Y
 CMP #$91
 BCC M221SunGraphicsAdvance
 CMP #$9C
 BCS M221SunGraphicsAdvance
 CLC
 ADC #$10
 STA Sprite_RAM+1,Y
M221SunGraphicsAdvance:
 INY
 INY
 INY
 INY
 DEX
 BNE M221SunGraphicsSprite
 LDA #136
 STA PatTable_BankSel+4
 RTS
M221HazardsEnd:

 .bank 26
 .org $BFD8
M221CopyEnemyList:
 JSR LevelLoad_CopyObjectList
 LDY #5
 JMP M21HazardCall
M221CopyEnemyListEnd:
