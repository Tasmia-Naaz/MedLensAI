# MedLens

AI-assisted clinical information organization with document provenance, deterministic reference-range validation, human verification, and audit-ready records.

> MedLens is an information organization and review tool. It is not a diagnostic, treatment, or medical advice system.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-not%20specified-lightgrey)](#license)

## Overview

MedLens turns uploaded laboratory reports and patient-provided details into a structured, traceable patient record. It supports offline demo extraction by default and can optionally use Google Gemini for document parsing. Clinical status labels are always calculated deterministically from ranges stated in the source document.

## Features

- Upload PDF and image-based medical reports.
- Extract tests, values, units, source text, page references, and confidence metadata.
- Calculate `LOW`, `NORMAL`, `HIGH`, or `UNKNOWN` without inventing reference ranges.
- Preserve provenance for user-provided, extracted, AI-generated, and human-verified data.
- Review factual profile/report inconsistencies without making clinical judgments.
- Compare report history and export a patient record PDF.
- Run in offline Demo Mode without an API key.

MedLens is a full-stack, hackathon-ready clinical intelligence web application built with **Python, Flask, SQLite, and Bootstrap 5**. It organizes and explains unstructured medical reports and patient-provided health details into a structured, reference-range-aware, and traceable patient dossier without diagnosing diseases or prescribing treatments.

---

## ⚖️ Safety & Regulatory Boundary

> [!IMPORTANT]
> **MedLens is NOT a medical diagnosis or treatment system.**
> It must NOT:
> - Diagnose diseases
> - Prescribe medicines
> - Recommend dosage changes
> - Recommend treatment
> - Present uncertain information as medical fact
>
> It only organizes and neutrally explains information found in patient-provided information and uploaded clinical reports.

---

## 🚀 Key Features & Architectural Workflow

```
Uploaded Medical Report (PDF / Image) OR Instant Demo Sample
                     │
                     ▼
           Text Extraction / OCR (pypdf)
                     │
                     ▼
       Modular AI Extraction Service
  (Gemini API / LLM or Offline Demo Engine)
                     │
                     ▼
       Structured JSON Extraction Format
                     │
                     ▼
   Backend Deterministic Range Validation
 (LOW if val < ref_low, HIGH if val > ref_high, else NORMAL, UNKNOWN if missing)
                     │
                     ▼
  Safety Conflict Detection Engine (Allergy vs Medication)
                     │
                     ▼
              SQLite Database
                     │
    ┌────────────────┼────────────────┐
    ▼                ▼                ▼
Structured Record  Human Review    AI Summary
 (Provenance)     & Verification  (Key Observations)
```

1. **Strict Reference Range Rule**:
   Clinical status (`LOW`, `NORMAL`, `HIGH`, `UNKNOWN`) is computed mathematically on the backend against document-stated ranges:
   ```python
   if value < reference_low:
       status = "LOW"
   elif value > reference_high:
       status = "HIGH"
   else:
       status = "NORMAL"
   # If reference range is missing from source report:
   # status = "UNKNOWN" (Reference Range: "Not provided")
   ```
   MedLens **never invents or guesses** medical reference ranges.

2. **Core Provenance & Audit Badges**:
   - 🟦 `USER PROVIDED`: Manually entered patient information.
   - 🟩 `EXTRACTED FROM REPORT`: Parsed from documents with page number and confidence score.
   - 🟪 `AI GENERATED`: Patient-friendly summaries and neutral clinical observations.
   - 🟨 `HUMAN VERIFIED`: Manually reviewed and approved by a clinical reviewer.

3. **Side-by-Side Traceability Audit Modal**:
   Clicking **[View Source]** on any extracted parameter opens a dual-pane modal:
   - **Left**: Original report excerpt with highlighted text bounding.
   - **Right**: Extracted structured record (Test, Value, Unit, Reference Range, Status, Confidence).

4. **Clinical Consistency & Conflict Detection**:
   Automatically cross-references patient profile allergies and conditions against medications or findings in uploaded documents (e.g. Allergy: Penicillin vs Recommended Medication: Amoxicillin). Displays neutral, factual alerts with **[Review]**, **[Resolve]**, and **[Ignore]** actions.

5. **Report Comparison & Trends**:
   Compare any two chronological accessions with delta computation and visual bar charts powered by **Chart.js**.

6. **Full Patient Record PDF Export**:
   One-click generation of high-quality clinical record PDF via **ReportLab** with headers, patient profile, lab tables, AI summaries, and safety disclaimers.

7. **Zero-Config Offline Demo Mode**:
   Works out of the box with zero external setup, even without an internet connection or AI API key!

---

## 💻 Tech Stack

- **Backend**: Python 3.10+, Flask 3.x, Werkzeug
- **Database**: SQLite 3 (`database.db`)
- **Frontend**: HTML5, CSS3 (Custom Healthcare Design System), JavaScript (Vanilla ES6), Bootstrap 5.3, Bootstrap Icons, Chart.js
- **Document Processing**: `pypdf`, `Pillow`
- **PDF Generation**: `reportlab`
- **AI Integration**: Modular `AIService` supporting Google Gemini API via `AI_API_KEY` with deterministic clinical fallback.

---

## 📁 4 Main Pages Structure

| Page | Route | Description |
|---|---|---|
| **Page 1** | `/login` | Clean login with hackathon quick-fill demo button, JavaScript validation, and Bootstrap registration modal. |
| **Page 2** | `/dashboard` | Welcome banner, Patient Information Card (🟦 User Provided), [Edit Patient] modal, 4 summary metric cards, Recent Reports table, and Clinical Audit Trail. |
| **Page 3** | `/record` | The central 5-tab clinical workspace: Upload Report, Extracted Data, Medical Record, Verification & Conflicts, AI Summary, plus Side-by-Side Traceability Modal. |
| **Page 4** | `/history` | Report History Archive with live search/filters, Report Comparison with Chart.js, and chronological Patient Timeline. |

---

## 🔑 Demo Credentials

| Field | Value |
|---|---|
| **Email** | `demo@medlens.com` |
| **Password** | `demo123` |

*Note: On the login page, you can simply click the **"Demo Login (demo@medlens.com)"** button to autofill and log in instantly.*

---

## 🛠️ Installation & Local Setup

### 1. Clone or Open the Repository
```bash
cd f:\MedLens
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional: Add `AI_API_KEY=your_gemini_key_here` if you wish to use live Google Gemini LLM extraction. If left blank, the built-in deterministic demo extraction engine operates seamlessly offline!)*

### 4. Initialize Database & Seed Demo Data
```bash
python -m utils.generate_samples
python -c "from utils.database import init_db; init_db(seed_demo=True)"
```

### 5. Run the Application
```bash
python app.py
```
Open your browser at: **`http://localhost:5000`**

---

## 🧪 Running Automated Tests

MedLens comes with a comprehensive unit and integration test suite:
```bash
python -m unittest tests/test_medlens.py
```

---

## ⏱️ 2-3 Minute Hackathon Demo Script

1. **Login**: Navigate to `http://localhost:5000/login`, click **"Demo Login"**.
2. **Dashboard**: View Patient Information Card with `🟦 User Provided` badges. Note the 4 summary metric cards and audit trail.
3. **Upload / Select Report**: Click **"+ Upload Medical Report"**. In Tab 1, click **"Blood_Report.pdf (Current)"**.
4. **Extraction Pipeline**: Watch the 7-stage pipeline checklist complete, switching to Tab 2 **Extracted Data**.
5. **Reference Ranges**: Observe how Hemoglobin (10.2) is marked `LOW`, Glucose (145) is marked `HIGH`, and TSH (3.2) is marked `NORMAL` purely based on source document bounds.
6. **Side-by-Side Traceability**: Click **[View Source]** to open the dual-pane modal showing the exact highlight in the document excerpt on the left alongside structured data on the right.
7. **Structured Record**: Switch to Tab 3 to view the consolidated patient record combining profile data and laboratory panels.
8. **Inconsistency & Human Verification**: Switch to Tab 4. Review the neutral conflict alert (Penicillin allergy vs Amoxicillin). In the verification cards, edit a value or click **[Verify]** to turn it into `🟨 Human Verified`.
9. **AI Summary**: Switch to Tab 5 to view the patient-friendly breakdown, source-cited key observations, safety notice, and click **[Download Patient Record PDF]**.
10. **History & Comparison**: Click **History & Trends** in the sidebar. Select Previous (June 2026) and Current (September 2026), view the delta changes, Chart.js comparison chart, and vertical patient timeline.

---

## 🚢 Deployment Guidelines

### Option A: Render / Railway / Heroku
MedLens is ready for deployment.
1. Set `PORT=5000` or use the platform-assigned `$PORT`.
2. Set `Procfile`:
   ```
   web: gunicorn app:app
   ```
3. Set optional environment variable: `AI_API_KEY`.

### Option B: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -m utils.generate_samples && python -c "from utils.database import init_db; init_db(seed_demo=True)"
EXPOSE 5000
CMD ["python", "app.py"]
```
