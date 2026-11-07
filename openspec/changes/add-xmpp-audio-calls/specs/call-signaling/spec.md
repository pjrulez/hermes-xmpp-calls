## ADDED Requirements

### Requirement: Capability advertisement
When `xmpp.calls.enabled` is true the plugin SHALL advertise through XEP-0115 the namespaces `urn:xmpp:jingle:1`, `urn:xmpp:jingle:transports:ice-udp:1`, `urn:xmpp:jingle:apps:rtp:1`, `urn:xmpp:jingle:apps:dtls:0`, `urn:xmpp:jingle:apps:rtp:audio` and `urn:xmpp:jingle-message:0`, and SHALL advertise none of them when the flag is false.

#### Scenario: Flag off
- **WHEN** the flag is false
- **THEN** disco and caps contain no call namespace and Conversations hides the call button

#### Scenario: Flag on
- **WHEN** the flag is true and the bot is online with mutual presence
- **THEN** Conversations shows the call button

### Requirement: Jingle Message Initiation
The plugin SHALL handle XEP-0353 `propose`, answer `proceed` for an accepted call and `reject` for a declined one, and SHALL handle `retract` and `finish`. The audio description in `propose` SHALL match the later `session-initiate`.

#### Scenario: Accepted call
- **WHEN** an authorized contact sends a `propose` for audio
- **THEN** the plugin replies `proceed` and waits for `session-initiate`

#### Scenario: Caller gives up
- **WHEN** a `retract` arrives before accept
- **THEN** the plugin discards the pending call and frees its state

### Requirement: Jingle session lifecycle
The plugin SHALL process `session-initiate`, send `session-accept`, exchange `transport-info` for trickled ICE candidates, and handle `session-terminate`, `session-info` (ringing, active, mute) and `content-modify` without crashing on unknown actions.

#### Scenario: Normal call
- **WHEN** `session-initiate` carries one audio content with Opus, ICE credentials and a DTLS fingerprint
- **THEN** the plugin answers with a compatible `session-accept` and ICE candidates arrive via `transport-info`

#### Scenario: Unsupported content
- **WHEN** the initiate includes video or no Opus payload
- **THEN** the plugin terminates with `unsupported-applications` or `unsupported-transports`, not a crash

### Requirement: DTLS mandatory
The plugin SHALL refuse any session without a DTLS fingerprint and SHALL terminate it with `security-error`.

#### Scenario: Missing fingerprint
- **WHEN** a peer offers no fingerprint
- **THEN** the session ends with `security-error` and no media starts

### Requirement: TURN and STUN discovery
The plugin SHALL obtain STUN/TURN services through XEP-0215 for its own account before accepting, refresh expired credentials, and fall back to host and server-reflexive candidates when none exist.

#### Scenario: Credentials present
- **WHEN** the server returns TURN services
- **THEN** the ICE configuration includes them with the temporary credentials, never logged

#### Scenario: No services
- **WHEN** discovery fails
- **THEN** the call proceeds with direct candidates and a warning is logged

### Requirement: Presence subscription for callers
The plugin SHALL keep the existing allowed-peer subscription handling so that an authorized user and the bot hold mutual presence, which Conversations requires for the call button.

#### Scenario: Allowed peer
- **WHEN** an allowed JID subscribes
- **THEN** the plugin accepts and subscribes back; others are ignored

### Requirement: Outgoing calls
The plugin SHALL be able to place a one-to-one audio call to an allowed JID on request of the agent or a scheduled job, using XEP-0353 `propose` to the bare JID, handling `accept`, `proceed`, `reject` and `retract`, then sending `session-initiate` to the responding full JID, and SHALL stop ringing after a configurable timeout.

#### Scenario: Answered
- **WHEN** the user answers on one device
- **THEN** the plugin sends `session-initiate` to that device and the call connects

#### Scenario: Unanswered
- **WHEN** nobody answers within the ring timeout
- **THEN** the plugin sends `retract`, reports "not answered" to the requester, and leaves no state

#### Scenario: Multiple devices
- **WHEN** several devices ring and one answers
- **THEN** the others stop ringing

#### Scenario: Not allowed
- **WHEN** a call is requested to a JID that is not allowed
- **THEN** the plugin refuses without sending any stanza
