## ADDED Requirements

### Requirement: Verified server requirement list
The README SHALL list each Prosody requirement for Conversations calls with the observed state, verification command and date.

#### Scenario: Reader
- **WHEN** an operator reads the README
- **THEN** each row can be reproduced with the stated command

### Requirement: TURN credentials for the bot
The project SHALL verify that the test bot can fetch XEP-0215 credentials from Prosody.

#### Scenario: Credential fetch
- **WHEN** the bot requests external services
- **THEN** it records the service types and counts without secrets

### Requirement: No hidden server changes
The project SHALL NOT change the Prosody deployment itself; fixes SHALL be proposed as changes in the Prosody repository.

#### Scenario: Fix needed
- **WHEN** a check fails because of server configuration
- **THEN** an entry points to the change to open in the Prosody repo
