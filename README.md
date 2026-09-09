# Smart Evidence Tracking System

A software prototype covering four pillars from the source concept:
RFID-tag simulation, digital chain-of-custody, data-science anomaly
detection, and blockchain-style tamper-evident integrity.

## Project structure

```
simulate_data.py       # Generates realistic RFID movement log with labeled ground-truth anomalies
chain_of_custody.py    # Builds per-box timelines, current status, custody-gap checks
anomaly_detection.py   # Rule-based checks + Isolation Forest (scikit-learn)
blockchain_seal.py     # SHA-256 hash-chaining + tamper verification
run_pipeline.py        # Orchestrates all of the above -> evidence_dashboard_data.json
app.py                 # Streamlit dashboard (the live demo UI)
requirements.txt
```

## How to run

```bash
pip install -r requirements.txt
python run_pipeline.py      # generates the dataset + all derived artifacts
streamlit run app.py        # opens the interactive dashboard in your browser
```

## What each pillar demonstrates

| Concept from the brief   | Implementation                                                             |
|---------------------------|-----------------------------------------------------------------------------|
| RFID tracking              | Simulated tag scans (`RFID_ID`) with timestamp, location, handler          |
| Chain of custody           | `chain_of_custody.py` — ordered timeline + current-status view per box     |
| Data science / anomaly detection | `anomaly_detection.py` — 4 rule-based checks + an Isolation Forest model over engineered features (hour, inter-scan gap, location/handler rarity) |
| Blockchain integrity       | `blockchain_seal.py` — SHA-256 hash chaining (`hash_i = SHA256(record_i + hash_{i-1})`), with a live tamper-detection demo |

## Files produced by run_pipeline.py

- `evidence_movement_log.csv` — raw simulated log
- `evidence_log_with_anomalies.csv` — log + anomaly flags
- `evidence_log_final_sealed.csv` — log + anomaly flags + blockchain hashes
- `evidence_dashboard_data.json` — everything bundled for the dashboard
- `anomaly_summary.json`, `box_status_summary.csv`, `blockchain_verification_demo.json`

## Notes for the report / viva

- Anomalies are injected with a **known ground truth** (unauthorized
  locations, odd-hour movement, impossibly fast transfers, duplicate
  scans) so detection can be reported honestly rather than just "it
  found some stuff."
- The Isolation Forest is there specifically to catch anomaly types the
  rules *didn't* anticipate — this is the actual data-science
  contribution, and is worth emphasizing over the rule checks in a viva.
- The blockchain layer is a genuine hash-chaining implementation (the
  real cryptographic idea behind blockchain tamper-evidence), not a
  simulated placeholder — running `blockchain_seal.py` directly shows a
  live before/after tamper detection in the terminal.
