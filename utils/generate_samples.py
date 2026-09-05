import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_sample_reports():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'sample_reports')
    os.makedirs(output_dir, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'LabTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#003366')
    )
    h2_style = ParagraphStyle(
        'LabH2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#003366'), spaceBefore=8, spaceAfter=4
    )
    body_style = ParagraphStyle('LabBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12)
    small_style = ParagraphStyle('LabSmall', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#555555'))

    # 1. Blood_Report.pdf (2 pages)
    p1 = os.path.join(output_dir, 'Blood_Report.pdf')
    doc1 = SimpleDocTemplate(p1, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elems1 = [
        Paragraph("METROPATH CLINICAL LABORATORIES", title_style),
        Paragraph("Accredited Medical Diagnostic Center — CLIA #99D0876543", small_style),
        Spacer(1, 10),
        Table([
            [Paragraph("<b>Patient Name:</b> Demo Patient", body_style), Paragraph("<b>DOB / Age:</b> 1981-04-12 (45 Y)", body_style)],
            [Paragraph("<b>Ordering Physician:</b> Dr. S. Mehta, MD", body_style), Paragraph("<b>Collection Date:</b> 2026-09-03 08:30 AM", body_style)],
            [Paragraph("<b>Accession Number:</b> MP-2026-99812", body_style), Paragraph("<b>Report Status:</b> Final Signed", body_style)],
        ], colWidths=[270, 270], style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')), ('PADDING', (0,0), (-1,-1), 4)]),
        Spacer(1, 12),
        Paragraph("METABOLIC & ENDOCRINE PANEL (Page 1)", h2_style),
        Table([
            [Paragraph("<b>Test Description</b>", body_style), Paragraph("<b>Result</b>", body_style), Paragraph("<b>Units</b>", body_style), Paragraph("<b>Reference Range</b>", body_style)],
            [Paragraph("Fasting Blood Glucose", body_style), Paragraph("<b>145</b>", body_style), Paragraph("mg/dL", body_style), Paragraph("70 – 100 mg/dL", body_style)],
            [Paragraph("Thyroid Stimulating Hormone (TSH)", body_style), Paragraph("<b>3.2</b>", body_style), Paragraph("mIU/L", body_style), Paragraph("0.4 – 4.0 mIU/L", body_style)],
            [Paragraph("Total Cholesterol", body_style), Paragraph("<b>215</b>", body_style), Paragraph("mg/dL", body_style), Paragraph("125 – 200 mg/dL", body_style)],
            [Paragraph("25-OH Vitamin D", body_style), Paragraph("<b>18</b>", body_style), Paragraph("ng/mL", body_style), Paragraph("30 – 100 ng/mL", body_style)],
        ], colWidths=[200, 70, 80, 190], style=[
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#d9e2ec')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]),
        Spacer(1, 10),
        Paragraph("Physician Consultation Notes:", h2_style),
        Paragraph("Patient presented with persistent fatigue and episodic headaches. Consider clinical evaluation of elevated fasting glycemic levels. Recommendation includes standard antibiotic prophylaxis with Amoxicillin (Penicillin-class) prior to scheduled dental procedure if clinically indicated.", body_style),
        PageBreak(),
        Paragraph("METROPATH CLINICAL LABORATORIES (Page 2)", title_style),
        Spacer(1, 10),
        Paragraph("HEMATOLOGY & RENAL PANEL (Page 2)", h2_style),
        Table([
            [Paragraph("<b>Test Description</b>", body_style), Paragraph("<b>Result</b>", body_style), Paragraph("<b>Units</b>", body_style), Paragraph("<b>Reference Range</b>", body_style)],
            [Paragraph("Hemoglobin", body_style), Paragraph("<b>10.2</b>", body_style), Paragraph("g/dL", body_style), Paragraph("12.0 – 16.0 g/dL", body_style)],
            [Paragraph("Platelet Count", body_style), Paragraph("<b>230</b>", body_style), Paragraph("x10^3/uL", body_style), Paragraph("150 – 450 x10^3/uL", body_style)],
            [Paragraph("Serum Creatinine", body_style), Paragraph("<b>0.9</b>", body_style), Paragraph("mg/dL", body_style), Paragraph("0.6 – 1.2 mg/dL", body_style)],
            [Paragraph("Glycated Hemoglobin (HbA1c)", body_style), Paragraph("<b>7.1</b>", body_style), Paragraph("%", body_style), Paragraph("4.0 – 5.6 %", body_style)],
        ], colWidths=[200, 70, 80, 190], style=[
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#d9e2ec')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]),
        Spacer(1, 15),
        Paragraph("Laboratory Director: Marcus Vance, MD, FACP. Electronic Signature Verified.", small_style)
    ]
    doc1.build(elems1)

    # 2. CBC_Report.pdf (1 page)
    p2 = os.path.join(output_dir, 'CBC_Report.pdf')
    doc2 = SimpleDocTemplate(p2, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elems2 = [
        Paragraph("CENTRAL DIAGNOSTIC PATHOLOGY", title_style),
        Paragraph("Complete Blood Count (CBC) Automated Panel — Accession: CBC-2026-8812", small_style),
        Spacer(1, 10),
        Table([
            [Paragraph("<b>Patient:</b> Demo Patient", body_style), Paragraph("<b>Age:</b> 45 Y", body_style), Paragraph("<b>Date:</b> 2026-08-20", body_style)]
        ], colWidths=[200, 140, 200], style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')), ('PADDING', (0,0), (-1,-1), 4)]),
        Spacer(1, 12),
        Table([
            [Paragraph("<b>Test Name</b>", body_style), Paragraph("<b>Result</b>", body_style), Paragraph("<b>Units</b>", body_style), Paragraph("<b>Reference Range</b>", body_style)],
            [Paragraph("Hemoglobin", body_style), Paragraph("<b>10.8</b>", body_style), Paragraph("g/dL", body_style), Paragraph("12.0 – 16.0 g/dL", body_style)],
            [Paragraph("White Blood Cell Count", body_style), Paragraph("<b>6.8</b>", body_style), Paragraph("x10^3/uL", body_style), Paragraph("4.0 – 11.0 x10^3/uL", body_style)],
            [Paragraph("Red Blood Cell Count", body_style), Paragraph("<b>3.9</b>", body_style), Paragraph("x10^6/uL", body_style), Paragraph("4.0 – 5.2 x10^6/uL", body_style)],
            [Paragraph("Hematocrit", body_style), Paragraph("<b>33.0</b>", body_style), Paragraph("%", body_style), Paragraph("36.0 – 46.0 %", body_style)],
            [Paragraph("Platelets", body_style), Paragraph("<b>240</b>", body_style), Paragraph("x10^3/uL", body_style), Paragraph("150 – 450 x10^3/uL", body_style)],
        ], colWidths=[200, 70, 80, 190], style=[
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#d9e2ec')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]),
        Spacer(1, 15),
        Paragraph("Verified and released electronically.", small_style)
    ]
    doc2.build(elems2)

    # 3. Blood_Report_Jun.pdf (1 page)
    p3 = os.path.join(output_dir, 'Blood_Report_Jun.pdf')
    doc3 = SimpleDocTemplate(p3, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elems3 = [
        Paragraph("METROPATH CLINICAL LABORATORIES", title_style),
        Paragraph("Routine Follow-up Panel — Accession: MP-2026-6140", small_style),
        Spacer(1, 10),
        Table([
            [Paragraph("<b>Patient:</b> Demo Patient", body_style), Paragraph("<b>Age:</b> 45 Y", body_style), Paragraph("<b>Date:</b> 2026-06-15", body_style)]
        ], colWidths=[200, 140, 200], style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')), ('PADDING', (0,0), (-1,-1), 4)]),
        Spacer(1, 12),
        Table([
            [Paragraph("<b>Test Name</b>", body_style), Paragraph("<b>Result</b>", body_style), Paragraph("<b>Units</b>", body_style), Paragraph("<b>Reference Range</b>", body_style)],
            [Paragraph("Hemoglobin", body_style), Paragraph("<b>11.2</b>", body_style), Paragraph("g/dL", body_style), Paragraph("12.0 – 16.0 g/dL", body_style)],
            [Paragraph("Glucose", body_style), Paragraph("<b>125</b>", body_style), Paragraph("mg/dL", body_style), Paragraph("70 – 100 mg/dL", body_style)],
            [Paragraph("TSH", body_style), Paragraph("<b>3.5</b>", body_style), Paragraph("mIU/L", body_style), Paragraph("0.4 – 4.0 mIU/L", body_style)],
            [Paragraph("Total Cholesterol", body_style), Paragraph("<b>195</b>", body_style), Paragraph("mg/dL", body_style), Paragraph("125 – 200 mg/dL", body_style)],
        ], colWidths=[200, 70, 80, 190], style=[
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#d9e2ec')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]),
        Spacer(1, 15),
        Paragraph("Verified and released electronically.", small_style)
    ]
    doc3.build(elems3)

    # 4. Health_Check_Mar.pdf (1 page)
    p4 = os.path.join(output_dir, 'Health_Check_Mar.pdf')
    doc4 = SimpleDocTemplate(p4, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elems4 = [
        Paragraph("WELLNESS FIRST HEALTH CENTER", title_style),
        Paragraph("Annual Preventive Health Checkup — Date: 2026-03-10", small_style),
        Spacer(1, 10),
        Table([
            [Paragraph("<b>Patient:</b> Demo Patient", body_style), Paragraph("<b>Age:</b> 45 Y", body_style), Paragraph("<b>Date:</b> 2026-03-10", body_style)]
        ], colWidths=[200, 140, 200], style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')), ('PADDING', (0,0), (-1,-1), 4)]),
        Spacer(1, 12),
        Table([
            [Paragraph("<b>Test Name</b>", body_style), Paragraph("<b>Result</b>", body_style), Paragraph("<b>Units</b>", body_style), Paragraph("<b>Reference Range</b>", body_style)],
            [Paragraph("Hemoglobin", body_style), Paragraph("<b>11.8</b>", body_style), Paragraph("g/dL", body_style), Paragraph("12.0 – 16.0 g/dL", body_style)],
            [Paragraph("Glucose", body_style), Paragraph("<b>118</b>", body_style), Paragraph("mg/dL", body_style), Paragraph("70 – 100 mg/dL", body_style)],
            [Paragraph("TSH", body_style), Paragraph("<b>3.8</b>", body_style), Paragraph("mIU/L", body_style), Paragraph("0.4 – 4.0 mIU/L", body_style)],
        ], colWidths=[200, 70, 80, 190], style=[
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#d9e2ec')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]),
        Spacer(1, 15),
        Paragraph("Verified and released electronically.", small_style)
    ]
    doc4.build(elems4)

    print("Sample PDF reports created successfully in:", output_dir)

if __name__ == '__main__':
    create_sample_reports()
