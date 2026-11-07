# hermes-xmpp-calls

Live audio calls with a Hermes Agent over XMPP, answered from Conversations (Android) and other Jingle clients.
Call `hermes-<host>-default@xmpp.example.org`, talk, hear streamed answers, interrupt.
Audio stays on our own stack: Whisper (STT) and PocketTTS (TTS) on `fw` through `fw-audio-control`.

Scope: a private Prosody on the tailnet. Public Internet deployment is out of scope. Test clients: Dino (Linux), Conversations (Android), Monal (iOS).

Status: **research done, specification drafted, implementation starting.**

## Layout
- `RESEARCH/` verified findings, open questions, dependency options, evidence scripts.
- `openspec/changes/` one umbrella change (`add-xmpp-audio-calls`) plus one change per dependency.
- `src/xmpp_calls/` development tree for the call engine (moves into the plugin fork).
- `plugin/` git-ignored working clone of the fork (`feat/xmpp-calls`); `.scratch/` git-ignored disposable files.
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
Server features that Jingle audio and video calls rely on, as set up on the tailnet Prosody (`xmpp.example.org`, Prosody 13.0 nightly). Calls between human users already work there with Dino, Conversations and Monal, so these are proven by use. Public-Internet exposure is out of scope.

| Requirement | Why | State |
|---|---|---|
| `mod_turn_external` (XEP-0215) with a coturn server | Clients fetch short-lived STUN/TURN credentials for ICE | enabled (`turn.example.org:3478`, tcp on, ttl 3600) |
| `mod_disco` and entity capabilities | Clients detect call support from caps | enabled |
| `mod_roster` plus mutual presence subscription between caller and bot | Conversations shows the call button only for mutual contacts | enabled; the plugin accepts subscriptions only from allowed peers and subscribes back |
| `mod_carbons` | Call proposals reach all of the caller's devices | enabled |
| `mod_smacks`, `mod_csi_simple`, `mod_cloud_notify` | Reliable delivery and wake-up of mobile clients | enabled |
| One account per agent | Each agent is its own JID | `hermes-fw-default`, `hermes-mad-default`, `hermes-django-default` |
| No Jingle-specific server module | Jingle is carried end to end as ordinary stanzas | n/a |

Note: `prosodyctl check turn` run inside the Prosody container reports "No STUN response: No route to host". Human calls work, so this is treated as a container-network quirk of the check, not a blocker. It is only revisited if a bot call fails to connect.
