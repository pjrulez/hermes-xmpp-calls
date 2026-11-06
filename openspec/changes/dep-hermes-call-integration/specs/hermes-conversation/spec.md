## ADDED Requirements

### Requirement: Supported interfaces only
The integration SHALL use only documented Hermes plugin interfaces and SHALL fail closed with a clear log when a required interface is missing.

#### Scenario: Interface missing
- **WHEN** Hermes lacks a required interface
- **THEN** calls are disabled and messages still work

### Requirement: Session parity
A call turn SHALL run in the same session and with the same tools, memory, approvals and authorization as a text message from that JID, with the call marked as the source.

#### Scenario: Tool use
- **WHEN** the caller asks for something needing a tool
- **THEN** the tool runs under normal approval rules and the result is spoken

### Requirement: Provider reuse
Transcription and speech SHALL use the profile's configured providers and the agent voice, and SHALL NOT require edits to `stt` or `tts` blocks.

#### Scenario: Unchanged config
- **WHEN** calls are enabled
- **THEN** `stt` and `tts` config remain byte-identical

### Requirement: Spoken reply routing
During a call replies SHALL be spoken, with a text copy in chat when configured, and SHALL fall back to chat text if speech fails.

#### Scenario: TTS down
- **WHEN** TTS fails
- **THEN** the reply appears as text and the call continues

### Requirement: Interruption note
After barge-in the next model turn SHALL include a note with the estimated fraction of the previous reply that was played.

#### Scenario: Half heard
- **WHEN** the caller interrupts at about half the reply
- **THEN** the note states roughly half was heard
