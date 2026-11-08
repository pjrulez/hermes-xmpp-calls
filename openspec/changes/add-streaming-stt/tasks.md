## Tasks (ordered; evidence file in brackets; operator-run tasks marked)

- [ ] 1. Gate G1: first plugin PR published; this change starts after it.
- [ ] 2. Replay corpus: record 20 short call recordings (Conversations and Dino, quiet room, noisy room, interruptions) with operator-approved transcripts; keep them out of git. Harness replays them through batch and streaming at real time and writes WER, final-latency and turn-count tables. [RESEARCH/evidence/stt-corpus.md] (operator-run recording)
- [ ] 3. Baseline: run the harness on batch Orukeet and Whisper large-v3-turbo; record the numbers that the acceptance targets are measured against. [RESEARCH/evidence/stt-baseline.txt]
- [ ] 4. Gate G2: confirm the fw streaming endpoint matches the contract in `design.md` with a recorded handshake, busy and drop test. [RESEARCH/evidence/stt-service-contract.txt] (fw audio session)
- [ ] 5. `StreamingSpeech` and a fake streaming server for tests; unit tests for feed, reset, busy, drop. [tests/test_stream_speech.py]
- [ ] 6. Fallback path: busy at start, drop mid-call, error at finalize; three-strike rule. [tests/test_stream_fallback.py]
- [ ] 7. Text-aware endpointer with a table-driven test for sentence end, comma, open-clause word, short text, mute, maximum length. [tests/test_text_endpointing.py]
- [ ] 8. Recognizer-confirmed turns: empty final creates no turn and no beep. [tests/test_conversation.py]
- [ ] 9. Word-aware barge-in and steer on `stable` text. [tests/test_conversation.py]
- [ ] 10. Per-turn timing log line and a script that computes medians from a log. [scripts/turn_timings.py]
- [ ] 11. Config keys, README options table, security review of the new socket (auth, TLS or tailnet-only, frame size limits). [plugin/README.md, RESEARCH/evidence/stt-security.md]
- [ ] 12. Replay corpus through the full path; compare with task 3 against the acceptance targets. [RESEARCH/evidence/stt-results.txt]
- [ ] 13. Live acceptance calls from Conversations and Dino, noise test, kill-the-service test. [RESEARCH/evidence/stt-live.txt] (operator-run)
- [ ] 14. Second PR text drafted for operator approval; no publication before the operator approves the exact text and a live retest of the deployed build.
