# Hermes integration points

Installed Hermes: v0.22.5 on fw. Status S unless noted.

- The XMPP plugin runs inside the gateway process. A call engine must not run its media on the gateway event loop. `hermes-deltachat-platform` documents why: aiortc ICE and RTP are asyncio tasks; when the agent turn starved the loop, ICE stalled and RTP died after about 4 s. Their fix: a dedicated event loop in its own daemon thread for every aiortc object. Adopt the same.
- Audio loop reference (deltachat docs): per-utterance buffering, about 1 s silence ends a turn, transcript enters the normal session pipeline, the reply is intercepted and spoken, sentence-by-sentence TTS drops time-to-first-audio to one sentence, barge-in after about 0.25 s of RMS-gated voiced audio, the model is told how much of its reply was heard, `[[hangup]]` marker ends the call, unauthorized callers are declined unanswered.
- Hermes dashboard routes (not running on fw now): `POST /api/audio/transcribe`, `POST /api/audio/speak`, `GET /api/audio/voice-config`, `WS /api/audio/transcribe-stream` (PCM in, partial/final text out, falls back when no streaming STT provider exists), `WS /api/audio/speak-stream` (text deltas in, int16 PCM out per sentence, `stop` = barge-in). Command providers synthesize per sentence through `text_to_speech_tool`. U17: confirm with `fw_queue`.
- STT and TTS configuration stays as is: `stt.provider: fw_queue`, `tts` via `fw_queue`. Calls reuse these providers and the per-agent voice map (`fw=javert`, `mad=eve`, `django=george`).
- Measured on fw (V): PocketTTS 2 sentences 0.57-0.69 s, Whisper large-v3-turbo on 7.3 s of speech 0.37 s. Audio is not the bottleneck; the LLM turn is.
- Queue constraints: the fw audio gateway for mad/django allows one transient remote job and 6 requests per minute. A call on fw uses the local interactive queue. Calls on mad/django need a rate review (later phase).
- Decoded audio from aiortc is 48 kHz s16, possibly stereo; resample to 16 kHz mono for Whisper, and encode TTS output to 48 kHz for Opus.
