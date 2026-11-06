## Why

slixmpp 1.15.0 and 1.17.0 ship XEP-0030, 0115, 0234 (stub) and 0353 only. Conversations calls need Jingle core, RTP, ICE-UDP, DTLS and external service discovery. We need those as slixmpp add-ons that work with both versions, live inside the plugin, and could be offered upstream.

## What changes

- Add `xmpp_calls/jingle/` implementing XEP-0166, 0167, 0176, 0320, 0215 and glue for the existing 0353 plugin, plus a Jingle to SDP and SDP to Jingle converter.
- Capture a real Conversations `session-initiate` and use it as the fixture oracle.
- Decide the approach (new add-ons, fork, port, or GStreamer) with evidence.

## Out of scope

Raw UDP (XEP-0177), file transfer (0234), video, group calls, OMEMO call verification, upstream PR (later).

## Dependencies

slixmpp 1.15.0 (plugin pin) and 1.17.0 (current). Prior art for reference: `xmpp-radio-tower` (license unverified), `hermes-deltachat-platform` (MPL-2.0).

## Acceptance

R3, R4, R5 evidence exists; a fake-peer test suite round-trips every stanza; the echo bot (B2) completes a Conversations call signaling to `active`.
