## ADDED Requirements

### Requirement: Optional streaming transcription
The engine SHALL send caller audio to a streaming STT service while the caller speaks when `xmpp.calls.stt_stream.enabled` is true, and SHALL use the service's final text as the turn text. With the option off, behavior SHALL be exactly the batch path.

#### Scenario: Streaming on
- **WHEN** the caller finishes a sentence
- **THEN** the turn text is the streaming final text and no batch STT request is made

#### Scenario: Streaming off
- **WHEN** the option is off or absent
- **THEN** every utterance is transcribed by the configured batch provider as before

### Requirement: Batch fallback
A call SHALL continue on the batch STT provider when the streaming service is busy, unreachable, disconnects, or returns an error, using the audio of the current utterance. The caller SHALL NOT hear an error.

#### Scenario: No free slot
- **WHEN** the service reports busy at call start
- **THEN** the whole call uses batch STT and one line is logged

#### Scenario: Service dies mid-call
- **WHEN** the connection drops between two utterances
- **THEN** the next utterance is transcribed by the batch provider and the call goes on

### Requirement: Text-aware endpointing
The engine SHALL end a turn using voice activity plus the partial text. A complete sentence of at least three words SHALL end the turn after `silence_fast`. A partial ending in a comma, an open-clause word, or fewer than three words SHALL wait `silence_slow`. Mute and the maximum utterance length SHALL end a turn at once.

#### Scenario: Finished sentence
- **WHEN** the partial ends with a full stop after four words and 350 ms of silence pass
- **THEN** the turn is sent to the agent

#### Scenario: Thinking aloud
- **WHEN** the partial ends with "and" and 800 ms of silence pass
- **THEN** the turn is not yet sent

### Requirement: Recognizer-confirmed turns
A voice-activity segment whose final text is empty SHALL NOT create a turn, play the acknowledgement beep, or call the agent.

#### Scenario: Room noise
- **WHEN** 60 seconds of non-speech noise are played into a call
- **THEN** no turn is created

### Requirement: Word-aware barge-in
With `barge_in: stop` and `word_barge_in` on, the agent SHALL stop speaking only after two or more recognized words, or a stop word, arrive within 1.5 seconds of speech start.

#### Scenario: Cough
- **WHEN** the caller coughs while the agent speaks
- **THEN** the agent keeps speaking

#### Scenario: Interruption
- **WHEN** the caller says "wait, that is wrong"
- **THEN** the agent stops within 500 ms of the second word

### Requirement: Stable text only for side effects
The engine SHALL use only the service's `stable` text for steer and barge-in decisions, and only the `final` text as the turn text.

#### Scenario: Revised partial
- **WHEN** a partial changes after being shown
- **THEN** nothing sent to the agent was based on the unstable part

### Requirement: Per-turn timing record
The engine SHALL log, for every turn, the times of speech end, final text, agent request and first audio.

#### Scenario: Measuring
- **WHEN** a call has three turns
- **THEN** the log has three timing lines that allow the acceptance medians to be computed
