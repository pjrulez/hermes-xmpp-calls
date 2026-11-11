# PR: optional live audio calls (Jingle RTP) and agent-initiated calls

Submitted as https://github.com/fastfinge/hermes-xmpp-plugin/pull/15 (head `pjrulez:xmpp-calls-pr`, 4 commits on top of `f5f25fc`).

## What this adds

Talk to your Hermes agent on a phone call from any XMPP client that supports audio calls
(tested with Conversations, Dino, Monal and Monocles Chat). The agent can also call you, for example from a cron job, and fall back to a text
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

`xmpp.calls.enabled` is `false`. While it is off, no call code is imported and the call packages
(`aiortc`, `av`, `numpy`, `webrtcvad-wheels`; Python 3.13+) are never downloaded.

They are big (about 230 MB: PyAV's bundled FFmpeg is most of it), so they are not in
`pip_dependencies`. With calls on, the first start builds an isolated Hermes environment for
them with `pm.ensure_environment()` under `<hermes root>/environments/hermes-xmpp-calls/`, from
`requirements-calls.txt`. That environment is outside the plugin folder and outside the main venv,
so `hermes update` (which re-syncs the main venv) does not prune it, and a plugin update leaves it
alone. Its `site-packages` is appended to `sys.path`, so Hermes' own numpy/av/cryptography win; it
is refused when its Python differs from Hermes'. `av` follows aiortc's own range (`>=14`).
If the first build takes longer than 25 s (the gateway gives `connect()` 30 s), chat starts anyway
and calls come with the next reconnect or restart. If `pm.ensure_environment` is missing (older Hermes) or lazy installs are off (Docker), a
`vendor/` folder next to the plugin is used instead, and the log prints the command to fill it.

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
                            # except agent_peers
    max_seconds: 600        # hard limit: the call ends this long after it was accepted; false = none
    greeting:               # incoming calls; a string or a list (one at random, never the same
      - "Hi, I'm here. What can I do for you?"   # twice in a row); "" / [] / false = silence
      - "Hello! What's up?"
      - "Yes? I'm listening."
      - "Hey there, go ahead."
      - "Hi! How can I help?"
      - "I'm all ears. What do you need?"
    silence_ms: 800         # pause that ends your turn (raise to 1000-1500 if you get cut off)
    vad_level: 2            # 0-3 noise rejection; higher ignores more background noise
    ack_tone: true          # short beep when your turn is captured; false / "" = off, or a sound file
    warn_tone: true         # the two falling beeps before a planned hang-up; same values
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
    max_calls_per_hour: 6   # xmpp_call placements per hour (1-100)
    opening_max_chars: 1500 # longest opening the agent may speak when it places a call (50-10000)
```

What the less obvious ones do:

- `allowed_users`: a caller who is not in it gets no answer at all. Agents that are only
  `agent_peers` can never call and are never called.
- `greeting` / `filler` / `filler_after`: the filler is spoken only if the agent has not answered
  after `filler_after` seconds. Each filler and each whole greeting is synthesized once and cached
  as `<HERMES_HOME>/cache/xmpp-calls/phrase-<hash>.npy`; later calls play the file without asking
  the TTS provider. After changing the voice or TTS provider, delete that folder.
- `ack_tone` / `warn_tone`: `true` is the built-in beep. `false` or `""` turns it off. A path plays
  that sound instead (any file PyAV reads, cut at 5 seconds, `~` and absolute paths work, a
  relative one is looked up in the Hermes home). Nothing ships with the plugin and there is no list
  of sounds in Hermes. A file that cannot be read logs a warning and the built-in beep plays.
  Example (`ffmpeg -f lavfi -i "sine=frequency=1200:duration=0.15" ~/.hermes/sounds/chime.wav`
  makes a chime):

  ```yaml
  calls:
    ack_tone: ~/.hermes/sounds/chime.wav   # instead of the built-in beep
    warn_tone: false                       # no falling beeps (hangup_grace still waits, silent)
  ```
- `ring_timeout`, `ring_attempts`, `ring_pause`: phones stop ringing after about half a minute by
  themselves, so the plugin rings again until `ring_timeout` is up (a quick rejection is
  respected as a refusal). With the default of one attempt, a call nobody picks up ends as a text
  message containing what the agent wanted to say; when the person calls back, the agent knows why
  it called.
- `max_seconds`: the call ends exactly then, with no warning and nothing that extends it; raise
  the value for longer calls, or set `false` for no limit (a silent call still ends after
  `idle_timeout`). (A spoken 30-second heads-up is specified in the development repository but
  deliberately not part of this PR.)
- `max_calls_per_hour`, `opening_max_chars`: limits on what a runaway agent can do with `xmpp_call`;
  the defaults are meant to be sound, raise them if you place many calls.
- `hangup_grace`: when the agent plans to hang up (goodbye, or `hang_up_after` in the tool), it
  plays two falling beeps and waits this long; speaking cancels the hang-up.
- `log_transcripts`: off by default so call content does not land in logs.

Related settings added by this PR (they also apply with calls off):

```yaml
xmpp:
  agent_peers: [hermes-worker@example.org]   # partner agents; XMPP_AGENT_PEERS
  agent_peer_limit: 4                        # messages accepted from one partner per 10 minutes
  message_tool_limit: 10                     # xmpp_message sends per recipient per 10 minutes
```

`agent_peers` marks other bots: their messages are rate-limited so two agents cannot loop, and the
gateway's own status lines are not exchanged with them. That covers the lines starting with ⚡
Interrupting, ⚙, 📞, ⏳, 💭, 🔧, ⏩, 🔄, 💾, ⏸, 💡, 🔁, 🗜, 📦 or "♻️ Gateway", and the transient
warnings the gateway writes while a turn is still retrying (stuck, no response from provider,
trying fallback, paused, restarting, ...). A real answer or warning written by the agent passes. Tool-progress lines start
with a different emoji per tool and cannot be recognised reliably, so the README tells partner
profiles to set `display.tool_progress: off`.

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
  # no calls section: the worker neither places nor receives calls; xmpp_message works without it
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

1. `xmpp.agent_peers` (above).
2. `xmpp_message` is offered whenever the adapter is connected; it needs neither `calls.enabled`
   nor the call packages (a worker profile that only sends text needs no aiortc).
3. Gateway status lines (see above) are no longer relayed to or acted on from a partner agent.
4. `xmpp.agent_peer_limit` and `xmpp.message_tool_limit` (defaults 4 and 10, as before).

## Security notes

- Everything from the peer is untrusted: Jingle parse errors raise one error type; strings that
  reach SDP are ASCII tokens only (no whitespace, `;` or `=` inside an fmtp name or value); one
  audio section; at most 16 ICE candidates, UDP, unicast, ports 1024-65535; duplicate session
  IDs refused; stanzas must come from the call's peer; carbons are accepted only from the
  account's own bare JID.
- Calls need `allowed_users`; others get no answer. Outgoing: by default at most 6 calls per hour
  and opening text of at most 1500 characters (`max_calls_per_hour`, `opening_max_chars`).
- DTLS-SRTP is required; Opus is the only codec; video offers are refused.
- Call audio goes to whichever `stt`/`tts` providers you configured: with a cloud provider it
  leaves your machine.
- Known limits, documented in the README: host candidates reveal local addresses to the peer
  (use TURN-only networks if that matters); `xmpp_message` can reach any allowed user.

## Commits

1. `feat(calls): Jingle RTP signalling and DTLS-SRTP media` - `calls/jingle/*`, `calls/media.py`,
   `calls/turn.py`. No Hermes imports.
2. `feat(calls): conversation engine, call lifecycle and text fallbacks` - `calls/audio.py`,
   `speech.py`, `conversation.py`, `controller.py`, `hermes_host.py`, and 175 tests with a real
   aiortc peer and recorded Conversations/Dino stanzas.
3. `feat(calls): Hermes integration, agent tools and an optional environment for the call
   packages` - `adapter.py`, `call_packages.py`, `plugin.yaml` (0.5.0), README, CHANGELOG, CI,
   adapter tests.
4. `feat(calls): greeting list with cached audio, custom tones, no time limit, configurable
   limits` - the options above that came out of the review round and live use.

The OMEMO key-store work that was part of the first version of this PR is now a separate PR
(see the review discussion), so this one does not change how an OMEMO store is read or written.

The engine under `calls/` is developed and reviewed in
https://github.com/pjrulez/hermes-xmpp-calls (research notes, OpenSpec change records, two
independent security reviews and a lifecycle review); that repository is not needed to use the
plugin.

## Testing

- Run as the repository CI does (`pytest tests/ -q -W error`, upstream's pinned dependencies,
  standalone checkout, `requirements-calls.txt` installed and `XMPP_REQUIRE_CALL_DEPS=1`, so a missing call
  package fails the run instead of silently skipping the 175 engine tests): 473 passed, 9
  skipped on Python 3.14. Without the call packages: 260 passed, 18 skipped.
- The workflow installs `requirements-calls.txt` and sets `XMPP_REQUIRE_CALL_DEPS=1`.
- Python 3.13 on a machine without `/etc/mime.types`: two `test_outgoing_voice_serialization`
  cases fail the same way on current `main`: 3.13's `mimetypes` only knows `.ogg` from the system
  file (3.14 has it built in). Not touched by this PR.
- Nothing in `requirements.txt` or `requirements-dev.txt` is changed.
- `call_packages.provide()` is unit-tested (environment, `vendor/` fallback, failure, Python mismatch)
  and was run for real against Hermes' `pm`: on x86_64 (a gateway's first start with calls on built
  the environment in 8 s, then a call worked) and on aarch64 (two Ubuntu VMs: 17-20 s from a cold download cache in a
  throwaway home, which is why the first-start wait is 25 s and not shorter; the real gateway
  restarts then logged "preparing the call packages environment" and "audio calls enabled" 5 s
  (django) and 7 s (mad) apart). In all cases aiortc came from the new environment and Hermes' own
  av and numpy were used.
- Live: calls with Conversations (Android), Dino (Linux), Monal (iOS) and Monocles Chat (Android) to a bot on three hosts, including
  incoming, outgoing, hang-up in the middle of a request, no-answer fallback to text, 60 s idle
  hang-up, and an agent-initiated call started by a hand-off message from another agent. 50 consecutive calls leave file descriptors, threads and tasks
  unchanged.
- Not covered: video (offers are refused) and other clients such as Gajim.

## Review tips

The diff is large (about 8.3k added lines: 4.5k tests, 3.2k code in `calls/` and `adapter.py`, the rest README, CHANGELOG and config). The best reading order is the README
section "Audio calls", then `calls/conversation.py` (the loop), `calls/controller.py` (lifecycle),
then `adapter.py` (search for `calls`). Besides `calls/`, the PR touches `adapter.py`, `plugin.yaml`, `.gitignore`, `requirements-calls.txt`, docs and tests.
