# hermes-xmpp-calls: agent rules

Baseline: `~/AGENTS.md` (sandbox, no secrets, no destructive system actions). This file adds project rules.

## Working style
- Ponytail **ultra**: smallest complete change; challenge any part of a request the need does not justify and say so before building. No new abstraction, option or dependency without a stated reason in the matching OpenSpec change.
- Caveman **lite** in chat: short, answer first, full sentences where meaning could blur. Committed docs, specs and code comments stay plain prose.
- Tooling: `uv` only. Python **3.14+** (`.python-version`), no 3.11 compatibility work. `ruff`, `pyrefly`, `prek`, `pytest` are dev dependencies. `prek install` once per clone; ruff check, ruff format --check and pyrefly run on every commit. Never use `--no-verify`.

## Environment and cleanliness
- Scope: network is the tailnet only. We do not target a public Prosody server and do not open the test server to the public. TURN/STUN already works for human calls here; do not re-open that question unless a test shows a failure.
- Temp and test files go in only two places: `.scratch/` inside this repo (git-ignored, disposable) and `/tmp` (wiped on reboot). Nothing else on this machine: no stray venvs, caches or logs in `$HOME`, `~/.hermes` or `~/Projects` siblings. Remove what you create when a task ends.
- Test credentials live in `.scratch/` only, mode 600, never in git or chat.
- Do not change `~/.hermes/config.yaml`, any `.env`, Prosody config, or the live `hermes-xmpp-plugin` install on fw, mad or django while developing. A dedicated bot JID is used for tests, never `hermes-fw-default`.

## Testing
- Run tests and live bots in the classic herdr session `hermes-xmpp-calls` (not herdr-app). Drive it with `herdr --session hermes-xmpp-calls workspace|tab|pane ...` (for example `pane run <pane> '<cmd>'`, `pane read <pane>`), so the operator can watch with `herdr session attach hermes-xmpp-calls`.
- Need `sudo`? Stop and ask the operator. They review, approve, and type the password themselves.
- Operator test clients: Dino (Linux), Conversations (Android), Monal (iOS). Audio and video calls already work between users on this Prosody. Never claim a device test passed; ask for it and record the result.

## Game plan (applies to every task)
1. **Reference, do not copy.** Study existing projects, but only reuse code whose license allows it. Checked: `xmpp-radio-tower` is GPL-3.0 and `hermes-deltachat-platform` is MPL-2.0, while the plugin fork is MIT. So we take knowledge (protocol facts, architecture, pitfalls) and rewrite from the XEPs and Conversations notes, optimizing as we go. Record each reference and what was learned in `RESEARCH/05-approach-decision.md`.
2. **Develop here, on our terms.** The call engine lives in `src/xmpp_calls/` and is built with our toolkit. A working clone of the fork sits in `plugin/` (git-ignored nested repo, branch `feat/xmpp-calls` from `feat/voice-messages`, remote `pjrulez/hermes-xmpp-plugin`) for reading the adapter and for integration experiments.
3. **Prove in layers.** logger bot (real stanzas) → Jingle layer with fixtures → echo-call bot with Dino, Conversations, Monal → conversation loop → plugin integration behind `xmpp.calls.enabled`.
4. **Integrate back.** When a version works end to end, port `src/xmpp_calls/` into the fork under its namespace, add `plugin.yaml` dependencies and hooks, test in the fork on fw, then open a PR from `pjrulez/hermes-xmpp-plugin` (show the exact PR title and body to the operator first; no upstream PR without approval).
5. **fw first.** Develop and test on fw. Check what mad and django need only after fw works.
6. Installing the fork next to Hermes must remain the whole install (OpenSpec `plugin-delivery`).

## OpenSpec
- `add-xmpp-audio-calls` is the one umbrella change for the whole project.
- Each dependency has its own change: `dep-slixmpp-jingle`, `dep-aiortc-media`, `dep-hermes-call-integration`, `dep-prosody-server`.
- Mark a task done only when its stated evidence file exists. Run `openspec validate --all --strict` before committing spec edits.
