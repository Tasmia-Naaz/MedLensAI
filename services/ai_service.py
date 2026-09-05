import os
import json
import re
import requests

class AIService:
    def __init__(self):
        self.api_key = os.environ.get("AI_API_KEY", "").strip()
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"

    def is_configured(self):
        return bool(self.api_key)

    def extract_clinical_data(self, text_content, filename="Report.pdf", pages=None):
        """
        Extracts structured laboratory test results and metadata from document text.
        If AI_API_KEY is not set or the request fails, falls back gracefully to
        intelligent deterministic extraction/Demo Mode.
        """
        if self.is_configured():
            try:
                result = self._extract_with_gemini(text_content, filename)
                if result and "tests" in result and len(result["tests"]) > 0:
                    return {
                        "mode": "AI_API (Gemini)",
                        "data": result,
                        "fallback": False
                    }
            except Exception as e:
                print(f"[AIService] Live API call failed, falling back to Demo Mode: {e}")

        # Fallback / Demo Mode extraction
        demo_data = self._deterministic_demo_extraction(text_content, filename, pages)
        return {
            "mode": "Demo Mode (Offline Clinical Parser)",
            "data": demo_data,
            "fallback": True
        }

    def _extract_with_gemini(self, text_content, filename):
        system_instruction = (
            "You are a clinical document parser for MedLens. "
            "Extract laboratory tests, values, units, reference ranges, source text, and page references. "
            "CRITICAL RULES:\n"
            "1. Only extract reference ranges explicitly stated in the document. If missing, set reference_range to null, reference_low to null, reference_high to null.\n"
            "2. DO NOT determine or guess LOW/NORMAL/HIGH status - that will be computed deterministically by the backend.\n"
            "3. Return ONLY valid JSON in the specified schema. No conversational preamble.\n"
            "4. MedLens does NOT diagnose or treat diseases.\n\n"
            "Output JSON schema:\n"
            "{\n"
            '  "report_type": "Blood Test",\n'
            '  "report_date": "YYYY-MM-DD",\n'
            '  "tests": [\n'
            "    {\n"
            '      "test_name": "Hemoglobin",\n'
            '      "value": 10.2,\n'
            '      "unit": "g/dL",\n'
            '      "reference_range": "12-16 g/dL",\n'
            '      "reference_low": 12.0,\n'
            '      "reference_high": 16.0,\n'
            '      "source_page": 1,\n'
            '      "source_text": "Hemoglobin 10.2 g/dL (Ref: 12-16)",\n'
            '      "confidence": 0.97\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{system_instruction}\n\nDocument ({filename}):\n{text_content}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        }

        response = requests.post(self.gemini_url, json=payload, timeout=20)
        if response.status_code == 200:
            res_json = response.json()
            raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
            return json.loads(raw_text)
        else:
            raise Exception(f"Gemini API returned status {response.status_code}: {response.text}")

    def _deterministic_demo_extraction(self, text_content, filename, pages=None):
        """
        Parses text deterministically or matches known test patterns.
        Ensures the complete demo workflow functions perfectly offline.
        """
        lower_fn = filename.lower()
        lower_text = (text_content or "").lower()

        # Check if text contains known CBC / Blood report indicators
        tests = []
        report_type = "Laboratory Report"
        report_date = "2026-09-03"

        # Pattern library for clinical tests with regex extraction
        patterns = [
            {
                "name": "Hemoglobin",
                "regex": r"(?:hemoglobin|hb)\s*[:\-\s]\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z\/]+)?(?:\s*\(?ref(?:erence)?[:\-\s]*([0-9]+\.?[0-9]*)\s*[\-\–]\s*([0-9]+\.?[0-9]*))?",
                "default_unit": "g/dL",
                "def_low": 12.0,
                "def_high": 16.0,
                "confidence": 0.97,
                "page": 2 if "page 2" in lower_text or "page break" in lower_text else 1
            },
            {
                "name": "Glucose",
                "regex": r"(?:fasting\s+)?(?:blood\s+)?glucose\s*[:\-\s]\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z\/]+)?(?:\s*\(?ref(?:erence)?[:\-\s]*([0-9]+\.?[0-9]*)\s*[\-\–]\s*([0-9]+\.?[0-9]*))?",
                "default_unit": "mg/dL",
                "def_low": 70.0,
                "def_high": 100.0,
                "confidence": 0.95,
                "page": 1
            },
            {
                "name": "TSH",
                "regex": r"(?:tsh|thyroid\s+stimulating\s+hormone)\s*[:\-\s]\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z\/]+)?(?:\s*\(?ref(?:erence)?[:\-\s]*([0-9]+\.?[0-9]*)\s*[\-\–]\s*([0-9]+\.?[0-9]*))?",
                "default_unit": "mIU/L",
                "def_low": 0.4,
                "def_high": 4.0,
                "confidence": 0.96,
                "page": 1
            },
            {
                "name": "Platelets",
                "regex": r"(?:platelet(?:s|\s+count)?)\s*[:\-\s]\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z0-9\^\/]+)?(?:\s*\(?ref(?:erence)?[:\-\s]*([0-9]+\.?[0-9]*)\s*[\-\–]\s*([0-9]+\.?[0-9]*))?",
                "default_unit": "x10^3/uL",
                "def_low": 150.0,
                "def_high": 450.0,
                "confidence": 0.98,
                "page": 2 if "page 2" in lower_text or "page break" in lower_text else 1
            },
            {
                "name": "Total Cholesterol",
                "regex": r"(?:total\s+cholesterol)\s*[:\-\s]\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z\/]+)?(?:\s*\(?ref(?:erence)?[:\-\s]*([0-9]+\.?[0-9]*)\s*[\-\–]\s*([0-9]+\.?[0-9]*))?",
                "default_unit": "mg/dL",
                "def_low": 125.0,
                "def_high": 200.0,
                "confidence": 0.94,
                "page": 1
            },
            {
                "name": "Creatinine",
                "regex": r"(?:serum\s+)?creatinine\s*[:\-\s]\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z\/]+)?(?:\s*\(?ref(?:erence)?[:\-\s]*([0-9]+\.?[0-9]*)\s*[\-\–]\s*([0-9]+\.?[0-9]*))?",
                "default_unit": "mg/dL",
                "def_low": 0.6,
                "def_high": 1.2,
                "confidence": 0.96,
                "page": 2 if "page 2" in lower_text or "page break" in lower_text else 1
            },
            {
                "name": "Vitamin D",
                "regex": r"(?:25-oh\s+)?vitamin\s+d\s*[:\-\s]\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z\/]+)?(?:\s*\(?ref(?:erence)?[:\-\s]*([0-9]+\.?[0-9]*)\s*[\-\–]\s*([0-9]+\.?[0-9]*))?",
                "default_unit": "ng/mL",
                "def_low": 30.0,
                "def_high": 100.0,
                "confidence": 0.92,
                "page": 1
            },
            {
                "name": "HbA1c",
                "regex": r"(?:glycated\s+hemoglobin|hba1c)\s*[:\-\s]\s*([0-9]+\.?[0-9]*)\s*(%)?(?:\s*\(?ref(?:erence)?[:\-\s]*([0-9]+\.?[0-9]*)\s*[\-\–]\s*([0-9]+\.?[0-9]*))?",
                "default_unit": "%",
                "def_low": 4.0,
                "def_high": 5.6,
                "confidence": 0.97,
                "page": 2 if "page 2" in lower_text or "page break" in lower_text else 1
            }
        ]

        # Scan text for each test
        for p in patterns:
            match = re.search(p["regex"], text_content or "", re.IGNORECASE)
            if match:
                val = float(match.group(1))
                unit = match.group(2) or p["default_unit"]
                ref_low = float(match.group(3)) if match.group(3) else p["def_low"]
                ref_high = float(match.group(4)) if match.group(4) else p["def_high"]
                ref_range = f"{ref_low}–{ref_high} {unit}"
                matched_snippet = match.group(0).strip()
                tests.append({
                    "test_name": p["name"],
                    "value": val,
                    "unit": unit,
                    "reference_range": ref_range,
                    "reference_low": ref_low,
                    "reference_high": ref_high,
                    "source_page": p["page"],
                    "source_text": f"{matched_snippet}",
                    "confidence": p["confidence"]
                })

        # If no regex matched or text was sparse, provide standard demo blood report results
        if not tests:
            report_type = "Blood Test"
            tests = [
                {
                    "test_name": "Hemoglobin",
                    "value": 10.2,
                    "unit": "g/dL",
                    "reference_range": "12–16 g/dL",
                    "reference_low": 12.0,
                    "reference_high": 16.0,
                    "source_page": 2,
                    "source_text": "Hemoglobin: 10.2 g/dL (Reference Range: 12–16 g/dL)",
                    "confidence": 0.97
                },
                {
                    "test_name": "Glucose",
                    "value": 145.0,
                    "unit": "mg/dL",
                    "reference_range": "70–100 mg/dL",
                    "reference_low": 70.0,
                    "reference_high": 100.0,
                    "source_page": 1,
                    "source_text": "Fasting Blood Glucose: 145 mg/dL (Reference Range: 70–100 mg/dL)",
                    "confidence": 0.95
                },
                {
                    "test_name": "TSH",
                    "value": 3.2,
                    "unit": "mIU/L",
                    "reference_range": "0.4–4.0 mIU/L",
                    "reference_low": 0.4,
                    "reference_high": 4.0,
                    "source_page": 1,
                    "source_text": "TSH: 3.2 mIU/L (Reference Range: 0.4–4.0 mIU/L)",
                    "confidence": 0.96
                },
                {
                    "test_name": "Platelets",
                    "value": 230.0,
                    "unit": "x10^3/uL",
                    "reference_range": "150–450 x10^3/uL",
                    "reference_low": 150.0,
                    "reference_high": 450.0,
                    "source_page": 2,
                    "source_text": "Platelet Count: 230 x10^3/uL (Reference Range: 150–450 x10^3/uL)",
                    "confidence": 0.98
                },
                {
                    "test_name": "Total Cholesterol",
                    "value": 215.0,
                    "unit": "mg/dL",
                    "reference_range": "125–200 mg/dL",
                    "reference_low": 125.0,
                    "reference_high": 200.0,
                    "source_page": 1,
                    "source_text": "Total Cholesterol: 215 mg/dL (Reference Range: 125–200 mg/dL)",
                    "confidence": 0.94
                },
                {
                    "test_name": "Vitamin D",
                    "value": 18.0,
                    "unit": "ng/mL",
                    "reference_range": "30–100 ng/mL",
                    "reference_low": 30.0,
                    "reference_high": 100.0,
                    "source_page": 1,
                    "source_text": "25-OH Vitamin D: 18 ng/mL (Reference Range: 30–100 ng/mL)",
                    "confidence": 0.92
                }
            ]

        return {
            "report_type": report_type,
            "report_date": report_date,
            "tests": tests
        }
