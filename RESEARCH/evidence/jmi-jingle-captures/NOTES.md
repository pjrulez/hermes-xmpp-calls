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

## Dino (complete, after the bot advertised call features correctly)
- Disco features: same call set plus `transports:raw-udp:1` and `muji:0`.
- `session-initiate` arrives ~0.8 s after our `accept` + `proceed` (see `dino-session-initiate.xml`):
  - `initiator` attribute set; one content `name="audio" senders="both" creator="initiator"`; no BUNDLE group.
  - Payload types: Opus 111 (48000/2, `useinbandfec=1`), speex 112/113/114, PCMU 0, PCMA 8; `rtcp-mux`.
  - **Both** SDES `<encryption><crypto .../></encryption>` (legacy) and a DTLS `fingerprint` (`setup=actpass`). We use DTLS only and must ignore `<encryption>`.
  - Inline host candidates for components 1 **and 2** (ignore component 2 with rtcp-mux), then `transport-info` with relay candidates (TURN works for Dino too).
- The earlier non-response was our fault: the bot advertised no call features on its full JID.

## Differences to handle
| | Conversations | Dino |
|---|---|---|
| content name | `0` + `group BUNDLE` | `audio`, no group |
| candidates | trickled in `transport-info` only | host candidates inline, relay trickled |
| payloads | opus 111, red 63, telephone-event 110, hdrext 1-4 | opus 111, speex, PCMU/PCMA, SDES |
| component | 1 | 1 and 2 |
| initiate attribute | none | `initiator` |

Both set `setup=actpass` and `sha-256` fingerprints; both offer trickle ICE support (Conversations advertises `trickle` and `renomination`; Dino sends relay candidates trickled).
