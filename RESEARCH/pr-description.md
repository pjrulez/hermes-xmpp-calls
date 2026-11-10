# PR: optional live audio calls (Jingle RTP) and agent-initiated calls

Submitted as https://github.com/fastfinge/hermes-xmpp-plugin/pull/15 (head `pjrulez:xmpp-calls-pr`, 3 commits on top of `f5f25fc`).

## What this adds

Talk to your Hermes agent on a phone call from any XMPP client that supports audio calls
(tested with Conversations, Dino and Monal). The agent can also call you, for example from a cron job, and fall back to a text
message when you do not pick up.

- Incoming and outgoing audio calls: Jingle RTP (XEP-0166/0167/0176/0320) with Jingle Message
  Initiation (XEP-0353), Opus over DTLS-SRTP, ICE-UDP, TURN credentials from the server (XEP-0215).
  aiortc does the media.
- Turn-based conversation: voice-activity endpointing, then the Hermes `stt` provider, then a
  normal agent turn (tools, memory and approvals apply), then the Hermes `tts` provider, spoken
  sentence by sentence. Nothing new to configure for speech: it uses the providers you already
  have.
- Barge-in (talk while the agent talks: queue, steer into the running turn, or stop), spoken
  goodbye with a short beep-and-wait before hanging up, idle timeout, and a filler phrase
  ("One moment.") when the agent is slow.
- Hanging up in the middle of a request does not cancel it: the answer is posted as text.
- Two agent tools: `xmpp_call` (the agent phones a person) and `xmpp_message` (to a person or a
  partner agent), toolset `xmpp_calls`. Every call is its own Hermes session with a title.

## It is off by default

`xmpp.calls.enabled` is `false`. While it is off, no call code is imported and the optional
dependencies (`aiortc`, `av`, `numpy`, `webrtcvad-wheels`; Python 3.13+) are not needed. They can be
installed into the Hermes environment or into a `vendor/` folder next to the plugin, which is
appended to `sys.path` after Hermes' own packages.

## Configuration

Minimal:

```yaml
xmpp:
  jid: hermes@example.org
  password: ${XMPP_PASSWORD}
  allowed_users: [sam@example.org]      # who may chat AND call
  calls:
    enabled: true                       # or XMPP_CALLS_ENABLED=true
```

Every option, with its default (all under `xmpp.calls`; a bad value logs `invalid calls.<key>` and
uses the default):

```yaml
xmpp:
  calls:
    enabled: false          # master switch
    allowed_users: []       # who may call and be called; empty = every xmpp.allowed_users JID
                            # except plaintext_peers and agent_peers
    max_seconds: 600        # hard limit: the call ends this long after it was accepted
    greeting: "Hi, I'm here. What can I do for you?"   # "" = silence (incoming calls)
    silence_ms: 800         # pause that ends your turn (raise to 1000-1500 if you get cut off)
    vad_level: 2            # 0-3 noise rejection; higher ignores more background noise
    ack_tone: true          # short beep when your turn is captured
    barge_in: queue         # queue | stop
    idle_timeout: 60        # seconds of silence before a goodbye and hang-up; 0 = never
    hangup_grace: 5         # seconds to speak after the two falling beeps before a planned hang-up
    filler_after: 3.0       # seconds of waiting for the agent before the filler
    filler:                 # unset = six built-in phrases, picked at random, never the same twice
      - One moment.         #   in a row. A string says that phrase. "" / [] / false = off.
      - Let me check.
      - Working on it.
    recap: true             # after a call with a request, text a 1-2 sentence summary
    log_transcripts: false  # log what was said (default: only word counts)
    ring_timeout: 60        # outgoing: ring for up to this long
    ring_attempts: 1        # outgoing: rings before the message goes out as text (1-5)
    ring_pause: 60          # seconds between rings
    busy_wait: 90           # an outgoing call waits this long for the current call to end
```

What the less obvious ones do:

- `allowed_users`: a caller who is not in it gets no answer at all. Agents that are only
  `agent_peers` can never call and are never called.
- `filler` / `filler_after`: the filler is spoken only if the agent has not answered after
  `filler_after` seconds. Each phrase is synthesized once and cached as
  `<HERMES_HOME>/cache/xmpp-calls/filler-<hash>.npy`; later calls play the file without asking
  the TTS provider. After changing the voice or TTS provider, delete that folder.
- `ring_timeout`, `ring_attempts`, `ring_pause`: phones stop ringing after about half a minute by
  themselves, so the plugin rings again until `ring_timeout` is up (a quick rejection is
  respected as a refusal). With the default of one attempt, a call nobody picks up ends as a text
  message containing what the agent wanted to say; when the person calls back, the agent knows why
  it called.
- `max_seconds`: the call ends exactly then, with no warning and nothing that extends it; raise
  the value for longer calls. (A spoken 30-second heads-up is specified in the development
  repository but deliberately not part of this PR.)
- `hangup_grace`: when the agent plans to hang up (goodbye, or `hang_up_after` in the tool), it
  plays two falling beeps and waits this long; speaking cancels the hang-up.
- `log_transcripts`: off by default so call content does not land in logs.

Related settings added by this PR (they also apply with calls off):

```yaml
xmpp:
  agent_peers: [hermes-worker@example.org]   # partner agents; XMPP_AGENT_PEERS
  plaintext_peers: []                        # bare JIDs that never get OMEMO; XMPP_PLAINTEXT_PEERS
```

`agent_peers` marks other bots: their messages are rate-limited (4 per 10 minutes) so two agents
cannot loop, and the gateway's own status lines are not exchanged with them. `plaintext_peers` is
an opt-in escape hatch for a peer that cannot do OMEMO; it is empty by default.

### Example: a phone agent and a worker that runs cron jobs

```yaml
# phone profile: hermes-phone@example.org  (the one you call)
xmpp:
  allowed_users: [sam@example.org, hermes-worker@example.org]
  agent_peers: [hermes-worker@example.org]
  calls: {enabled: true}                   # callable: sam only

# worker profile: hermes-worker@example.org
xmpp:
  allowed_users: [sam@example.org, hermes-phone@example.org]
  agent_peers: [hermes-phone@example.org]
  calls: {enabled: true}                   # only so the worker gets xmpp_message
```

A cron job on the worker sends the phone agent a message that starts with `CALL REQUEST` and a
`BRIEFING:` section; the phone agent calls you with `xmpp_call`, you can ask follow-up questions,
and a requested change goes back to the worker with `xmpp_message`. The plugin only remembers
the request context for 10 minutes; the rest is a prompt convention (README, "Hand-off pattern").

Server side: the README lists what Prosody (or another server) needs: TURN via XEP-0215, carbons,
and mutual presence subscription between the person and the bot (Conversations shows the call
button only for mutual contacts; the bot accepts subscription requests only from `allowed_users`
and subscribes back).

## Behaviour changes that apply even with calls off

1. **OMEMO key store safety.** One process per store file (an `flock` on `<file>.lock`),
   atomic owner-only (0600) writes, and the adapter refuses to start OMEMO when the file exists but
   cannot be read, instead of silently starting empty (a new identity key breaks every existing
   session). Several storage objects for one file in one process share their data. Reason: two
   gateways sharing one home, or a crash during a write, otherwise destroy the double ratchets.
2. `xmpp.plaintext_peers` and `xmpp.agent_peers` (above).
3. Gateway status lines (tool progress, "interrupting" and similar) are no longer relayed to or
   acted on from a partner agent.

## Security notes

- Everything from the peer is untrusted: Jingle parse errors raise one error type; strings that
  reach SDP are ASCII tokens only (no whitespace, `;` or `=` inside an fmtp name or value); one
  audio section; at most 16 ICE candidates, UDP, unicast, ports 1024-65535; duplicate session
  IDs refused; stanzas must come from the call's peer; carbons are accepted only from the
  account's own bare JID.
- Calls need `allowed_users`; others get no answer. Outgoing: at most 6 calls per hour, opening
  text at most 1500 characters.
- DTLS-SRTP is required; Opus is the only codec; video offers are refused.
- Call audio goes to whichever `stt`/`tts` providers you configured: with a cloud provider it
  leaves your machine.
- Known limits, documented in the README: host candidates reveal local addresses to the peer
  (use TURN-only networks if that matters); if OMEMO fails to initialise the adapter falls back to
  plaintext as it already did; `xmpp_message` can reach any allowed user.

## Commits

1. `feat(calls): Jingle RTP signalling and DTLS-SRTP media` - `calls/jingle/*`, `calls/media.py`,
   `calls/turn.py`. No Hermes imports.
2. `feat(calls): conversation engine, call lifecycle and text fallbacks` - `calls/audio.py`,
   `speech.py`, `conversation.py`, `controller.py`, `hermes_host.py`, and 179 tests with a real
   aiortc peer and recorded Conversations/Dino stanzas.
3. `feat(calls): Hermes integration, agent tools and OMEMO store safety` - `adapter.py`,
   `plugin.yaml`, README, CHANGELOG, adapter tests.

The engine under `calls/` is developed and reviewed in
https://github.com/pjrulez/hermes-xmpp-calls (research notes, OpenSpec change records, two
independent security reviews and a lifecycle review); that repository is not needed to use the
plugin.

## Testing

- Run exactly as the repository CI does (`pytest tests/ -q -W error`, upstream's pinned
  dependencies, standalone checkout): 592 passed, 9 skipped on Python 3.14. Without the optional
  call dependencies: 359 passed, 18 skipped (the engine tests skip themselves).
- On Python 3.13 the same run passes except two `test_outgoing_voice_serialization` cases that
  fail identically on current `main` (not touched by this PR).
- Nothing in `requirements.txt` or `requirements-dev.txt` is changed; the new
  `requirements-calls.txt` is only for the optional call dependencies.
- Live: calls with Conversations (Android), Dino (Linux) and Monal (iOS) to a bot on three hosts, including
  incoming, outgoing, hang-up in the middle of a request, no-answer fallback to text, 60 s idle
  hang-up, and an agent-initiated call started by a hand-off message from another agent. 50 consecutive calls leave file descriptors, threads and tasks
  unchanged.
- Not covered: video (offers are refused) and other clients such as Gajim.

## Review tips

The diff is large (about 8k lines, 5k of them tests). The best reading order is the README
section "Audio calls", then `calls/conversation.py` (the loop), `calls/controller.py` (lifecycle),
then `adapter.py` (search for `calls`). Besides `calls/`, the PR touches `adapter.py`, `plugin.yaml`, `.gitignore`, `requirements-calls.txt`, docs and tests.
