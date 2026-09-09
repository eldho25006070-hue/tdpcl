"""
simulate_data.py
-----------------
Simulates RFID-tagged evidence-box movement data for the Smart Evidence
Tracking System.

Why simulation? Real RFID hardware and a live police chain-of-custody feed
aren't available for a student project, so this module generates
statistically realistic movement logs: normal custody transfers PLUS a
controlled set of injected anomalies (unauthorized locations, impossible
transfer speeds, odd-hour movements, duplicate/overlapping scans). This
lets the anomaly-detection module be evaluated against a known ground
truth, which is good data-science practice (you can quote a precision/
recall number in the report instead of just "it found some anomalies").
"""

import random
import hashlib
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

random.seed(42)
np.random.seed(42)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

AUTHORIZED_LOCATIONS = [
    "Crime Scene",
    "Evidence Intake",
    "Storage Room A",
    "Storage Room B",
    "Forensic Lab",
    "Court Room",
    "Transport Vehicle",
]

UNAUTHORIZED_LOCATIONS = ["Cafeteria", "Parking Lot", "Personal Vehicle", "Off-site (Unknown)"]

HANDLERS = [
    "Officer A. Rao", "Officer B. Singh", "Officer C. Mehta",
    "Lab Tech D. Iyer", "Lab Tech E. Khan", "Officer F. Verma",
    "Clerk G. Nair", "Officer H. Das",
]

ACTIONS = ["Collected", "Received", "Transferred", "Analyzed", "Returned", "Checked-Out", "Checked-In"]

# Approximate "distance" cost between locations, used to decide whether a
# transfer time is physically plausible (pure heuristic, not real GPS).
LOCATION_TRAVEL_MINUTES = {
    ("Crime Scene", "Evidence Intake"): 30,
    ("Evidence Intake", "Storage Room A"): 10,
    ("Evidence Intake", "Storage Room B"): 10,
    ("Storage Room A", "Forensic Lab"): 15,
    ("Storage Room B", "Forensic Lab"): 15,
    ("Forensic Lab", "Storage Room A"): 15,
    ("Forensic Lab", "Court Room"): 25,
    ("Storage Room A", "Court Room"): 30,
    ("Storage Room B", "Transport Vehicle"): 5,
    ("Transport Vehicle", "Court Room"): 20,
}

WORKING_HOURS = (8, 20)  # 08:00 - 20:00 considered "normal"

N_EVIDENCE_BOXES = 8
N_ANOMALIES_TARGET = 14  # injected ground-truth anomalies


def _new_tag_id(i):
    return f"EB{101 + i}"


def _make_case_id(i):
    return f"FIR-2026-{1000 + i}"


def generate_dataset(n_boxes=N_EVIDENCE_BOXES, start_date="2026-09-01"):
    rows = []
    start = datetime.strptime(start_date, "%Y-%m-%d")
    ground_truth = []  # list of dict: index, type, reason -> filled after building df

    for i in range(n_boxes):
        tag = _new_tag_id(i)
        case_id = _make_case_id(i)
        current_time = start + timedelta(days=i, hours=random.randint(8, 11))
        # Every box starts at the crime scene, being collected
        loc = "Crime Scene"
        rows.append({
            "Timestamp": current_time,
            "RFID_ID": tag,
            "Case_ID": case_id,
            "Location": loc,
            "Action": "Collected",
            "Handler": random.choice(HANDLERS),
        })

        n_events = random.randint(6, 10)
        path = ["Evidence Intake", "Storage Room A", "Forensic Lab", "Storage Room A",
                "Court Room", "Storage Room B", "Transport Vehicle"]

        for j in range(n_events):
            prev_loc = loc
            loc = path[j % len(path)]
            gap_minutes = LOCATION_TRAVEL_MINUTES.get((prev_loc, loc), random.randint(20, 90))
            # normal jitter around expected travel time
            gap_minutes = max(5, int(np.random.normal(gap_minutes + 20, 10)))
            current_time = current_time + timedelta(minutes=gap_minutes)
            action = random.choice(["Received", "Transferred", "Analyzed", "Checked-In", "Checked-Out"])
            rows.append({
                "Timestamp": current_time,
                "RFID_ID": tag,
                "Case_ID": case_id,
                "Location": loc,
                "Action": action,
                "Handler": random.choice(HANDLERS),
            })

        # Final return to storage
        current_time = current_time + timedelta(minutes=random.randint(30, 60))
        rows.append({
            "Timestamp": current_time,
            "RFID_ID": tag,
            "Case_ID": case_id,
            "Location": "Storage Room A",
            "Action": "Returned",
            "Handler": random.choice(HANDLERS),
        })

    df = pd.DataFrame(rows).sort_values(["RFID_ID", "Timestamp"]).reset_index(drop=True)

    # -----------------------------------------------------------------
    # Inject controlled, labeled anomalies (ground truth for evaluation)
    # -----------------------------------------------------------------
    anomaly_rows = []

    # Type 1: Unauthorized location visits (5 events)
    for _ in range(5):
        idx = random.randint(0, len(df) - 1)
        base = df.loc[idx]
        t = base["Timestamp"] + timedelta(minutes=random.randint(15, 45))
        anomaly_rows.append({
            "Timestamp": t, "RFID_ID": base["RFID_ID"], "Case_ID": base["Case_ID"],
            "Location": random.choice(UNAUTHORIZED_LOCATIONS), "Action": "Unauthorized Movement",
            "Handler": "UNKNOWN",
        })

    # Type 2: Odd-hour movements (4 events, between 00:00-05:00)
    for _ in range(4):
        idx = random.randint(0, len(df) - 1)
        base = df.loc[idx]
        odd_time = base["Timestamp"].replace(hour=random.randint(0, 4), minute=random.randint(0, 59))
        anomaly_rows.append({
            "Timestamp": odd_time, "RFID_ID": base["RFID_ID"], "Case_ID": base["Case_ID"],
            "Location": random.choice(AUTHORIZED_LOCATIONS), "Action": "Checked-Out",
            "Handler": random.choice(HANDLERS),
        })

    # Type 3: Impossibly fast transfers (3 events) -> handled by adjusting an
    # existing consecutive pair's gap to <2 minutes across a long real distance
    fast_candidates = df[df["Location"].isin(["Crime Scene", "Court Room"])].index.tolist()
    for idx in random.sample(fast_candidates, min(3, len(fast_candidates))):
        if idx + 1 < len(df) and df.loc[idx + 1, "RFID_ID"] == df.loc[idx, "RFID_ID"]:
            df.loc[idx + 1, "Timestamp"] = df.loc[idx, "Timestamp"] + timedelta(minutes=1)

    # Type 4: Duplicate simultaneous scans at two different locations (2 events)
    for _ in range(2):
        idx = random.randint(0, len(df) - 1)
        base = df.loc[idx]
        anomaly_rows.append({
            "Timestamp": base["Timestamp"], "RFID_ID": base["RFID_ID"], "Case_ID": base["Case_ID"],
            "Location": random.choice([l for l in AUTHORIZED_LOCATIONS if l != base["Location"]]),
            "Action": "Received", "Handler": random.choice(HANDLERS),
        })

    df = pd.concat([df, pd.DataFrame(anomaly_rows)], ignore_index=True)
    df = df.sort_values(["RFID_ID", "Timestamp"]).reset_index(drop=True)

    # Assign a stable Event_ID after final ordering (needed for hash chaining)
    df.insert(0, "Event_ID", [f"EVT{idx:04d}" for idx in range(len(df))])

    return df


if __name__ == "__main__":
    df = generate_dataset()
    df.to_csv("evidence_movement_log.csv", index=False)
    print(f"Generated {len(df)} movement records for {df['RFID_ID'].nunique()} evidence boxes.")
    print(df.head(10).to_string(index=False))
