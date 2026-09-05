# Copilot instructions for MedLens

## Mission

MedLens is a Flask app that turns uploaded reports and patient details into structured, reference-aware clinical records while preserving provenance and safety boundaries.

## Non-negotiable behavior

- Never provide diagnoses, treatment plans, medication dosing, or patient-specific medical advice.
- Never fabricate reference ranges or test values when the source document does not provide them.
- Keep descriptions neutral and evidence-based.
- Preserve human verification and audit-trace metadata.

## Key implementation notes

- Validation should follow deterministic comparison rules against document-stated reference ranges.
- Conflict detection should remain factual and non-alarmist, describing possible inconsistencies without making clinical judgments.
- PDF export, DB interactions, and API behavior should remain stable for the existing test suite.

## Validation

Before considering work complete, run:

```bash
python -m unittest tests/test_medlens.py
```

## Repository focus

- Backend logic lives in `services/` and `utils/`.
- UI markup lives in `templates/` and front-end logic in `static/js/`.
- Integration and regression coverage lives in `tests/test_medlens.py`.

Keep changes surgical and consistent with the project’s clinical safety and reproducibility goals.
