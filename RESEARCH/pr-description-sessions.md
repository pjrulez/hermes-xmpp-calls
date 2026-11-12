Title: feat(calls): session modes (per_call, per_peer), session_title and a spoken time-limit notice

Draft. Based on current `main` and independent of the OMEMO PR (#16). One commit: `feat(calls): session
modes ...`. Bumps the plugin to 0.6.0 (new options) and adds the missing `[Unreleased]` changelog
entry for #17 under Fixed.

## What it changes

1. **`xmpp.calls.session`**: `per_call` (default, today's behaviour: a new Hermes session for
   every call, DM thread `call-<id>`) or `per_peer` (one persistent session per person, thread
   `calls`, shared by all their calls so the agent remembers earlier ones). Any other value logs
   a warning and means `per_call`. Calls never run in the person's text chat session in either
   mode.
2. **`xmpp.calls.session_title`**: a template for the session title with `{direction}` (`from` /
   `to`), `{name}`, `{jid}`, `{time}`, `{date}` and `{topic}`. Empty means
   `Call {direction} {name} {time} {topic}` for `per_call` and `Calls with {name}` for `per_peer`.
   The result is one plain line of at most 100 characters (it travels inside a `/title`
   command, so a leading `/` is stripped). A template with another field, a format spec or a
   stray brace logs a warning and the default is used. Hermes keeps session titles unique and
   refuses a taken one (the plugin used to swallow that reply, leaving the session untitled), so
   the host asks the session database first: a session is titled once, and a taken title gets
   Hermes' own numbering (`Calls with sam #2`). Without the gateway's session database (older
   Hermes) the title is sent as it is.
3. **A spoken heads-up**: 30 s before `max_seconds` the call says once "This call will end in
   thirty seconds." It is queued behind the sentence being spoken, never delays the cut, and is
   skipped for very short limits and for `max_seconds: false`. Nothing extends the limit.
   (This was specified in the first PR and left out of it.)

```yaml
xmpp:
  calls:
    session: per_peer
    session_title: "Calls with {name}"     # or e.g. "{topic} {date}" for cron calls
```

## Which mode when

- `per_call`: a dedicated call-center profile; unrelated requests; one entry per call, easy to
  find and delete; small constant context.
- `per_peer`: a personal assistant you phone repeatedly; a recurring cron call that should know
  what it said last time. Context grows until `/new`, `/reset` or compression, and everything ever
  said is in one session (deleting it removes all calls at once).

The README has the full comparison (section "Sessions").

## Open question: resetting a `per_peer` session

A `per_peer` session grows, and a person cannot reset it from XMPP (a `/new` in the chat resets the
normal chat session). I ship it without a reset and document the Desktop/CLI way; see the comment
below for the options and a request for your view.

## Not in this PR (on purpose)

- A `chat` mode (calls inside the person's text session): a text message sent during a call would
  collide with the running call turn, and the call prompt style would leak into text answers.
- Deleting a call's session after the call.
- Extending a call.

## Tests

`render_title` table (fields, whitespace, injection, bad templates), every call asking the host to
title, the host titling once with unique `#N` titles (and never blocking a call when the database
fails), adapter parsing of both keys, thread id per mode, and a controller test that
the heads-up is spoken once and the call still ends on time. Counts with this PR: 479 passed and 9 skipped on 3.13 and 3.14 (call packages installed), 262 passed without them.
