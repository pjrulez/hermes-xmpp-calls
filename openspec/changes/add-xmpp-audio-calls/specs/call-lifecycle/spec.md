## ADDED Requirements

### Requirement: Warned hang-up
Before the agent ends a call on its own (after a goodbye or with `hang_up_after`), the engine SHALL play two falling beeps and wait `hangup_grace` seconds. Recognised words from the caller within that time SHALL keep the call open; noise that produces no words SHALL NOT. Unless the caller speaks, the call SHALL then end.

#### Scenario: Silence after goodbye
- **WHEN** the agent says goodbye and the caller stays silent for `hangup_grace`
- **THEN** the call ends

#### Scenario: Room noise after goodbye
- **WHEN** the voice detector fires but the transcript is empty
- **THEN** the call still ends

### Requirement: Hanging up does not cancel the request
When a call ends for any reason, the engine SHALL transcribe the speech in progress, let a running agent turn complete, and deliver its reply to the person's chat as text. Nothing SHALL be spoken after the call is over.

#### Scenario: Hang-up mid-request
- **WHEN** the caller hangs up while the agent is working on their request
- **THEN** the agent finishes and the answer arrives as a text message

### Requirement: Post-call recap
After a call in which the agent answered at least one turn, the engine SHALL ask the call's own session what the person asked for and did, and send the answer to the chat as text, unless the answer is NONE or `recap` is off.

#### Scenario: Request made
- **WHEN** the caller asked for a change and hung up
- **THEN** a text beginning "Call recap:" names the request and the action

### Requirement: Missed call
When an outgoing call is not answered after the configured rings, the opening SHALL be sent to the person's chat as text and remembered, and if the person then calls the agent, its first turn SHALL be told what was texted.

#### Scenario: Unanswered
- **WHEN** nobody picks up
- **THEN** the opening arrives as a text and the tool result says so

### Requirement: Ringing
An outgoing call SHALL ring for `ring_timeout` seconds (default 60). A phone's own ring limit (a rejection after at least 25 seconds) SHALL be treated as time-out and the call SHALL ring again until `ring_timeout`; a quicker rejection SHALL be treated as a refusal. `ring_attempts` (default 1) rings, `ring_pause` apart, SHALL be made before the text fallback; one call MAY ask for more attempts.

#### Scenario: Quick refusal
- **WHEN** the person rejects after five seconds
- **THEN** no further ring is made and the text fallback is sent

### Requirement: Busy line
An outgoing call to a person who is already on a call with the agent SHALL be spoken inside that call. A call to anyone else SHALL wait up to `busy_wait` seconds for the line before reporting busy.

#### Scenario: Result arrives during a call
- **WHEN** the agent has a result for the person while they are on the line
- **THEN** it is spoken in that call and no second call is placed

### Requirement: Recognisable sessions
Every call SHALL be its own Hermes session titled "Call from|to <person> <date time>", followed by the call's topic when one was given.

#### Scenario: Cron call
- **WHEN** a cron job's call has topic `daily-note`
- **THEN** the session title ends with `daily-note`

### Requirement: Noise phrases
A short transcript that is only a stock phrase ("Thank you", "Thanks for watching", "you", "bye"), the same stock phrase repeated, or text with no letters or digits SHALL NOT create a turn.

#### Scenario: Silence transcribed as words
- **WHEN** the recognizer returns "Thank you." for a one-second sound
- **THEN** no turn is created

### Requirement: Idle timeout
A call in which nobody has spoken, no reply is playing and the agent is not working for `idle_timeout` seconds SHALL end with a spoken goodbye.

#### Scenario: Forgotten call
- **WHEN** the line stays silent past the idle timeout
- **THEN** the agent says it is hanging up and the call ends

### Requirement: Transcripts stay out of the log
Transcripts and replies SHALL be logged only as word counts unless `log_transcripts` is on.

#### Scenario: Default log
- **WHEN** a caller says three words
- **THEN** the log shows "caller: 3 words" and not the words

### Requirement: Call time limit with spoken heads-up
A call SHALL end when it has lasted `max_seconds` (default 600), measured from acceptance. Thirty seconds before that moment the agent SHALL say, once, a short spoken notice that the call will end in thirty seconds. If `max_seconds` is 30 or less, no notice SHALL be spoken. Nothing SHALL extend the limit: not the caller's speech, not an agent tool, not any per-call option. A longer call requires a larger `max_seconds` in the configuration and a gateway restart. The notice SHALL NOT interrupt a sentence in progress, and SHALL NOT be spoken after the caller has hung up. When the limit is reached the call SHALL end as it does today, and the requirement "Hanging up does not cancel the request" SHALL apply.

#### Scenario: Notice before the limit
- **WHEN** a call has lasted `max_seconds` minus thirty seconds
- **THEN** the agent says once that the call will end in thirty seconds, after the sentence it is speaking

#### Scenario: Caller tries to extend
- **WHEN** the caller asks for more time during the last thirty seconds
- **THEN** the call still ends at `max_seconds`

#### Scenario: Short limit
- **WHEN** `max_seconds` is 30 or less
- **THEN** no notice is spoken and the call ends at `max_seconds`

#### Scenario: Request in progress at the limit
- **WHEN** the limit is reached while the agent is still working on a request
- **THEN** the call ends and the answer arrives as text

### Requirement: Call sessions are configurable
A call SHALL run in a Hermes session of its own, never in the person's text chat session. `session` SHALL be `per_call` (default: a new session for every call) or `per_peer` (one persistent session per person shared by all their calls); any other value SHALL log a warning and mean `per_call`. `session_title` SHALL be a template over `direction`, `name`, `jid`, `time`, `date` and `topic`; a template that names another field SHALL be refused with a warning and the default for the mode used. A `per_peer` session SHALL be re-titled only when the rendered title changes.

#### Scenario: One session per person
- **WHEN** `session` is `per_peer` and the same person calls twice
- **THEN** both calls use the same session and the agent sees the first call's history in the second

#### Scenario: Unusable title template
- **WHEN** `session_title` contains `{nope}`
- **THEN** a warning is logged and the session gets the default title
