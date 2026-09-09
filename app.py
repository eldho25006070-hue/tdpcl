"""
app.py
------
Streamlit dashboard for the Smart Evidence Tracking System.

Run with:
    streamlit run app.py

If evidence_dashboard_data.json doesn't exist yet, run the pipeline first:
    python run_pipeline.py
"""

import json
import copy
import pandas as pd
import streamlit as st
import plotly.express as px

from blockchain_seal import verify_chain, canonical_record
import hashlib

st.set_page_config(page_title="Smart Evidence Tracking System", layout="wide", page_icon="🔒")


@st.cache_data
def load_bundle():
    with open("evidence_dashboard_data.json") as f:
        return json.load(f)


bundle = load_bundle()
events_df = pd.DataFrame(bundle["events"])
events_df["Timestamp"] = pd.to_datetime(events_df["Timestamp"])
status_df = pd.DataFrame(bundle["box_status"])

st.title("🔒 Smart Evidence Tracking System")
st.caption("RFID Simulation • Digital Chain-of-Custody • Anomaly Detection • Blockchain Integrity")

# ---------------------------------------------------------------------
# Top-level KPIs
# ---------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Evidence Boxes Tracked", bundle["meta"]["total_boxes"])
c2.metric("Total Custody Events", bundle["meta"]["total_events"])
c3.metric("Anomalies Detected", bundle["anomaly_summary"]["total_anomalies"],
          f"{bundle['anomaly_summary']['anomaly_rate_pct']}% of events")
c4.metric("Chain Integrity", "VALID ✅" if bundle["integrity_clean"]["is_valid"] else "BROKEN ❌")

tab1, tab2, tab3, tab4 = st.tabs([
    "📦 Chain of Custody", "🚨 Anomaly Detection", "⛓️ Blockchain Integrity", "📊 Overview"
])

# ---------------------------------------------------------------------
# TAB 1: Chain of custody timeline
# ---------------------------------------------------------------------
with tab1:
    st.subheader("Evidence Box Status")
    st.dataframe(status_df, use_container_width=True)

    st.subheader("Custody Timeline")
    selected_box = st.selectbox("Select Evidence Box", sorted(events_df["RFID_ID"].unique()))
    box_events = events_df[events_df["RFID_ID"] == selected_box].sort_values("Timestamp")

    for _, ev in box_events.iterrows():
        icon = "🚨" if ev.get("Is_Anomaly") else "✅"
        st.markdown(
            f"{icon} **{ev['Timestamp']}** — *{ev['Action']}* at **{ev['Location']}** "
            f"(Handler: {ev['Handler']}) — `{ev['Event_ID']}`"
        )
        if ev.get("Is_Anomaly") and ev.get("Anomaly_Reasons"):
            st.caption(f"⚠️ Flagged: {ev['Anomaly_Reasons']}")

# ---------------------------------------------------------------------
# TAB 2: Anomaly detection
# ---------------------------------------------------------------------
with tab2:
    st.subheader("Anomaly Summary")
    summary = bundle["anomaly_summary"]
    st.json(summary["by_type"])

    fig = px.bar(
        x=list(summary["by_type"].keys()), y=list(summary["by_type"].values()),
        labels={"x": "Anomaly Type", "y": "Count"}, title="Anomalies by Type",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Flagged Records")
    anomalies = events_df[events_df["Is_Anomaly"] == True]  # noqa: E712
    st.dataframe(
        anomalies[["Event_ID", "RFID_ID", "Timestamp", "Location", "Handler", "Anomaly_Reasons"]],
        use_container_width=True,
    )

# ---------------------------------------------------------------------
# TAB 3: Blockchain integrity verification
# ---------------------------------------------------------------------
with tab3:
    st.subheader("Verify Chain Integrity")
    st.write(
        "Every custody event is hashed together with the previous event's hash "
        "(`SHA-256`), forming a chain. Altering any past record breaks every "
        "hash after it — this is what makes the log tamper-evident."
    )

    if st.button("🔍 Verify Integrity (current log)"):
        result = verify_chain(events_df)
        if result["is_valid"]:
            st.success(f"✅ Chain is VALID — all {result['total_records']} blocks verified.")
        else:
            st.error(f"❌ Chain BROKEN at {len(result['broken_records'])} record(s)!")
            st.json(result["broken_records"])

    st.divider()
    st.subheader("Live Tamper Simulation")
    st.write("Pick a record and edit it — then re-verify to see the chain break in real time.")

    tamper_event = st.selectbox("Select an event to tamper with", events_df["Event_ID"].tolist())
    new_location = st.text_input("New (forged) Location value", "Cafeteria")

    if st.button("✏️ Apply Tamper & Re-verify"):
        tampered = events_df.copy()
        idx = tampered[tampered["Event_ID"] == tamper_event].index[0]
        tampered.loc[idx, "Location"] = new_location
        result = verify_chain(tampered)
        st.error(f"❌ Tampering detected! Chain broken starting at `{tamper_event}`.")
        st.json(result["broken_records"][:3])

# ---------------------------------------------------------------------
# TAB 4: Overview charts
# ---------------------------------------------------------------------
with tab4:
    col1, col2 = st.columns(2)
    with col1:
        loc_counts = events_df["Location"].value_counts().reset_index()
        loc_counts.columns = ["Location", "Count"]
        fig = px.pie(loc_counts, names="Location", values="Count", title="Events by Location")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        events_df["Hour"] = events_df["Timestamp"].dt.hour
        fig2 = px.histogram(events_df, x="Hour", nbins=24, title="Events by Hour of Day")
        st.plotly_chart(fig2, use_container_width=True)

    events_by_box = events_df.groupby("RFID_ID").size().reset_index(name="Events")
    fig3 = px.bar(events_by_box, x="RFID_ID", y="Events", title="Custody Events per Evidence Box")
    st.plotly_chart(fig3, use_container_width=True)
