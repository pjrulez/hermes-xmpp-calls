# Lifecycle and portability review

This third review used three independent read-only reviewers: conversation/audio, adapter integration, and JMI/Jingle lifecycle. Reproductions were run offline against the development tree. A passing reproduction may assert the buggy behavior; it is not evidence of a fix. Implementation and regression-test status must be recorded separately below.

No live gateway change or client acceptance test is implied by this report. No real OMEMO store is used in the reproduction tests.

## Findings to verify and fix

Status at intake: open. Fix implementations now exist for all listed findings. The parent ran
both complete suites after syncing the engine into the plugin: 167 passed / 1 skipped in the
engine, 410 passed / 9 skipped in the plugin. The skipped engine test is exercised separately:
50 calls left file descriptors 10→10, threads 2→2 and tasks 1→1 (see
`RESEARCH/evidence/lifecycle-leak-loop.txt`). Ruff, format and pyrefly passed; pyrefly reports
30 existing suppressions and two hidden warnings. Pytest emits an external anyio deprecation
warning. The focused final reviewer found no confirmed blockers, independently ran all 67 new
engine lifecycle tests, and passed three additional cleanup/queued-reply probes. That review's
engine environment lacked `slixmpp_omemo`; the parent separately reran all 123 adapter regressions
and the complete 410-test plugin suite in `/tmp/plugin-venv`, including the OMEMO-dependent
cases, successfully. Live acceptance has not run.

Regression targets: `tests/test_conversation_lifecycle.py` (27 cases),
`tests/test_controller_lifecycle.py` (40 cases), and
`plugin/tests/test_review_edge_cases.py` (123 cases). Existing tests also remain in place.

| ID | Priority | Finding | Regression target |
|---|---|---|---|
| C1 | P1 | A goodbye response starts grace while transcribed speech is already queued; grace clears its activity signals and hangs up, abandoning the queued requests. | Process queued speech before planned hang-up and during finish. |
| C2 | P1 | A steer callback can suspend while the current turn finishes, then return false and append speech to a queue no task consumes. | Recheck current task after the await. |
| C3 | P2 | A failed agent turn leaves queued requests unprocessed. | Drain the queue after recoverable errors too. |
| C4 | P2 | TTS that completes after finish can repopulate closed-call playback and lose the remaining text reply. | Recheck closed after synthesis and deliver remaining text. |
| C5 | P2 | Optional filler synthesis failure discards an otherwise successful agent answer. | Filler failure must not determine the agent result. |
| C6 | P2 | finish deadline expiration leaves agent/STT tasks and retained PCM alive. | Cancel and await owned tasks at deadline; document limits of cancelling provider threads. |
| C7 | P2 | Concurrent grace calls consume separate word notifications and disagree about whether the caller spoke. | Coalesce grace evaluation. |
| C8 | P2 | Playback concatenates an unbounded backlog while synthesizing every sentence. | Backpressure without truncating legitimate replies. |
| C9 | P3 | stop permits pending STT to start a new agent turn. | Terminal stop state and cancellation of owned hearing tasks. |
| C10 | P3 | Endpointer preroll of zero keeps all silence because Python list[-0:] is the entire list. | Zero preroll retains zero idle frames. |
| A1 | P1 | Module reload loses the module-local OMEMO lock registry but leaves raw lock descriptors open, making the same process refuse its own store on reimport. | Reload-safe lock ownership without permitting a distinct process to open it. |
| A2 | P2 | Atomic save replaces a configured symlink rather than updating its canonical target; locking and saving then use different paths. | Canonicalize once for load, lock and save. |
| A3 | P2 | Unconditional fcntl import disables existing OMEMO installations on Windows. | Platform-appropriate exclusive locking; no weakening of store protection. |
| A4 | P2 | Infinity raises OverflowError in integer call config even when calls are disabled; float settings accept non-finite values. | Finite numbers only, default with warning; protect bounded tool integers too. |
| A5 | P2 | Partner notice filtering and CALL REQUEST metadata operate before decryption and inspect the fallback body instead of the real content. | Authorize first, decrypt, then filter/rate-limit/parse final body. |
| A6 | P2 | Mixed-case call target passes tool validation but fails actual authorization. | Normalize whitespace, resource and case once. |
| J1 | P1 | Incoming terminate/candidates during TURN discovery are dropped before the call record exists; a cancelled call can later be accepted. | Register pending session before await; retain candidate/cancel state. |
| J2 | P1 | Controller close leaves ringing/setup operations alive; a late proceed starts a new call after disconnect. | Terminal closed state and cancellation of pending operations. |
| J3 | P2 | Unsupported actions and unknown sessions receive unconditional IQ success; unauthorized set IQs receive no reply. | Exactly one protocol-appropriate result/error response. |
| J4 | P2 | Remote terminate does not wake outgoing acceptance wait; tool later reports timeout and sends misleading missed-call text. | Race acceptance/connect against terminal outcome. |
| J5 | P2 | JMI retract, duplicate and delayed proposal state is not tracked. | Bounded dedup/tombstones and freshness checks while preserving standalone Jingle initiation. |
| J6 | P2 | Audio/video offer receives an audio-only answer with a BUNDLE group that still references omitted video. | Explicitly reject unsupported multi-content offers. |
| J7 | P2 | Received-carbon wrapped JMI does not match the direct-child handlers. | Authenticated received-carbon handling; ignore sent/forged wrappers. |
| J8 | P3 | Outgoing cancellation emits invalid Jingle reason cancelled. | Use XEP-0166 reason cancel. |

## Reviewer artifacts

Scratch reproductions were produced under `/tmp/edge1`, `/tmp/edge2`, and `/tmp/edge3`; these are disposable, not shipped tests. Regression tests belong in the repository and must demonstrate the intended behavior before fixes are accepted.

## Release gates

- Verify each finding independently rather than treating reviewer summaries as proof.
- Run focused regression tests, both complete suites, ruff and pyrefly.
- Re-run the 50-call leak loop after lifecycle changes.
- Sync the engine into the plugin and prove byte-for-byte parity with the sync checker.
- Keep development history; update only the separate PR branch with a cleaned-up history after verification.
- Keep installed gateways unchanged until the operator approves the exact deployment steps.
- Run operator live acceptance on the eventual deployed build before publishing a PR; present exact PR text for approval.
