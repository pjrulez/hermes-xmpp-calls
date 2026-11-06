# hermes-xmpp-calls

Live audio calls with a Hermes Agent over XMPP, answered from Conversations (Android) and other Jingle clients.
Call `hermes-<host>-default@xmpp.example.org`, talk, hear streamed answers, interrupt.
Audio stays on our own stack: Whisper (STT) and PocketTTS (TTS) on `fw` through `fw-audio-control`.

Status: **research round 1 done, specification drafted, no implementation yet.**

## Layout
- `RESEARCH/` verified findings, open questions, dependency options, evidence scripts.
- `openspec/changes/` one umbrella change (`add-xmpp-audio-calls`) plus one change per dependency.
- `src/xmpp_calls/` development tree for the call engine (moves into the plugin fork).
- `AGENTS.md` working rules.

## Development
```
uv sync            # Python 3.14, runtime and dev dependencies
uv run prek install
uv run pytest
uv run ruff check && uv run ruff format --check && uv run pyrefly check
```
Hooks run ruff check, ruff format --check and pyrefly on every commit.

## Start here
1. `RESEARCH/00-summary.md` what is verified, what is not.
2. `openspec/changes/add-xmpp-audio-calls/proposal.md` goals, non-goals, acceptance.
3. `openspec/changes/add-xmpp-audio-calls/tasks.md` research and build breakdown.

## Prosody server requirements
Full compatibility with Conversations calls needs the following on the server. Status is for `xmpp.example.org` on mad (Prosody 13.0 nightly 98), from `DEPLOYMENTS/mad-prosody/prosody.cfg.lua.template` and a live probe on 2026-11-06.

| Requirement | Why | Status |
|---|---|---|
| `mod_turn_external` (XEP-0215) with `turn_external_host/port/secret/ttl` | Clients and the bot fetch short-lived TURN/STUN credentials; mobile networks usually need relay | enabled; host `turn.example.org:3478`, tcp on, ttl 3600 |
| coturn reachable by clients on UDP and TCP 3478 plus its relay port range | Media relays through it | container `prosody-coturn` runs. **`prosodyctl check turn` from the Prosody container failed: "No STUN response: No route to host".** Needs an external reachability test (task P2) |
| `mod_disco` and entity capabilities passthrough | Clients detect call support from caps | enabled |
| `mod_roster` and mutual presence subscription between caller and bot | Conversations shows the call button only for mutual contacts | enabled; plugin approves subscriptions only for allowed peers and subscribes back |
| `mod_carbons` | Call proposals reach all of the caller's devices and are cleared when answered elsewhere | enabled |
| `mod_smacks`, `mod_csi_simple`, `mod_cloud_notify` | Reliable delivery and wake-up of sleeping mobile clients for call ringing | enabled |
| `mod_mam`, `mod_pep` | Message archive, OMEMO device lists | enabled |
| Valid TLS certificate on C2S (5222) | Client trust | enabled |
| Bot accounts, one per agent | Each agent is its own JID | `hermes-fw-default`, `hermes-mad-default`, `hermes-django-default` exist |
| No Jingle-specific server module | Jingle is carried end to end as ordinary IQ/message stanzas | n/a |
| Not needed | Federation (s2s is off), MUC for 1:1 calls | n/a |

The check that decides TURN health is `prosodyctl check turn`; keep the credential rotation and relay range documented next to the coturn deployment, not here.
