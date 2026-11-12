## Open question: a `per_peer` call session only grows. How should it be reset?

`calls.session: per_peer` keeps one Hermes session per person (thread `calls`) for all their calls, so the agent remembers earlier calls. That is the point of it, and also the problem: Hermes gateway sessions are not reset by inactivity, so the session keeps growing. Compression keeps it inside the context window, but then the exact words of old calls become summaries.

The part I could not solve cleanly: **a person cannot reset it from XMPP.** A `/new` typed in the chat is routed to the person's normal chat session (inbound XMPP messages carry no thread id), not to the `calls` thread. Today the only ways are `/new` or deleting the session from Hermes Desktop or the CLI (`hermes sessions`).

This PR ships `per_call` (default, unchanged) and `per_peer` without a reset, and says so in the README. Before adding one I would like your view on which of these fits the plugin best.

| # | Option | For | Against |
|---|---|---|---|
| 1 | **Nothing.** Document it; reset from Desktop/CLI. | No code, no new surface. | A person phoning from a mobile client has no way to start over. Bots cannot either. |
| 2 | **Time rotation**, e.g. `session_rotate: never \| daily \| weekly \| monthly`. The thread id gets the period (`calls-2026-W46`); a new period is a new session, titled by `session_title`. | No command to learn or secure, works for cron callers and bots, growth is bounded, continuity within the period. | Continuity is lost at the boundary whether or not it was wanted; a long conversation can be cut mid-topic; yet another option. |
| 3 | **A plugin command**, e.g. `/newcall`, handled in the adapter before the gateway sees the text, from allowed users and partner agents (a bot sends it with `xmpp_message`); refused while that person is on a call. | Explicit and on demand, for humans and bots. | A custom slash command that Hermes does not know (and would not list in `/help`); needs its own authorisation and rate limit; one more thing for a reviewer to trust. |
| 4 | **An agent tool**, e.g. `xmpp_calls_reset`, that the agent calls when asked ("start a fresh call session"). | No parsing of text; the existing allowed-users and tool gating apply. | The model decides; it can be asked in a call, but also talked into it; needs the same session-routing internals as option 3. |
| 5 | **Size or age triggered**, e.g. start a new session when the current one passes N messages or N tokens. | Bounded without a calendar. | Needs Hermes' session database (internal API); harder to explain than a calendar period. |
| 6 | **Ask Hermes core** to route `<thread>` from inbound XMPP messages (and so let a person's `/new` reach a thread). | The cleanest fit in the long run. | Needs a core change plus clients that can set a thread, which the common ones cannot. |

My own lean: **2 (rotation, off by default) for the case "I just want it bounded", and 3 if people want an explicit reset**; I would not build 4 to 6 now. But this is your plugin and your trust model, so I would rather ask than guess: which of these (or none) would you want in this repository?

### Also considered and not built: deleting a call's session after the call

Hermes has a delete path used by its API server (`delete_session` with the active-turn guard, then drop the gateway routing entry). A `session_keep: false` option could use it after the recap. It is a real privacy delete for sensitive call profiles and keeps the session list small. It costs the audit trail ("what did we decide on Tuesday's call"), it only makes sense with `per_call`, and it relies on gateway internals (`gateway_runner._session_db`, the session store) that can change between Hermes releases. I left it out and mention it here as a possible follow-up if there is interest.
