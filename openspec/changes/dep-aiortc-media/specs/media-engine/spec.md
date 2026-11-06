## ADDED Requirements

### Requirement: Engine thread isolation
The engine SHALL create and use every aiortc object on its own loop thread and SHALL expose only thread-safe methods and callbacks to callers.

#### Scenario: Busy caller loop
- **WHEN** the caller's loop is blocked
- **THEN** the engine thread continues to send and receive RTP

### Requirement: Audio conversion
The engine SHALL deliver 16 kHz mono PCM for inbound audio and accept PCM at any common sample rate for outbound audio, preserving duration and pitch.

#### Scenario: Duration check
- **WHEN** a one-second 24 kHz clip is queued
- **THEN** about one second of Opus audio is transmitted

### Requirement: Pacing and keepalive
The engine SHALL send audio in 20 ms frames in real time and silence when idle.

#### Scenario: Idle
- **WHEN** nothing is queued for 10 s
- **THEN** RTP packets continue and the connection stays up

### Requirement: Platform statement
The project SHALL record a tested matrix of interpreter, OS and aiortc/av versions, and SHALL document known unsupported combinations.

#### Scenario: NixOS system Python
- **WHEN** av is imported under the NixOS system Python without libstdc++
- **THEN** the documented error and workaround apply

### Requirement: Resource accounting
The engine SHALL leave no extra tasks, threads or open sockets after a call ends and SHALL expose counters for diagnostics.

#### Scenario: Leak test
- **WHEN** 50 calls complete
- **THEN** counts match the baseline
