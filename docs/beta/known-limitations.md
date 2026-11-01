<!-- SPDX-License-Identifier: MPL-2.0 -->
# Known beta limitations

- Windows x64, official AP 0.6.8 and exact supported BizHawk 2.10/2.11/2.11.1
  NesHawk installations only. No other emulator/platform qualification is implied.
- Safe automatic checkpoints are not continuous or exact mid-level crash saves.
  Normal close does not guarantee an additional checkpoint. Map movement alone
  may Resume at the prior progress-save position.
- Existing games are bound to their original emulator/core and runtime. No
  cross-version State migration, arbitrary State loading, reset/rewind recovery,
  old-room migration or checkpoint transplantation is supported.
- Some uncertified rooms retain native content. Shuffle modes use their certified
  compatibility boundaries; no all-arrangement/full-campaign claim is made.
- Private R3 music and external soundtrack packs are not included or supported by
  this build. Use Vanilla/Shuffled native music. No World 9 or Classic Level Pack.
- Automated fixtures include assisted navigation/goal approach and synthetic
  rooms. No exhaustive human multiplayer, every-option or complete human eight-world
  campaign certification is claimed. Desktop dialogs/controller setup and every
  other APWorld combination have not been exhaustively tested.
- The three specific native adaptation groups in the licensing notice retain
  unresolved copyright interpretations. No legal clearance is asserted.

[Checkpoint details](player-guide.md#checkpoints-and-resume) ·
[Emulator qualification](../emulator-qualification.md) · [Licensing](licensing.md)
