; M20 data banking uses the original SMB3 sound decoder.
; Source audit: Southbird PRG028/029/031. Constants supplied from verified rebuild.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 28
 .org $BE17
AudioExtension:
AudioTick:
 LDA SndCur_Music2
 JSR SelectAudioBank
 JMP Sound_PlayMusic
SelectAudioBank:
 CMP #$D0
 BCC NativeAudioBank
 CMP M20CustomLimit
 BCS NativeAudioBank
 AND #$0F
 ORA #$20
 BNE MapAudioBank
NativeAudioBank:
 LDA #29
MapAudioBank:
 PHA
 LDA #$46
 STA $8000
 PLA
 STA $8001
 RTS
QueueMusic:
 CMP #$D0
 BCC QueueNative
 CMP M20CustomLimit
 BCS QueueInvalid
 STA SndCur_Music2
 JSR SelectAudioBank
 LDY #0
 STY SndCur_Music1
 LDA $C000
 STA Music_Start
 LDA $C001
 CLC
 ADC #2
 STA Music_End
 LDA $C002
 STA Music_Loop
 LDA Music_Start
 JMP SndMus2B_NextOrStop
QueueInvalid:
 ; An unallocated additional selector must never read a blank PRG bank.
 LDA #$10
QueueNative:
 PHA
 JSR NativeAudioBank
 PLA
 STA SndCur_Music2
 JMP SndMus_QueueSet2B+3
LoadCustomHeader:
 LDA SndCur_Music2
 CMP #$D0
 BCC LoadNativeHeader
 CMP M20CustomLimit
 BCS LoadNativeHeader
 LDA $C00F,Y
 TAY
 LDA $C040,Y
 STA Music_RestH_Base
 LDA $C041,Y
 STA Music_Base_L
 LDA $C042,Y
 STA Music_Base_H
 LDA $C043,Y
 STA Music_TriTrkPos
 LDA $C044,Y
 STA Music_Sq1TrkOff
 LDA $C045,Y
 STA Music_NseTrkPos
 STA Music_NseStart
 LDA $C046,Y
 STA Music_PCMTrkPos
 STA Music_PCMStart
 JMP PRG031_E48C
LoadNativeHeader:
 LDA Music_Set2B_IndexOffs-1,Y
 JMP SndMus2B_LoadNext+3
LoadEventHeader:
 JSR NativeAudioBank
 LDA Music_Set1_Set2A_IndexOffs-1,Y
 JMP SndMus2A_LoadNext+3
M20CustomLimit:
 .byte $D0
AudioExtensionEnd:
