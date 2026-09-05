from .ocr_service import OCRService
from .ai_service import AIService
from .validation_service import ValidationService

class ExtractionService:
    def __init__(self):
        self.ocr_service = OCRService()
        self.ai_service = AIService()
        self.validation_service = ValidationService()

    def process_document(self, file_path, original_filename, patient_profile):
        """
        Executes the end-to-end extraction pipeline:
        1. Document Upload & File Parse
        2. OCR / Text Extraction
        3. Modular AI Extraction (or Demo Mode)
        4. Backend Deterministic Reference Range Evaluation
        5. Clinical Inconsistency / Conflict Detection
        """
        # Step 1: Text extraction
        ocr_result = self.ocr_service.extract_text(file_path)
        if not ocr_result["success"]:
            return {
                "success": False,
                "error": ocr_result["error"],
                "stages_completed": ["Document uploaded", "Text extraction failed"]
            }

        full_text = ocr_result["full_text"]
        pages = ocr_result["pages"]
        page_count = ocr_result["page_count"]

        # Step 2: AI extraction / Demo Mode
        ai_result = self.ai_service.extract_clinical_data(full_text, original_filename, pages)
        extracted_data = ai_result["data"]
        raw_tests = extracted_data.get("tests", [])

        # Step 3: Deterministic reference range calculation
        validated_tests = []
        for test in raw_tests:
            val = test.get("value")
            ref_low = test.get("reference_low")
            ref_high = test.get("reference_high")
            ref_range = test.get("reference_range")

            # Calculate deterministic status
            status = self.validation_service.calculate_reference_status(val, ref_low, ref_high)

            # Display range string or "Not provided"
            disp_range = ref_range if ref_range else "Not provided"

            validated_tests.append({
                "test_name": test.get("test_name", "Unknown Test"),
                "value": val,
                "value_text": str(val) if val is not None else "",
                "unit": test.get("unit", ""),
                "reference_range": disp_range,
                "reference_low": ref_low,
                "reference_high": ref_high,
                "status": status,
                "confidence": test.get("confidence", 0.95),
                "source_page": test.get("source_page", 1),
                "source_text": test.get("source_text", f"{test.get('test_name')}: {val} {test.get('unit', '')}")
            })

        # Step 4: Detect profile conflicts
        conflicts = self.validation_service.detect_conflicts(patient_profile, full_text, validated_tests)

        return {
            "success": True,
            "report_type": extracted_data.get("report_type", "Laboratory Report"),
            "report_date": extracted_data.get("report_date", "2026-09-03"),
            "page_count": page_count,
            "extraction_mode": ai_result["mode"],
            "tests": validated_tests,
            "conflicts": conflicts,
            "pipeline_stages": [
                "Document uploaded",
                "Text extracted",
                "Medical information identified",
                "Test values extracted",
                "Reference ranges detected",
                "Source linked",
                "Structured record created"
            ]
        }
