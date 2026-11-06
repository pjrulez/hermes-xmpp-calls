## Why

Calls depend on server features that must be proven, not assumed: TURN credentials via XEP-0215, a reachable coturn, caps passthrough, carbons, mobile wake-up. `prosodyctl check turn` currently fails from the Prosody container ("No STUN response: No route to host"). The README must list the requirements so another operator can reproduce compatibility.

## What changes

- Verify each requirement on `xmpp.example.org` with commands and record the results.
- Diagnose the TURN failure (container hairpin vs real unreachability) with an external test.
- Maintain the README "Prosody server requirements" section.

## Out of scope

Changing the Prosody deployment (that is done in the Prosody repo with its own gates), federation, MUC calls.

## Dependencies

mad Prosody deployment (`~/Projects/Prosody`), coturn container, Headscale and firewall rules, bot accounts.

## Acceptance

P1 to P4 evidence exists; the README table matches observed state; an external client can fetch TURN credentials and gather a relay candidate.
