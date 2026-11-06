## ADDED Requirements

### Requirement: Dedicated media loop
All `RTCPeerConnection` objects, tracks, jitter buffers and audio queues SHALL run on one dedicated asyncio loop in a daemon thread, and only completed utterances and reply text SHALL cross to the gateway loop.

#### Scenario: Long agent turn
- **WHEN** a Hermes turn blocks the gateway loop for over 10 s
- **THEN** RTP keeps flowing and ICE stays connected

### Requirement: Audio format handling
Inbound Opus (48 kHz, possibly stereo) SHALL be downmixed and resampled to 16 kHz mono signed 16-bit for STT, and outbound TTS audio at any provider rate SHALL be resampled to 48 kHz and paced in 20 ms frames.

#### Scenario: Stereo inbound
- **WHEN** aiortc yields stereo frames
- **THEN** STT receives mono 16 kHz audio with correct duration

#### Scenario: Provider rate
- **WHEN** TTS returns 24 kHz audio
- **THEN** the caller hears it at correct pitch and speed

### Requirement: Silence keepalive
The outbound track SHALL send silence frames when no speech is queued so the RTP stream and NAT bindings stay alive.

#### Scenario: Idle call
- **WHEN** the agent is not speaking
- **THEN** RTP packets continue at 50 per second

### Requirement: Connection health and teardown
The engine SHALL end a call when the peer connection reaches `failed` or `closed`, or ICE does not connect within 30 s, and SHALL release peer connection, tasks, queues and buffers on every exit path, including exceptions and gateway shutdown.

#### Scenario: Caller drops
- **WHEN** the caller loses network without hanging up
- **THEN** the call ends within 40 s and the slot is free

#### Scenario: Repeated calls
- **WHEN** 50 calls start and end in a test
- **THEN** task count, thread count and resident memory return to baseline within a stated tolerance

### Requirement: Observability
The engine SHALL expose counters (frames in/out, jitter, selected candidate type, time to connect, utterance lengths, time to first audio) in logs without audio content or credentials.

#### Scenario: Call summary
- **WHEN** a call ends
- **THEN** one summary log line lists these counters
