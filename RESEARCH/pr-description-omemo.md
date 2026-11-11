Title: feat(omemo): key-store safety, device-list refresh and plaintext_peers

Draft, stacked on #15 (live audio calls). Until #15 is merged this PR's diff also shows its
commits; the OMEMO change is the last commit only: `feat(omemo): ...`. This is the split
requested in the review of #15, so it can be reverted on its own.

## What it changes

All of it is about not destroying an OMEMO identity, and none of it needs calls.

1. **Store safety.** One process per store file (an `flock` on `<file>.lock`; Windows locking is
   simulated in tests only), atomic owner-only (0600) writes that follow symlinks without replacing
   them, and the lock survives a module reload. The adapter refuses to start OMEMO when the file
   exists but cannot be read, instead of silently starting empty (a new identity key breaks every
   existing session). Several storage objects for one file in one process share one data dict.
   Reason: two gateways sharing a home, or a crash during a write, otherwise destroy the double
   ratchets, which needs a manual cleanup.
2. **One-shot sender.** `send_xmpp_message` (the cron/`send_message` path) never uses OMEMO: it
   is a second process next to the gateway and would advance the same ratchets.
3. **Device lists.** A contact's device list is downloaded before encrypting to them, at most
   every 10 minutes. slixmpp-omemo skips the download under mutual presence, so a fresh store
   failed with `NoEligibleDevices`.
4. **`xmpp.plaintext_peers`** (`XMPP_PLAINTEXT_PEERS`): bare JIDs that never get OMEMO-encrypted
   messages; empty by default. For a trusted partner agent that cannot do OMEMO.

## Behaviour change to be aware of

An unreadable or corrupt store now stops OMEMO from starting (logged as an error) instead of
being replaced by an empty one. That is deliberate. Removing the file is the explicit way to
start over.

## Testing

Same CI-style run as #15 (`pytest tests/ -q -W error`, upstream pins): 600 passed, 9 skipped on
3.14; 367 passed, 18 skipped without the call packages. Tests cover the lock, atomic and private
writes, an unreadable store never being overwritten, a second process being refused, a
world-readable key file being locked down, two storages for one file, symlinked stores, the
simulated Windows lock, the device-list refresh and the plaintext peers.
Live: the gateways on three hosts run this code with their own OMEMO stores (initialised, no store errors in the logs). No long soak test yet.

## Not covered

Windows locking is only tested by simulation. Existing stores are read as before (format unchanged).
