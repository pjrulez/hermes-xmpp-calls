## Why

Voice notes work end to end. The operator wants live calls: call the agent from Conversations on Android, talk, hear streamed answers, interrupt. A few seconds of latency is fine if replies stream. Audio stays on the local stack (Whisper and PocketTTS on fw through `fw-audio-control`). Text, MUC and voice-note behavior must not change.

## Current state (verified or sourced in `RESEARCH/00-summary.md`)

- `hermes-xmpp-plugin` fork (`feat/voice-messages`, 03fd781) handles text, MUC and voice notes; no call code.
- slixmpp 1.15.0 and 1.17.0 lack Jingle core, RTP, ICE-UDP, DTLS and XEP-0215 (finding 4).
- aiortc 1.16.0 with av 19.0.2 and aioice 0.13.0 loops back with DTLS-SRTP and Opus on Python 3.14.9 (findings 1, 2).
- Prior art with the same stack reports Conversations calls working: `xmpp-radio-tower`; and a Hermes call pipeline exists for Delta Chat (findings 7, 8).
- Local audio is fast (TTS about 0.6 s per two sentences, STT 0.4 s per 7 s); the agent turn dominates latency (finding 10).
- Prosody on mad has `turn_external`, carbons, csi, cloud_notify, and a coturn container, but `prosodyctl check turn` fails from the container (finding 18).

## What changes

One umbrella delivers the whole feature inside the plugin fork:
1. A Jingle RTP signaling stack (XEP-0166/0167/0176/0320/0215 plus 0353 JMI) as slixmpp add-ons: `dep-slixmpp-jingle`.
2. A media engine on aiortc, on its own event loop thread, with resampling, pacing and clean teardown: `dep-aiortc-media`.
3. A conversation loop that reuses the configured Hermes STT and TTS providers, per-agent voices, sentence streaming and barge-in, wired into the plugin through supported Hermes APIs: `dep-hermes-call-integration`.
4. Verified Prosody server requirements and checks, documented in the README: `dep-prosody-server`.
5. Single-plugin delivery: installing the fork next to Hermes is the whole install.

## Non-goals (first release)

Video, group or MUC calls, outgoing calls (agent calls the user), OMEMO fingerprint shield, rollout to mad and django, upstream publication, any change to `stt` or `tts` provider configuration, replacing voice notes.

## Dependencies and gates

- Each dependency change has its own gate list; the umbrella build phase starts after R3, R4 and P2 produce evidence.
- Every media milestone needs an operator-run Conversations Android test.
- Prototypes use a dedicated bot JID. Production gateway account stays untouched until the engine is behind a default-off flag and reviewed.

## Acceptance

An operator-run call from Conversations Android to the fw agent where the call connects, speech is transcribed, the agent answers aloud in its voice within a few seconds with the first sentence audible before the full reply is synthesized, speaking over the agent cuts it off within 500 ms, hangup releases every resource, and text and voice notes still work during and after the call. Evidence records counters and timings, not audio or secrets.
