# What Conversations needs from a call peer

Source: Conversations A/V notes by its author (gist `a28c438d9bbf3f4a3d4c663ffaa224d9`). Status S.

Discovery
- Call button appears when a contact resource advertises, via XEP-0115 caps: `urn:xmpp:jingle:1`, `urn:xmpp:jingle:transports:ice-udp:1`, `urn:xmpp:jingle:apps:rtp:1`, `urn:xmpp:jingle:apps:dtls:0`, `urn:xmpp:jingle:apps:rtp:audio`.
- The two accounts need mutual presence subscription. The contact must be online.

Initiation
- If a resource advertises `urn:xmpp:jingle-message:0`, Conversations sends XEP-0353 JMI to the bare JID, else it sends `session-initiate` directly.
- Our side answers `proceed`, then receives `session-initiate`, sends `session-accept`.
- The `propose` media description must equal the later `session-initiate` description, or the call is rejected.
- DTLS fingerprint is required, else the call ends with a `security-error` reason.

Network
- Servers must offer STUN and TURN through XEP-0215. Both ends fetch temporary TURN credentials. The bot account needs the same.
- Candidates are trickled with `transport-info`.

Termination reasons are human readable. Use them for debugging: "Unable to connect call" is a network failure, "application error" is a protocol mismatch.

Open: the exact `session-accept` content Conversations accepts (payload types, `rtcp-mux`, header extensions) is not documented. Capture a real Conversations `session-initiate` from a test call and record it (redacted) as task R3.
