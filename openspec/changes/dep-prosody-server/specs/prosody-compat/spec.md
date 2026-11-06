## ADDED Requirements

### Requirement: Verified server requirement list
The README SHALL list each Prosody requirement for Conversations calls with the observed state, verification command and date.

#### Scenario: Reader
- **WHEN** an operator reads the README
- **THEN** each row can be reproduced with the stated command

### Requirement: TURN readiness
The project SHALL verify that Prosody returns TURN credentials and that a client outside the server host can allocate a relay.

#### Scenario: External allocation
- **WHEN** the check runs from fw
- **THEN** it records the allocation result and relay candidate type without secrets

### Requirement: No hidden server changes
The project SHALL NOT change the Prosody deployment itself; fixes SHALL be proposed as changes in the Prosody repository.

#### Scenario: Fix needed
- **WHEN** a check fails because of server configuration
- **THEN** an entry points to the change to open in the Prosody repo
