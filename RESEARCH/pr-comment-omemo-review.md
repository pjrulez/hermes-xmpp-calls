Thank you, this is a careful review, and the zero-byte case was a real hole. Everything below is pushed (one commit again, rebased on current `main`, CI to follow).

**Zero-byte store.** Fixed: an existing store file that is empty is treated like an unreadable one. `OmemoStoreError`, OMEMO stays off, the log says "is empty (an interrupted write?)" and tells you to restore a backup or move the file away; the file is not touched. A test covers it.

**Connect test.** Added `test_unusable_omemo_store_leaves_chat_up_with_omemo_off`: a corrupt store is opened from inside `register_plugin("xep_0384", ...)` as slixmpp's `plugin_init` does, and the test asserts `connect()` returns True, `"xep_0384" not in _registered_plugins`, `_use_omemo(...)` is False and the file is unchanged. Honest note: it also passes on the previous code, because that behaviour was already there; it is a lock-in, as you suggested.

**One-shot sender.** Agreed, and it is now said louder: a "Behaviour changes" item at the top of the PR body, a "Changed" entry in the CHANGELOG, and a sentence in the README OMEMO section (TLS only, readable by the server operator, previously OMEMO-encrypted; the running gateway is unaffected). I also moved this PR's CHANGELOG entries out of the 0.5.0 section into `[Unreleased]`, where they belong now that 0.5.0 is merged.

**Nits.** Removed the stray `_csv` assert; added the blank line; `_omemo_refreshed` is pruned when it passes 64 entries (entries older than the 10-minute window are inert anyway; there is a test); `_save()` now also fsyncs the directory after the rename (POSIX; a test checks the file is synced, then the directory).

The count in the body is now 493 passed, 9 skipped on both 3.13 and 3.14 (yours was 488 before these tests and the voice fix that merged in the meantime).
