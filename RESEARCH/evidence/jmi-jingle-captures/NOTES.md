# Real call captures, 2026-11-07 (task R3)

Redacted by `xmpp_calls.devtools.logbot` (ufrag, pwd, fingerprint text, IPs replaced by `X`). Bot: `hermes-calls-test`. Caller: `owner` from Dino (Linux) and Conversations (Android).

## Conversations (complete)
- Disco features include `jingle:1`, `ice-udp:1`, `rtp:1`, `dtls:0`, `rtp:audio`, `rtp:video`, `jingle-message:0`, `transports:webrtc-datachannel:1`.
- `propose` (to bare JID) carries `<description media="audio"/>` only, plus receipt request.
- After our `proceed` it sends `session-initiate` to our full JID within ~1 s:
  - one content `name="0" creator="initiator"`, audio description with Opus pt 111 (48000/2, `minptime=10`, `useinbandfec=1`, `rtcp-fb transport-cc`), `red` pt 63, `telephone-event` pt 110;
  - four `rtp-hdrext` (ids 1-4: ssrc-audio-level, abs-send-time, transport-wide-cc, sdes:mid), `extmap-allow-mixed`, `source` (ssma) with cname and msid, `rtcp-mux`;
  - ICE-UDP transport with ufrag and pwd, DTLS `fingerprint hash=sha-256 setup=actpass`, option elements `trickle` and `renomination`;
  - `group semantics=BUNDLE` with content `0`.
- Candidates arrive afterwards as separate `transport-info` stanzas (trickle; first seen: `type=relay udp`, so Conversations relays through TURN even on the tailnet).
- We must reply to each `iq set` with a result; the logbot declines with `session-terminate` reason `decline`.

## Dino (partial)
- Disco features include the same call set plus `transports:raw-udp:1` and `muji:0`. Call button works.
- `propose` identical in shape. The logbot sent `proceed`, but Dino did not send `session-initiate` within 6 s and the operator hung up (`retract`).
- Hypothesis to test: Dino also needs `accept` to the bot's own bare JID before `proceed` (what Conversations did when it was the callee). Logbot now sends both.
