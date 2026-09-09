"""
blockchain_seal.py
-------------------
Implements a lightweight, blockchain-inspired integrity layer for the
evidence log. This is NOT a distributed ledger / consensus network (that
would be out of scope for a prototype) - it's the core cryptographic idea
that gives blockchain its tamper-evidence: each record's hash is derived
from its own data PLUS the previous record's hash, forming a chain. If any
past record is altered, every hash after it breaks, which is exactly the
tamper-detection property chain-of-custody needs.

Design:
    block_hash_i = SHA256( canonical(record_i) + block_hash_(i-1) )

The genesis block uses a fixed seed hash of all zeros.
"""

import hashlib
import json
import pandas as pd

GENESIS_HASH = "0" * 64


def canonical_record(row: pd.Series) -> str:
    """Deterministic string representation of a record for hashing.
    Only the fields that matter for custody integrity are included -
    Event_ID, Timestamp, RFID_ID, Case_ID, Location, Action, Handler.
    """
    fields = ["Event_ID", "Timestamp", "RFID_ID", "Case_ID", "Location", "Action", "Handler"]
    payload = {f: str(row[f]) for f in fields}
    return json.dumps(payload, sort_keys=True)


def build_chain(df: pd.DataFrame) -> pd.DataFrame:
    """Adds Prev_Hash and Block_Hash columns to the dataframe, chaining
    each row's hash to the previous row's hash."""
    prev_hash = GENESIS_HASH
    prev_hashes, block_hashes = [], []

    for _, row in df.iterrows():
        record_str = canonical_record(row)
        block_hash = hashlib.sha256((record_str + prev_hash).encode()).hexdigest()
        prev_hashes.append(prev_hash)
        block_hashes.append(block_hash)
        prev_hash = block_hash

    out = df.copy()
    out["Prev_Hash"] = prev_hashes
    out["Block_Hash"] = block_hashes
    return out


def verify_chain(df: pd.DataFrame) -> dict:
    """Recomputes the hash chain from scratch and compares it to the
    stored Prev_Hash / Block_Hash columns. Returns a report describing
    exactly which record(s), if any, have been tampered with.
    """
    prev_hash = GENESIS_HASH
    broken_at = []

    for i, row in df.iterrows():
        expected_prev = prev_hash
        record_str = canonical_record(row)
        recomputed_hash = hashlib.sha256((record_str + expected_prev).encode()).hexdigest()

        stored_prev = row.get("Prev_Hash")
        stored_hash = row.get("Block_Hash")

        if stored_prev != expected_prev or stored_hash != recomputed_hash:
            broken_at.append({
                "row_index": int(i),
                "Event_ID": row.get("Event_ID"),
                "expected_prev_hash": expected_prev,
                "stored_prev_hash": stored_prev,
                "recomputed_hash": recomputed_hash,
                "stored_hash": stored_hash,
            })

        # Chain continues from the *recomputed* hash regardless, so a single
        # tampered record is pinpointed rather than cascading false positives
        # for every record after it.
        prev_hash = recomputed_hash if stored_hash is None else stored_hash if stored_hash == recomputed_hash else recomputed_hash

    return {
        "is_valid": len(broken_at) == 0,
        "total_records": len(df),
        "broken_records": broken_at,
    }


if __name__ == "__main__":
    df = pd.read_csv("evidence_movement_log.csv")
    chained = build_chain(df)
    chained.to_csv("evidence_log_sealed.csv", index=False)

    result = verify_chain(chained)
    print(f"Integrity check on clean sealed log: valid = {result['is_valid']}")

    # --- Demonstrate tamper detection ---
    tampered = chained.copy()
    tamper_idx = 5
    original_location = tampered.loc[tamper_idx, "Location"]
    tampered.loc[tamper_idx, "Location"] = "Cafeteria"  # simulate a forged record
    print(f"\nSimulating tampering: row {tamper_idx} Location changed "
          f"'{original_location}' -> 'Cafeteria' (Block_Hash left unchanged, as a forger would do)")

    tamper_result = verify_chain(tampered)
    print(f"Integrity check after tampering: valid = {tamper_result['is_valid']}")
    if not tamper_result["is_valid"]:
        print("Detected broken record(s):")
        for b in tamper_result["broken_records"][:3]:
            print(f"  -> {b['Event_ID']} (row {b['row_index']}): hash mismatch detected")

    with open("blockchain_verification_demo.json", "w") as f:
        json.dump({
            "clean_check": result,
            "tampered_check": tamper_result,
        }, f, indent=2, default=str)
