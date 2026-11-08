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
| 14 | Jingle/SDP parsers | Malformed numbers in a peer's offer or candidate raised bare `ValueError`s (the controller survived them through its catch-all). Both now raise `JingleError`; 800 mutated real offers and hostile candidate lines are in `tests/test_jingle_fuzz.py`. | F |
| 15 | Incoming proposals | A `propose` from an allowed user is answered at once and keeps no state until a `session-initiate` arrives; a second call gets `busy`. Nothing accumulates, so no per-user proposal limit is needed. | OK |
| 16 | Open | Review by a second person before the PR; run the parsers under a real fuzzer (hypothesis or atheris) for longer than the unit test. | O |

## Second review (independent reviewer, 2026-11-08)

| # | Finding | Status |
|---|---|---|
| R1 | A call whose media died (ICE never connected, phone left wifi) kept the line forever: the goodbye waited for audio that nobody pulled, so `max_seconds` never applied. Now bounded waits, `failed`/`closed` ends the call, 40 s connect limit. | F |
| R2 | SDP injection: XML character references could put a newline in ufrag/pwd/mid/fmtp and add a second `m=` section. Now every SDP value is checked, and the offer must produce exactly one audio section. | F |
| R3 | Remote ICE candidates were not filtered (loopback, cloud metadata, hostnames, mDNS, thousands of them). Now UDP unicast only, ports 1024+, 16 per call, bounded wait. | F |
| R4 | The `xmpp_call` tool gave up after `ring_timeout + 60` s and cancelled a call mid-ring, leaving a ghost call and no text fallback. Timeout now covers the schedule, and cancellation retracts the ring and ends the call. | F |
| R5 | The one-call limit raced with the TURN fetch. The line is now claimed before the first await. | F |
| R6 | `xmpp_call` had no limit. Now 6 per hour and 1500 characters of opening. | F |
| R7 | Jingle stanzas were not tied to the call's peer; a repeated sid or a failing stanza from another allowed user could end someone's call. Now ignored. | F |
| R8 | A bounced own `propose` (error message) was treated as an incoming call. Now ignored. | F |
| R9 | `CALL REQUEST` context was recorded before the loop guard and stayed usable. Now recorded after the guard and used once. | F |
| R10 | Recap and missed-call text could be captured as speech of a running turn. They now carry their own `reply_to`. | F |
| R11 | The `heard no words` log line printed the transcript even with `log_transcripts` off. Removed. | F |
| R12 | One-shot sends, recap, missed-call text and `xmpp_message` fall back to plaintext when OMEMO is unavailable or fails. Documented in the README; an `omemo_required` option is a possible follow-up. | A |
| R13 | `xmpp_message` can reach any allowed user, not just the person of the current chat. Single-operator setups are unaffected; documented. | A |
| R14 | Host candidates reveal LAN/tailnet addresses to the peer and server. A relay-only policy is a possible follow-up. | A |
| R15 | The OMEMO store is fsynced on the event loop (a brief stall). | A |
