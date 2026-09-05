import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(seed_demo=False):
    conn = get_db()
    cur = conn.cursor()

    # 1. Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Patients table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            sex TEXT,
            symptoms TEXT,
            conditions TEXT,
            allergies TEXT,
            medications TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # 3. Reports table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            report_type TEXT NOT NULL,
            report_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Uploaded',
            page_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
        )
    ''')

    # 4. Extracted Results table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS extracted_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            test_name TEXT NOT NULL,
            value REAL,
            value_text TEXT,
            unit TEXT,
            reference_range TEXT,
            reference_low REAL,
            reference_high REAL,
            status TEXT NOT NULL, -- 'LOW', 'NORMAL', 'HIGH', 'UNKNOWN'
            confidence REAL DEFAULT 0.95,
            source_page INTEGER DEFAULT 1,
            source_text TEXT,
            is_verified INTEGER DEFAULT 0,
            edited_value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE CASCADE
        )
    ''')

    # 5. Conflicts table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            report_id INTEGER,
            conflict_type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'detected', -- 'detected', 'reviewed', 'resolved', 'ignored'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE,
            FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE SET NULL
        )
    ''')

    # 6. Verification Records table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS verification_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL,
            original_value TEXT,
            edited_value TEXT,
            verified_by TEXT,
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (result_id) REFERENCES extracted_results (id) ON DELETE CASCADE
        )
    ''')

    # 7. Audit Logs table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            report_id INTEGER,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
            FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE SET NULL
        )
    ''')

    conn.commit()

    if seed_demo:
        seed_demo_data(conn)

    conn.close()

def seed_demo_data(conn):
    cur = conn.cursor()

    # Check if demo user already exists
    cur.execute("SELECT id FROM users WHERE email = ?", ('demo@medlens.com',))
    user_row = cur.fetchone()

    if not user_row:
        # Create Demo User
        demo_pwd_hash = generate_password_hash('demo123')
        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ('Dr. Demo Reviewer', 'demo@medlens.com', demo_pwd_hash)
        )
        user_id = cur.lastrowid

        # Create Demo Patient
        cur.execute('''
            INSERT INTO patients (user_id, name, age, sex, symptoms, conditions, allergies, medications)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            'Demo Patient',
            45,
            'Female',
            'Fatigue, Headache',
            'Diabetes',
            'Penicillin',
            'Metformin (500mg daily)'
        ))
        patient_id = cur.lastrowid

        # Sample Report 1: Blood_Report.pdf (Current - 03 Sep 2026)
        cur.execute('''
            INSERT INTO reports (patient_id, filename, original_filename, file_path, file_size, report_type, report_date, status, page_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id,
            'Blood_Report.pdf',
            'Blood_Report.pdf',
            'uploads/sample_reports/Blood_Report.pdf',
            148200,
            'Blood Test',
            '2026-09-03',
            'Processed',
            2
        ))
        rep1_id = cur.lastrowid

        rep1_tests = [
            ('Hemoglobin', 10.2, '10.2', 'g/dL', '12–16 g/dL', 12.0, 16.0, 'LOW', 0.97, 2, 'Hemoglobin: 10.2 g/dL (Ref: 12–16 g/dL)'),
            ('Glucose', 145.0, '145', 'mg/dL', '70–100 mg/dL', 70.0, 100.0, 'HIGH', 0.95, 1, 'Fasting Blood Glucose: 145 mg/dL (Ref: 70–100 mg/dL)'),
            ('TSH', 3.2, '3.2', 'mIU/L', '0.4–4.0 mIU/L', 0.4, 4.0, 'NORMAL', 0.96, 1, 'Thyroid Stimulating Hormone: 3.2 mIU/L (Ref: 0.4–4.0 mIU/L)'),
            ('Platelets', 230.0, '230', 'x10^3/uL', '150–450 x10^3/uL', 150.0, 450.0, 'NORMAL', 0.98, 2, 'Platelet Count: 230 x10^3/uL (Ref: 150–450 x10^3/uL)'),
            ('Total Cholesterol', 215.0, '215', 'mg/dL', '125–200 mg/dL', 125.0, 200.0, 'HIGH', 0.94, 1, 'Total Serum Cholesterol: 215 mg/dL (Ref: 125–200 mg/dL)'),
            ('Creatinine', 0.9, '0.9', 'mg/dL', '0.6–1.2 mg/dL', 0.6, 1.2, 'NORMAL', 0.96, 2, 'Serum Creatinine: 0.9 mg/dL (Ref: 0.6–1.2 mg/dL)'),
            ('Vitamin D', 18.0, '18', 'ng/mL', '30–100 ng/mL', 30.0, 100.0, 'LOW', 0.92, 1, '25-OH Vitamin D: 18 ng/mL (Ref: 30–100 ng/mL)'),
            ('HbA1c', 7.1, '7.1', '%', '4.0–5.6 %', 4.0, 5.6, 'HIGH', 0.97, 2, 'Glycated Hemoglobin (HbA1c): 7.1 % (Ref: 4.0–5.6 %)')
        ]

        for t in rep1_tests:
            cur.execute('''
                INSERT INTO extracted_results (
                    report_id, test_name, value, value_text, unit, reference_range,
                    reference_low, reference_high, status, confidence, source_page, source_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (rep1_id, t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10]))

        # Sample Report 2: CBC_Report.pdf (20 Aug 2026)
        cur.execute('''
            INSERT INTO reports (patient_id, filename, original_filename, file_path, file_size, report_type, report_date, status, page_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id,
            'CBC_Report.pdf',
            'CBC_Report.pdf',
            'uploads/sample_reports/CBC_Report.pdf',
            124500,
            'CBC',
            '2026-08-20',
            'Verified',
            1
        ))
        rep2_id = cur.lastrowid

        rep2_tests = [
            ('Hemoglobin', 10.8, '10.8', 'g/dL', '12–16 g/dL', 12.0, 16.0, 'LOW', 0.98, 1, 'Hemoglobin: 10.8 g/dL (Ref: 12–16 g/dL)'),
            ('WBC Count', 6.8, '6.8', 'x10^3/uL', '4.0–11.0 x10^3/uL', 4.0, 11.0, 'NORMAL', 0.97, 1, 'White Blood Cell Count: 6.8 x10^3/uL (Ref: 4.0–11.0 x10^3/uL)'),
            ('RBC Count', 3.9, '3.9', 'x10^6/uL', '4.0–5.2 x10^6/uL', 4.0, 5.2, 'LOW', 0.94, 1, 'Red Blood Cell Count: 3.9 x10^6/uL (Ref: 4.0–5.2 x10^6/uL)'),
            ('Hematocrit', 33.0, '33', '%', '36–46 %', 36.0, 46.0, 'LOW', 0.96, 1, 'Hematocrit: 33.0 % (Ref: 36–46 %)'),
            ('Platelets', 240.0, '240', 'x10^3/uL', '150–450 x10^3/uL', 150.0, 450.0, 'NORMAL', 0.98, 1, 'Platelets: 240 x10^3/uL (Ref: 150–450 x10^3/uL)')
        ]
        for t in rep2_tests:
            cur.execute('''
                INSERT INTO extracted_results (
                    report_id, test_name, value, value_text, unit, reference_range,
                    reference_low, reference_high, status, confidence, source_page, source_text, is_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (rep2_id, t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10]))

        # Sample Report 3: Blood_Report_Jun.pdf (15 Jun 2026)
        cur.execute('''
            INSERT INTO reports (patient_id, filename, original_filename, file_path, file_size, report_type, report_date, status, page_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id,
            'Blood_Report_Jun.pdf',
            'Blood_Report_Jun.pdf',
            'uploads/sample_reports/Blood_Report_Jun.pdf',
            110200,
            'Blood Test',
            '2026-06-15',
            'Verified',
            1
        ))
        rep3_id = cur.lastrowid

        rep3_tests = [
            ('Hemoglobin', 11.2, '11.2', 'g/dL', '12–16 g/dL', 12.0, 16.0, 'LOW', 0.96, 1, 'Hemoglobin: 11.2 g/dL (Ref: 12–16 g/dL)'),
            ('Glucose', 125.0, '125', 'mg/dL', '70–100 mg/dL', 70.0, 100.0, 'HIGH', 0.95, 1, 'Glucose: 125 mg/dL (Ref: 70–100 mg/dL)'),
            ('TSH', 3.5, '3.5', 'mIU/L', '0.4–4.0 mIU/L', 0.4, 4.0, 'NORMAL', 0.97, 1, 'TSH: 3.5 mIU/L (Ref: 0.4–4.0 mIU/L)'),
            ('Total Cholesterol', 195.0, '195', 'mg/dL', '125–200 mg/dL', 125.0, 200.0, 'NORMAL', 0.95, 1, 'Total Cholesterol: 195 mg/dL (Ref: 125–200 mg/dL)')
        ]
        for t in rep3_tests:
            cur.execute('''
                INSERT INTO extracted_results (
                    report_id, test_name, value, value_text, unit, reference_range,
                    reference_low, reference_high, status, confidence, source_page, source_text, is_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (rep3_id, t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10]))

        # Sample Report 4: Health_Check_Mar.pdf (10 Mar 2026)
        cur.execute('''
            INSERT INTO reports (patient_id, filename, original_filename, file_path, file_size, report_type, report_date, status, page_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id,
            'Health_Check_Mar.pdf',
            'Health_Check_Mar.pdf',
            'uploads/sample_reports/Health_Check_Mar.pdf',
            98400,
            'Comprehensive Health',
            '2026-03-10',
            'Verified',
            1
        ))
        rep4_id = cur.lastrowid

        rep4_tests = [
            ('Hemoglobin', 11.8, '11.8', 'g/dL', '12–16 g/dL', 12.0, 16.0, 'LOW', 0.95, 1, 'Hemoglobin: 11.8 g/dL (Ref: 12–16 g/dL)'),
            ('Glucose', 118.0, '118', 'mg/dL', '70–100 mg/dL', 70.0, 100.0, 'HIGH', 0.94, 1, 'Glucose: 118 mg/dL (Ref: 70–100 mg/dL)'),
            ('TSH', 3.8, '3.8', 'mIU/L', '0.4–4.0 mIU/L', 0.4, 4.0, 'NORMAL', 0.96, 1, 'TSH: 3.8 mIU/L (Ref: 0.4–4.0 mIU/L)')
        ]
        for t in rep4_tests:
            cur.execute('''
                INSERT INTO extracted_results (
                    report_id, test_name, value, value_text, unit, reference_range,
                    reference_low, reference_high, status, confidence, source_page, source_text, is_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (rep4_id, t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10]))

        # Conflicts
        cur.execute('''
            INSERT INTO conflicts (patient_id, report_id, conflict_type, description, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            patient_id,
            rep1_id,
            'Allergy vs Medication Inconsistency',
            'Potential inconsistency detected between patient allergy profile (Penicillin) and medication note in uploaded record (Amoxicillin/Penicillin class). Please review the original information.',
            'detected'
        ))

        cur.execute('''
            INSERT INTO conflicts (patient_id, report_id, conflict_type, description, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            patient_id,
            rep1_id,
            'Condition vs Dietary Formulation',
            'Potential inconsistency detected between patient condition (Diabetes) and reported high-glucose supplemental intake note. Please verify with patient profile.',
            'reviewed'
        ))

        # Audit logs
        audit_events = [
            (user_id, rep1_id, 'Report uploaded', 'Blood_Report.pdf (148 KB) added to queue'),
            (user_id, rep1_id, 'AI extraction completed', 'Extracted 8 laboratory test results with source provenance'),
            (user_id, rep1_id, 'Reference range analysis completed', 'Deterministic range calculations applied'),
            (user_id, rep1_id, 'Potential conflict detected', 'Allergy Penicillin flagged against uploaded record notes'),
            (user_id, rep2_id, 'Information verified', 'Human reviewer confirmed CBC laboratory panel results')
        ]
        for ev in audit_events:
            cur.execute('''
                INSERT INTO audit_logs (user_id, report_id, action, details)
                VALUES (?, ?, ?, ?)
            ''', ev)

        conn.commit()

def log_audit(user_id, report_id, action, details):
    conn = get_db()
    conn.execute('''
        INSERT INTO audit_logs (user_id, report_id, action, details)
        VALUES (?, ?, ?, ?)
    ''', (user_id, report_id, action, details))
    conn.commit()
    conn.close()
