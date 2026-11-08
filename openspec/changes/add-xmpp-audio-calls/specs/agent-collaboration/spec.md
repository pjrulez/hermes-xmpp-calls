## ADDED Requirements

### Requirement: Partner agents
Accounts listed in `agent_peers` SHALL be able to message the agent when also allowed users, SHALL NOT be callable or able to call, SHALL be limited to 4 accepted messages per 10 minutes, and SHALL be told by prompt that the sender is a machine.

#### Scenario: Loop between two agents
- **WHEN** two agents answer each other
- **THEN** the sixth message inside ten minutes is dropped with a log warning

### Requirement: Gateway notices stay out of agent chats
The engine SHALL NOT send gateway status lines (tool progress, "interrupting", steer acknowledgements, the silence-marker warning) to a partner agent and SHALL NOT act on them when received. A genuine warning from the other agent SHALL pass.

#### Scenario: Silence-marker warning
- **WHEN** the gateway would send "returned only a silence marker" to a partner
- **THEN** it is not sent

### Requirement: Message tool
The plugin SHALL provide an `xmpp_message` tool (`to`, `text`) that sends through the running adapter, only to allowed users and partner agents, and that is never read aloud as a call reply.

#### Scenario: Delegation
- **WHEN** a phone agent asks another agent to change a file
- **THEN** one message reaches that agent and the reply starting `RESULT:` comes back to the phone agent

#### Scenario: Stranger
- **WHEN** the tool is asked to message an unknown address
- **THEN** it refuses and names the allowed addresses

### Requirement: Request metadata
When a partner agent's message starts with `CALL REQUEST`, the plugin SHALL keep its `topic=` and the text before `BRIEFING:` for 10 minutes and use them for `topic` and `context` of the next `xmpp_call` that omits them.

#### Scenario: Model forgets the topic
- **WHEN** the model calls `xmpp_call` without `topic`
- **THEN** the call session title still carries the request's topic

### Requirement: Silence in calls
In a live call the agent SHALL always answer aloud. An empty reply or the gateway's silence-marker warning SHALL NOT be spoken: the engine SHALL ask once more and otherwise say nothing.

#### Scenario: Model replies [SILENT]
- **WHEN** the model returns a bare silence marker during a call
- **THEN** the warning text is not spoken
