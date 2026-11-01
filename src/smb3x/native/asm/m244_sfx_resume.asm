; Private experiment m244-sfx-resume-1. Southbird PRG028/031 decoder.
; Only exact accepted effect-free R3 payloads: current note is cursor minus one.
; No new persistent RAM. $6D is the native frequency calculator's dead scratch.
 .inesprg 16
 .ineschr 0
 .inesmap 4
 .inesmir 0
 .bank 28
 .org $BECB
ResumePulse1:
 STX $4015
 PHP
 PHA
 TXA
 PHA
 TYA
 PHA
 LDX #2
 BNE ResumeCommon
ResumePulse2:
 STX $4015
 PHP
 PHA
 TXA
 PHA
 TYA
 PHA
 LDX #0
ResumeCommon:
 TXA
 PHA
 LDA SndCur_Music1
 BEQ CheckCustom
 JMP ResumePop
CheckCustom:
 LDA SndCur_Music2
 CMP #$D0
 BCC ResumePop
 CMP M20CustomLimit
 BCS ResumePop
 ; Do not touch another owner or the last tick of an expiring note.
 CPX #0
 BEQ CheckPulse2
 LDA SndCur_Map
 BNE ResumePop
CheckPulse2:
 LDA Music_Sq2Rest,X
 CMP #2
 BCC ResumePop
 LDA SndCur_Music2
 JSR SelectAudioBank
 CPX #0
 BEQ ReadPulse2
 LDY Music_Sq1TrkOff
 JMP ReadCurrent
ReadPulse2:
 LDY Music_Sq2TrkOff
ReadCurrent:
 DEY
 LDA [Music_Base_L],Y
 CMP #$7E
 BEQ ResumeRest
 ; Defensive rejection of commands/terminators. Accepted banks have no bends.
 CMP #$7E
 BCS ResumePop
 CMP #0
 BEQ ResumePop
 CPX #0
 BEQ PlayPulse2
 JSR Sound_Sq1_NoteOn_NoPAPURAMP
 JMP ResumeEnvelope
PlayPulse2:
 JSR Sound_Sq2_NoteOn_NoPAPURAMP
ResumeEnvelope:
 PLA
 TAX
 CPX #0
 BEQ HoldPulse2
 LDA Music_Sq1RestH
 JMP AgeEnvelope
HoldPulse2:
 LDA Music_Sq2RestH
AgeEnvelope:
 PHA
 SEC
 SBC Music_Sq2Rest,X
 STA <Sound_Sqr_FreqL
 PLA
 CMP #19
 LDA #$3F
 BCS EnvelopeLength
 LDA #$16
EnvelopeLength:
 SEC
 SBC <Sound_Sqr_FreqL
 BCS StoreEnvelope
 LDA #0
StoreEnvelope:
 STA Music_Sq2NoteLen,X
 JMP ResumeDone
ResumeRest:
 PLA
 TAX
 LDA #0
 STA Music_Sq2NoteLen,X
 JMP ResumeDone
ResumePop:
 PLA
ResumeDone:
 PLA
 TAY
 PLA
 TAX
 PLA
 PLP
 RTS
ResumeEnd:
