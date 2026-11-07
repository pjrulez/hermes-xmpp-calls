## 1. Research gates (finish before planning the build)

Evidence names the file that must exist before the box is ticked. "Operator" = needs the Conversations device.

- [x] R1 aiortc, av, aioice, slixmpp import and loopback on fw Python 3.14.9. Evidence: `RESEARCH/evidence/loopback-result.txt`.
- [x] R2 Inventory slixmpp Jingle support. Evidence: `RESEARCH/00-summary.md` finding 4.
- [ ] R3 Capture real calls from Dino, Conversations and Monal (logger bot, redacted `propose`, `session-initiate`, caps, termination). Operator. Evidence: `RESEARCH/evidence/conversations-session-initiate.xml`. (`dep-slixmpp-jingle` T1)
- [x] R4 Review prior art, license terms, reuse decision, choose approach A/B/C/D. Evidence: `RESEARCH/05-approach-decision.md`. (`dep-slixmpp-jingle` T2)
- [ ] R5 slixmpp 1.15.0 vs 1.17.0 add-on compatibility. Evidence: `RESEARCH/evidence/slixmpp-compat.txt`. (`dep-slixmpp-jingle` T3)
- [ ] R6 Endpointing comparison on recorded speech. Evidence: `RESEARCH/evidence/endpointing.txt`. (`dep-aiortc-media` T4)
- [ ] R7 Call-path STT/TTS via Hermes provider functions, first-audio latency with `fw_queue`. Evidence: `RESEARCH/evidence/tts-stt-call-path.txt`. (`dep-hermes-call-integration` T1)
- [ ] R8 Plugin integration points (authorization, injection, reply interception, hooks). Evidence: `RESEARCH/06-plugin-integration.md`. (`dep-hermes-call-integration` T2)
- [ ] R9 Platform matrix: aiortc/av on Python 3.14 (fw), 3.14 tools python on VMs, 3.11. Evidence: `RESEARCH/evidence/platform-matrix.txt`. (`dep-aiortc-media` T1)
- [ ] R10 Bot fetches XEP-0215 credentials and gathers a relay candidate. Evidence: `RESEARCH/evidence/turn-fetch.txt`. (`dep-prosody-server` P3)

## 2. Build (outline; order, sizes and owners set in the planning stage)

- [ ] B1 `jingle/` layer: stanzas, state machine, SDP conversion, unit tests with fixtures from R3. (`dep-slixmpp-jingle`)
- [ ] B2 Echo-call bot against Conversations. Operator test. (`dep-slixmpp-jingle` + `dep-aiortc-media`)
- [ ] B3 `media/` engine on its own loop thread, resampling, pacing, teardown tests. (`dep-aiortc-media`)
- [ ] B4 Endpointing and transcript into a session (text reply logged). (`dep-hermes-call-integration`)
- [ ] B5 Sentence-streamed speech in the agent voice. (`dep-hermes-call-integration`)
- [ ] B6 Barge-in and heard-fraction note. (`dep-hermes-call-integration`)
- [ ] B6b Outgoing calls: JMI initiation, ring timeout, opening synthesized during ringing, agent tool and cron use. Operator. (`dep-hermes-call-integration`)
- [ ] B7 Plugin integration behind `xmpp.calls.enabled`, authorization, limits, failure isolation, `plugin.yaml` dependencies. (all)
- [ ] B8 Layer-boundary and leak tests (50-call loop). (`dep-aiortc-media`)
- [ ] B9 fw trial with the production account after review. Operator.
- [ ] B10 README compatibility statement and Prosody checklist. (`dep-prosody-server`)
- [ ] B11 Rollout change for mad and django (separate change, needs VM Python decision).
