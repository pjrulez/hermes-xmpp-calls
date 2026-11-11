Title: fix(voice): fall back to the voice MIME table when the system has no mime.types

`mimetypes.guess_type()` reads the system `/etc/mime.types`. Python before 3.14 does not know
`.ogg` without it, so on a minimal host or container (no `mime.types`) `send_voice` and
`_upload_and_send` uploaded without a content type. The slot then carries no type, and servers
tend to store it as `application/octet-stream`, which some clients will not play inline.

The adapter already has `_VOICE_EXT_MIME` (`.ogg`, `.oga`, `.opus`, `.m4a` ...). The fix is a small
helper, `_guess_content_type(path)`: `mimetypes` first, the table when it finds nothing. Both
upload call sites use it. 8 lines changed in `adapter.py`.

Tests: one new test forces `mimetypes.guess_type` to return nothing and checks `.OGG`, `.m4a` and an
unknown extension. This also makes the two existing
`test_voice_wire_contains_sfs_and_matching_legacy_url` cases pass on Python 3.13 on a host without
`/etc/mime.types` (they failed there before; the maintainer's machine has the file, so upstream CI is green).
Run as CI does (`pytest tests/ -q -W error`): 245 passed, 9 skipped on 3.13 and 3.14.
