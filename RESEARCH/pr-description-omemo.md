Title: feat(omemo): key-store safety, device-list refresh and plaintext_peers

Draft, based on current `main`: one commit, `feat(omemo): ...`. This is the split requested in the
review of #15, so it can be reverted on its own.

## What it changes

All of it is about not destroying an OMEMO identity, and none of it needs calls.

1. **Store safety.** One process per store file (an `flock` on `<file>.lock`; Windows locking is
   simulated in tests only), atomic owner-only (0600) writes (file and directory are synced) that follow symlinks without
   replacing them, and the lock survives a module reload. The adapter refuses to start OMEMO when the file
   exists but cannot be read or is empty (what a crash between truncating and writing leaves),
   instead of silently starting empty (a new identity key breaks every
   existing session). Several storage objects for one file in one process share one data dict.
   Reason: two gateways sharing a home, or a crash during a write, otherwise destroy the double
   ratchets, which needs a manual cleanup.
2. **One-shot sender.** `send_xmpp_message` (`hermes send` and CLI cron delivery) never uses OMEMO:
   it is a second process next to the gateway and would advance the same ratchets. See the
   behaviour change below.
3. **Device lists.** A contact's device list is downloaded before encrypting to them, at most
   every 10 minutes. slixmpp-omemo skips the download under mutual presence, so a fresh store
   failed with `NoEligibleDevices`.
4. **`xmpp.plaintext_peers`** (`XMPP_PLAINTEXT_PEERS`): bare JIDs that never get OMEMO-encrypted
   messages; empty by default. For a trusted partner agent that cannot do OMEMO.

## Existing stores keep working: no conversion

The file format is unchanged: still one JSON object of key to value, written with `indent=2`. A
store written by the previous version loads as it is, and the previous version can read one written
by this version, so going back is possible too. What is new around the file: its mode is set to 0600
on load, a `<file>.lock` file sits next to it while a process uses it, and a `<file>.tmp` exists for
an instant while it is written. A test writes a store the old way, loads it, saves, and checks the
content, the mode and the files left in the directory. Copying the store file before the first start
costs nothing if you want a backup.

## Behaviour changes to be aware of

1. **Messages from the one-shot sender are now protected by TLS only.** They used to be
   OMEMO-encrypted, so an operator will experience this as "my scheduled messages stopped being
   end-to-end encrypted". The trade is deliberate: a second process advancing the ratchets breaks
   the live gateway's sessions (and the new lock would refuse it anyway). Messages sent by the
   running gateway are not affected. The CHANGELOG and the README OMEMO section say so.
2. An unreadable, corrupt or empty store now stops OMEMO from starting (logged as an error)
   instead of being replaced by an empty one. That is deliberate. Removing the file is the
   explicit way to start over.

## Testing

Same CI-style run as #15 (`pytest tests/ -q -W error`, upstream pins): 493 passed, 9 skipped on
3.13 and 3.14; 269 passed, 18 skipped without the call packages. Tests cover the lock, atomic and
private writes (including the directory sync), an unreadable or empty store never being
overwritten, `connect()` completing with OMEMO off when the store is refused, a second process being refused, a
world-readable key file being locked down, two storages for one file, symlinked stores, the
simulated Windows lock, the device-list refresh (and its throttle table not growing) and the plaintext peers.
Live: the gateways on three hosts run this code with their own OMEMO stores (initialised, no store errors in the logs). No long soak test yet.

## Not covered

Windows locking is only tested by simulation. Existing stores are read as before (format unchanged).
