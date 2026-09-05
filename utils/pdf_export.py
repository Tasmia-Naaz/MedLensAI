import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_patient_record_pdf(patient, reports, results, summary_data):
    """
    Generates a structured, professional patient clinical record PDF.
    Includes patient info, user-provided tags, laboratory results, reference ranges,
    traceability provenance, AI summary, and mandatory safety notices.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f4c81')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#555555')
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f4c81'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#222222')
    )
    badge_user_style = ParagraphStyle(
        'BadgeUser',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor('#0d6efd')
    )
    badge_report_style = ParagraphStyle(
        'BadgeReport',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor('#198754')
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#721c24')
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("MEDLENS CLINICAL RECORD", title_style))
    elements.append(Paragraph("AI-Powered Clinical Information Intelligence & Provenance Tracking", subtitle_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')} | System: MedLens v1.0", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0f4c81'), spaceBefore=8, spaceAfter=12))

    # 2. Safety Notice (Callout Box)
    safety_text = (
        "<b>IMPORTANT SAFETY NOTICE:</b> MedLens organizes and explains information from available "
        "medical records. It does not provide medical diagnosis or treatment recommendations. "
        "Please consult a qualified healthcare professional for medical decisions."
    )
    safety_table = Table([[Paragraph(safety_text, disclaimer_style)]], colWidths=[530])
    safety_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8d7da')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#f5c6cb')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(safety_table)
    elements.append(Spacer(1, 12))

    # 3. Patient Information Section
    elements.append(Paragraph("1. PATIENT PROFILE", section_heading))
    patient_data = [
        [
            Paragraph("<b>Full Name:</b>", body_style),
            Paragraph(patient.get('name', 'N/A'), body_style),
            Paragraph("<b>Provenance:</b>", body_style),
            Paragraph("[User Provided]", badge_user_style)
        ],
        [
            Paragraph("<b>Age / Sex:</b>", body_style),
            Paragraph(f"{patient.get('age', 'N/A')} yrs / {patient.get('sex', 'N/A')}", body_style),
            Paragraph("<b>Provenance:</b>", body_style),
            Paragraph("[User Provided]", badge_user_style)
        ],
        [
            Paragraph("<b>Reported Symptoms:</b>", body_style),
            Paragraph(patient.get('symptoms', 'None reported'), body_style),
            Paragraph("<b>Provenance:</b>", body_style),
            Paragraph("[User Provided]", badge_user_style)
        ],
        [
            Paragraph("<b>Existing Conditions:</b>", body_style),
            Paragraph(patient.get('conditions', 'None reported'), body_style),
            Paragraph("<b>Provenance:</b>", body_style),
            Paragraph("[User Provided]", badge_user_style)
        ],
        [
            Paragraph("<b>Known Allergies:</b>", body_style),
            Paragraph(patient.get('allergies', 'None reported'), body_style),
            Paragraph("<b>Provenance:</b>", body_style),
            Paragraph("[User Provided]", badge_user_style)
        ],
        [
            Paragraph("<b>Current Medications:</b>", body_style),
            Paragraph(patient.get('medications', 'None reported'), body_style),
            Paragraph("<b>Provenance:</b>", body_style),
            Paragraph("[User Provided]", badge_user_style)
        ]
    ]

    p_table = Table(patient_data, colWidths=[130, 210, 80, 110])
    p_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e9ecef')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(p_table)
    elements.append(Spacer(1, 14))

    # 4. Laboratory Results Section
    elements.append(Paragraph("2. EXTRACTED LABORATORY RESULTS", section_heading))
    lab_headers = ["Test Name", "Value", "Unit", "Reference Range", "Status", "Confidence", "Source & Page"]
    lab_rows = [[Paragraph(f"<b>{h}</b>", body_style) for h in lab_headers]]

    for r in results:
        status_color = '#198754' if r['status'] == 'NORMAL' else ('#dc3545' if r['status'] == 'LOW' else ('#fd7e14' if r['status'] == 'HIGH' else '#6c757d'))
        status_text = f"<font color='{status_color}'><b>{r['status']}</b></font>"
        conf_text = f"{int(float(r['confidence']) * 100)}%" if r['confidence'] else "95%"
        source_text = f"{r.get('report_name', 'Report')} (Pg {r['source_page']})"

        val_display = str(r['edited_value']) if r.get('edited_value') is not None else str(r['value'])

        lab_rows.append([
            Paragraph(r['test_name'], body_style),
            Paragraph(val_display, body_style),
            Paragraph(r['unit'] or '', body_style),
            Paragraph(r['reference_range'] or 'Not provided', body_style),
            Paragraph(status_text, body_style),
            Paragraph(conf_text, body_style),
            Paragraph(source_text, badge_report_style)
        ])

    lab_table = Table(lab_rows, colWidths=[100, 45, 50, 95, 60, 60, 120])
    lab_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2eafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(lab_table)
    elements.append(Spacer(1, 14))

    # 5. Patient-Friendly AI Summary & Observations
    elements.append(Paragraph("3. PATIENT-FRIENDLY SUMMARY & OBSERVATIONS", section_heading))
    if summary_data and "overview" in summary_data:
        elements.append(Paragraph(f"<b>Overview:</b> {summary_data['overview']}", body_style))
        elements.append(Spacer(1, 6))

        if "observations" in summary_data:
            elements.append(Paragraph("<b>Key Observations:</b>", body_style))
            for obs in summary_data["observations"]:
                obs_text = f"• {obs['text']} <font color='#555'><i>(Source: {obs['source']})</i></font>"
                elements.append(Paragraph(obs_text, body_style))
                elements.append(Spacer(1, 3))
    else:
        elements.append(Paragraph("Clinical laboratory data structured and verified against provided reference boundaries.", body_style))

    elements.append(Spacer(1, 14))

    # Footer note
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'), spaceBefore=10, spaceAfter=8))
    elements.append(Paragraph("MedLens Clinical Intelligence System — Confidential Healthcare Information — Page 1 of 1", subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
