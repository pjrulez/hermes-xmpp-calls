## ADDED Requirements

### Requirement: Queued speech survives turn completion
The conversation SHALL process already transcribed queued speech after a reply, including a goodbye reply or a recoverable agent failure. It SHALL recheck the running turn after awaiting steering so rejected steering cannot strand the request. Concurrent hang-up grace evaluations SHALL share the same result.

#### Scenario: Another request before goodbye
- **WHEN** the caller queues another request while the agent prepares a goodbye
- **THEN** the queued request is handled rather than discarded by the planned hang-up

#### Scenario: Steering races with turn completion
- **WHEN** steering returns false after the previous turn completes
- **THEN** the caller's words start a new turn instead of remaining in an idle queue

### Requirement: Terminal conversation cleanup
After hang-up the conversation SHALL finish captured work within a 180-second budget, then cancel and await its remaining owned asynchronous tasks and release retained audio. No late STT completion SHALL start work after terminal stop. No late synthesis SHALL enqueue playback after hang-up; the pending reply SHALL take the text path. Optional filler failure SHALL NOT discard a successful agent result.

#### Scenario: TTS completes after hang-up
- **WHEN** a sentence synthesis completes after the caller hangs up
- **THEN** no audio is queued and the pending answer is sent as text

#### Scenario: Finishing budget expires
- **WHEN** asynchronous work is still pending at the finishing deadline
- **THEN** owned tasks are cancelled and audio references are released, without claiming to undo completed tools or forcibly stop provider threads

### Requirement: Playback backpressure
The speech loop SHALL wait for playback room before synthesizing additional sentences. The target backlog SHALL be five seconds plus the next indivisible sentence. Pre-synthesis caching SHALL also be bounded. Zero configured preroll SHALL retain no idle audio.

#### Scenario: Fast TTS and slow playback
- **WHEN** the provider can synthesize faster than audio is consumed
- **THEN** the speech loop waits for room without truncating the answer

### Requirement: Pending call signalling and shutdown
The controller SHALL register incoming session state before TURN discovery and retain early candidates and termination. Shutdown SHALL stop pending proposals and setup, and a late proceed SHALL NOT create a call. Remote termination SHALL wake outgoing setup immediately instead of producing a false timeout. Unsupported Jingle actions and unknown sessions SHALL receive appropriate single IQ error responses. Multiple-content audio/video offers SHALL be refused explicitly. Cancellation SHALL use the standard Jingle reason `cancel`.

#### Scenario: Termination during TURN discovery
- **WHEN** the caller terminates while TURN discovery is pending
- **THEN** setup is cancelled and no session-accept is emitted

#### Scenario: Proceed after disconnect
- **WHEN** a proposal is answered after controller shutdown
- **THEN** no media connection or session-initiate is created

### Requirement: Bounded JMI replay handling
The controller SHALL remember the last 256 proposal IDs with their peer and retraction state in memory, ignore duplicates and proposals delayed beyond the ringing deadline, and preserve standalone audio Jingle initiation. Received carbons SHALL be processed only from the account's authenticated own bare JID; sent and forged wrappers SHALL NOT initiate calls.

#### Scenario: Retracted proposal
- **WHEN** a session-initiate arrives for a remembered retracted proposal
- **THEN** the controller refuses it instead of reviving the call

### Requirement: Adapter portability and decrypted metadata
OMEMO locks SHALL remain effective across module reloads and use platform-appropriate exclusive locking. Loading, locking and atomic saving SHALL use one canonical store path so symlinks are preserved. Nonfinite numeric call settings SHALL default safely even when calls are disabled. Partner notice filtering, rate accounting and request metadata extraction SHALL use successfully decrypted text, after authorization. Tool targets SHALL be normalized before validation and dispatch.

#### Scenario: Same-process reload and another process
- **WHEN** the adapter reloads while its process retains the store lock
- **THEN** the reloaded adapter recognizes that ownership while a distinct interpreter remains excluded

#### Scenario: Encrypted call request
- **WHEN** an authorized partner sends an encrypted CALL REQUEST
- **THEN** request metadata is extracted from the decrypted body rather than the encryption fallback
