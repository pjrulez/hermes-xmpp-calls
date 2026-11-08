## Value levers, ranked by expected gain

| # | Lever | Where it saves | Expected |
|---|---|---|---|
| L1 | Final transcript at end of speech | removes the batch STT wait | 0.4 to 1.5 s per turn (V for batch cost) |
| L2 | Text-aware endpointing | shortens the silence wait for finished sentences, lengthens it mid-clause | about 400 to 500 ms on most turns, fewer cut-offs (U until measured) |
| L3 | Recognizer-confirmed turns | no turn or beep from noise | removes phantom turns; stock-phrase list becomes a backstop |
| L4 | Word-aware barge-in | backchannels and noise stop interrupting the agent | quality, not latency |
| L5 | Steer on finished sentence | words reach a running agent turn without waiting for silence | seconds on long tool turns |
| L6 | Stop words ("stop", "hang up") on partials | acts before the turn ends | small; guarded by L4 rules |

Honest limit: the agent turn (2 to 19 s) dominates. Streaming STT removes a fixed 1 to 2 s from the start of each turn. Anything beyond that needs speculative agent starts, which are out of scope here.

## Service contract (handoff to the fw audio session)

A WebSocket endpoint on the existing gateway, same bearer auth and the same admission scheduler, one session holding one streaming slot for its lifetime (the operator's design: two batch slots plus one streaming slot).

- Client to server, text frame first: `{"op":"begin","model":"nemotron-speech-streaming-en-0.6b","rate":16000,"latency_ms":480}`; then binary frames of PCM16 mono, 20 to 160 ms each; `{"op":"reset"}` ends an utterance and clears the decoder state; `{"op":"end"}` closes.
- Server to client: `{"ev":"ready"}`; `{"ev":"partial","text":"...","stable":"...","t0":0.0,"t1":1.2}`; `{"ev":"final","text":"...","t0":0.0,"t1":2.4}` after `reset`; `{"ev":"busy"}` or HTTP 429 when no slot is free; `{"ev":"error","code":"..."}`.
- `stable` is the part of the partial that will not change; the plugin uses it for steer and barge-in, never for the final turn text.
- Guarantees to test: `final` within one lookahead plus 100 ms of `reset`; an idle session costs no compute; a client that disappears frees the slot within 5 s.
- Latency setting: 80 ms for fastest turn-taking, 480 ms default for calls, 1040 ms for best accuracy. The client chooses per session.

## Plugin design

- `StreamingSpeech` (Protocol): `open() -> StreamSession`; a session has `feed(pcm)`, `partials()` (async iterator of `Partial(text, stable)`), `finalize() -> str`, `close()`. One implementation for the WebSocket contract above. The existing `Speech` (batch) stays and is the fallback.
- Session lifetime: one per call, opened at call start so the slot is held for the call and a busy service is known immediately (fall back at once, not mid-sentence). Feeding is gated by the VAD with a 300 ms pre-roll, so silence costs nothing. `reset` after each utterance.
- Endpointer: keep the WebRTC VAD as the speech-start and hard-stop detector. Add a policy on top, inputs `(silence_ms_so_far, partial_text)`:
  - ends the turn at `silence_fast` (default 350 ms) when the text ends with `. ! ?` and has at least 3 words;
  - waits until `silence_slow` (default 1400 ms) when the text ends with a comma, an open clause word (and, but, so, because, the, a, to, of, or, if) or has fewer than 3 words;
  - otherwise ends at today's `silence_ms`.
  The mute signal and the maximum utterance length still win.
- Noise: a VAD segment that ends with an empty final creates no turn, no beep and no agent call. The stock-phrase list stays as the batch path's filter.
- Barge-in (`stop`): stop playback when partials reach 2 words, or contain a stop word, within 1.5 s of speech start. `queue` is unchanged except that a `stable` sentence is steered at once while the agent is thinking.
- Fallback: the plugin keeps the PCM of the current utterance. If the session is unusable at `finalize`, the batch provider transcribes that buffer. After three failures in a call it stays on batch for the rest of the call and logs once.
- Observability: one log line per turn with `speech_end`, `final`, `agent_request`, `first_audio` times, so every claim above can be re-measured.
- Config (all under `xmpp.calls.stt_stream`, default off): `enabled`, `url`, `latency_ms`, `silence_fast`, `silence_slow`, `text_endpointing`, `word_barge_in`, `batch_fallback`. Auth reuses the existing STT bearer setting; no secret goes in the plugin config file.

## Risks

- The text policy ends a turn too early on a sentence the caller continues: mitigated by the join-on-pause behavior already in the conversation loop (a quick follow-up joins the previous turn) and by tuning on the corpus.
- RNN-T partials revise themselves: the plugin acts on `stable` only.
- One slot for a whole call blocks a second concurrent call from streaming: the second call falls back to batch, which is the existing behavior.
- U: streaming accuracy on phone-quality Opus audio is unmeasured; the corpus (task 2) is the gate.
