## ADDED Requirements

### Requirement: Authorization before accept
The plugin SHALL evaluate the caller with the same authorization rules as messages before replying to `propose` or `session-initiate`, SHALL reject unauthorized callers without media or state, and SHALL NOT reveal whether the account exists as a bot.

#### Scenario: Stranger calls
- **WHEN** an unauthorized JID calls
- **THEN** the call is rejected and no ICE, DTLS or STT work happens

### Requirement: Single active call and bounds
The plugin SHALL allow one active call per account, reject others with `busy`, enforce a maximum call duration and idle timeout, and bound queue sizes.

#### Scenario: Busy
- **WHEN** a second authorized call arrives
- **THEN** it is rejected with `busy`

#### Scenario: Idle timeout
- **WHEN** no speech occurs for the idle timeout
- **THEN** the agent ends the call politely

### Requirement: Privacy
Call audio SHALL NOT be written to disk by default, logs SHALL NOT contain audio, transcripts beyond the session store, TURN credentials or candidate IPs of third parties beyond the selected type, and temporary files SHALL be removed on every exit path.

#### Scenario: Default run
- **WHEN** a call completes
- **THEN** no audio files remain in the working directories

### Requirement: Failure isolation
An exception in call code SHALL end that call only and SHALL NOT disconnect the XMPP session or block text and voice-note handling.

#### Scenario: Media crash
- **WHEN** the media engine raises
- **THEN** the call terminates with `failed-application` and messages still work
