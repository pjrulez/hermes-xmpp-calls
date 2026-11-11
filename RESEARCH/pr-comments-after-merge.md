# Comment on #15 (merged; commenting does not reopen it)

Thank you for the careful review, for taking the time to run it yourself, and for merging. The `webrtcvad` catch in `call_packages` (4d68934) is a good one: I only tested on hosts where nothing was installed, so a partly satisfied set never came up.

Two follow-ups are already open: #16 (the OMEMO store work, rebased onto current main, still a draft as you wanted) and #17 (the small `.ogg` content-type fix that explained the 3.13 failures). If anything misbehaves when you try calls with Conversations or Monal, tell me which client and we can try to reproduce it.

# Comment on #16 (draft)

Rebased onto current `main` (after the squash merge and 4d68934): the PR is the one OMEMO commit again, CI is green. It stays a draft so it can sit on a real store first. I run this code on three hosts. No long soak test yet.
