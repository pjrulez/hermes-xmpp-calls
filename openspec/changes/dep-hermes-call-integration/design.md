## Context

Facts: STT/TTS configured through `fw_queue` command providers; dashboard routes exist but the dashboard does not run on fw; the adapter already handles authorization for messages and voice notes; `hermes-deltachat-platform` shows a working Hermes call pipeline.

## Design

- `conversation/` module adapts the engine to Hermes: transcription function, turn submit, reply stream, speech function, each injected into the controller so tests use fakes.
- Reply interception: calls route replies to the call speaker instead of chat, with chat fallback on failure and a short note in chat for the transcript.
- Sentence splitting reuses Hermes' chunker if public, else a small sentence cutter documented and tested.
- Voice from the agent voice map; the plugin passes the voice through the configured TTS path. The path used by voice notes is the reference.
- Config: `xmpp.calls.enabled`, `xmpp.calls.max_seconds`, `xmpp.calls.idle_seconds`, `xmpp.calls.max_utterance_seconds`, `xmpp.calls.silence_ms`, `xmpp.calls.barge_in_ms`. Set via `hermes config set`.
- Failure isolation: all call handlers wrapped; exceptions end the call, not the session.

## Risks

Unstable internal Hermes APIs across updates. Mitigation: use public plugin hooks only, add version guard, smoke test.
