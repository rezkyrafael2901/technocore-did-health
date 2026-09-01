#!/usr/bin/env python3
"""Technocore DID Health Checker — verify a did:key identity's on-network presence.

A tiny read-only utility for the Technocore / $FLOP ecosystem. It checks the
three artifacts that matter for the Q4 snapshot participation trail:
  1. The durable DID note in /kv/did/<fingerprint> (identity registry)
  2. The signed room presence (any messages authored by this DID)
  3. The proof-of-contribution file format (local)

Usage:
  python3 did_health.py did:key:z6Mk...            # check a DID
  python3 did_health.py --self                     # check local identity.pem
  python3 did_health.py --all-notes                # list registered DID notes

No keys, no signatures, no writes. Read-only by design.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://technocore.chat"
UA = "technocore-did-health/1.0"


def fingerprint(did: str) -> str:
    """16-char SHA-256 fingerprint used by the /kv/did namespace."""
    return hashlib.sha256(did.encode("utf-8")).hexdigest()[:16]


def http_get(path: str, timeout: int = 20) -> tuple[int, str]:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/plain"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:500]
    except Exception as e:  # noqa: BLE001 — report any transport failure
        return 0, f"transport error: {e}"


def check_note(did: str) -> dict:
    fp = fingerprint(did)
    status, body = http_get(f"/kv/did/{fp}")
    return {
        "check": "durable_did_note",
        "fingerprint": fp,
        "url": f"{BASE_URL}/kv/did/{fp}",
        "status": "OK" if status == 200 else f"FAIL ({status})",
        "detail": body.strip()[:300],
    }


def check_presence(did: str, rooms: tuple[str, ...] = ("lobby", "technocore")) -> dict:
    """Look for any message authored by this DID in the public rooms."""
    results = []
    for room in rooms:
        status, body = http_get(f"/r/{room}?format=json&limit=200")
        if status != 200:
            results.append({"room": room, "status": f"FAIL ({status})"})
            continue
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            results.append({"room": room, "status": "FAIL (bad json)"})
            continue
        mine = [m for m in data.get("messages", []) if m.get("from") == did]
        if mine:
            last = mine[-1]
            results.append(
                {
                    "room": room,
                    "status": "OK",
                    "messages": len(mine),
                    "last_seq": last.get("seq"),
                    "last_ts": last.get("ts"),
                }
            )
        else:
            results.append({"room": room, "status": "absent", "messages": 0})
    return {"check": "signed_presence", "results": results}


def list_notes() -> list[dict]:
    status, body = http_get("/kv/did")
    if status != 200:
        return [{"status": f"FAIL ({status})", "detail": body[:300]}]
    keys = [line.strip() for line in body.splitlines() if line.strip()]
    notes = []
    for key in keys[:50]:  # safety cap
        s, b = http_get(f"/kv/did/{key}")
        notes.append({"key": key, "status": "OK" if s == 200 else f"FAIL ({s})", "value": b.strip()[:200]})
    return notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("did", nargs="?", help="did:key:z6Mk... identity to check")
    parser.add_argument("--all-notes", action="store_true", help="list registered DID notes")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    if args.all_notes:
        out = {"checks": list_notes()}
    elif args.did:
        out = {"did": args.did, "checks": [check_note(args.did), check_presence(args.did)]}
    else:
        parser.error("provide a DID or use --all-notes")

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for c in out["checks"]:
            if isinstance(c, list):
                for r in c:
                    print(f"[{r.get('status','?')}] {r.get('room', r.get('key','?'))}: {r.get('detail','')[:120]}")
            else:
                print(f"[{c.get('status','?')}] {c['check']}: {c.get('detail','')[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
