import os
import io
from functools import wraps
from datetime import datetime
from flask import 
(
    Flask, render_template, request, jsonify, session, redirect,
    url_for, send_file, send_from_directory, flash
)
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from utils.database import get_db, init_db, log_audit
from utils.pdf_export import generate_patient_record_pdf
from services.extraction_service import ExtractionService
from services.summary_service import SummaryService

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "medlens-super-secure-hackathon-key-2026")
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'sample_reports'), exist_ok=True)

extraction_service = ExtractionService()

# ----------------- Helper Functions -----------------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_patient(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE user_id = ?", (user_id,))
    patient = cur.fetchone()
    conn.close()
    return patient

# ----------------- View Routes (4 Main Pages) -----------------

@app.route('/')
@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    user_id = session['user_id']
    patient = get_current_patient(user_id)
    return render_template('dashboard.html', user_name=session.get('user_name', 'Healthcare User'), patient=patient)

@app.route('/record')
@app.route('/report/<int:report_id>')
@login_required
def medical_record_page(report_id=None):
    user_id = session['user_id']
    patient = get_current_patient(user_id)
    return render_template('medical_record.html', user_name=session.get('user_name'), patient=patient, initial_report_id=report_id)

@app.route('/history')
@login_required
def history_page():
    user_id = session['user_id']
    patient = get_current_patient(user_id)
    return render_template('history.html', user_name=session.get('user_name'), patient=patient)

# Serve uploaded / sample files for preview in Side-by-Side Modal
@app.route('/uploads/<path:filename>')
@login_required
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ----------------- Auth API -----------------

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
    user = cur.fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        log_audit(user['id'], None, 'User logged in', f"User {user['email']} authenticated successfully")
        return jsonify({"success": True, "message": "Login successful", "redirect": "/dashboard"})
    else:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not name or not email or not password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
    if cur.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Email address already registered"}), 409

    pwd_hash = generate_password_hash(password)
    cur.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, pwd_hash))
    user_id = cur.lastrowid

    # Create default patient record for user
    cur.execute('''
        INSERT INTO patients (user_id, name, age, sex, symptoms, conditions, allergies, medications)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, 35, 'Not specified', 'None', 'None', 'None', 'None'))
    conn.commit()
    conn.close()

    session['user_id'] = user_id
    session['user_name'] = name
    session['user_email'] = email
    log_audit(user_id, None, 'Account registered', f"New account created for {email}")
    return jsonify({"success": True, "message": "Account created successfully", "redirect": "/dashboard"})

@app.route('/api/logout', methods=['POST', 'GET'])
def api_logout():
    user_id = session.get('user_id')
    if user_id:
        log_audit(user_id, None, 'User logged out', 'Session terminated')
    session.clear()
    return redirect(url_for('login_page'))

# ----------------- Patient API -----------------

@app.route('/api/patient', methods=['GET'])
@login_required
def get_patient():
    patient = get_current_patient(session['user_id'])
    if not patient:
        return jsonify({"error": "Patient record not found"}), 404
    return jsonify(dict(patient))

@app.route('/api/patient', methods=['PUT'])
@login_required
def update_patient():
    user_id = session['user_id']
    data = request.get_json() or {}
    patient = get_current_patient(user_id)
    if not patient:
        return jsonify({"error": "Patient record not found"}), 404

    name = data.get('name', patient['name'])
    age = data.get('age', patient['age'])
    sex = data.get('sex', patient['sex'])
    symptoms = data.get('symptoms', patient['symptoms'])
    conditions = data.get('conditions', patient['conditions'])
    allergies = data.get('allergies', patient['allergies'])
    medications = data.get('medications', patient['medications'])

    conn = get_db()
    conn.execute('''
        UPDATE patients
        SET name = ?, age = ?, sex = ?, symptoms = ?, conditions = ?, allergies = ?, medications = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (name, age, sex, symptoms, conditions, allergies, medications, patient['id']))
    conn.commit()
    conn.close()

    log_audit(user_id, None, 'Patient information updated', f"Updated clinical profile for {name}")
    return jsonify({"success": True, "message": "Patient information updated successfully"})

# ----------------- Reports & Extraction API -----------------

@app.route('/api/reports/upload', methods=['POST'])
@login_required
def upload_report():
    user_id = session['user_id']
    patient = get_current_patient(user_id)
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    # Option A: Fast sample selection for hackathon demo
    sample_file = request.form.get('sample_file')
    if sample_file:
        sample_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sample_reports', sample_file)
        if not os.path.exists(sample_path):
            return jsonify({"error": f"Sample report {sample_file} not found"}), 404

        file_size = os.path.getsize(sample_path)
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO reports (patient_id, filename, original_filename, file_path, file_size, report_type, report_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient['id'],
            sample_file,
            sample_file,
            f"uploads/sample_reports/{sample_file}",
            file_size,
            "Blood Test" if "blood" in sample_file.lower() else "CBC",
            datetime.now().strftime("%Y-%m-%d"),
            "Uploaded"
        ))
        rep_id = cur.lastrowid
        conn.commit()
        conn.close()

        log_audit(user_id, rep_id, 'Report uploaded', f"Loaded sample report {sample_file}")
        return jsonify({
            "success": True,
            "report_id": rep_id,
            "filename": sample_file,
            "size": file_size,
            "message": "Sample report selected successfully"
        })

    # Option B: Real file upload
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not supported. Allowed: PDF, JPG, JPEG, PNG"}), 400

    original_filename = file.filename
    sec_name = secure_filename(original_filename)
    timestamp_prefix = datetime.now().strftime("%Y%m%d_%H%M%S_")
    saved_filename = f"{timestamp_prefix}{sec_name}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
    file.save(save_path)

    file_size = os.path.getsize(save_path)
    rel_path = f"uploads/{saved_filename}"

    # Determine default report type from filename
    ext = os.path.splitext(sec_name)[1].lower()
    report_type = "Diagnostic Report"
    if "cbc" in sec_name.lower():
        report_type = "CBC"
    elif "blood" in sec_name.lower():
        report_type = "Blood Test"

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO reports (patient_id, filename, original_filename, file_path, file_size, report_type, report_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (patient['id'], saved_filename, original_filename, rel_path, file_size, report_type, datetime.now().strftime("%Y-%m-%d"), "Uploaded"))
    rep_id = cur.lastrowid
    conn.commit()
    conn.close()

    log_audit(user_id, rep_id, 'Report uploaded', f"{original_filename} ({file_size} bytes)")
    return jsonify({
        "success": True,
        "report_id": rep_id,
        "filename": original_filename,
        "size": file_size,
        "type": ext.replace('.', '').upper()
    })

@app.route('/api/reports/<int:report_id>/process', methods=['POST'])
@login_required
def process_report(report_id):
    user_id = session['user_id']
    patient = get_current_patient(user_id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reports WHERE id = ? AND patient_id = ?", (report_id, patient['id']))
    report = cur.fetchone()

    if not report:
        conn.close()
        return jsonify({"error": "Report not found"}), 404

    # Determine absolute path to file
    abs_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), report['file_path'])
    if not os.path.exists(abs_file_path):
        # Check if stored in uploads root
        alt_path = os.path.join(app.config['UPLOAD_FOLDER'], report['filename'])
        if os.path.exists(alt_path):
            abs_file_path = alt_path

    # Run extraction pipeline
    result = extraction_service.process_document(
        file_path=abs_file_path,
        original_filename=report['original_filename'],
        patient_profile=dict(patient)
    )

    if not result["success"]:
        conn.close()
        return jsonify({"success": False, "error": result["error"]}), 500

    # Clear previous extracted results for this report if re-processing
    cur.execute("DELETE FROM extracted_results WHERE report_id = ?", (report_id,))

    # Insert extracted results
    for t in result["tests"]:
        cur.execute('''
            INSERT INTO extracted_results (
                report_id, test_name, value, value_text, unit, reference_range,
                reference_low, reference_high, status, confidence, source_page, source_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id,
            t["test_name"],
            t["value"],
            t["value_text"],
            t["unit"],
            t["reference_range"],
            t["reference_low"],
            t["reference_high"],
            t["status"],
            t["confidence"],
            t["source_page"],
            t["source_text"]
        ))

    # Update report status and page count
    cur.execute('''
        UPDATE reports
        SET status = 'Processed', page_count = ?, report_type = ?, report_date = ?
        WHERE id = ?
    ''', (result["page_count"], result["report_type"], result["report_date"], report_id))

    # Record any detected conflicts
    for c in result.get("conflicts", []):
        cur.execute('''
            INSERT INTO conflicts (patient_id, report_id, conflict_type, description, status)
            VALUES (?, ?, ?, ?, 'detected')
        ''', (patient['id'], report_id, c["type"], c["description"]))

    conn.commit()
    conn.close()

    log_audit(user_id, report_id, 'AI extraction completed', f"Extracted {len(result['tests'])} tests via {result['extraction_mode']}")
    log_audit(user_id, report_id, 'Reference range analysis completed', 'Deterministic range calculations applied')

    return jsonify({
        "success": True,
        "report_id": report_id,
        "stages": result["pipeline_stages"],
        "tests": result["tests"],
        "conflicts": result.get("conflicts", []),
        "mode": result["extraction_mode"],
        "page_count": result["page_count"]
    })

@app.route('/api/reports', methods=['GET'])
@login_required
def get_reports():
    patient = get_current_patient(session['user_id'])
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, filename, original_filename, file_size, report_type, report_date, status, page_count, created_at
        FROM reports
        WHERE patient_id = ?
        ORDER BY report_date DESC, id DESC
    ''', (patient['id'],))
    reports = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(reports)

@app.route('/api/reports/<int:report_id>', methods=['GET'])
@login_required
def get_report_details(report_id):
    patient = get_current_patient(session['user_id'])
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reports WHERE id = ? AND patient_id = ?", (report_id, patient['id']))
    report = cur.fetchone()
    if not report:
        conn.close()
        return jsonify({"error": "Report not found"}), 404

    cur.execute('''
        SELECT * FROM extracted_results
        WHERE report_id = ?
        ORDER BY source_page ASC, id ASC
    ''', (report_id,))
    results = [dict(row) for row in cur.fetchall()]
    conn.close()

    rep_dict = dict(report)
    rep_dict["results"] = results
    return jsonify(rep_dict)

@app.route('/api/records', methods=['GET'])
@login_required
def get_full_medical_record():
    patient = get_current_patient(session['user_id'])
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT r.id, r.original_filename, r.report_type, r.report_date, r.status as report_status,
               e.id as result_id, e.test_name, e.value, e.edited_value, e.unit,
               e.reference_range, e.status, e.confidence, e.source_page, e.source_text, e.is_verified
        FROM extracted_results e
        JOIN reports r ON e.report_id = r.id
        WHERE r.patient_id = ?
        ORDER BY r.report_date DESC, e.source_page ASC
    ''', (patient['id'],))
    raw_results = [dict(row) for row in cur.fetchall()]
    conn.close()

    return jsonify({
        "patient": dict(patient),
        "results": raw_results
    })

# ----------------- Verification & Editing API -----------------

@app.route('/api/verification/<int:result_id>', methods=['PUT'])
@login_required
def verify_or_edit_result(result_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM extracted_results WHERE id = ?", (result_id,))
    res = cur.fetchone()
    if not res:
        conn.close()
        return jsonify({"error": "Result not found"}), 404

    is_verified = 1 if data.get('verify', True) else 0
    new_value = data.get('edited_value')
    notes = data.get('notes', '')

    original_val = str(res['value'])
    edited_val = str(new_value) if new_value is not None else None

    # If new value provided, update the value and recalculate reference status deterministically!
    if new_value is not None:
        try:
            val_float = float(new_value)
            from services.validation_service import ValidationService
            new_status = ValidationService.calculate_reference_status(
                val_float, res['reference_low'], res['reference_high']
            )
            cur.execute('''
                UPDATE extracted_results
                SET value = ?, edited_value = ?, status = ?, is_verified = 1
                WHERE id = ?
            ''', (val_float, val_float, new_status, result_id))
        except ValueError:
            cur.execute('''
                UPDATE extracted_results
                SET edited_value = ?, is_verified = 1
                WHERE id = ?
            ''', (new_value, result_id))
    else:
        cur.execute("UPDATE extracted_results SET is_verified = ? WHERE id = ?", (is_verified, result_id))

    # Log verification record
    cur.execute('''
        INSERT INTO verification_records (result_id, original_value, edited_value, verified_by, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (result_id, original_val, edited_val, session.get('user_name', 'Human Reviewer'), notes))

    conn.commit()
    conn.close()

    log_audit(user_id, res['report_id'], 'Information verified', f"{res['test_name']} marked human-verified")
    return jsonify({"success": True, "message": "Result updated and verified successfully"})

# ----------------- Conflicts API -----------------

@app.route('/api/conflicts', methods=['GET'])
@login_required
def get_conflicts():
    patient = get_current_patient(session['user_id'])
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT c.*, r.original_filename as report_name
        FROM conflicts c
        LEFT JOIN reports r ON c.report_id = r.id
        WHERE c.patient_id = ?
        ORDER BY c.created_at DESC
    ''', (patient['id'],))
    conflicts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(conflicts)

@app.route('/api/conflicts/<int:conflict_id>', methods=['PUT'])
@login_required
def update_conflict_status(conflict_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    new_status = data.get('status')  # 'reviewed', 'resolved', 'ignored'

    if new_status not in ['reviewed', 'resolved', 'ignored', 'detected']:
        return jsonify({"error": "Invalid conflict status"}), 400

    conn = get_db()
    conn.execute("UPDATE conflicts SET status = ? WHERE id = ?", (new_status, conflict_id))
    conn.commit()
    conn.close()

    log_audit(user_id, None, f"Conflict status updated to {new_status}", f"Conflict ID {conflict_id} changed to {new_status}")
    return jsonify({"success": True, "status": new_status})

# ----------------- AI Summary API -----------------

@app.route('/api/summary', methods=['POST', 'GET'])
@login_required
def get_summary():
    report_id = request.args.get('report_id')
    if not report_id and request.is_json:
        report_id = request.get_json().get('report_id')

    patient = get_current_patient(session['user_id'])
    conn = get_db()
    cur = conn.cursor()

    if report_id:
        cur.execute("SELECT * FROM reports WHERE id = ? AND patient_id = ?", (report_id, patient['id']))
        report = cur.fetchone()
    else:
        # Default to most recent processed report
        cur.execute("SELECT * FROM reports WHERE patient_id = ? ORDER BY report_date DESC, id DESC LIMIT 1", (patient['id'],))
        report = cur.fetchone()

    if not report:
        conn.close()
        return jsonify({"error": "No report available to summarize"}), 404

    cur.execute("SELECT * FROM extracted_results WHERE report_id = ?", (report['id'],))
    tests = [dict(row) for row in cur.fetchall()]
    conn.close()

    summary_data = SummaryService.generate_summary(report['original_filename'], tests)
    summary_data["report_id"] = report['id']
    summary_data["report_name"] = report['original_filename']

    return jsonify(summary_data)

# ----------------- History & Comparison API -----------------

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    patient = get_current_patient(session['user_id'])
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT id, original_filename, report_type, report_date, status, file_size, page_count
        FROM reports
        WHERE patient_id = ?
        ORDER BY report_date DESC
    ''', (patient['id'],))
    reports = [dict(row) for row in cur.fetchall()]

    # Construct chronological timeline events
    timeline = []
    for r in sorted(reports, key=lambda x: x['report_date']):
        date_obj = datetime.strptime(r['report_date'], "%Y-%m-%d")
        month_year = date_obj.strftime("%B %Y")
        timeline.append({
            "report_id": r['id'],
            "date": r['report_date'],
            "display_date": month_year,
            "title": f"{r['report_type']} uploaded",
            "filename": r['original_filename'],
            "status": r['status']
        })

    conn.close()
    return jsonify({
        "reports": reports,
        "timeline": timeline
    })

@app.route('/api/compare', methods=['POST'])
@login_required
def compare_reports():
    data = request.get_json() or {}
    prev_id = data.get('previous_report_id')
    curr_id = data.get('current_report_id')

    if not prev_id or not curr_id:
        return jsonify({"error": "Both previous_report_id and current_report_id are required"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM reports WHERE id = ?", (prev_id,))
    prev_rep = cur.fetchone()

    cur.execute("SELECT * FROM reports WHERE id = ?", (curr_id,))
    curr_rep = cur.fetchone()

    if not prev_rep or not curr_rep:
        conn.close()
        return jsonify({"error": "One or both reports not found"}), 404

    cur.execute("SELECT * FROM extracted_results WHERE report_id = ?", (prev_id,))
    prev_tests = {row['test_name'].lower().strip(): dict(row) for row in cur.fetchall()}

    cur.execute("SELECT * FROM extracted_results WHERE report_id = ?", (curr_id,))
    curr_tests = {row['test_name'].lower().strip(): dict(row) for row in cur.fetchall()}
    conn.close()

    comparison_rows = []
    chart_labels = []
    chart_prev_vals = []
    chart_curr_vals = []

    # Match tests by normalized name
    all_keys = list(set(list(prev_tests.keys()) + list(curr_tests.keys())))

    for k in sorted(all_keys):
        p_item = prev_tests.get(k)
        c_item = curr_tests.get(k)

        name = (c_item or p_item)['test_name']
        unit = (c_item or p_item)['unit']

        p_val = p_item['value'] if p_item and p_item['value'] is not None else None
        c_val = c_item['value'] if c_item and c_item['value'] is not None else None

        change_display = "—"
        neutral_statement = "Single data point recorded."

        if p_val is not None and c_val is not None:
            delta = round(c_val - p_val, 2)
            sign = "+" if delta > 0 else ""
            change_display = f"{sign}{delta}"
            neutral_statement = f"Value changed from {p_val} to {c_val}."
            chart_labels.append(name)
            chart_prev_vals.append(p_val)
            chart_curr_vals.append(c_val)

        comparison_rows.append({
            "test_name": name,
            "unit": unit,
            "previous_value": p_val,
            "current_value": c_val,
            "change": change_display,
            "neutral_statement": neutral_statement,
            "previous_date": prev_rep['report_date'],
            "current_date": curr_rep['report_date']
        })

    return jsonify({
        "previous_report": dict(prev_rep),
        "current_report": dict(curr_rep),
        "comparisons": comparison_rows,
        "chart_data": {
            "labels": chart_labels,
            "previous": chart_prev_vals,
            "current": chart_curr_vals
        }
    })

# ----------------- PDF Export API -----------------

@app.route('/api/export/pdf', methods=['GET'])
@login_required
def export_pdf():
    user_id = session['user_id']
    patient = get_current_patient(user_id)
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM reports WHERE patient_id = ? ORDER BY report_date DESC", (patient['id'],))
    reports = [dict(row) for row in cur.fetchall()]

    cur.execute('''
        SELECT e.*, r.original_filename as report_name
        FROM extracted_results e
        JOIN reports r ON e.report_id = r.id
        WHERE r.patient_id = ?
        ORDER BY r.report_date DESC, e.source_page ASC
    ''', (patient['id'],))
    results = [dict(row) for row in cur.fetchall()]

    # Generate summary
    rep_name = reports[0]['original_filename'] if reports else "Clinical Record"
    summary_data = SummaryService.generate_summary(rep_name, results)
    conn.close()

    pdf_bytes = generate_patient_record_pdf(dict(patient), reports, results, summary_data)

    log_audit(user_id, None, 'PDF report exported', f"Generated complete clinical dossier for {patient['name']}")

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"MedLens_Record_{secure_filename(patient['name'])}.pdf"
    )

# ----------------- Audit Log API -----------------

@app.route('/api/audit', methods=['GET'])
@login_required
def get_audit_events():
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT a.*, r.original_filename as report_name
        FROM audit_logs a
        LEFT JOIN reports r ON a.report_id = r.id
        WHERE a.user_id = ?
        ORDER BY a.timestamp DESC
        LIMIT 10
    ''', (user_id,))
    logs = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(logs)

# ----------------- Dashboard Summary Metrics API -----------------

@app.route('/api/dashboard/metrics', methods=['GET'])
@login_required
def get_dashboard_metrics():
    patient = get_current_patient(session['user_id'])
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as count FROM reports WHERE patient_id = ?", (patient['id'],))
    rep_count = cur.fetchone()['count']

    cur.execute('''
        SELECT COUNT(*) as count FROM extracted_results e
        JOIN reports r ON e.report_id = r.id
        WHERE r.patient_id = ?
    ''', (patient['id'],))
    results_count = cur.fetchone()['count']

    cur.execute('''
        SELECT COUNT(*) as count FROM extracted_results e
        JOIN reports r ON e.report_id = r.id
        WHERE r.patient_id = ? AND e.is_verified = 0
    ''', (patient['id'],))
    unverified_count = cur.fetchone()['count']

    cur.execute('''
        SELECT COUNT(*) as count FROM conflicts
        WHERE patient_id = ? AND status = 'detected'
    ''', (patient['id'],))
    conflicts_count = cur.fetchone()['count']

    conn.close()

    return jsonify({
        "reports_count": rep_count,
        "extracted_results_count": results_count,
        "needs_verification_count": unverified_count,
        "potential_conflicts_count": conflicts_count
    })

# ----------------- Error Handlers -----------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', content="<div class='container py-5 text-center'><h3>Page Not Found</h3><a href='/dashboard' class='btn btn-primary mt-3'>Return to Dashboard</a></div>"), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error occurred. MedLens is safely handling this exception."}), 500

if __name__ == '__main__':
    seed_demo = os.environ.get('SEED_DEMO_DATA', '').strip().lower() in {'1', 'true', 'yes', 'y'}
    init_db(seed_demo=seed_demo)
    app.run(host='0.0.0.0', port=5000, debug=True)
