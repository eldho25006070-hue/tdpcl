"""
anomaly_detection.py
---------------------
The Data Science core of the project. Two complementary detection
strategies are combined, which is a defensible design choice to explain
in a viva/demo:

1. RULE-BASED detectors (deterministic, explainable, catch known-bad
   patterns immediately):
     - Unauthorized location visited
     - Movement during non-working hours
     - Impossibly fast transfer between two locations
     - Duplicate/simultaneous scans of the same tag at different places

2. STATISTICAL / ML detector (unsupervised, catches UNKNOWN patterns the
   rules didn't anticipate):
     - Isolation Forest over engineered features (hour of day, gap since
       previous scan, location-visit frequency) flags records that look
       globally "weird" even if no single rule fires.

Combining both means: rules give high-precision explainable alerts, and
the Isolation Forest gives recall on novel anomaly types - a standard
hybrid approach in real fraud/intrusion detection systems, and a good
talking point for "why is this actually data science and not just
if-statements".
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

AUTHORIZED_LOCATIONS = {
    "Crime Scene", "Evidence Intake", "Storage Room A", "Storage Room B",
    "Forensic Lab", "Court Room", "Transport Vehicle",
}

WORKING_HOURS = (6, 22)  # outside this window = flagged as odd-hour
MIN_PLAUSIBLE_TRANSFER_MINUTES = 3  # below this, a transfer is "impossibly fast"


def _load(df_or_path):
    if isinstance(df_or_path, pd.DataFrame):
        df = df_or_path.copy()
    else:
        df = pd.read_csv(df_or_path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    return df.sort_values(["RFID_ID", "Timestamp"]).reset_index(drop=True)


def rule_based_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Flag_Unauthorized_Location"] = ~df["Location"].isin(AUTHORIZED_LOCATIONS)
    df["Flag_Odd_Hour"] = ~df["Timestamp"].dt.hour.between(*WORKING_HOURS)

    df["Prev_Timestamp"] = df.groupby("RFID_ID")["Timestamp"].shift(1)
    df["Prev_Location"] = df.groupby("RFID_ID")["Location"].shift(1)
    df["Gap_Minutes"] = (df["Timestamp"] - df["Prev_Timestamp"]).dt.total_seconds() / 60

    moved = df["Location"] != df["Prev_Location"]
    df["Flag_Impossible_Speed"] = moved & (df["Gap_Minutes"] >= 0) & (df["Gap_Minutes"] < MIN_PLAUSIBLE_TRANSFER_MINUTES)

    # Duplicate/simultaneous scan: same tag, same timestamp appears twice
    dup_mask = df.duplicated(subset=["RFID_ID", "Timestamp"], keep=False)
    df["Flag_Duplicate_Scan"] = dup_mask

    return df


def statistical_flags(df: pd.DataFrame, contamination=0.08) -> pd.DataFrame:
    df = df.copy()
    features = pd.DataFrame(index=df.index)
    features["hour"] = df["Timestamp"].dt.hour
    features["gap_minutes"] = df["Gap_Minutes"].fillna(df["Gap_Minutes"].median())
    features["gap_minutes"] = features["gap_minutes"].clip(lower=0)

    loc_freq = df["Location"].value_counts(normalize=True)
    features["location_rarity"] = df["Location"].map(lambda l: 1 - loc_freq.get(l, 0))

    handler_freq = df["Handler"].value_counts(normalize=True)
    features["handler_rarity"] = df["Handler"].map(lambda h: 1 - handler_freq.get(h, 0))

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
    )
    preds = model.fit_predict(features)  # -1 = anomaly, 1 = normal
    scores = model.decision_function(features)  # lower = more anomalous

    df["Anomaly_Score"] = scores
    df["Flag_Statistical_Outlier"] = preds == -1
    return df


def run_detection(df_or_path):
    df = _load(df_or_path)
    df = rule_based_flags(df)
    df = statistical_flags(df)

    flag_cols = [c for c in df.columns if c.startswith("Flag_")]
    df["Is_Anomaly"] = df[flag_cols].any(axis=1)
    df["Anomaly_Reasons"] = df[flag_cols].apply(
        lambda r: ", ".join(c.replace("Flag_", "").replace("_", " ") for c in flag_cols if r[c]),
        axis=1,
    )
    return df


def summarize(df: pd.DataFrame) -> dict:
    total = len(df)
    anomalies = df[df["Is_Anomaly"]]
    by_reason = {}
    for c in [c for c in df.columns if c.startswith("Flag_")]:
        by_reason[c.replace("Flag_", "")] = int(df[c].sum())

    return {
        "total_records": total,
        "total_anomalies": int(anomalies.shape[0]),
        "anomaly_rate_pct": round(100 * anomalies.shape[0] / total, 2),
        "by_type": by_reason,
        "affected_evidence_boxes": sorted(anomalies["RFID_ID"].unique().tolist()),
    }


if __name__ == "__main__":
    df = run_detection("evidence_movement_log.csv")
    df.to_csv("evidence_log_with_anomalies.csv", index=False)

    summary = summarize(df)
    import json
    with open("anomaly_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print("\nSample flagged records:")
    print(df[df["Is_Anomaly"]][["Event_ID", "RFID_ID", "Timestamp", "Location", "Anomaly_Reasons"]].head(15).to_string(index=False))
