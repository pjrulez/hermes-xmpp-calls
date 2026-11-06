# hermes-xmpp-calls: agent rules

Baseline: `~/AGENTS.md` (sandbox, no secrets, no destructive system actions). This file adds project rules.

## Working style
- Ponytail **ultra**: smallest complete change; challenge any part of a request the need does not justify and say so before building. No new abstraction, option or dependency without a stated reason in the matching OpenSpec change.
- Caveman **lite** in chat: short, answer first, full sentences where meaning could blur. Committed docs, specs and code comments stay plain prose.
- Tooling: `uv` only. Python **3.14+** (`.python-version`). `ruff`, `pyrefly`, `prek`, `pytest` are dev dependencies. `prek install` once per clone; ruff check, ruff format --check and pyrefly run on every commit (`.pre-commit-config.yaml`). Never bypass hooks with `--no-verify`.

## Boundaries
- Work only under `~/Projects/hermes-xmpp-calls`. Scratch goes to `.venv/` or `~/.hermes/cache/scratch/` (git-ignored).
- Do not change `~/.hermes/config.yaml`, any `.env`, Prosody, or the live `hermes-xmpp-plugin` install on fw, mad or django while researching or prototyping. Prototypes run from this repo.
- Test client: Conversations on Android. Only the operator can place calls; ask for the device test, never assume it passed.
- Prototypes use a dedicated bot JID, never `hermes-fw-default`, so the production gateway keeps its session.
- Never store credentials, TURN secrets or call audio in git. Evidence holds counts, timings and redacted XML.

## Delivery target
The product is the fork `github.com/pjrulez/hermes-xmpp-plugin` (branch `feat/voice-messages`, commit 03fd781; upstream `fastfinge/hermes-xmpp-plugin`). Installing that plugin next to Hermes must be enough: all call code ships inside it and every Python dependency is declared in its `plugin.yaml`. `src/xmpp_calls/` here is the development tree that moves into the fork (see OpenSpec `add-xmpp-audio-calls`, requirement "Single-plugin delivery"). Clone the fork as `../hermes-xmpp-plugin` when implementation starts; do not vendor it here.

## OpenSpec
- `add-xmpp-audio-calls` is the one umbrella change for the whole project.
- Each dependency has its own change: `dep-slixmpp-jingle`, `dep-aiortc-media`, `dep-hermes-call-integration`, `dep-prosody-server`.
- Mark a task done only when its stated evidence file exists. Run `openspec validate --all --strict` before committing spec edits.
