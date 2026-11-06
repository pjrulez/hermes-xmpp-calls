## ADDED Requirements

### Requirement: Jingle RTP stanza support
The library SHALL parse and build XEP-0166 `jingle` actions, XEP-0167 `description` with payload types, XEP-0176 ICE-UDP `transport` and `candidate`, and XEP-0320 DTLS `fingerprint` with `setup`, and SHALL ignore unknown child elements without failing.

#### Scenario: Round trip
- **WHEN** a recorded Conversations `session-initiate` is parsed and rebuilt
- **THEN** the result is semantically equal to the original

### Requirement: Session state machine
The library SHALL track each session by `sid` and peer, reject actions that are invalid for the state with `unexpected-request`, and release state on terminate.

#### Scenario: Out-of-order
- **WHEN** `transport-info` arrives before `session-initiate`
- **THEN** the library replies with an error and creates no session

### Requirement: SDP bridge
The library SHALL convert between Jingle audio content and SDP offers/answers with fingerprint, setup role, ICE credentials, candidates and Opus parameters, with no import of aiortc.

#### Scenario: Offer conversion
- **WHEN** a Jingle initiate with Opus 48000/2 is converted
- **THEN** the SDP offer carries the same payload, fingerprint, ufrag, pwd and candidates

### Requirement: Version compatibility
The library SHALL work on slixmpp 1.15.0 and 1.17.0 and SHALL fail at import with a clear message on unsupported versions.

#### Scenario: Both versions
- **WHEN** the suite runs on either version
- **THEN** all tests pass

### Requirement: External service discovery
The library SHALL request XEP-0215 services, return STUN/TURN entries with expiry, and never log credentials.

#### Scenario: Credentials
- **WHEN** services are returned
- **THEN** callers receive structured entries and logs show only counts and types
