## ADDED Requirements

### Requirement: Single-plugin delivery
All call code SHALL ship inside the `hermes-xmpp-plugin` fork, and installing that plugin with Hermes SHALL be sufficient: `plugin.yaml` declares every Python dependency, and no separate package, service or process is required.

#### Scenario: Clean install
- **WHEN** the plugin is enabled on a Hermes install with Python 3.14
- **THEN** its dependencies are installed by Hermes and calls work after setting the flag

### Requirement: Default-off flag and configuration
The feature SHALL be controlled by `xmpp.calls.enabled` (default false) with documented keys for limits, thresholds and voice, set through `hermes config set`, and SHALL not require changes to `stt` or `tts` blocks.

#### Scenario: Upgrade
- **WHEN** the plugin updates and the flag is unset
- **THEN** behavior is identical to the previous version

### Requirement: Module boundaries
The package SHALL keep `jingle/` free of aiortc and Hermes imports, `media/` free of Hermes imports, and SHALL enforce this by import checks in the test suite.

#### Scenario: Layer violation
- **WHEN** a lower layer imports a higher one
- **THEN** a test fails

### Requirement: Quality gates
Every commit SHALL pass `ruff check`, `ruff format --check` and `pyrefly check`, and unit tests SHALL run with fake peers and no network.

#### Scenario: Commit
- **WHEN** a commit is made
- **THEN** prek runs the three tools and blocks on failure

### Requirement: Compatibility statement
The README SHALL list tested clients and servers, Python versions, the Prosody server requirements, and known limits.

#### Scenario: Release
- **WHEN** a release is tagged
- **THEN** the list matches the last recorded device and server tests

### Requirement: OMEMO key safety
The OMEMO key file SHALL be written atomically with owner-only permissions, SHALL be held under a lock by one process, and SHALL NOT be replaced when it cannot be read; in those cases OMEMO SHALL stay off and the reason SHALL be logged. The one-shot sender SHALL NOT use OMEMO.

#### Scenario: Corrupt file
- **WHEN** the key file is cut off mid-write
- **THEN** it is left untouched and OMEMO is off

#### Scenario: Second process
- **WHEN** another process already holds the file
- **THEN** this process runs without OMEMO and does not write the file
