## Context

The call engine is new code. Hermes has no server-side WebRTC peer, slixmpp has no Jingle media plugins, and the plugin has no call code. See `RESEARCH/`.

## Architecture

```
Conversations ─ JMI + Jingle (XMPP) ─▶ jingle layer (dep-slixmpp-jingle)
                                          │ SDP
                                          ▼
                      media engine (dep-aiortc-media), own event-loop thread
                         ICE/TURN · DTLS-SRTP · Opus RTP
                          │ 48 kHz PCM in            ▲ 48 kHz PCM out
                      resample 16 kHz mono        sentence PCM queue
                          │                          ▲
                   endpointing ─▶ STT ─▶ Hermes turn ─▶ sentence chunker ─▶ TTS (voice)
                                 (dep-hermes-call-integration)
```

Code lives in one package, `xmpp_calls`, with three layers: `jingle/` (no aiortc, no Hermes), `media/` (aiortc, no Hermes), `conversation/` (Hermes-facing). Layers import downward only, so the first two are testable with fake peers. The package moves into the plugin fork under the plugin's own namespace; no separate distribution.

## Decisions

- **D1 Jingle approach.** Candidates A new add-ons on slixmpp, B slixmpp fork, C port from prior art, D GStreamer. Lean: A, delivered vendored in the plugin (no slixmpp fork to carry), C as reference and oracle, D as fallback. Gate: R3 (real Conversations stanzas) and R4 (prior art review, license).
- **D2 Single-plugin delivery.** All call code ships in the plugin tree; `plugin.yaml` `pip_dependencies` lists `slixmpp`, `aiortc`, `av`, `numpy`. No second package to install. Upstreamable pieces (the Jingle add-ons) stay isolated in `jingle/` so they can be offered to slixmpp later without changing the plugin.
- **D3 Event loops.** Every aiortc object lives on one dedicated asyncio loop in a daemon thread. The gateway loop only receives completed utterances and sends reply text. Reason: ICE and RTP are loop tasks and stall when agent work blocks the loop (documented by `hermes-deltachat-platform`).
- **D4 Endpointing.** RMS silence first; add a VAD dependency only if R6 shows RMS fails. No dependency without evidence.
- **D5 STT/TTS path.** In-process through Hermes provider functions, same providers as voice notes, voice from the agent voice map. Dashboard routes are a fallback only (the dashboard does not run on fw). Gate: R7.
- **D6 Python.** 3.14 or newer (fw runs 3.14.9). Hermes VM venvs are 3.11, so VM rollout is a later change and depends on the VMs' Python (finding 14).
- **D7 slixmpp pin.** The plugin pins 1.15.0; 1.17.0 is current. Add-ons must run on both until the pin moves. Gate: R5.
- **D8 Feature flag.** `xmpp.calls.enabled`, default false. No caps advertised and no call code started when off.
- **D9 Authorization.** Same allowed-user check as messages, evaluated before `proceed`/accept. Unknown callers are rejected silently.

## Risks and mitigations

- aiortc vs Conversations libwebrtc interop (DTLS role, trickle ICE, payload/header-extension choice). Mitigate: R3 capture, echo bot B2 early, GStreamer fallback.
- Gateway starvation or crashes from media code. Mitigate: D3, exception boundary around the call controller, session and messaging keep running.
- Laptop NAT and roaming. Mitigate: TURN from Prosody; test relay-only; P2 first.
- Queue contention with other local audio. Mitigate: interactive priority, bounded utterance length, one call at a time.
- Echo and noisy input. Conversations applies AEC; bot-side output is TTS only. Mitigate: RMS gate and a barge-in hold time.
- Version drift (aiortc, av, slixmpp, Hermes API). Mitigate: pin ranges in `pyproject.toml` and `plugin.yaml`, smoke test in CI-less prek hook set.
