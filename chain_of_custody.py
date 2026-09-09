"""
chain_of_custody.py
--------------------
Builds the digital Chain-of-Custody view: for each RFID-tagged evidence
box, an ordered timeline of every custody event (who had it, where, when,
what action was taken), plus a per-box status summary. This is the piece
that directly digitizes the paper custody log the video describes.
"""

import pandas as pd


def build_timelines(df: pd.DataFrame) -> dict:
    """Returns {rfid_id: [event_dict, ...]} ordered by time."""
    timelines = {}
    for rfid, group in df.groupby("RFID_ID"):
        g = group.sort_values("Timestamp")
        timelines[rfid] = g.to_dict(orient="records")
    return timelines


def box_status_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Latest known location/handler/status per evidence box, plus a
    custody-gap check (time since last scan)."""
    df = df.copy()
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    latest = df.sort_values("Timestamp").groupby("RFID_ID").tail(1)
    latest = latest[["RFID_ID", "Case_ID", "Timestamp", "Location", "Action", "Handler"]]
    latest = latest.rename(columns={
        "Timestamp": "Last_Seen", "Location": "Current_Location",
        "Handler": "Current_Handler", "Action": "Last_Action",
    })

    counts = df.groupby("RFID_ID").size().rename("Total_Events")
    latest = latest.merge(counts, on="RFID_ID")
    return latest.reset_index(drop=True)


def custody_gaps(df: pd.DataFrame, max_gap_hours=48) -> pd.DataFrame:
    """Flags any box that hasn't had a scan logged in more than
    max_gap_hours - a real chain-of-custody red flag (evidence
    unaccounted for)."""
    df = df.copy()
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    latest = df.groupby("RFID_ID")["Timestamp"].max()
    now = df["Timestamp"].max()  # use dataset's own "now" for reproducibility
    gap_hours = (now - latest).dt.total_seconds() / 3600
    flagged = gap_hours[gap_hours > max_gap_hours]
    return flagged.reset_index().rename(columns={"Timestamp": "Hours_Since_Last_Scan"})


if __name__ == "__main__":
    df = pd.read_csv("evidence_movement_log.csv")
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    summary = box_status_summary(df)
    summary.to_csv("box_status_summary.csv", index=False)
    print("Current status of each evidence box:")
    print(summary.to_string(index=False))

    gaps = custody_gaps(df)
    print(f"\nBoxes with custody gaps > 48h: {len(gaps)}")
