# Approach decision (task R4)

Decision: **A**. Write Jingle add-ons for slixmpp in `src/xmpp_calls/jingle/`, an aiortc media engine in `media/`, and the Hermes-facing loop in `conversation/`. Rewrite everything from the XEPs and the Conversations notes. Fall back to GStreamer (D) only if aiortc fails interop on a real device.

## References and licenses

| Project | License | Use |
|---|---|---|
| `xmpp-radio-tower` (Python, slixmpp + aiortc) | GPL-3.0 | Knowledge only. Cannot copy into an MIT plugin. |
| `hermes-deltachat-platform` (Python, aiortc, Hermes call pipeline) | MPL-2.0 | Knowledge only. Copied files would stay MPL; we rewrite instead. |
| Siproxylin (Python + C++ GStreamer) | AGPL-3.0 | Knowledge only. |
| `hermes-xmpp-plugin` fork | MIT | Our delivery target. |

Check `otalk/sdp-jingle-json` (JS) license before treating it as a mapping reference; the XEP-0167 and XEP-0176 examples are the primary source.

## What we learned (to apply in a rewrite)

From `xmpp-radio-tower` (reports Conversations, Cheogram, Monocles, Monal, Dino, Movim working):
- One `RTCPeerConnection` per Jingle session. The Jingle content maps to one audio `m=` line with ICE ufrag/pwd, DTLS fingerprint and setup, `rtcp-mux`, and `rtpmap` for each payload type.
- A Jingle `setup=actpass` from the initiator is answered as `active` in the SDP view.
- Explicit teardown of tracks, peer connection and references, with a GC pass, was needed to stop leaks.
- Cleanup of proposed (JMI) sessions is separate from active sessions.

From `hermes-deltachat-platform` (call pipeline docs):
- Run all aiortc objects on a dedicated event loop thread; heavy agent work on the gateway loop starved ICE and killed RTP after seconds.
- Outgoing offers worked as audio-only; extra data channels broke ICE with some answerers.
- Endpointing about 1 s silence; barge-in after about 0.25 s of sustained voiced RMS; sentence-streamed TTS cuts time-to-first-audio; tell the model how much of a cut reply was heard; `[[hangup]]` marker; decline unauthorized callers unanswered.
- Latency budget is dominated by the LLM turn, as in our measurements.

From Siproxylin:
- Interop with Conversations is the hard part. Moving from Go Pion to GStreamer webrtcbin fixed incoming Conversations calls. Treat Conversations as the strictest peer and keep D as the fallback.

## Rewrite targets that beat the references

- Pure-function Jingle/SDP bridge with fixtures from real captured stanzas (R3), not string-built SDP inline in a session class.
- Layered package with import checks (jingle has no aiortc; media has no Hermes).
- Typed state machine per session, one teardown path, leak test with counters.
- Resample once, in the media layer, to fixed formats; STT and TTS stay provider-agnostic.

## Open before B1

R3: capture real `propose`, `session-initiate`, `session-accept` and caps from Dino, Conversations and Monal with the logger bot. The fixtures must come from those captures.
