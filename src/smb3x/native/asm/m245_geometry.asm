; Fixed-at-open geometry, current camera, and bounded PPU command descriptors.
UiConfigure:
 LDA $12
 ASL A
 ASL A
 ASL A
 ASL A
 STA UiCamera
 LDA $FD
 LSR A
 LSR A
 LSR A
 LSR A
 ORA UiCamera
 STA UiCamera
 CLC
 ADC #1
 STA UiStartMeta
 AND #1
 CLC
 ADC #7
 STA UiAttrCount
 LDA #4
 LDX $9F3D
 BNE UiConfigurePages
 LDA #3
UiConfigurePages:
 STA UiPageCount
 LDA #14
 STA UiAnchor
 LDA #10
 STA UiHeight
 LDA Menu
 CMP #1
 BNE UiConfigureProgression
 LDA #16
 STA UiAnchor
 LDA #8
 STA UiHeight
 JMP UiConfigureBounds
UiConfigureProgression:
 LDA UiPage
 CMP #1
 BNE UiConfigureBounds
 ; Native player spans Y-16..Y+16; the southern candidate extends toY+32.
 ; Protect that entire48-pixel union plus a one-pixel safety margin.
 LDA $75
 CMP #32
 BCC UiConfigureRefuse
 CMP #161
 BCS UiConfigureRefuse
 CMP #112
 BCC UiConfigureLower
 LDA #4
 STA UiAnchor
 JMP UiConfigureHammer
UiConfigureLower:
 LDA #18
 STA UiAnchor
UiConfigureHammer:
 LDA #6
 STA UiHeight
 JMP UiConfigureBounds
UiConfigureRefuse:
 LDA #0
 STA UiPage
 LDA #1
 STA UiError
UiConfigureBounds:
 LDA UiAnchor
 CLC
 ADC UiHeight
 ASL A
 ASL A
 ASL A
 STA UiBottom
 LDA UiAnchor
 ASL A
 ASL A
 ASL A
 SEC
 SBC #16
 STA UiTop
 LDA UiAnchor
 CLC
 ADC UiHeight
 SEC
 SBC #1
 LSR A
 LSR A
 STA UiAttrRows
 LDA UiAnchor
 LSR A
 LSR A
 STA UiAttrRow
 LDA UiAttrRows
 SEC
 SBC UiAttrRow
 CLC
 ADC #1
 STA UiAttrRows
 CLC
 ADC UiHeight
 STA UiTotalRows
 RTS

UiDescriptor:
 LDX UiRow
 CPX UiHeight
 BCS UiDescriptorAttr
 LDA UiCacheLow,X
 STA UiCacheLo
 LDA UiCacheHigh,X
 STA UiCacheHi
 LDA UiRow
 CLC
 ADC UiAnchor
 PHA
 LSR A
 LSR A
 LSR A
 ORA #$28
 STA UiHi
 PLA
 AND #7
 ASL A
 ASL A
 ASL A
 ASL A
 ASL A
 STA UiLo
 LDA UiStartMeta
 ASL A
 AND #31
 ORA UiLo
 STA UiLo
 AND #31
 EOR #31
 CLC
 ADC #1
 CMP #28
 BCC UiDescriptorFirst
 LDA #28
UiDescriptorFirst:
 STA UiFirstCount
 LDA #28
 STA UiCount
 LDA UiStartMeta
 JMP UiDescriptorBank
UiDescriptorAttr:
 TXA
 SEC
 SBC UiHeight
 ASL A
 ASL A
 ASL A
 STA UiCacheLo
 LDA #$72
 STA UiCacheHi
 LDA UiRow
 SEC
 SBC UiHeight
 CLC
 ADC UiAttrRow
 ASL A
 ASL A
 ASL A
 ORA #$C0
 STA UiLo
 LDA UiStartMeta
 LSR A
 AND #7
 STA UiAttrColumn
 ORA UiLo
 STA UiLo
 LDA UiAttrCount
 STA UiCount
 LDA UiAttrColumn
 EOR #7
 CLC
 ADC #1
 CMP UiCount
 BCC UiDescriptorAttrFirst
 LDA UiCount
UiDescriptorAttrFirst:
 STA UiFirstCount
 LDA #$2B
 STA UiHi
 LDA UiStartMeta
UiDescriptorBank:
 AND #$10
 LSR A
 LSR A
 ORA UiHi
 STA UiHi
 RTS

UiAttributeMask:
 LDA UiRow
 CMP UiHeight
 BNE UiAttributeLast
 LDA UiAnchor
 AND #2
 BEQ UiAttributeLast
 LDA #$F0
 RTS
UiAttributeLast:
 LDA UiRow
 CLC
 ADC #1
 CMP UiTotalRows
 BNE UiAttributeFull
 LDA UiAnchor
 CLC
 ADC UiHeight
 AND #2
 BEQ UiAttributeFull
 LDA #$0F
 RTS
UiAttributeFull:
 LDA #$FF
 RTS
