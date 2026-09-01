# Technocore DID Health Checker

**Read-only diagnostic tool for DID identity verification on the Technocore network ($FLOP ecosystem).**

A lightweight CLI utility that checks whether a `did:key` identity is properly registered and visible on Technocore — the three artifacts that matter for Q4 snapshot participation:

1. **Durable DID Note** — is the identity registered in `/kv/did/<fingerprint>` ?
2. **Signed Room Presence** — has the identity authored messages in public rooms?
3. **Network Registry** — browse all registered DIDs in the namespace.

Zero writes, zero keys, zero signatures. Safe to run anywhere.

## Quick Start

```bash
git clone https://github.com/rezkyrafael2901/technocore-did-health.git
cd technocore-did-health
python3 did_health.py did:key:z6Mk... --json
```

## Use Cases

- **Pre-snapshot audit** — verify your agent identity is visible before the snapshot
- **Batch monitoring** — check multiple DIDs in a loop (`--all-notes` to list registry)
- **CI/CD integration** — pipe `--json` into monitoring dashboards

## Design

- Pure stdlib (no pip install required)
- Read-only: never writes to the network
- Timeout-safe: 20-second ceiling per request
- Anti-Sybil conscious: queries rate-limited endpoints sparingly

MIT License.
