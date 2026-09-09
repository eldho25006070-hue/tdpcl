"""
run_pipeline.py
----------------
Master orchestrator. Runs the full pipeline end-to-end:
  simulate -> chain-of-custody -> anomaly detection -> blockchain sealing
and exports a single evidence_dashboard_data.json bundle that the
Streamlit app (or any front-end) can load directly, plus a tampering
demo for the "Verify Integrity" feature.

Run this any time you want to regenerate all artifacts from scratch:
    python run_pipeline.py
"""

import json
import pandas as pd

from simulate_data import generate_dataset
from chain_of_custody import box_status_summary, custody_gaps
from anomaly_detection import run_detection, summarize
from blockchain_seal import build_chain, verify_chain, GENESIS_HASH


def main():
    print("Step 1/4: Simulating RFID evidence movement data...")
    raw_df = generate_dataset()
    raw_df.to_csv("evidence_movement_log.csv", index=False)
    print(f"  -> {len(raw_df)} events across {raw_df['RFID_ID'].nunique()} evidence boxes")

    print("Step 2/4: Running anomaly detection (rule-based + Isolation Forest)...")
    detected_df = run_detection(raw_df)
    anomaly_summary = summarize(detected_df)
    print(f"  -> {anomaly_summary['total_anomalies']} anomalies flagged "
          f"({anomaly_summary['anomaly_rate_pct']}% of events)")

    print("Step 3/4: Building chain-of-custody summaries...")
    status_df = box_status_summary(raw_df)
    gaps_df = custody_gaps(raw_df)

    print("Step 4/4: Sealing log with blockchain-style hash chain...")
    sealed_df = build_chain(detected_df)
    integrity = verify_chain(sealed_df)
    print(f"  -> Chain valid: {integrity['is_valid']} ({len(sealed_df)} blocks)")

    # Also produce a tampered copy for the live "detect tampering" demo
    tampered_df = sealed_df.copy()
    tamper_target = 5
    tampered_df.loc[tamper_target, "Location"] = "Cafeteria"
    tampered_df.loc[tamper_target, "Action"] = "Unauthorized Movement"
    tamper_check = verify_chain(tampered_df)

    # -------------------------------------------------------------
    # Bundle everything the dashboard needs into one JSON file
    # -------------------------------------------------------------
    def records(df):
        out = df.copy()
        for col in out.columns:
            if pd.api.types.is_datetime64_any_dtype(out[col]):
                out[col] = out[col].astype(str)
        return json.loads(out.to_json(orient="records"))

    bundle = {
        "meta": {
            "project": "Smart Evidence Tracking System",
            "genesis_hash": GENESIS_HASH,
            "total_boxes": int(raw_df["RFID_ID"].nunique()),
            "total_events": int(len(raw_df)),
        },
        "events": records(sealed_df),
        "box_status": records(status_df),
        "custody_gaps": records(gaps_df) if len(gaps_df) else [],
        "anomaly_summary": anomaly_summary,
        "integrity_clean": integrity,
        "integrity_tampered_demo": {
            "tampered_event_id": str(sealed_df.loc[tamper_target, "Event_ID"]),
            "result": tamper_check,
        },
    }

    with open("evidence_dashboard_data.json", "w") as f:
        json.dump(bundle, f, indent=2, default=str)

    sealed_df.to_csv("evidence_log_final_sealed.csv", index=False)
    print("\nPipeline complete. Outputs written:")
    print("  - evidence_movement_log.csv")
    print("  - evidence_log_final_sealed.csv")
    print("  - evidence_dashboard_data.json  (feed this to app.py / the dashboard)")


if __name__ == "__main__":
    main()
