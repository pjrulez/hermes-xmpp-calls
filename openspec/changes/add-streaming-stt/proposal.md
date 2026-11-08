## Why

Calls today cut each utterance with a voice detector, wait `silence_ms` (800 ms) of silence, then send the whole recording to a batch STT command. Measured turn cost before the agent starts: about 0.8 s of endpointing wait plus 0.4 to 1.5 s of batch STT (V: call logs, `RESEARCH/00-summary.md` finding 10). The agent itself takes 2 to 19 s (V). Batch STT also invents words from noise ("Thank you.", "♪♪♪♪") that we filter with a stock-phrase list (V: call logs 2026-11-08).

A streaming recognizer (Nemotron Speech Streaming EN 0.6B: cache-aware FastConformer encoder, RNN-T decoder, punctuation and capitalization, lookahead 0, 80, 480 or 1040 ms; S: model card and `transcribe.cpp` port) hears the caller while they speak. Used only as "the same transcript, sooner", it saves the batch STT time. Used for what text-while-speaking makes possible, it also gives better turn-taking, which the voice detector alone cannot.

## Current state

- STT is a Hermes `command` provider (`fw-audio-hermes stt --input FILE`), one request per utterance, scheduled by `fw-audio-control` (V).
- fw has Whisper large-v3-turbo and Orukeet selectable for batch STT; the Nemotron streaming model is downloaded and checksum-verified (operator, 2026-11-08). The operator chose one long-lived streaming slot next to two batch slots in the same scheduler.
- Endpointing: WebRTC VAD plus `silence_ms`; stock-phrase filter; mute signal ends a turn at once (V).

## What changes

A second, optional STT path, default off, shipped as its own change after the first plugin PR:

1. **Streaming transcript** (`StreamingSpeech`): PCM goes to the streaming service while the caller speaks; partials arrive during speech; the final text is ready within one lookahead of the last word.
2. **Text-aware endpointing**: the end of a turn is decided from VAD plus the partial text. A finished sentence ends the turn sooner; a trailing "and", "but", "so" or a comma waits longer. Target: median end of speech to agent request under 500 ms (from about 800 ms plus STT today), with fewer cut-offs.
3. **Recognizer-confirmed turns**: a VAD "speech" segment that yields no words creates no turn and no beep. This replaces the stock-phrase list on the streaming path.
4. **Word-aware barge-in and steer**: with `barge_in: stop`, the agent stops for two or more words or a stop word, not for a cough or "uh-huh". With `queue`, a finished sentence is steered into a running agent turn at once.
5. **Fallback**: no free slot, a dropped connection or a bad frame falls back to the batch path for that utterance, using the PCM the plugin already keeps. A call never fails because streaming did.

## Non-goals

Other languages (the model is English only); speaker separation; sending audio to the LLM; streaming TTS; speculative agent runs before the transcript is final (needs Hermes support to hold tool side effects back; recorded as a follow-up, U); any change to the batch `stt` provider config; the audio service itself (separate fw session, contract in `design.md`).

## Dependencies and gates

- G1: the first plugin PR is published and its calls feature is stable. This change does not start before that.
- G2: the fw audio service offers the streaming endpoint in `design.md`, behind the same bearer auth and admission scheduler.
- G3: the replay corpus (task 2) exists, so the gain is measured and not assumed.

## Acceptance

Measured on the same recorded calls and on live calls from Conversations and Dino:

- median end of speech to agent request is at least 40 % lower than the batch path;
- word error rate on the corpus is no worse than batch Orukeet by more than 2 points absolute;
- 60 s of room noise and a muted-then-unmuted call create zero turns;
- killing the streaming service mid-call leaves the call working on batch STT;
- text, voice notes and the batch call path behave as before with the feature off.
