# Research summary (2026-11-06)

Question: can Hermes take a live XMPP audio call from Conversations Android, using local Whisper and PocketTTS, with a few seconds of delay but streaming replies and barge-in?

Answer: **feasible, no blocker found.** The signaling layer does not exist in our dependencies and must be written or borrowed. Two public projects prove the same stack works.

Status key: V = verified here with evidence, S = verified from source or docs only, U = unverified (needs a test, often a device).

| # | Finding | Status | Evidence |
|---|---------|--------|----------|
| 1 | aiortc 1.16.0, av 19.0.2, aioice 0.13.0, slixmpp 1.17.0 install and import on Python 3.14.9 (Hermes tools python on fw) | V | `evidence/loopback.py` |
| 2 | aiortc peers connect with DTLS-SRTP, Opus is negotiated, SDP carries `a=fingerprint`, `a=setup:actpass`, ICE ufrag/pwd; 194 audio frames in 4 s received | V | `evidence/loopback-result.txt` |
| 3 | The NixOS system Python 3.13 cannot import `av` (missing libstdc++); use the Hermes-managed 3.14 or a Nix-provided interpreter | V | same scratch run |
| 4 | slixmpp 1.15.0 and 1.17.0 ship XEP-0030, 0115, 0234 (stub), 0353 only. No XEP-0166, 0167, 0176, 0215, 0320 | V | sdist plugin listing |
| 5 | Conversations shows the call button only if the peer advertises `jingle:1`, `ice-udp:1`, `apps:rtp:1`, `apps:dtls:0`, `rtp:audio` via XEP-0115; it uses XEP-0353 JMI when `urn:xmpp:jingle-message:0` is announced; `propose` and `session-initiate` descriptions must match; DTLS is mandatory | S | `01-conversations-call-requirements.md` |
| 6 | Prosody on mad already serves TURN credentials (`turn_external`, coturn container running); Dino and Conversations calls worked on 2026-10-21 | S | Prosody repo template, operator evidence |
| 7 | Prior art: `xmpp-radio-tower` (Python, slixmpp + aiortc) reports calls working with Conversations, Cheogram, Monocles, Monal, Dino, Movim; includes a Jingle to SDP converter | S | `02-dependency-options.md` |
| 8 | Prior art: `hermes-deltachat-platform` is a Hermes platform plugin with live calls on aiortc (MPL-2.0): endpointing, STT, agent, sentence-streaming TTS, barge-in, outgoing calls | S | `03-hermes-integration.md` |
| 9 | Siproxylin moved from Go Pion to C++ GStreamer webrtcbin to get Conversations calls working: interop is the risk, not signaling syntax | S | `02-dependency-options.md` |
| 10 | Local audio latency on fw: PocketTTS 2 sentences 0.57-0.69 s, Whisper on a 7.3 s clip 0.37 s, both through `fw-audio-hermes` | V | measured |
| 11 | Hermes 0.22.5 has no server-side WebRTC peer. Dashboard audio routes exist: `transcribe`, `speak`, `speak-stream` (sentence chunked, barge-in `stop`), `transcribe-stream` | S | `03-hermes-integration.md` |
| 12 | Conduit realtime calls for Hermes use OpenAI GPT-Live over WebRTC through the dashboard SDP relay; its Standard call is turn-based and uses the dashboard `transcribe` and `speak` routes | S | `04-conduit.md` |
| 13 | aiortc against Conversations Android | U | needs device test |
| 18 | `prosodyctl check turn` inside the Prosody container: "No STUN response: No route to host". Human Dino/Conversations/Monal calls work on the tailnet, so treated as a check quirk, not a blocker | V (symptom) | live probe 2026-11-06, operator report |
| 14 | Python 3.11 wheels for aiortc and av on the cloud VMs (arm64). Project target is Python 3.14; Hermes VM venvs are 3.11 but a 3.14.7 tools python exists there | U | |
| 15 | slixmpp 1.15.0 (pinned by the plugin) vs 1.17.0 | U | |
| 16 | Reuse terms of `xmpp-radio-tower` code (license not found) | U | |
| 17 | Hermes `speak-stream` with our `fw_queue` command provider | U | |

Decision inputs for the next stage are in `02-dependency-options.md` (what to build on) and `openspec/changes/add-xmpp-audio-calls/design.md`.
