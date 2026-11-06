## ADDED Requirements

### Requirement: Endpointing
The engine SHALL cut caller speech into utterances using silence detection with configurable thresholds, a minimum utterance length, and a maximum utterance length.

#### Scenario: Normal question
- **WHEN** the caller speaks and pauses for the configured silence
- **THEN** one utterance is produced

#### Scenario: Long monologue
- **WHEN** speech exceeds the maximum length
- **THEN** the utterance is cut and processed, and the call continues

### Requirement: Turn through configured providers
Each utterance SHALL be transcribed by the Hermes STT provider configured for the profile and run as a normal session turn with the call marked as the source, so tools, memory and approvals apply as in text. `stt` and `tts` configuration SHALL NOT need changes.

#### Scenario: Spoken question
- **WHEN** the caller asks a question
- **THEN** the transcript enters the session and the reply is spoken

#### Scenario: Empty transcript
- **WHEN** STT returns no text
- **THEN** no turn is created

### Requirement: Sentence-streamed speech in the agent voice
Reply text SHALL be split into sentences and each synthesized with the configured TTS provider and the agent voice (fw `javert`, mad `eve`, django `george` by default), starting playback before the full reply is synthesized.

#### Scenario: Multi-sentence reply
- **WHEN** a reply has several sentences
- **THEN** the first sentence is audible before the last is synthesized

#### Scenario: Markup in reply
- **WHEN** the reply contains markdown, code or URLs
- **THEN** speech omits or summarizes them using a documented rule

### Requirement: Barge-in
Sustained caller speech during playback SHALL stop playback within 500 ms, flush queued audio and pending TTS jobs, and add a note to the next turn stating how much of the reply was heard.

#### Scenario: Interrupt
- **WHEN** the caller speaks over the agent
- **THEN** playback stops and the next turn includes the heard-fraction note

#### Scenario: Short noise
- **WHEN** a click shorter than the hold time occurs
- **THEN** playback continues

### Requirement: Hangup and spoken status
The agent SHALL be able to end the call with a reply marker, and SHALL speak a short message when a recoverable error occurs (STT or TTS failure) before ending or continuing.

#### Scenario: Goodbye
- **WHEN** the reply ends with the hangup marker
- **THEN** the marker is not spoken and the call ends after playback

#### Scenario: TTS failure
- **WHEN** TTS fails for a sentence
- **THEN** the failure is logged, the turn text is posted to chat, and the call stays up
