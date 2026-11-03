# 0.36.3 private hotfix evidence

Private candidate only. No release, tag, merge, installed APWorld replacement or
played-session migration is part of this change. Current main `ec96ef6` was fetched
before branching; its README and documentation are preserved.

## Changes and safety boundaries

The accepted 0.36.2 archive (full identity below) reproduces the chained
matching-card lock. Native
automatic entry continues advancing frames while an uncommitted save request
suppresses input and waits for a settled overworld. The controller now explicitly
defers that request when native encounter entry invalidates the opportunity. It
retains dirty progress and the request. Published grants, unacknowledged grants,
completed grant batches, capture/restore, connection and uncertain-write ownership
continue to hold input.

Short exact-baseline trace: frame 4431 is map operation 13, safe, requested,
quiescing, stable=1. At frame 4432 native operation becomes 15, safe=false,
stable=0, yet quiescing/input suppression persists without a grant/ack owner.
Frame 4483 loads the bonus introduction; frame 4970 loads matching cards. Native
frames continue to 14797 while input remains zero. The first incorrect transition
is retaining exclusive save input ownership at frame 4432.

A second overlap was found with an AP item: delivery's old settled-map counter
survived periods when the checkpoint owner did not call delivery processing. It
could publish on the first return frame before automatic entry. Settlement now
requires 30 consecutive native frames; duplicate calls on one frame cannot count
twice. Native grant/acknowledgement semantics remain unchanged.

Hammer Bros. uses the shared boundary, without changing its movement or identity
rules. The native landing validator rejects a cleared ordinary-level tile. The
legal two-encounter chain passes on both baseline and candidate: movement goes
directly into automatic entry before the save request. The first encounter in the
candidate fixture enters after a completed checkpoint, and a different roaming
slot enters after its completion. No movement is manufactured during a frozen
State operation. Unit regressions additionally exercise pending-request timing.

There is no blanket fortress exclusion in the current native effect predicate.
The reproducible failure is the scheduler canceling a pending delay when a doorway
changes room identity. The fix retains the selected receipt, entry limit and
remaining active-frame delay across rooms. Destination-room eligibility still
applies. Native pause, death, exits, transformations and save ownership remain
excluded; Micro-Goomba graphics/slot/water restrictions remain effect-specific.
Late receipts still wait for a later entry. Already-small Forced Small remains a
valid no-op. Existing active-effect cleanup is unchanged.

Victory uses **credits entry**. The existing native ending-v1 producer already
observes authentic Bowser defeat (phase 1), the genuine Peach door (phase 2), then
credits entry (phase 3). Controller phase 2 is a different field. The delay was
the Python requirement that ending evidence equal an ordinary map checkpoint.
No native event, persisted phase meaning or ROM instruction is changed.

A small goal-only `ENDING.json` record is written and read back after authenticated
native/journal reconciliation. It binds the session, ROM/runtime binding, native
sequence, current verified checkpoint ancestry, physical-check set and received
server-history prefix. It cannot restore RAM, add checks or replay grants. It is
not created while grant, capture, restore or uncertain ownership is active. Resume
validates it before changing the epoch. Existing goal prerequisites and saved
physical-check publication remain mandatory. Network submission and server
confirmation remain separate; an uncertain submission can be reasserted.

Closing during credits resumes the latest verified map State, with trustworthy
completion retained separately. Known discarded gameplay still uses the existing
loss acknowledgement. This does not introduce cutscene State saves.

## Newly executed verification

All native runs used disposable official AP 0.6.8 rooms and copied managed emulator
roots. No completion bits, successful receipt records, checkpoint outcomes or
ending phases were injected. Route/position, spawn threshold, movement counter,
native suit queue and contact-protection assistance are disclosed below. These
are automated native tests, not new human/controller acceptance.

| Case | New result |
| --- | --- |
| Exact accepted 0.36.2 N-Spade | First game reward; return/save request; automatic second entry; advancing native frames with quiescing/input zero indefinitely. No flight or acknowledgement owned the hold. |
| Candidate chained N-Spade, 2.10 | Genuine level check, AP Leaf receipt/use/save, two native matching games, AP arrival and reconnect during chain, second exit/save, cold Resume. Four each of native Mushroom/Flower/Star rewards; one additional AP Mushroom; consumed Leaf stays consumed. |
| Single matching game, 2.11.1 | Native completion, reward, return and checkpoint. |
| Hammer Bros., baseline and candidate 2.11 | Native movement validation/collision, two distinct battles, native combat/chest collection, separate physical check IDs and receipt bits, AP overlap, save and cold Resume. |
| Nearby scenes, 2.11.1 | Static Spade reels, Toad House chest, inventory menu and return saves; queued Micro-Goomba remains unapplied in these scenes. |
| Exact 0.36.2 fortress doorway | Pending Walking Only delay canceled on room change; receipt retained but never activates during that entry. |
| Fixed doorway | Delay retained through native doorway, Walking Only activates in destination room and expires after 600 active frames. |
| Fortress mechanics | Forced Small 2.10, Icy Feet 2.11, Micro-Goomba 2.11.1: actual native callbacks/behavior and cleanup. Direct engine probes isolate mechanics from the separate managed scheduling tests. |
| Helpful/shared predicates | Starman 2.11, Emergency Mushroom 2.10; remote death 2.11.1 observed with no local-death echo. Ordinary-level Walking Only positive control. |
| Multi-room/boss, 2.10 | Native doorway sequence, Icy Feet activation/expiry with live Boom Boom, native stomp defeat/orb/fortress exit saved. Contact protection and route approach assisted; no boss state or completion writes. |
| Mixed Fortresses and pause, 2.11 | Official generation places W6 Fortress 3 at W1-2. Actual assigned layout loads; native pause suspends delay; Walking Only activates and expires. |
| Death/re-entry, 2.11.1 | Assisted pit approach crosses native death boundary; scheduled receipt requeues, then activates/completes once on entry 2. |
| Genuine ending, 2.11.1 | Native Bowser AI breaks floor/falls, real door into Peach, natural credits entry; durable record, Standard submission and server confirmation during credits. Credits, THE END and native postgame return proceed; map checkpoint succeeds. |
| Ending reconnect/close/Resume | Reconnect during credits, confirmed goal, ordinary close during credits, cold Resume to prior verified map with goal retained; normal delivery handles server auto-release items. |
| Uncertain goal send, 2.10 | First StatusUpdate deliberately dropped with socket closure; reconnect reasserts and server confirms during credits. |
| Ending write failure, 2.11 | Actual native credits event, injected pre-write storage error: no terminal record, no goal submission/confirmation; safety suspension retained. |
| Maintained tests | 235 pass, including 7 shared input-owner regressions, 3 continuous-settlement tests, doorway/restricted-effect tests and 8 durable-ending tests and 4 goal-transport tests. Mock State/RAM tests are not native execution. |

Ending prerequisite combinations (Standard, all seven Koopalings, all enabled
locations, missing-check negatives) and corrupt/foreign/uncertain terminal records
are source/unit tested. Castle-room entry and unrelated Up/door interactions in
the actual native route leave ending/goal unset. Star/access rules and guarded
native instructions are byte-identical; this work does not claim a new full
Star-gated campaign or exhaustive fortress layout qualification.

Initial exploratory native fixtures used 0.36.0 by mistake. They are not cited as
exact 0.36.2 baseline proof; both reported failures and the passing Hammer chain
were rerun against the accepted 0.36.2 archive. Failed route experiments, an
impossible landing setup, a fixture JSON-read race, and a short postgame run that
ended while draining server auto-release items remain private failed evidence.
The latter still establishes credits/return/checkpoint observations, not a full
fixture pass. No previous campaign/report was silently promoted to new evidence.

## Package and applicability

Accepted baseline source: `7a4438a840116d279ff9688ded1c0e1b7f26d3fb`.
Accepted baseline archive SHA256:
`88e4766294c4ed6687229114069d6d4d7d228b6bc6e68b8fd65f1c351f9a60e3`.

Candidate APWorld **0.36.3**, private **36.0.3-rc2**, runtime **m36-python-4**.
Packaged source: `a630e1f5a7a56f6da2c94c75185acc34b3333843`.
Resource identity:
`daa01d0a5fc8604f91c1b28903ae6e375c525d04620bfdbc3c74a83644b199ac`.
Archive SHA256:
`0f87ff4d6e503ffe5b3c306ac9353ca28cbab60383b8cda7d366f30e23cb6054`.
Recipe SHA256:
`93e291104527ba7a9578d3b5bba1989772bcdb5ee3d1d3d7ad622d2ac50c9f51`.

Independent clean-source reproduction matches the complete archive. The earlier
combined native candidate differs only in network/service transport resources;
those two files were corrected after review. All Lua, native and persistence
resources used for the earlier native cases remain byte-identical. Source closure verifies 220 resources and 13 unchanged
native assembly certificates. No ROM, State, private room details or raw logs are
included in source or PR attachments.

Existing player files dispatch to their embedded resource runtime. Installing this
APWorld does **not** update an already-generated room. These fixes apply to newly
generated compatible games. No cached-runtime patch, transplantation or migration
is supplied. Existing non-pristine emulator installation support is preserved;
the maintained installation/profile tests pass for 2.10, 2.11 and 2.11.1/NesHawk.

The single GPT-6.1 Sol / High independent review found one reconnect blocker:
AP CommonClient resends a prior goal before SMB3X's Connected callback validates
history. Generic CLIENT_GOAL sends are now filtered; only the validated watcher
uses the explicit goal transport, with owner checks before and after its await.
The reviewer checked the correction, independently ran four transport regressions,
and verified the final archive/reproduction/source closure. No remaining actionable
finding. The reviewer inspected native evidence; it did not rerun BizHawk. Final
rc2 native reruns are recorded separately below. Raw evidence and disposable retest
helpers remain local.

## Final archive checks after review

The exact rc2 archive completed the integrated 2.11 lifecycle: native W1-1 clear,
AP Leaf receipt, native consumption, checkpoint, two consecutive N-Spades, an AP
Mushroom during the chain, reconnect, second-game exit/save, ordinary close and
cold Resume. The inventory is identical after Resume (five Mushrooms, four Flowers,
four Stars, consumed Leaf absent); one physical level check and two handled AP
receipts remain, with no pending receipt. The three maintained transition
regressions also fail when run against the original Lua sources.

The exact rc2 ending test on 2.10 deliberately dropped the first **explicit watcher**
goal send and closed the socket. On reconnect the trace records received-history
validation, a second watcher submission, then the server Goal broadcast while
credits continue. Ordinary close during credits and cold Resume retain confirmed
goal status. The restored State still has native ending phase 0, while the separate
validated terminal record retains phase 3. No physical check was fabricated.
The server's normal Standard-goal auto-release delivered 125 additional items;
all 126 indexed receipts were handled once and saved, with none pending.

A separate full native ending/postgame run on the identical Lua/persistence
resources completed credits, THE END, native return and the final map checkpoint,
including all auto-release delivery. Its earlier short timed-out predecessor
remains a failed fixture, not substituted evidence. Storage-fault and remaining
native-mechanics runs predate the transport-only review correction; their relevant
Lua/native/persistence bytes are unchanged.

The final clean reproduction passes all **235 maintained tests**. Main was fetched
again before handoff and remains `ec96ef6`. Local retest helpers generate fresh
disposable setups: the card helper plays the first game and leaves the second to
the owner; the ending helper reaches the real credits boundary without a campaign.
No new human acceptance or exhaustive campaign/layout coverage is claimed.
