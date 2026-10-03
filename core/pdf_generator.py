"""
core/pdf_generator.py
PDF Career Report Generator using ReportLab.

Generates a professional, formatted PDF career pathway report
for each student. Implements Phase 2, Use Case UC-05.

ReportLab is chosen because:
1. It is open-source and runs entirely offline — no API needed.
2. It produces production-quality PDFs programmatically.
3. It is widely used in academic and enterprise Django projects.
"""

import io
from datetime import date
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Colour palette ────────────────────────────────────────────────
DARK_BLUE   = colors.HexColor('#1a3c5e')
MID_BLUE    = colors.HexColor('#2563eb')
LIGHT_BLUE  = colors.HexColor('#dbeafe')
GREEN       = colors.HexColor('#16a34a')
LIGHT_GREEN = colors.HexColor('#dcfce7')
ORANGE      = colors.HexColor('#ea580c')
LIGHT_ORANGE= colors.HexColor('#ffedd5')
RED         = colors.HexColor('#dc2626')
LIGHT_RED   = colors.HexColor('#fee2e2')
GREY_LIGHT  = colors.HexColor('#f1f5f9')
GREY_MED    = colors.HexColor('#94a3b8')
GREY_DARK   = colors.HexColor('#334155')
WHITE       = colors.white
BLACK       = colors.black

DEMAND_COLORS = {
    'High':      (GREEN,       LIGHT_GREEN),
    'Moderate':  (MID_BLUE,    LIGHT_BLUE),
    'Low':       (GREY_MED,    GREY_LIGHT),
    'Saturated': (RED,         LIGHT_RED),
}


def _get_styles():
    base   = getSampleStyleSheet()
    styles = {}

    styles['title'] = ParagraphStyle(
        'Title', fontSize=22, textColor=WHITE,
        alignment=TA_CENTER, fontName='Helvetica-Bold',
        spaceAfter=4, leading=26
    )
    styles['subtitle'] = ParagraphStyle(
        'Subtitle', fontSize=11, textColor=LIGHT_BLUE,
        alignment=TA_CENTER, fontName='Helvetica', spaceAfter=2
    )
    styles['section_header'] = ParagraphStyle(
        'SectionHeader', fontSize=13, textColor=DARK_BLUE,
        fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=6,
        borderPad=4
    )
    styles['cluster_title'] = ParagraphStyle(
        'ClusterTitle', fontSize=12, textColor=WHITE,
        fontName='Helvetica-Bold', alignment=TA_LEFT, leading=16
    )
    styles['body'] = ParagraphStyle(
        'Body', fontSize=9, textColor=GREY_DARK,
        fontName='Helvetica', spaceAfter=4, leading=14
    )
    styles['small'] = ParagraphStyle(
        'Small', fontSize=8, textColor=GREY_MED,
        fontName='Helvetica', spaceAfter=2
    )
    styles['bold'] = ParagraphStyle(
        'Bold', fontSize=9, textColor=GREY_DARK,
        fontName='Helvetica-Bold', spaceAfter=4
    )
    styles['center'] = ParagraphStyle(
        'Center', fontSize=9, textColor=GREY_DARK,
        alignment=TA_CENTER, fontName='Helvetica'
    )
    styles['cell'] = ParagraphStyle(
        'Cell', fontSize=7.5, textColor=GREY_DARK,
        fontName='Helvetica', leading=9.5
    )
    styles['cell_lm'] = ParagraphStyle(
        'CellLM', fontSize=8, textColor=GREY_DARK,
        fontName='Helvetica', leading=10
    )
    styles['footer'] = ParagraphStyle(
        'Footer', fontSize=7, textColor=GREY_MED,
        alignment=TA_CENTER, fontName='Helvetica'
    )
    return styles


def _p(text, style):
    """Paragraph with escaped text, so '&' and '<' in data can't break markup."""
    return Paragraph(escape(str(text)), style)


def _score_bar(score, width):
    """Horizontal bar drawn as a two-cell table (Helvetica has no block glyphs)."""
    filled = max(0.0, min(float(score), 100.0)) / 100.0 * width
    if filled < 1:
        widths, fills = [width], [GREY_LIGHT]
    elif filled > width - 1:
        widths, fills = [width], [MID_BLUE]
    else:
        widths, fills = [filled, width - filled], [MID_BLUE, GREY_LIGHT]
    bar = Table([[''] * len(widths)], colWidths=widths, rowHeights=[7])
    bar.setStyle(TableStyle(
        [('BACKGROUND', (i, 0), (i, 0), c) for i, c in enumerate(fills)] +
        [('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
         ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]
    ))
    return bar


def generate_career_report_pdf(user, engine_result):
    """
    Build and return a BytesIO buffer containing the PDF report.

    Args:
        user:          StudentUser instance
        engine_result: dict returned by generate_recommendations()

    Returns:
        io.BytesIO: PDF bytes ready for HTTP response
    """
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm,
        title=f"Career Pathway Report — {user.get_full_name()}",
        author="Career Pathway Analysis System"
    )

    styles   = _get_styles()
    story    = []
    W        = 17.4 * cm  # usable page width

    # ── HEADER BANNER ─────────────────────────────────────────────
    header_data = [[
        Paragraph("CAREER PATHWAY ANALYSIS REPORT", styles['title']),
    ]]
    header_table = Table(header_data, colWidths=[W])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK_BLUE),
        ('TOPPADDING',    (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    sub_data = [[
        Paragraph("Web-Based Career Pathway Analysis System | Kenya", styles['subtitle'])
    ]]
    sub_table = Table(sub_data, colWidths=[W])
    sub_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), MID_BLUE),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 14))

    # ── STUDENT INFORMATION ───────────────────────────────────────
    story.append(Paragraph("STUDENT INFORMATION", styles['section_header']))
    story.append(HRFlowable(width=W, thickness=1, color=MID_BLUE))
    story.append(Spacer(1, 8))

    info_data = [
        ['Full Name:',      user.get_full_name(),
         'Date Generated:', date.today().strftime('%d %B %Y')],
        ['Email:',          user.email,
         'School:',         user.school_name or 'Not specified'],
        ['Curriculum:',     user.curriculum,
         'Year Completed:', str(user.year_completed) if user.year_completed else 'N/A'],
        ['County:',         user.county or 'Not specified',
         'Gender:',         user.gender or 'Not specified'],
    ]
    info_table = Table(info_data, colWidths=[3.0*cm, 5.5*cm, 3.2*cm, 5.7*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME',    (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',    (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 8.5),
        ('TEXTCOLOR',   (0,0), (0,-1), DARK_BLUE),
        ('TEXTCOLOR',   (2,0), (2,-1), DARK_BLUE),
        ('TEXTCOLOR',   (1,0), (1,-1), GREY_DARK),
        ('TEXTCOLOR',   (3,0), (3,-1), GREY_DARK),
        ('BACKGROUND',  (0,0), (-1,-1), GREY_LIGHT),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, GREY_LIGHT]),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.3, GREY_MED),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    # ── RIASEC INTEREST PROFILE ───────────────────────────────────
    story.append(Paragraph("YOUR INTEREST PROFILE (RIASEC)", styles['section_header']))
    story.append(HRFlowable(width=W, thickness=1, color=MID_BLUE))
    story.append(Spacer(1, 8))

    riasec_scores = engine_result.get('riasec_scores', {})
    dominant_types = engine_result.get('dominant_types', '')

    riasec_rows = [['Type', 'Category', 'Score (/100)', 'Visual Bar']]
    type_names = {
        'R': 'Realistic', 'I': 'Investigative', 'A': 'Artistic',
        'S': 'Social', 'E': 'Enterprising', 'C': 'Conventional'
    }
    dominant_list = dominant_types.split(',') if dominant_types else []
    dominant_rows = []
    for row_idx, rtype in enumerate(['R', 'I', 'A', 'S', 'E', 'C'], start=1):
        score     = riasec_scores.get(rtype, 0)
        is_dom    = rtype in dominant_list
        label     = f"{rtype} *" if is_dom else rtype
        if is_dom:
            dominant_rows.append(row_idx)
        riasec_rows.append([label, type_names[rtype], f"{score:.1f}", _score_bar(score, 7.6*cm)])

    riasec_table = Table(riasec_rows, colWidths=[1.8*cm, 4.0*cm, 3.2*cm, 8.4*cm])
    riasec_table.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), DARK_BLUE),
        ('TEXTCOLOR',   (0,0), (-1,0), WHITE),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GREY_LIGHT]),
        ('GRID',        (0,0), (-1,-1), 0.3, GREY_MED),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
    ] + [('FONTNAME', (0,r), (2,r), 'Helvetica-Bold') for r in dominant_rows]))
    story.append(riasec_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"<b>Dominant Interest Types (*):</b> {escape(dominant_types)} — "
        "These types most strongly shape your career suitability scores.",
        styles['small']
    ))
    story.append(Spacer(1, 16))

    # ── TOP 3 CAREER CLUSTER RECOMMENDATIONS ─────────────────────
    story.append(Paragraph("YOUR TOP 3 CAREER PATHWAY RECOMMENDATIONS", styles['section_header']))
    story.append(HRFlowable(width=W, thickness=1, color=MID_BLUE))
    story.append(Spacer(1, 10))

    top_clusters = engine_result.get('top_clusters', [])
    rank_labels  = ['#1 BEST MATCH', '#2 STRONG MATCH', '#3 GOOD MATCH']
    rank_colors  = [GREEN, MID_BLUE, DARK_BLUE]

    for idx, cluster_data in enumerate(top_clusters[:len(rank_labels)]):
        cluster = cluster_data['cluster']
        scores  = cluster_data['scores']
        courses = cluster_data['courses']
        labor   = cluster_data['labor_market']

        elements = []

        # Cluster title banner
        title_data = [[
            _p(f"{rank_labels[idx]}: {cluster.name.upper()}", styles['cluster_title'])
        ]]
        title_table = Table(title_data, colWidths=[W])
        title_table.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), rank_colors[idx]),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ]))
        elements.append(title_table)
        elements.append(Spacer(1, 4))

        # Score breakdown
        score_data = [
            ['Academic Score', 'Interest Score', 'Combined Score', 'Labor Demand'],
            [
                f"{scores['academic_score']:.1f} / 100",
                f"{scores['interest_score']:.1f} / 100",
                f"{scores['combined_score']:.1f} / 100",
                cluster.labor_demand,
            ]
        ]
        demand_c, demand_bg = DEMAND_COLORS.get(cluster.labor_demand, (GREY_MED, GREY_LIGHT))
        score_table = Table(score_data, colWidths=[W/4]*4)
        score_table.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,0), LIGHT_BLUE),
            ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0,0), (-1,-1), 8.5),
            ('ALIGN',       (0,0), (-1,-1), 'CENTER'),
            ('GRID',        (0,0), (-1,-1), 0.3, GREY_MED),
            ('TOPPADDING',  (0,0), (-1,-1), 5),
            ('BOTTOMPADDING',(0,0),(-1,-1), 5),
            ('BACKGROUND',  (3,1), (3,1), demand_bg),
            ('TEXTCOLOR',   (3,1), (3,1), demand_c),
            ('FONTNAME',    (3,1), (3,1), 'Helvetica-Bold'),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 6))

        # Description
        elements.append(_p(cluster.description, styles['body']))

        # Recommended courses
        if courses:
            elements.append(Paragraph("<b>Recommended Courses:</b>", styles['bold']))
            course_rows = [['Course Name', 'Type', 'Duration', 'Min. Cluster Pts', 'Institutions']]
            for course in courses[:5]:
                inst_names = ', '.join([i['name'] for i in course['institutions'][:3]])
                if not inst_names:
                    inst_names = 'Various institutions'
                course_rows.append([
                    _p(course['name'], styles['cell']),
                    _p(course['type'], styles['cell']),
                    f"{course['duration']} yrs",
                    str(course['min_pts']),
                    _p(inst_names, styles['cell']),
                ])
            c_table = Table(course_rows, colWidths=[4.5*cm, 2.5*cm, 1.8*cm, 2.2*cm, 6.4*cm])
            c_table.setStyle(TableStyle([
                ('BACKGROUND',  (0,0), (-1,0), GREY_DARK),
                ('TEXTCOLOR',   (0,0), (-1,0), WHITE),
                ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',    (0,0), (-1,-1), 7.5),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GREY_LIGHT]),
                ('GRID',        (0,0), (-1,-1), 0.2, GREY_MED),
                ('TOPPADDING',  (0,0), (-1,-1), 3),
                ('BOTTOMPADDING',(0,0),(-1,-1), 3),
                ('LEFTPADDING', (0,0), (-1,-1), 4),
                ('VALIGN',      (0,0), (-1,-1), 'TOP'),
            ]))
            elements.append(c_table)
            elements.append(Spacer(1, 6))

        # Labor market
        if labor:
            sal_text = (f"KES {labor['salary_min']:,} – {labor['salary_max']:,} / month")
            employers = ', '.join(labor['employers'][:5]) if labor['employers'] else 'Various'
            lm_data = [
                ['Labor Market Insights', ''],
                ['Monthly Salary Range:', sal_text],
                ['Growth Outlook:',       _p(labor['growth_outlook'], styles['cell_lm'])],
                ['Key Employers:',        _p(employers, styles['cell_lm'])],
                ['In-Demand Skills:',     _p(labor.get('in_demand_skills') or 'N/A', styles['cell_lm'])],
            ]
            if labor.get('saturation_note'):
                lm_data.append(['Warning:', _p(labor['saturation_note'], styles['cell_lm'])])

            lm_table = Table(lm_data, colWidths=[4.0*cm, 13.4*cm])
            lm_table.setStyle(TableStyle([
                ('SPAN',        (0,0), (1,0)),
                ('BACKGROUND',  (0,0), (1,0), LIGHT_BLUE),
                ('FONTNAME',    (0,0), (1,0), 'Helvetica-Bold'),
                ('FONTNAME',    (0,1), (0,-1), 'Helvetica-Bold'),
                ('FONTSIZE',    (0,0), (-1,-1), 8),
                ('TEXTCOLOR',   (0,1), (0,-1), DARK_BLUE),
                ('GRID',        (0,0), (-1,-1), 0.2, GREY_MED),
                ('TOPPADDING',  (0,0), (-1,-1), 4),
                ('BOTTOMPADDING',(0,0),(-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GREY_LIGHT]),
                ('VALIGN',      (0,0), (-1,-1), 'TOP'),
            ]))
            elements.append(lm_table)

        elements.append(Spacer(1, 12))
        story.append(KeepTogether(elements))

    # ── FULL CLUSTER RANKING TABLE ────────────────────────────────
    story.append(Paragraph("FULL CAREER CLUSTER RANKING", styles['section_header']))
    story.append(HRFlowable(width=W, thickness=1, color=MID_BLUE))
    story.append(Spacer(1, 8))

    full_ranking = engine_result.get('full_ranking', [])
    rank_rows    = [['Rank', 'Career Cluster', 'Academic Score', 'Interest Score',
                     'Combined Score', 'Labor Demand']]
    for item in full_ranking:
        rank_rows.append([
            f"#{item['rank']}",
            item['cluster_name'],
            f"{item['academic_score']:.1f}",
            f"{item['interest_score']:.1f}",
            f"{item['combined_score']:.1f}",
            item['labor_demand'],
        ])
    rank_table = Table(rank_rows, colWidths=[1.2*cm, 5.6*cm, 2.65*cm, 2.65*cm, 2.65*cm, 2.65*cm])
    rank_table.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), DARK_BLUE),
        ('TEXTCOLOR',   (0,0), (-1,0), WHITE),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 8),
        ('ALIGN',       (2,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GREY_LIGHT]),
        ('GRID',        (0,0), (-1,-1), 0.3, GREY_MED),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND',  (0,1), (-1,3), LIGHT_GREEN),   # top 3 highlighted
    ]))
    story.append(rank_table)
    story.append(Spacer(1, 20))

    # ── METHODOLOGY NOTE ─────────────────────────────────────────
    story.append(Paragraph("ABOUT THIS ANALYSIS", styles['section_header']))
    story.append(HRFlowable(width=W, thickness=1, color=MID_BLUE))
    story.append(Spacer(1, 6))
    methodology_text = (
        "This career pathway analysis was generated using a rule-based weighted scoring model "
        "that integrates your KCSE academic performance (60% weight) with your RIASEC interest "
        "profile (40% weight). Academic scores are computed by matching your subject grades "
        "against subject-cluster relevance weights derived from KUCCPS cluster requirements. "
        "Interest scores are derived from your responses to 30 standardized RIASEC questions "
        "mapped to career cluster affinities. Labor-market data is sourced from KNBS and KEPSA "
        "reports. Saturated career clusters receive a -5 point penalty to encourage informed "
        "course selection. Recommendations should be used alongside formal career counseling."
    )
    story.append(Paragraph(methodology_text, styles['body']))
    story.append(Spacer(1, 20))

    # ── FOOTER ───────────────────────────────────────────────────
    footer_text = (
        f"Generated by Career Pathway Analysis System | {date.today().strftime('%d %B %Y')} | "
        "For: Secondary School Graduates in Kenya | "
        "Data Sources: KUCCPS, TVETA, KNBS, KEPSA"
    )
    story.append(HRFlowable(width=W, thickness=0.5, color=GREY_MED))
    story.append(Spacer(1, 4))
    story.append(Paragraph(footer_text, styles['footer']))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
