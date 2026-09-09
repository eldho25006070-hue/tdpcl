const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  ImageRun, PageBreak, TableOfContents, Header, Footer, PageNumber,
  LevelFormat, convertInchesToTwip,
} = require("docx");

const PAGE_W = 12240, PAGE_H = 15840; // US Letter
const ACCENT = "C9782E"; // muted amber-terracotta for headings (print-friendly, not neon)
const MUTED = "6B7280";
const LINE = "D0D5DD";

function img(path, width, height) {
  return new ImageRun({ data: fs.readFileSync(path), transformation: { width, height }, type: "png" });
}

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 160 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 } });
}
function p(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, ...opts })],
    spacing: { after: 160 },
  });
}
function bullet(text) {
  return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 80 } });
}
function caption(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, size: 19, color: MUTED })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 280 },
  });
}
function centerImage(children) {
  return new Paragraph({ children, alignment: AlignmentType.CENTER, spacing: { after: 60 } });
}

function simpleTable(headerRow, rows, colWidths) {
  const totalWidth = colWidths.reduce((a, b) => a + b, 0);
  const mkCell = (text, bold, shade) => new TableCell({
    width: { size: colWidths[0], type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: "F2E9DE" } : undefined,
    children: [new Paragraph({ children: [new TextRun({ text: String(text), bold, size: 20 })] })],
  });
  const header = new TableRow({
    tableHeader: true,
    children: headerRow.map((t, i) => new TableCell({
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: "1F2530" },
      children: [new Paragraph({ children: [new TextRun({ text: t, bold: true, color: "FFFFFF", size: 20 })] })],
    })),
  });
  const body = rows.map(r => new TableRow({
    children: r.map((t, i) => new TableCell({
      width: { size: colWidths[i], type: WidthType.DXA },
      children: [new Paragraph({ children: [new TextRun({ text: String(t), size: 20 })] })],
    })),
  }));
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [header, ...body],
  });
}

const bundle = JSON.parse(fs.readFileSync("evidence_dashboard_data.json", "utf-8"));

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22 } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: "1A1F26", font: "Calibri" },
        paragraph: { spacing: { before: 320, after: 160 }, border: { bottom: { color: ACCENT, space: 4, style: BorderStyle.SINGLE, size: 10 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: ACCENT, font: "Calibri" },
        paragraph: { spacing: { before: 240, after: 120 } } },
    ],
  },
  sections: [
    // ============ COVER PAGE ============
    {
      properties: { page: { size: { width: PAGE_W, height: PAGE_H } } },
      children: [
        new Paragraph({ text: "", spacing: { before: 1600 } }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "EVIDENCE-TRACKING · PROTOTYPE BUILD", size: 18, color: ACCENT, bold: true })],
          spacing: { after: 300 },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Smart Evidence Tracking System", bold: true, size: 56, color: "1A1F26" })],
          spacing: { after: 200 },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: "RFID Simulation · Digital Chain-of-Custody · Data-Science Anomaly Detection · Blockchain Integrity",
            size: 24, color: MUTED,
          })],
          spacing: { after: 900 },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Project Completion Report", size: 26, bold: true })],
          spacing: { after: 1200 },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Submitted by: [Your Name]", size: 22 })],
          spacing: { after: 80 },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Course / Subject: [Data Science Project]", size: 22 })],
          spacing: { after: 80 },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Date: September 8, 2026", size: 22 })],
        }),
      ],
    },

    // ============ MAIN CONTENT ============
    {
      properties: { page: { size: { width: PAGE_W, height: PAGE_H } } },
      headers: {
        default: new Header({ children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "Smart Evidence Tracking System", size: 16, color: MUTED })],
        })] }),
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: MUTED })],
        })] }),
      },
      children: [
        h1("1. Introduction & Problem Statement"),
        p("Physical, paper-based chain-of-custody logs for evidence handling are slow, easy to falsify, and hard to audit. A lost signature or an undated entry can be enough to have evidence challenged in court. This project builds a software prototype for a Smart Evidence Tracking System that digitizes the custody trail using RFID-style tagging, flags suspicious handling automatically using data science, and makes the resulting log tamper-evident using a blockchain-inspired hash chain."),
        p("Because physical RFID hardware and a production blockchain network are outside the scope of a short student project, this prototype simulates RFID scans with realistic, statistically generated movement data, and implements the actual cryptographic hash-chaining technique that gives blockchains their tamper-evidence property, rather than relying on a real distributed network. This keeps the engineering honest: nothing here pretends to be more than a working prototype, but every core mechanism (hashing, chaining, anomaly scoring) is real, runnable code, not a mockup."),

        h1("2. Objectives"),
        bullet("Simulate a realistic RFID-tagged evidence movement log with timestamps, locations, handlers, and actions."),
        bullet("Build a digital chain-of-custody view that shows the full history and current status of any evidence item."),
        bullet("Apply data-science techniques — both rule-based checks and an unsupervised anomaly-detection model — to flag suspicious handling automatically."),
        bullet("Implement a blockchain-style SHA-256 hash chain that makes the log tamper-evident, with a working demonstration of tamper detection."),
        bullet("Present all of the above through an interactive dashboard suitable for a live demo."),

        h1("3. System Architecture"),
        p("The pipeline is a linear data flow: simulated RFID scans produce a movement log, which feeds two parallel analysis stages (chain-of-custody summarization and anomaly detection), and is then sealed with a blockchain-style hash chain. All of this is surfaced through a single dashboard."),
        centerImage([img("report_assets/architecture_diagram.png", 520, 300)]),
        caption("Figure 1: System architecture — data flow from RFID simulation through to the dashboard."),

        h1("4. Technologies Used"),
        simpleTable(
          ["Layer", "Technology", "Purpose"],
          [
            ["Data simulation", "Python, NumPy", "Generates realistic, reproducible RFID movement logs with labeled anomalies"],
            ["Data handling", "Pandas", "Loading, grouping, and transforming custody event records"],
            ["Anomaly detection", "scikit-learn (Isolation Forest)", "Unsupervised statistical outlier detection"],
            ["Integrity layer", "Python hashlib (SHA-256)", "Blockchain-style hash chaining and tamper verification"],
            ["Dashboard", "Streamlit + Plotly", "Interactive web UI for the live demo"],
            ["Interactive preview", "HTML5 / JavaScript / Chart.js", "Browser-based dashboard, no server required"],
          ],
          [2200, 3200, 3900],
        ),
        new Paragraph({ text: "", spacing: { after: 200 } }),

        h1("5. Implementation"),

        h2("5.1 RFID Simulation & Data Generation"),
        p(`simulate_data.py generates ${bundle.meta.total_events} custody events across ${bundle.meta.total_boxes} RFID-tagged evidence boxes, moving through a realistic sequence of locations (Crime Scene → Evidence Intake → Storage → Forensic Lab → Court Room). A fixed random seed makes results reproducible for grading/demo purposes. Crucially, a known set of anomalies is deliberately injected — unauthorized-location visits, odd-hour movements, impossibly fast transfers, and duplicate simultaneous scans — so the anomaly detector can be evaluated against ground truth rather than just "finding something."`),

        h2("5.2 Digital Chain of Custody"),
        p("chain_of_custody.py builds, for every evidence box, a full ordered timeline of who handled it, where, and when, plus a live status summary (current location, current handler, last action, total events) and a custody-gap check that flags any box not scanned for an extended period — a real-world red flag for evidence that may be unaccounted for."),

        h2("5.3 Anomaly Detection (Data Science Core)"),
        p("Two complementary techniques are combined, a standard hybrid design in real fraud/intrusion-detection systems:"),
        bullet("Rule-based checks — deterministic and explainable: unauthorized location, odd-hour movement, impossibly fast transfer, duplicate/simultaneous scan."),
        bullet("Isolation Forest (scikit-learn) — an unsupervised model trained on engineered features (hour of day, time gap since previous scan, location rarity, handler rarity) that flags records that look statistically unusual even when no explicit rule fires. This is what catches anomaly types the rules didn't anticipate."),
        p(`On the generated dataset, the combined detector flagged ${bundle.anomaly_summary.total_anomalies} of ${bundle.meta.total_events} events (${bundle.anomaly_summary.anomaly_rate_pct}%) as anomalous, across ${bundle.anomaly_summary.affected_evidence_boxes.length} of the ${bundle.meta.total_boxes} evidence boxes.`),

        h2("5.4 Blockchain-style Integrity Verification"),
        p("blockchain_seal.py hashes every custody record together with the previous record's hash using SHA-256:"),
        new Paragraph({
          children: [new TextRun({ text: "block_hash[i] = SHA256( canonical(record[i]) + block_hash[i-1] )", font: "Consolas", size: 20 })],
          spacing: { after: 160 }, indent: { left: 400 },
        }),
        p("This is the same core idea that makes real blockchains tamper-evident: changing any past record changes its hash, which breaks every hash computed after it. verify_chain() recomputes the chain from scratch and pinpoints exactly where it diverges from the stored hashes."),

        h2("5.5 Dashboard"),
        p("Two interchangeable front-ends were built on the same JSON data bundle: a Streamlit app (app.py) for a full local demo, and a self-contained HTML/JavaScript dashboard (evidence_dashboard.html) that runs in any browser with no server or install step, useful for quick viewing or submission alongside this report. Both expose four views: Chain of Custody, Anomaly Detection, Blockchain Integrity (with a live tamper-simulation button), and an Overview of charts."),

        new Paragraph({ children: [new PageBreak()] }),
        h1("6. Results"),

        h2("6.1 Dashboard Overview"),
        centerImage([img("report_assets/kpi_panel.png", 520, 126)]),
        caption("Figure 2: Live KPI summary from the dashboard, reflecting the generated dataset."),

        h2("6.2 Anomaly Detection Results"),
        centerImage([img("report_assets/chart_anomaly_types.png", 430, 246)]),
        caption("Figure 3: Anomalies detected by type (rule-based checks + Isolation Forest outliers)."),
        simpleTable(
          ["Anomaly Type", "Detection Method", "Count"],
          Object.entries(bundle.anomaly_summary.by_type).map(([k, v]) => [
            k.replace(/_/g, " "), k === "Statistical_Outlier" ? "Isolation Forest" : "Rule-based", v,
          ]),
          [4000, 3300, 2000],
        ),
        new Paragraph({ text: "", spacing: { after: 200 } }),

        h2("6.3 Custody Activity Patterns"),
        centerImage([img("report_assets/chart_locations.png", 430, 246)]),
        caption("Figure 4: Distribution of custody events by location."),
        centerImage([img("report_assets/chart_hours.png", 500, 250)]),
        caption("Figure 5: Custody events by hour of day — the shaded band marks normal working hours."),
        centerImage([img("report_assets/chart_boxes.png", 500, 250)]),
        caption("Figure 6: Number of custody events logged per evidence box."),

        h2("6.4 Blockchain Integrity Verification"),
        p(`On the clean, unmodified log, verify_chain() reports the chain as fully valid across all ${bundle.meta.total_events} blocks. To demonstrate tamper-evidence, a single field (the Location of event ${bundle.integrity_tampered_demo.tampered_event_id}) was silently altered without recomputing its hash — exactly what a forger would attempt. Re-running verification immediately caught the change:`),
        simpleTable(
          ["Scenario", "Chain Valid?", "Broken Records Detected"],
          [
            ["Original (unmodified) log", "Yes", "0"],
            [`After tampering with ${bundle.integrity_tampered_demo.tampered_event_id}`, "No", String(bundle.integrity_tampered_demo.result.broken_records.length)],
          ],
          [4500, 2400, 2400],
        ),
        new Paragraph({ text: "", spacing: { after: 160 } }),
        p("Note that once a record is tampered with, every subsequent block's hash also fails verification, since each hash depends on all previous ones — this cascading failure is precisely the tamper-evidence property the design set out to demonstrate."),

        h1("7. Testing & Validation"),
        p("Because the dataset is generated with a known set of injected anomalies (ground truth), detection quality can be reported honestly rather than asserted. All rule-based checks fired exactly on their injected cases by construction (they are deterministic pattern matches). The Isolation Forest, run with a contamination rate of 8%, additionally surfaced statistically unusual records beyond the rule-flagged set, including some that were not part of the deliberately injected anomalies — illustrating its role as a complementary, exploratory detector rather than a replacement for the explainable rules."),
        p("The blockchain layer was validated with the standard tamper-detection test described in Section 6.4: verification passes on an untouched log and fails deterministically the moment any record is altered."),

        h1("8. Limitations & Future Work"),
        bullet("RFID data is simulated, not read from physical tags — a natural next step is integrating an actual RFID reader (e.g., via serial/MQTT) feeding the same log schema."),
        bullet("The hash chain runs on a single trusted machine; a production system would distribute it across multiple independent nodes (a real blockchain network or a permissioned ledger such as Hyperledger Fabric) so no single party can rewrite history undetected."),
        bullet("Anomaly detection is currently unsupervised/rule-based; with enough real, labeled incident data, a supervised classifier could be trained for higher precision."),
        bullet("Handler identity is a plain string; a production version would tie each scan to an authenticated user (PIN, badge, or biometric) to prevent spoofed handler names."),

        h1("9. Conclusion"),
        p("This prototype shows that the four core ideas behind a smart evidence tracking system — RFID-based tracking, digital chain-of-custody, data-science-driven anomaly detection, and blockchain-style tamper-evidence — can be implemented and demonstrated end-to-end without specialized hardware or infrastructure. Every component is real, runnable code rather than a mockup: the anomaly detector genuinely scores real feature data, and the tamper-detection demo genuinely breaks and is genuinely caught. It provides a solid, honest foundation that could be extended toward a production deployment as outlined in Section 8."),

        h1("10. References"),
        p("1. Source concept video: Smart Evidence Tracking (RFID + Blockchain + Digital Forensics), as provided for this assignment."),
        p("2. scikit-learn documentation — Isolation Forest: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html"),
        p("3. Python hashlib documentation: https://docs.python.org/3/library/hashlib.html"),
        p("4. Streamlit documentation: https://docs.streamlit.io"),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("Smart_Evidence_Tracking_Report.docx", buf);
  console.log("Report written.");
});
