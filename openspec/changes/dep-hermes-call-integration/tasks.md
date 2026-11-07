## 1. Tasks

- [ ] T1 In-process STT and TTS call path with per-agent voice, timing with `fw_queue` (R7). Evidence: `RESEARCH/evidence/tts-stt-call-path.txt`.
- [ ] T2 Plugin integration map (R8). Evidence: `RESEARCH/06-plugin-integration.md`.
- [ ] T3 Call controller with fake engine and fake Hermes: states, authorization, limits.
- [ ] T4 Session mapping and reply interception.
- [ ] T5 Sentence splitter and speech rules for markup, code, URLs.
- [ ] T6 Barge-in note and heard-fraction estimate.
- [ ] T7 Hangup marker and spoken error messages.
- [ ] T8 `plugin.yaml` dependency and config declarations; clean-install test.
- [ ] T8b Agent tool to place a call with an opening, usable from cron jobs; documented limits (one call, ring timeout, allowed JIDs only).
- [ ] T9 End-to-end fw trial with a bot JID, then production account. Operator.
