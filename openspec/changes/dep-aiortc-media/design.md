## Context

Verified: loopback on Python 3.14.9 connects, negotiates Opus, DTLS fingerprint, 194 frames in 4 s (`RESEARCH/evidence`). The NixOS system Python 3.13 cannot import `av` (libstdc++); Hermes-managed Python works.

## Design

- One `MediaEngine` thread with its own loop; a thread-safe API (`start_call`, `stop_call`, `speak`, `flush`, event callbacks) bridging to the gateway loop with `call_soon_threadsafe`.
- Inbound: Opus to PCM through aiortc, downmix, resample to 16 kHz mono with `av.AudioResampler`; endpointing produces utterance bytes.
- Outbound: queue of PCM sentences, resample to 48 kHz, 20 ms pacing, silence frames when idle, flush on barge-in.
- Teardown: single `close()` path in `finally`, tracked tasks, `pc.close()` awaited, thread joined with timeout.
- Endpointing: RMS with hysteresis first; `webrtcvad` or Silero only if R6 shows RMS fails.
- Platform: record import tests on 3.14 fw, VM 3.14 tools python, VM 3.11 venv; document the NixOS requirement for `libstdc++`.

## Risks

Drift between pacing and RTP timestamps, CPU spikes during resample, leaks of aiortc objects (prior art uses explicit gc). Mitigation: counters, 50-call loop test, long-call test.
