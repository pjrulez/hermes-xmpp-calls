# Conduit comparison

Two unrelated apps share the name.
- **Hermes Conduit** (hermesconduit.app): Apple only (iPhone, Watch, CarPlay). Live voice via Gemini/GPT/Grok/Local Live. Not usable on Android.
- **cogwheel0/conduit** (Flutter, iOS and Android, GPL-3.0): has a Hermes Agent mode and a call mode.

How cogwheel0/conduit calls Hermes (PR #842, merged 2026-10-13):
- Realtime call: WebRTC through `flutter_webrtc`. It posts an SDP offer to the dashboard `POST /api/audio/voice-live/session`; Hermes relays it to OpenAI (GPT-Live). Audio never terminates in Hermes. Needs `voice.voice_chat_mode: gpt-live` and an OpenAI key. Not local.
- Standard call: turn-based, uses `/api/audio/transcribe` and `/api/audio/speak` for the connection's profile. Works with local providers in principle (U).
- Takeaway for this project: Hermes has no server-side WebRTC peer to reuse. The XMPP call engine is new code. Conduit still gives a design reference for endpointing, barge-in (cancel reply, tell the model how much was heard), approvals during calls, and fallback rules.

Not chosen as the primary path: user wants XMPP calls, self-hosted audio, and one app (Conversations) for voice notes, text and calls.
