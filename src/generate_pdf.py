import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages after page 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "MoveInSync Play Store Ratings Intelligence | Forward Deployed Engineer Assignment")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer on all pages
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, "Confidential | Prepared for MoveInSync Evaluation")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)
        self.restoreState()


def build_pdf(filename="reports/MoveInSync_Ratings_Executive_Submission.pdf"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0F172A")    # Slate 900
    brand_blue = colors.HexColor("#2563EB")       # Blue 600
    accent_dark = colors.HexColor("#1E293B")
    text_muted = colors.HexColor("#475569")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=text_muted,
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=brand_blue,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=primary_color,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=accent_dark,
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.5,
        textColor=accent_dark,
        leftIndent=12,
        spaceAfter=3
    )
    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E3A8A")
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=accent_dark
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=primary_color
    )

    story = []

    # ==================== PAGE 1: EXECUTIVE SUMMARY ====================
    story.append(Paragraph("MoveInSync Play Store Ratings Analysis & Action Plan", title_style))
    story.append(Paragraph("Forward Deployed Engineer Candidate Assignment &nbsp;|&nbsp; Target: <i>com.moveinsync.ets</i> &nbsp;|&nbsp; October 2026", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=brand_blue, spaceBefore=0, spaceAfter=10))

    story.append(Paragraph("1. The Executive Problem: The 4.64 Paradox", h1_style))
    story.append(Paragraph(
        "MoveInSync’s headline Play Store rating of <b>4.64</b> (anchored across 114,881 cumulative ratings) masks severe friction among vocal commuters. "
        "Analysis of recent written feedback reveals a <b>rolling 90-day average of only 3.81</b>, with <b>28% of reviews falling into the 1–2 star bracket</b>. "
        "Historical trajectory analysis (2014–2026) confirms this is a <b>chronic operational issue rather than a recent collapse</b>: written averages have crawled slowly from 3.45 (2022) to ~3.85 (2026), but a stubborn core of rider pain points never resolves.",
        body_style
    ))

    # Metric summary table
    kpi_data = [
        [Paragraph("Metric", table_cell_bold), Paragraph("Store Benchmark (All-Time)", table_cell_bold), Paragraph("Written Reviews (Last 90 Days)", table_cell_bold), Paragraph("Observation", table_cell_bold)],
        [Paragraph("Average Rating", table_cell), Paragraph("⭐ 4.64 (114,881 ratings)", table_cell), Paragraph("⭐ 3.81 (721 reviews)", table_cell), Paragraph("0.83 star gap between passive ratings and written feedback", table_cell)],
        [Paragraph("1–2 Star Share", table_cell), Paragraph("7.1% (8,154 total)", table_cell), Paragraph("28.4% (205 reviews)", table_cell), Paragraph("Complaints are 4x more prevalent among vocal reviewers", table_cell)],
        [Paragraph("Trajectory", table_cell), Paragraph("Slow creep upwards", table_cell), Paragraph("Flat vs prior 90d (3.82, 27%)", table_cell), Paragraph("Chronic baseline; demands root-cause engineering fixes", table_cell)]
    ]
    t_kpi = Table(kpi_data, colWidths=[95, 125, 130, 154])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Primary Complaint Drivers (Feb–Oct 2026 Classified Cohort, n = 434 Low-Star Reviews)", h1_style))
    story.append(Paragraph(
        "Through strict LLM taxonomy classification verified against ground-truth labels, the 434 negative reviews from the recent operational period fall into distinct functional clusters:",
        body_style
    ))

    breakdown_data = [
        [Paragraph("Functional Theme", table_cell_bold), Paragraph("Share of Complaints", table_cell_bold), Paragraph("Suspected Team Owner", table_cell_bold), Paragraph("Est. 90-Day Rating Lift", table_cell_bold)],
        [Paragraph("<b>App Won't Open / Crash / Lag</b>", table_cell), Paragraph("<b>15.7%</b> (Spiked to <b>31.7%</b> in last 30d)", table_cell), Paragraph("Mobile App Engineering", table_cell), Paragraph("+0.08 to +0.17", table_cell)],
        [Paragraph("<b>Login & OTP Failures</b>", table_cell), Paragraph("<b>11.7%</b> (Severe blocker; sev 2.98/5)", table_cell), Paragraph("Eng / Backend / Client IT", table_cell), Paragraph("+0.06 to +0.13", table_cell)],
        [Paragraph("<b>Route, ETA & GPS Tracking</b>", table_cell), Paragraph("<b>~15.0%</b> (Route 9.0% + GPS 6.3%)", table_cell), Paragraph("Backend Routing & Product", table_cell), Paragraph("+0.08 to +0.16", table_cell)],
        [Paragraph("<b>Booking Failures</b>", table_cell), Paragraph("7.4% (Roster sync / cutoff)", table_cell), Paragraph("Backend / Roster Systems", table_cell), Paragraph("+0.04 to +0.08", table_cell)],
        [Paragraph("<b>Cab Late / No-Show</b>", table_cell), Paragraph("5.5% (Dispatch delay)", table_cell), Paragraph("Fleet Operations", table_cell), Paragraph("+0.03 to +0.06", table_cell)],
        [Paragraph("<b>Support Unresponsive</b>", table_cell), Paragraph("5.1% (Helpdesk latency)", table_cell), Paragraph("Support Process", table_cell), Paragraph("+0.02 to +0.05", table_cell)],
        [Paragraph("<b>Vague / Other Feedback</b>", table_cell), Paragraph("17.7% ('worst app', permissions)", table_cell), Paragraph("Unclear / Multiple", table_cell), Paragraph("Baseline noise", table_cell)]
    ]
    t_breakdown = Table(breakdown_data, colWidths=[140, 140, 115, 109])
    t_breakdown.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EFF6FF")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_breakdown)
    story.append(Spacer(1, 8))

    # Callout box on Page 1
    callout_content = [
        [Paragraph("<b>Key Takeaway for Leadership:</b> Fixing the top 2 software friction points (Crashes and Login/OTP) tackles over <b>27% of all low-star complaints</b> and delivers an immediate estimated lift of <b>+0.14 to +0.30</b> on written reviews. All tickets begin with internal telemetry validation before modifying code.", callout_style)]
    ]
    t_callout = Table(callout_content, colWidths=[504])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#DBEAFE")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#3B82F6")),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_callout)

    story.append(PageBreak())

    # ==================== PAGE 2: ACTIONABLE TICKETS ====================
    story.append(Paragraph("3. Actionable Engineering Tickets: What to Do Tomorrow", h1_style))
    story.append(Paragraph("Because store reviews capture commuter-reported symptoms rather than verified server stack traces, each ticket is structured to begin with internal telemetry validation, progressing to acceptance criteria and quantifiable success metrics.", body_style))
    story.append(Spacer(1, 4))

    # Ticket 1
    story.append(Paragraph("Ticket 1: App Won’t Open / Startup Crash & ANR Triage", h2_style))
    story.append(Paragraph("<b>Owner:</b> Mobile App Engineering &nbsp;|&nbsp; <b>Share:</b> 15.7% (surged to 31.7% in last 30d) &nbsp;|&nbsp; <b>Target Lift:</b> +0.08 to +0.17", bullet_style))
    story.append(Paragraph("• <b>Evidence:</b> <i>'whenever i update this app, i am not able to open the app again, I need to uninstall and reinstall again'</i> (2026-10-09); <i>'Doesn't Open, always gets stuck... tried all options'</i> (2026-08-12, v12.17.0).", bullet_style))
    story.append(Paragraph("• <b>Hypothesis:</b> Startup migration failure or local database/cache corruption on app upgrade, clustering on specific OEM Android builds or Android 14+ background permission limits.", bullet_style))
    story.append(Paragraph("• <b>Validation Step:</b> Pull crash traces and ANR clusters from Google Play Console Android Vitals filtered by releases 12.18–12.20 and cross-tabulate against OEM hardware.", bullet_style))
    story.append(Paragraph("• <b>Proposed Action:</b> Resolve top 3 crash signatures; implement defensive try/catch around startup schema migrations; introduce staged rollouts (10% → 25% → 100%) with automated halt on crash regressions.", bullet_style))
    story.append(Paragraph("• <b>Acceptance Criteria:</b> Crash-free user sessions > 99.5% on Android Vitals; zero startup loops on app update.", bullet_style))
    story.append(Paragraph("• <b>Success Metric:</b> <code>crash_lag</code> complaint share drops from 15.7% to <b>under 8%</b> of 1–2 star reviews within 60 days.", bullet_style))
    story.append(Spacer(1, 6))

    # Ticket 2
    story.append(Paragraph("Ticket 2: Login and OTP Delivery / Session Continuity Audit", h2_style))
    story.append(Paragraph("<b>Owner:</b> App Engineering, Backend Auth & Enterprise IT &nbsp;|&nbsp; <b>Share:</b> 11.7% &nbsp;|&nbsp; <b>Target Lift:</b> +0.06 to +0.13", bullet_style))
    story.append(Paragraph("• <b>Evidence:</b> <i>'Didn't get any otp to login'</i> (2026-06-03); <i>'I am not receiving the OTP even after trying multiple times'</i> (2026-09-24, v12.19.0); <i>'email otp system don't work everyday have to login via otp'</i> (2026-06-02).", bullet_style))
    story.append(Paragraph("• <b>Hypothesis:</b> High SMS gateway drop rates on specific telecom carriers, corporate email gateway spam throttling, and overly aggressive session invalidation forcing daily re-logins.", bullet_style))
    story.append(Paragraph("• <b>Validation Step:</b> Instrument end-to-end OTP funnel (Request → Gateway Dispatched → Delivery Receipt → User Verified) segmented by SMS provider, carrier, and corporate domain.", bullet_style))
    story.append(Paragraph("• <b>Proposed Action:</b> Implement multi-gateway automatic failover (SMS Provider A → Provider B after 25s); offer instant fallback via WhatsApp/Email OTP; extend secure refresh token lifetimes with biometric unlock.", bullet_style))
    story.append(Paragraph("• <b>Acceptance Criteria:</b> P95 OTP delivery under 15 seconds; delivery rate > 98.5% across all carriers; clear user-facing error guidance when IT SSO blocks authentication.", bullet_style))
    story.append(Paragraph("• <b>Success Metric:</b> <code>login_otp</code> complaints drop to <b>under 6%</b> of 1–2 star reviews within 60 days.", bullet_style))
    story.append(Spacer(1, 6))

    # Ticket 3
    story.append(Paragraph("Ticket 3: Route Inefficiency and Live Tracking Telemetry Latency", h2_style))
    story.append(Paragraph("<b>Owner:</b> Backend Routing Engine & Product &nbsp;|&nbsp; <b>Share:</b> ~15.0% combined &nbsp;|&nbsp; <b>Target Lift:</b> +0.08 to +0.16", bullet_style))
    story.append(Paragraph("• <b>Evidence:</b> <i>'Terrible tracking, the ETA keeps increasing until the vehicle is 2-3 stops away. Then it decreases suddenly'</i> (2026-06-03); <i>'terrible routing - picks the wrong and longer route'</i> (2026-08-14).", bullet_style))
    story.append(Paragraph("• <b>Hypothesis:</b> Inconsistent GPS ping intervals from driver devices (battery saver mode), unbuffered route recalculation causing erratic ETA jumps, and sub-optimal pooling detours.", bullet_style))
    story.append(Paragraph("• <b>Validation Step:</b> Benchmark predicted ETA vs. actual GPS pickup timestamp across 1,000 real employee trips; audit driver app location ping frequency during active rides.", bullet_style))
    story.append(Paragraph("• <b>Proposed Action:</b> Display realistic ETA ranges (e.g., '8–12 mins' rather than volatile exact numbers); add transparent 'Last updated X seconds ago' status; enforce driver telematics heartbeat intervals.", bullet_style))
    story.append(Paragraph("• <b>Acceptance Criteria:</b> Mean Absolute Error (MAE) on pickup ETA under 3 minutes; driver GPS refresh rate under 10 seconds during active route legs.", bullet_style))
    story.append(Paragraph("• <b>Success Metric:</b> Combined tracking and route complaints drop to <b>under 10%</b> of negative reviews within 90 days.", bullet_style))

    story.append(PageBreak())

    # ==================== PAGE 3: METHOD & REPRODUCIBILITY ====================
    story.append(Paragraph("4. Technical Method, Validation & Tooling Note", h1_style))
    story.append(Paragraph("<i>A short summary of how I got there, which tools I used, and how this analysis is built for continuous operational execution.</i>", subtitle_style))

    story.append(Paragraph("How I Got There (Analytical Workflow)", h2_style))
    story.append(Paragraph(
        "1. <b>Full Dataset Ingestion:</b> Scraped all 24,318 historical reviews (2014 to Oct 2026) for <code>com.moveinsync.ets</code> using <code>google-play-scraper</code>. "
        "Mathematically reconciled the weighted average of the 5-star histogram (4.6389), perfectly matching the store benchmark. Stored data in an idempotent SQLite schema (<code>data/reviews.db</code>) with automated deduplication.",
        body_style
    ))
    story.append(Paragraph(
        "2. <b>Cleaning & Journey Taxonomy:</b> Filtered 3,178 eligible reviews (last 24 months, ≥3 words). Isolated 190 short 1–2 star reviews (<i>'worst app'</i>) as <code>low_no_detail</code> to prevent distorting functional themes. Designed a 19-label mutually exclusive taxonomy mapped across 9 commuter journey stages.",
        body_style
    ))
    story.append(Paragraph(
        "3. <b>LLM Classification & Schema Enforcement:</b> Classified recent reviews using an LLM via OpenRouter (<code>anthropic/claude-5.5-haiku</code>) at temperature 0 with strict Pydantic JSON schema enforcement, extracting primary theme, secondary themes, severity (1–5), suspected team owner, and exact evidence quotes.",
        body_style
    ))
    story.append(Paragraph(
        "4. <b>Ground Truth Validation:</b> Audited model classifications against an independently labeled gold benchmark (n = 27). Achieved <b>Cohen’s Kappa κ = 0.87</b> (89.0% theme agreement), <b>κ = 0.67</b> (81.0% owner agreement), and <b>100% agreement</b> on distinguishing complaints from positive feedback.",
        body_style
    ))
    story.append(Paragraph(
        "5. <b>Statistical Hypothesis Testing & Lift Simulation:</b> Tested an early hypothesis that app version 12.19.0 represented a severe performance regression. A pooled two-proportion test yielded <b>z = 1.40 (p ≈ 0.16)</b>, ruling it out as normal small-sample variance. Built a mathematical simulation modeling conservative (+0.23) and optimistic (+0.49) score lifts on the rolling 90-day cohort.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Tools & Technology Stack Used", h2_style))
    story.append(Paragraph("• <b>Data Scraping & Storage:</b> Python 3.13, <code>google-play-scraper</code>, SQLite 3 (<code>data/reviews.db</code>), CSV snapshots.", bullet_style))
    story.append(Paragraph("• <b>Data Processing & Statistics:</b> <code>pandas</code>, <code>numpy</code>, <code>scipy</code> (two-proportion z-tests, distribution weighting).", bullet_style))
    story.append(Paragraph("• <b>Classification & Validation:</b> OpenRouter API (Claude 3.5 Haiku), <code>pydantic</code> (strict schema validation), <code>scikit-learn</code> (Cohen's Kappa).", bullet_style))
    story.append(Paragraph("• <b>Interactive Dashboard:</b> <code>streamlit</code>, <code>plotly</code> (multi-view operational dashboard with cached SQL loaders).", bullet_style))
    story.append(Paragraph("• <b>Automation & CI/CD:</b> GitHub Actions (<code>.github/workflows/weekly.yml</code>), Git, PyYAML.", bullet_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Answering 'How Are Our Ratings?' Continuously", h2_style))
    story.append(Paragraph(
        "To satisfy MoveInSync's need for repeated evaluation, the repository includes a complete GitHub Actions automation workflow (<code>.github/workflows/weekly.yml</code>). "
        "Every Monday at 03:00 UTC (or on manual trigger), the pipeline automatically captures daily store score snapshots, scrapes incremental reviews, cleans text, and updates analytical outputs. "
        "It supports both a free zero-key mode and full LLM classification mode when an API key is provided.",
        body_style
    ))

    story.append(PageBreak())

    # ==================== PAGE 4: DASHBOARD SCREENSHOTS ====================
    story.append(Paragraph("5. Interactive Intelligence Dashboard", h1_style))
    story.append(Paragraph(
        "To empower product, engineering, and operations teams to interactively explore the data, I built a dedicated, local-first Streamlit dashboard (<code>app/dashboard.py</code>). "
        "It connects directly to the deduplicated SQLite database and provides real-time slicing across rolling windows, functional themes, team owners, and release versions.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Placeholders for screenshots
    ph_data = [
        [Paragraph("<b>[ SCREENSHOT PLACEHOLDER 1: Overview & KPI Trajectory ]</b><br/><br/><i>Paste screenshot showing: Store Score vs. 90-day Written Review Average, Star Distribution, and Historical Timeline (2014–2026).</i><br/><br/>", table_cell)],
    ]
    t_ph1 = Table(ph_data, colWidths=[504])
    t_ph1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94A3B8")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 32),
        ('BOTTOMPADDING', (0,0), (-1,-1), 32),
    ]))
    story.append(t_ph1)
    story.append(Spacer(1, 14))

    ph_data2 = [
        [Paragraph("<b>[ SCREENSHOT PLACEHOLDER 2: Complaint Themes, Owner Allocation & Action Backlog ]</b><br/><br/><i>Paste screenshot showing: Pareto of 1–2 star complaint themes, suspected team ownership breakdown, rating-lift simulator, and the 3 action tickets.</i><br/><br/>", table_cell)],
    ]
    t_ph2 = Table(ph_data2, colWidths=[504])
    t_ph2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94A3B8")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 32),
        ('BOTTOMPADDING', (0,0), (-1,-1), 32),
    ]))
    story.append(t_ph2)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>To launch locally:</b> <code>streamlit run app/dashboard.py</code> &nbsp;|&nbsp; <b>GitHub Repository:</b> <code>https://github.com/jhanvi-11/moveinsync-ratings</code>", subtitle_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF built successfully at {filename}")

if __name__ == "__main__":
    build_pdf()
