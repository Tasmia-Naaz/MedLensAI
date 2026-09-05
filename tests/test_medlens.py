import os
import io
import tempfile
import unittest
import json
from app import app
import utils.database as database_module
from utils.database import init_db, get_db
from services.validation_service import ValidationService
from services.summary_service import SummaryService
from services.extraction_service import ExtractionService
from utils.pdf_export import generate_patient_record_pdf

class MedLensComprehensiveTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db(seed_demo=True)
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_00_default_init_db_does_not_seed_demo_reports(self):
        """Ensure default app startup doesn't create demo reports automatically."""
        original_db_path = database_module.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            database_module.DB_PATH = os.path.join(tmpdir, 'medlens_no_seed.db')
            try:
                database_module.init_db()
                conn = database_module.get_db()
                cur = conn.cursor()
                cur.execute('SELECT COUNT(*) FROM reports')
                report_count = cur.fetchone()[0]
                conn.close()
                self.assertEqual(report_count, 0)
            finally:
                database_module.DB_PATH = original_db_path

    def test_01_deterministic_reference_range_logic(self):
        """Verify strict non-AI numerical reference range calculation rules"""
        # Case 1: Hemoglobin 10.2 g/dL (Range: 12-16) -> LOW
        status_low = ValidationService.calculate_reference_status(10.2, 12.0, 16.0)
        self.assertEqual(status_low, "LOW")

        # Case 2: Glucose 145 mg/dL (Range: 70-100) -> HIGH
        status_high = ValidationService.calculate_reference_status(145.0, 70.0, 100.0)
        self.assertEqual(status_high, "HIGH")

        # Case 3: TSH 3.2 mIU/L (Range: 0.4-4.0) -> NORMAL
        status_normal = ValidationService.calculate_reference_status(3.2, 0.4, 4.0)
        self.assertEqual(status_normal, "NORMAL")

        # Case 4: Missing reference range -> strictly UNKNOWN, NEVER guess!
        status_unknown = ValidationService.calculate_reference_status(50.0, None, None)
        self.assertEqual(status_unknown, "UNKNOWN")

    def test_02_conflict_detection_logic(self):
        """Verify neutral conflict detection between patient profile and document notes"""
        patient_profile = {
            "allergies": "Penicillin",
            "conditions": "Diabetes",
            "medications": "Metformin"
        }
        report_text = (
            "Patient with fatigue. Physician notes: Recommended prophylactic Amoxicillin "
            "(Penicillin-class) prior to procedure."
        )
        conflicts = ValidationService.detect_conflicts(patient_profile, report_text)
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0]["type"], "Allergy Profile Inconsistency")
        # Must be neutral language
        self.assertIn("Potential inconsistency detected", conflicts[0]["description"])
        self.assertNotIn("dangerous", conflicts[0]["description"].lower())

    def test_03_login_demo_credentials(self):
        """Test demo account login with demo@medlens.com / demo123"""
        res = self.client.post('/api/login', data=json.dumps({
            "email": "demo@medlens.com",
            "password": "demo123"
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['redirect'], '/dashboard')

    def test_04_patient_api(self):
        """Verify fetching and updating patient information with user-provided provenance"""
        # Login first
        self.client.post('/api/login', data=json.dumps({
            "email": "demo@medlens.com",
            "password": "demo123"
        }), content_type='application/json')

        res = self.client.get('/api/patient')
        self.assertEqual(res.status_code, 200)
        patient = res.get_json()
        self.assertEqual(patient['name'], 'Demo Patient')
        self.assertEqual(patient['allergies'], 'Penicillin')

        # Update symptoms
        res_update = self.client.put('/api/patient', data=json.dumps({
            "name": "Demo Patient",
            "age": 45,
            "sex": "Female",
            "symptoms": "Fatigue, Mild Headache",
            "conditions": "Diabetes",
            "allergies": "Penicillin",
            "medications": "Metformin (500mg)"
        }), content_type='application/json')
        self.assertEqual(res_update.status_code, 200)

    def test_05_extraction_service_sample_report(self):
        """Verify extraction service on physical Blood_Report.pdf"""
        sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'sample_reports', 'Blood_Report.pdf')
        self.assertTrue(os.path.exists(sample_path))

        svc = ExtractionService()
        patient_profile = {"allergies": "Penicillin", "conditions": "Diabetes"}
        result = svc.process_document(sample_path, 'Blood_Report.pdf', patient_profile)

        self.assertTrue(result['success'])
        self.assertGreater(len(result['tests']), 0)
        # Verify page count is 2
        self.assertEqual(result['page_count'], 2)
        # Verify conflict detected
        self.assertGreater(len(result['conflicts']), 0)

    def test_06_human_verification_and_editing(self):
        """Test human verification and editing API with deterministic re-validation"""
        self.client.post('/api/login', data=json.dumps({
            "email": "demo@medlens.com",
            "password": "demo123"
        }), content_type='application/json')

        # Verify existing result (ID 1)
        res_ver = self.client.put('/api/verification/1', data=json.dumps({
            "verify": True
        }), content_type='application/json')
        self.assertEqual(res_ver.status_code, 200)

        # Edit existing result value (ID 1 Hemoglobin from 10.2 to 13.5 g/dL -> should become NORMAL)
        res_edit = self.client.put('/api/verification/1', data=json.dumps({
            "edited_value": 13.5,
            "notes": "Correction verified with lab director"
        }), content_type='application/json')
        self.assertEqual(res_edit.status_code, 200)

        # Re-fetch report details
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM extracted_results WHERE id = 1")
        row = cur.fetchone()
        conn.close()
        self.assertEqual(row['status'], 'NORMAL')
        self.assertEqual(row['is_verified'], 1)

    def test_07_compare_reports_api(self):
        """Test comparative report analysis and delta calculations"""
        self.client.post('/api/login', data=json.dumps({
            "email": "demo@medlens.com",
            "password": "demo123"
        }), content_type='application/json')

        # Compare report 3 (June) and report 1 (September)
        res = self.client.post('/api/compare', data=json.dumps({
            "previous_report_id": 3,
            "current_report_id": 1
        }), content_type='application/json')

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('comparisons', data)
        self.assertIn('chart_data', data)
        self.assertGreater(len(data['comparisons']), 0)

    def test_08_pdf_export(self):
        """Test PDF export generation via ReportLab"""
        self.client.post('/api/login', data=json.dumps({
            "email": "demo@medlens.com",
            "password": "demo123"
        }), content_type='application/json')

        res = self.client.get('/api/export/pdf')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'application/pdf')
        pdf_content = res.data
        self.assertTrue(pdf_content.startswith(b'%PDF-'))
        self.assertGreater(len(pdf_content), 1000)

if __name__ == '__main__':
    unittest.main()
