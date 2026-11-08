# Security review of the calls feature (first pass, 2026-11-08)

Scope: everything the first PR adds. Status: **F** found and fixed, **A** accepted risk, **O** open.

| # | Surface | Finding | Status |
|---|---|---|---|
| 1 | Call authorization | JMI `propose` and Jingle `session-initiate` are checked against the allowed users before any media or STT work; partner agents are never callable; strangers get a reject and no state (tests: `test_controller.py`). | OK |
| 2 | OMEMO key file | An unreadable file was silently replaced by an empty one (identity key lost on the next write), two processes could overwrite each other's sessions, writes were not atomic and the file was world-readable (0644). Now: lock, atomic write, 0600, never reset. | F |
| 3 | One-shot sender | `send_xmpp_message` opened a second full adapter on the live OMEMO file. Now OMEMO is off for it. | F |
| 4 | Logs | Transcripts and agent replies were logged at INFO, against the Privacy requirement. Now word counts only unless `log_transcripts`. aioice logs the own TURN relay address (tailnet) at INFO: accepted. | F / A |
| 5 | `xmpp_message` tool | Recipients limited to allowed users and partner agents; 10 sends per recipient per 10 minutes; text is not interpreted. A prompt-injected agent can still send up to the limit to those addresses: accepted. | F / A |
| 6 | `CALL REQUEST` parsing | Only read from messages by a partner agent that passed authorization; `topic` limited to word characters, `context` to 3000 characters, both expire after 10 minutes. The text reaches the call agent as background: a compromised partner agent could steer the call agent. Partner agents are trusted by configuration: accepted, documented. | A |
| 7 | Session title | `topic` becomes part of a `/title` command. Control characters and `/` sequences are removed, 60 characters at most. | F |
| 8 | Partner-agent loop | Two agents answering each other: 4 accepted messages per 10 minutes, gateway status lines neither sent nor acted on, prompt marks the sender as a machine. | F |
| 9 | Idle and long calls | `max_seconds` (600) and `idle_timeout` (180) end forgotten calls; one call at a time. | F |
| 10 | Hang-up | Hanging up no longer cancels work in progress; the reply goes to the chat as text (the person's own chat only). | OK |
| 11 | Dependencies | `aiortc`, `av`, `webrtcvad-wheels` and friends are optional, installed into `vendor/` or the Hermes env, imported only when `calls.enabled`. Licenses reviewed for the plugin fork in `RESEARCH/05-approach-decision.md`. No code copied from GPL, AGPL or MPL projects. | OK |
| 12 | `plaintext_peers` | Turns OMEMO off for listed peers: opt-in, empty by default, documented as a security trade-off. | A |
| 13 | Resource use | 50 sequential calls: file descriptors 10 to 10, threads 2 to 2, tasks 1 to 1 (`RESEARCH/evidence/leak-loop.txt`). | OK |
| 14 | Open | Fuzzing of the SDP and Jingle parsers with hostile input; a limit on concurrent unanswered JMI proposals from an allowed user; review by a second person before the PR. | O |
