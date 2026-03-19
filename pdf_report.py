from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# ── Colour palette matching the UI ──
GREEN  = colors.HexColor('#00cc7a')
DARK   = colors.HexColor('#0b120e')
GRAY   = colors.HexColor('#4a5568')
LIGHT  = colors.HexColor('#f7fafc')
RED    = colors.HexColor('#ff5c5c')
AMBER  = colors.HexColor('#f5a623')


def generate_scan_report(scan, treatment: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f'AGRI-PATHogen Report — {scan.disease}',
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', fontSize=22, textColor=DARK,
                                 fontName='Helvetica-Bold', spaceAfter=4, alignment=TA_LEFT)
    sub_style   = ParagraphStyle('sub',   fontSize=11, textColor=GRAY,
                                 fontName='Helvetica', spaceAfter=2)
    label_style = ParagraphStyle('label', fontSize=9, textColor=GRAY,
                                 fontName='Helvetica', spaceAfter=2, spaceBefore=12,
                                 textTransform='uppercase')
    value_style = ParagraphStyle('value', fontSize=13, textColor=DARK,
                                 fontName='Helvetica-Bold', spaceAfter=4)
    body_style  = ParagraphStyle('body',  fontSize=11, textColor=DARK,
                                 fontName='Helvetica', spaceAfter=6, leading=16)

    severity_color = {'high': RED, 'medium': AMBER, 'low': GREEN}.get(
        treatment.get('severity', 'medium'), GRAY)

    elements = []

    # Header bar
    header_data = [[
        Paragraph('🌿 AGRI-PATHogen AI', ParagraphStyle('h', fontSize=16,
                  textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph('Diagnostic Report', ParagraphStyle('hr', fontSize=11,
                  textColor=colors.white, fontName='Helvetica', alignment=1)),
    ]]
    header_table = Table(header_data, colWidths=[12*cm, 5*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING',    (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [8]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.5*cm))

    # Disease name
    elements.append(Paragraph('Diagnosis', label_style))
    elements.append(Paragraph(scan.disease, title_style))

    # Severity badge
    sev_text = treatment.get('severity', 'medium').upper()
    sev_data = [[Paragraph(f'● {sev_text} SEVERITY',
                           ParagraphStyle('sev', fontSize=10, textColor=severity_color,
                                         fontName='Helvetica-Bold'))]]
    sev_table = Table(sev_data, colWidths=[4*cm])
    sev_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
        ('ROUNDEDCORNERS', [6]),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(sev_table)
    elements.append(Spacer(1, 0.3*cm))

    # Scan metadata table
    meta = [
        ['Crop',        scan.crop],
        ['Confidence',  f'{scan.confidence:.1f}%'],
        ['Scanned at',  scan.scanned_at.strftime('%d %B %Y at %H:%M')],
        ['Note',        scan.note or '—'],
    ]
    meta_table = Table(meta, colWidths=[4*cm, 13*cm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME',    (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',    (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',    (0, 0), (-1, -1), 11),
        ('TEXTCOLOR',   (0, 0), (0, -1), GRAY),
        ('TEXTCOLOR',   (1, 0), (1, -1), DARK),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [LIGHT, colors.white]),
        ('PADDING',     (0, 0), (-1, -1), 8),
        ('GRID',        (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e2e8f0')))
    elements.append(Spacer(1, 0.3*cm))

    # Treatment section
    elements.append(Paragraph('Treatment & Action Plan', ParagraphStyle(
        'sec', fontSize=14, fontName='Helvetica-Bold', textColor=DARK, spaceAfter=10)))

    for heading, key, icon in [
        ('Immediate Action', 'immediate',  '💊'),
        ('Prevention',       'prevention', '🌱'),
        ('Notes',            'notes',      '📋'),
    ]:
        elements.append(Paragraph(f'{icon}  {heading}', label_style))
        elements.append(Paragraph(treatment.get(key, '—'), body_style))

    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0')))
    elements.append(Spacer(1, 0.2*cm))

    # Footer
    elements.append(Paragraph(
        'Generated by AGRI-PATHogen AI  ·  For informational purposes only  ·  Consult a local agronomist for field decisions.',
        ParagraphStyle('foot', fontSize=8, textColor=GRAY, fontName='Helvetica', alignment=TA_CENTER)
    ))

    doc.build(elements)
    return buf.getvalue()