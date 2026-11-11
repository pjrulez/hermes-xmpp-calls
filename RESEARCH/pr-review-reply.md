Thanks, this is a good review. Done, all in the force-pushed `xmpp-calls-pr` (A, this PR) and a new draft PR B stacked on it.

**1. Split.** The seam was clean, no duplicated guts. B (`xmpp-omemo-pr`, draft, link below) holds exactly the OMEMO store rewrite: lock, shared storage data, atomic 0600 writes, refusing an unreadable store, the one-shot sender never using OMEMO, the device-list refresh, and `plaintext_peers`. `agent_peers` stayed in A because `xmpp_message` needs it. A no longer touches how an OMEMO store is read or written. B shows A's commits in its diff until A merges; the OMEMO change is its last commit.

**2. CI.** The workflow installs `requirements-calls.txt` and sets `XMPP_REQUIRE_CALL_DEPS=1`, so a missing call package is an error instead of a silent skip. Verified: with the packages hidden, the run fails. A: 587 passed, 9 skipped on 3.14.

**3. Version.** `plugin.yaml` is 0.5.0, CHANGELOG has the 0.5.0 heading.

**xmpp_message.** It is now offered whenever the adapter is connected. It does not need `calls.enabled` or aiortc. There is a test with calls off and no call packages, and the hand-off example in the README no longer enables calls on the worker.

**3.13 failures.** Environment dependent, thanks for checking. My machine has no `/etc/mime.types`, and Python 3.13's `mimetypes` only knows `.ogg` from that file (3.14 has it built in). I'll send a small separate PR for the `.ogg` type.

**Optional call dependencies.** You were right: `hermes update` would prune them. I did not want to declare ~230 MB (PyAV's FFmpeg is most of it) for everyone, so with calls on the first start now builds an isolated Hermes environment with `pm.ensure_environment()` under `<hermes root>/environments/hermes-xmpp-calls/`, from `requirements-calls.txt`. It is outside the plugin folder and the main venv, so `hermes update` leaves it alone. Calls off means nothing is downloaded. A slow first build (over 15 s) does not hold up chat: calls start with the next reconnect. Hermes' own numpy and av still win. A `vendor/` folder is the fallback (older Hermes, or lazy installs off), and the log prints the command. I ran it for real: 6.5 s, 227 MB. Reasoning is in the README ("Where the call packages live"). `av` now follows aiortc's own range (`>=14`).

One thing to check on your side: `pm.ensure_environment` is a new Hermes API, so it is only exercised against current Hermes. I have not run it under your pinned-core CI job.
