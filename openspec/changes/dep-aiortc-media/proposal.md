## Why

aiortc (with aioice and av) gives ICE, TURN, DTLS-SRTP and Opus in Python, but needs wrapping for our call: dedicated loop thread, audio resampling, pacing, silence keepalive, endpointing, clean teardown, and a verified platform matrix (NixOS needs a working libstdc++ for av wheels).

## What changes

- Add `xmpp_calls/media/` with an engine class that owns the loop thread, peer connections and audio queues.
- Pin version ranges and record platform results for fw (3.14.9), the VMs, and NixOS.
- Select the endpointing method with evidence.

## Out of scope

Video, recording, SFU, any Hermes imports.

## Dependencies

aiortc 1.16.0, aioice 0.13.0, av 19.0.2, numpy, pyOpenSSL/pylibsrtp as pulled by aiortc.

## Acceptance

R6 and R9 evidence exists; the engine passes loopback and 50-call leak tests; a Conversations call (B2) carries audio both ways for 5 minutes without drift or stall.
