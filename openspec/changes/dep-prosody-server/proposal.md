## Why

Calls rely on a few Prosody features (XEP-0215 credentials, caps, carbons, mutual presence). The README must list them so another tailnet operator can reproduce the setup. Human calls already work here, so the work is documentation and one bot-specific check, not infrastructure.

## What changes

- Verify each requirement on the tailnet Prosody with a command and record it in the README table.
- Confirm the test bot can fetch XEP-0215 credentials.
- Keep the `prosodyctl check turn` quirk noted; investigate only if a bot call fails to connect.

## Out of scope

Public-Internet deployment, changes to the Prosody deployment (done in the Prosody repo), federation, MUC calls.

## Acceptance

P1 and P3 evidence exists and the README table matches observed state.
