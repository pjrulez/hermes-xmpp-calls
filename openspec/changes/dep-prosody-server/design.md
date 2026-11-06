## Context

Observed on 2026-11-06: modules enabled include turn_external, carbons, smacks, csi_simple, cloud_notify, mam, pep; TURN host `turn.example.org:3478`, tcp on, ttl 3600; the coturn container runs; `prosodyctl check turn` reports no STUN response.

## Design

- Checks are read-only: `prosodyctl check turn`, `prosodyctl shell` queries, an XEP-0215 IQ from a bot session, an external STUN binding request and a TURN allocation from fw.
- Failure analysis separates three layers: Prosody to coturn (container network), client to coturn (public reachability, UDP and TCP 3478, relay port range), credential validity (shared secret, ttl, realm).
- Results go into the README table with date and command, never secrets or full addresses.

## Risks

Residential or Tailnet-only reachability means calls work only for some networks. Document the supported topology instead of hiding it.
