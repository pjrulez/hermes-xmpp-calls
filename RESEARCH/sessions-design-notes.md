# Call sessions: design notes (not for the PR text)

Verified from the Hermes sources on fw (2026-11-11), not from a live test unless said so.

## What a "session" is for a call

The plugin sends each spoken turn into the gateway as a normal DM message from the person, with
a thread id. The gateway keys a session by profile, platform, chat and thread, so the thread id
decides which Hermes session (history, context, title) a call lives in:

- `per_call` (today's behaviour, stays the default): thread `call-<id>`, one session per call.
- `per_peer` (new): thread `calls`, one session per person, shared by all their calls.
- the person's text chat is thread `None`; calls never touch it in either mode.

Gateway sessions are not reset by inactivity or at a daily boundary (docs: "Session continuity"),
so a `per_peer` session lasts until someone sends `/new` or `/reset`, or a reset-policy plugin
is installed. Compression keeps it within the context window.

Title: `/title` is sent into the call's session. `per_call` titles contain the time, so they are
unique; `per_peer` re-titles only when the rendered title changes, so `Calls with {name}` is set
once. Whether Hermes refuses a title another session already uses was not tested; the default
templates avoid it.

## `per_call` vs `per_peer`

| | per_call | per_peer |
|---|---|---|
| Context the agent has | this call only | every earlier call with that person |
| Cost per turn | small, constant | grows with history until compression |
| Finding one call later | easy: one entry per call, titled with time and topic | hard: one long entry |
| Deleting one call | delete one session | all calls at once, or nothing |
| Privacy blast radius | one call | everything ever said |
| Cron "daily note" call | a fresh session per day, titled with the job name | the agent can say "same as yesterday, plus ..." |
| Several unrelated tasks by phone | clean separation | topics bleed into each other |

Use cases for `per_call`: a dedicated call-center or phone profile (the smartphone profile here);
profiles that handle unrelated requests; anything where "one call, one record" is how you audit.

Use cases for `per_peer`: a personal assistant you phone every day and want to remember last
week's call; a recurring cron call that reports on the same job and should know what it
reported before; a long-running project you talk through over several calls.

Not obviously good: a per_peer session for a profile shared by several people is still one
session per person (the key includes the chat id), so sharing is not an issue; the real cost is
growth, which compression handles but at the price of summaries replacing the exact words.

## A third mode, `chat`: calls in the person's normal text chat session

Not built. It would be a one-line change in the plugin (thread `None`), which is part of why it
needs thought first.

Pros:
- One conversation for voice and text: ask by text what you said on the phone, continue a call's
  topic in text afterwards.
- One place for history; no extra session list entries.
- Matches Hermes' "forever chat" idea for one-person assistants.

Cons:
- The agent's context fills with spoken-style turns and the plugin's call prompts
  (`CALL_PROMPT`: "answer in one to three short sentences ..."), which can leak into text
  answers' style.
- Busy-session collisions: a text message sent during a call arrives in the same session as the
  running call turn, so the gateway's busy-input rules (interrupt or queue) apply to the call. In
  `per_call` and `per_peer` the two never collide. This is the main risk and would need a live
  test before shipping.
- The call recap and `/title` handling would have to be special-cased (renaming the person's
  text chat to "Call from ..." is wrong).
- `/new` in the text chat would also wipe the call context (arguably a feature).
- The hand-off pattern (a worker agent asks the phone agent to call) would mix machine messages,
  call turns and the person's own chat in one history.

Use cases that might justify it: a single-user personal assistant profile, used hands-free in the
car and then continued in text, where one continuous conversation matters more than isolation;
an agent without tools where collisions do not matter. My take: do not offer it until the
collision behaviour is tested and someone asks for it; `per_peer` covers continuity without the
collisions.

## Deleting the call's session after the call (not built)

Feasibility: Hermes can delete sessions (`hermes sessions delete`, `SessionDB.delete_session`,
and the gateway deletes sessions for `prune`). The adapter receives the gateway's session store
(`set_session_store`), so the plugin could end the session key and delete the old session id after
the recap. That path uses internal gateway APIs, was not tried, and would need a test against
a live gateway: estimate 0.5-1 day, mostly the end-to-end check.

What it would and would not remove:
- Removed: the call's turns and the agent's replies from Hermes' session history and search.
- Not removed: `log_transcripts` log lines (off by default); whatever the stt/tts provider kept;
  anything the agent wrote to memory or files during the call; the recap text and any
  missed-call text that were sent to your XMPP client.
- Your XMPP client will not have "the call" in its history in either case: spoken turns are not
  XMPP messages. The client only shows texts the plugin sent (recap, missed-call text, replies
  that could not be spoken).

Pros:
- A real privacy delete (Hermes' docs: compression is not one).
- Keeps the sessions list and `state.db` small for high-volume call profiles.
- Useful for calls that are pure noise: a cron "daily note" call that reads a note aloud.

Cons:
- No audit trail and no way to ask the agent "what did we decide on Tuesday's call" (unless the
  recap or the agent's memory kept it).
- Deletes while a turn is still finishing must be avoided (hang-up keeps the request running for
  up to 180 s); the delete has to wait for that, then for the recap.
- Combined with `per_peer` it would delete the whole running history after every call, so it only
  makes sense with `per_call`.
- Internal API risk across Hermes updates.

Good use cases: (1) a call-center profile that handles sensitive requests where the transcript
should not stay in Hermes (health, finance); (2) a recurring cron call that reads an update
aloud, where one session per day is clutter.

If it is built, the safe shape is: `session_keep: true` default; `false` deletes only `per_call`
sessions, only after the recap has been sent, never one with an active turn, with a log line per
delete, and it refuses to run in `per_peer`.
