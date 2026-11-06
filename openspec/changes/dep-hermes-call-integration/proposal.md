## Why

The call must behave like any other Hermes conversation: same authorization, session, tools, memory and approvals, same STT and TTS providers and the agent voice, without touching `stt`/`tts` configuration. Hermes 0.22.5 has no server-side WebRTC peer, so the plugin has to use supported Hermes interfaces for transcription, turn injection, reply interception and speech.

## What changes

- Determine the supported plugin APIs to transcribe an utterance and synthesize sentences in-process with the configured providers and voice.
- Add the call controller inside the plugin adapter: authorization, flag, state, limits, session mapping, reply interception, hangup marker, interruption note.
- Declare dependencies and config keys in `plugin.yaml`.

## Out of scope

Hermes core changes, dashboard use as the primary path, new providers, per-call model overrides (later).

## Dependencies

Hermes 0.22.5 plugin API, the fork's adapter, `fw-audio-hermes` providers.

## Acceptance

R7 and R8 evidence exists; a text-only call turn (B4) produces a session turn from speech; spoken replies use the agent voice with the first sentence audible early (B5); barge-in note reaches the model (B6).
