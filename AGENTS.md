# MedLens Agent Guide

This repository contains MedLens, a Flask-based clinical information intelligence app for organizing medical report data, provenance, and review workflows. The app is not a diagnosis or treatment system.

## Core rules

- Do not add diagnostic or treatment recommendations.
- Keep all output neutral, factual, and evidence-based.
- Preserve provenance tracking and validation semantics.
- Never invent medical reference ranges; if missing, use UNKNOWN.
- Keep the project safety-first and clinically cautious.

## Project layout

- `app.py`: Flask application entry point and route registration.
- `services/`: AI extraction, validation, OCR, summary, and verification services.
- `utils/`: database helpers, PDF export, sample generation, and utility logic.
- `templates/`: HTML templates.
- `static/`: CSS and JS assets.
- `tests/test_medlens.py`: project regression and feature tests.

## Commands

- Run the full test suite: `python -m unittest tests/test_medlens.py`
- Start the app locally: `python app.py`
- Seed demo data: `python -m utils.generate_samples` and `python -c "from utils.database import init_db; init_db(seed_demo=True)"`

## Development expectations

- Prefer deterministic backend logic over speculative AI output.
- Preserve user-provided, extracted, AI-generated, and human-verified provenance labels.
- When editing validation logic, keep the reference-range rule consistent: LOW if value < ref_low, HIGH if value > ref_high, otherwise NORMAL, and UNKNOWN when the source range is absent.
- Update or add tests when modifying behavior that is covered by the test suite.
- Avoid broad rewrites; make minimal, targeted changes.

## Safety boundary

MedLens should only organize, explain, and summarize patient-entered data and uploaded document content. It must not diagnose conditions, prescribe medications, or present uncertain findings as medical fact.
