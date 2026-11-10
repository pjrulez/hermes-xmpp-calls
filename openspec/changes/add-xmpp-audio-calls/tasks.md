## 1. Research gates (finish before planning the build)

Evidence names the file that must exist before the box is ticked. "Operator" = needs the Conversations device.

- [x] R1 aiortc, av, aioice, slixmpp import and loopback on fw Python 3.14.9. Evidence: `RESEARCH/evidence/loopback-result.txt`.
- [x] R2 Inventory slixmpp Jingle support. Evidence: `RESEARCH/00-summary.md` finding 4.
- [x] R3 (Dino and Conversations done 2026-11-07, Monal before final acceptance) Capture real calls from Dino, Conversations and Monal (logger bot, redacted `propose`, `session-initiate`, caps, termination). Operator. Evidence: `RESEARCH/evidence/conversations-session-initiate.xml`. (`dep-slixmpp-jingle` T1)
- [x] R4 Review prior art, license terms, reuse decision, choose approach A/B/C/D. Evidence: `RESEARCH/05-approach-decision.md`. (`dep-slixmpp-jingle` T2)
- [ ] R5 slixmpp 1.15.0 vs 1.17.0 add-on compatibility. Evidence: `RESEARCH/evidence/slixmpp-compat.txt`. (`dep-slixmpp-jingle` T3)
- [x] R6 Endpointing comparison on recorded speech. Evidence: `RESEARCH/evidence/endpointing.txt`. (`dep-aiortc-media` T4)
- [ ] R7 Call-path STT/TTS via Hermes provider functions, first-audio latency with `fw_queue`. Evidence: `RESEARCH/evidence/tts-stt-call-path.txt`. (`dep-hermes-call-integration` T1)
- [ ] R8 Plugin integration points (authorization, injection, reply interception, hooks). Evidence: `RESEARCH/06-plugin-integration.md`. (`dep-hermes-call-integration` T2)
- [ ] R9 Platform matrix: aiortc/av on Python 3.14 (fw), 3.14 tools python on VMs, 3.11. Evidence: `RESEARCH/evidence/platform-matrix.txt`. (`dep-aiortc-media` T1)
- [ ] R10 Bot fetches XEP-0215 credentials and gathers a relay candidate. Evidence: `RESEARCH/evidence/turn-fetch.txt`. (`dep-prosody-server` P3)

## 2. Build (outline; order, sizes and owners set in the planning stage)

- [x] B1 `jingle/` layer: stanzas, state machine, SDP conversion, unit tests with fixtures from R3. (`dep-slixmpp-jingle`) Evidence: `src/xmpp_calls/jingle/`, tests `tests/test_jingle_*.py`.
- [x] B2 Echo-call bot against Conversations. Operator test. (`dep-slixmpp-jingle` + `dep-aiortc-media`) Evidence: operator-run 2026-11-07, `RESEARCH/evidence/echo-signaling.txt`.
- [x] B3 `media/` engine on its own loop thread, resampling, pacing, teardown tests. (`dep-aiortc-media`) Evidence: `src/xmpp_calls/media.py`, `tests/test_media_*.py`.
- [x] B4 Endpointing and transcript into a session (text reply logged). (`dep-hermes-call-integration`) Evidence: `src/xmpp_calls/conversation.py`, live calls 2026-11-08.
- [x] B5 Sentence-streamed speech in the agent voice. (`dep-hermes-call-integration`) Evidence: `speech.py`, live calls 2026-11-08.
- [x] B6 Barge-in and heard-fraction note. (`dep-hermes-call-integration`) Evidence: queue/steer/stop; steer seen live ("steered the running turn").
- [x] B6b Outgoing calls: JMI initiation, ring timeout, opening synthesized during ringing, agent tool and cron use. Operator. (`dep-hermes-call-integration`) Evidence: live: agent calls operator, missed-call text, call-back note.
- [x] B7 Plugin integration behind `xmpp.calls.enabled`, authorization, limits, failure isolation, `plugin.yaml` dependencies. (all) Evidence: plugin glue, `plugin/tests/test_calls_glue.py`, live on the fw gateway.
- [x] B8 Layer-boundary and leak tests (50-call loop). (`dep-aiortc-media`) Evidence: `RESEARCH/evidence/leak-loop.txt` (50 calls: fds 10->10, threads 2->2, tasks 1->1; `RUN_LEAK=1 pytest tests/test_leaks.py`).
- [ ] B9 fw trial with the production account after review. Operator.
- [ ] B10 README compatibility statement and Prosody checklist. (`dep-prosody-server`)
- [ ] B11 Rollout change for mad and django (separate change, needs VM Python decision).

- [ ] B12 Final release gate for later additions (see `specs/call-lifecycle`, `specs/agent-collaboration`, and `specs/lifecycle-hardening`): hang-up grace and beeps, request completion after hang-up, recap, missed-call text, session titles, ringing, `xmpp_message`, partner guards and OMEMO key safety. Offline security/lifecycle reviews and the leak loop are recorded in `RESEARCH/security-review.md` and `RESEARCH/lifecycle-review.md`; README and CHANGELOG describe the implementation. Refresh the separate PR branch from the final verified tree, obtain operator approval of deployment steps, retest the deployed build, and obtain exact PR-text approval before publication.

- [ ] B13 Spoken 30-second heads-up before `max_seconds` (see `specs/call-lifecycle`, requirement "Call time limit with spoken heads-up"). Specified only; deliberately not implemented in the first plugin PR. Not extendable by design.
