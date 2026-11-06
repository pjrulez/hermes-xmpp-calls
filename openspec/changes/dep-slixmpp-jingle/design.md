## Context

The signaling layer must produce what Conversations accepts: caps listed in `RESEARCH/01`, DTLS mandatory, matching `propose` and `session-initiate`, trickle ICE, XEP-0215 credentials.

## Design

- Plain slixmpp plugins using `register_plugin`, stanza classes with `ElementBase`, and one `JingleSession` state machine per sid: `pending → accepted → active → terminated`.
- SDP bridge as pure functions over dataclasses: Jingle content to SDP offer, SDP answer to Jingle `session-accept`, ICE candidate both ways. Tested against recorded real stanzas.
- No import of aiortc or Hermes. The media layer receives an SDP string and returns one.
- Compatibility: use only slixmpp APIs present in both 1.15.0 and 1.17.0; test matrix in R5.

## Options (decide in T2)

A new add-ons (lean), B slixmpp fork, C port from prior art, D GStreamer. Records go to `RESEARCH/05-approach-decision.md`.

## Risks

Undocumented Conversations expectations (payload ids, `rtcp-mux`, header extensions). Mitigation: fixtures from a real call, early echo bot.
