import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class MonochromeCanvas(canvas.Canvas):
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
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.black)
        
        # Header on pages 2..N
        if self._pageNumber > 1:
            self.drawString(54, 750, "MoveInSync Play Store Ratings & Friction Analysis | Candidate Memo")
            self.drawRightString(558, 750, "October 2026")
            self.setStrokeColor(colors.black)
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer on all pages
        self.drawString(54, 34, "MoveInSync Forward Deployed Engineer Assignment • Prepared by Jhanvi")
        self.drawRightString(558, 34, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(colors.black)
        self.setLineWidth(0.5)
        self.line(54, 44, 558, 44)
        
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

    # Pure monochrome styling
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.black,
        spaceAfter=3
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.black,
        spaceAfter=10
    )
    sec_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=colors.black,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    sub_heading = ParagraphStyle(
        'SubHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.black,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=13,
        textColor=colors.black,
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.black,
        leftIndent=12,
        spaceAfter=3
    )
    t_header = ParagraphStyle(
        'THeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.black
    )
    t_cell = ParagraphStyle(
        'TCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.black
    )

    story = []

    # =========================================================================
    # PAGE 1: CONTEXT, THE PARADOX & REAL COMPLAINT DRIVERS
    # =========================================================================
    story.append(Paragraph("Why MoveInSync's Play Store Ratings Sit Where They Do", title_style))
    story.append(Paragraph("A Technical Deep-Dive & Action Plan for Engineering | Target App: com.moveinsync.ets", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("The Reality Behind the 4.64 Headline Score", sec_heading))
    story.append(Paragraph(
        "At a surface glance, MoveInSync seems healthy with a <b>4.64 Play Store rating</b> anchored across 114,881 cumulative ratings. "
        "However, looking specifically at commuters who take the time to write text feedback reveals a completely different picture: "
        "the <b>last-90-day written review average drops to 3.81</b>, with <b>28% of reviews rated 1 or 2 stars</b>.",
        body_style
    ))
    story.append(Paragraph(
        "When I analyzed the full 12-year history (2014-2026), I found this is <b>not an overnight crash from a recent release</b>. "
        "It is a chronic, stubborn reality. Written ratings have slowly climbed from 3.45 in 2022 to ~3.85 in 2026, but the same core friction points "
        "continue to drag down everyday commuter satisfaction.",
        body_style
    ))

    # Clean Monochrome KPI Table
    kpi_data = [
        [Paragraph("Perspective", t_header), Paragraph("Store Score (Cumulative)", t_header), Paragraph("Written Reviews (Last 90 Days)", t_header), Paragraph("What It Means", t_header)],
        [Paragraph("Average Rating", t_cell), Paragraph("4.64 (114,881 ratings)", t_cell), Paragraph("3.81 (721 reviews)", t_cell), Paragraph("Vocal riders experience a 0.83-star drop vs passive raters", t_cell)],
        [Paragraph("1-2 Star Share", t_cell), Paragraph("7.1% (8,154 total)", t_cell), Paragraph("28.4% (205 reviews)", t_cell), Paragraph("Severe complaints are 4x higher among active reviewers", t_cell)],
        [Paragraph("Trajectory", t_cell), Paragraph("Creeping up gradually", t_cell), Paragraph("Flat vs prior 90d (3.82, 27%)", t_cell), Paragraph("Passive 5-star ratings hide persistent software friction", t_cell)]
    ]
    t_kpi = Table(kpi_data, colWidths=[90, 125, 135, 154])
    t_kpi.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 6))

    story.append(Paragraph("What Commuters Actually Complain About", sec_heading))
    story.append(Paragraph(
        "By classifying recent low-star reviews (Feb-Oct 2026 cohort, n = 434) using an LLM taxonomy verified against ground-truth labels, "
        "the real friction clusters clearly into a handful of functional areas:",
        body_style
    ))

    breakdown_data = [
        [Paragraph("Complaint Category", t_header), Paragraph("Share of Complaints", t_header), Paragraph("Likely Owner", t_header), Paragraph("Est. 90-Day Rating Lift", t_header)],
        [Paragraph("<b>App Won't Open / Crashes / Freezes</b>", t_cell), Paragraph("<b>15.7%</b> (Spiked to <b>31.7%</b> in last 30d)", t_cell), Paragraph("Mobile App Engineering", t_cell), Paragraph("+0.08 to +0.17", t_cell)],
        [Paragraph("<b>Login & OTP Delivery Failures</b>", t_cell), Paragraph("<b>11.7%</b> (Severe blocker; 2.98/5 sev)", t_cell), Paragraph("Backend / Enterprise IT", t_cell), Paragraph("+0.06 to +0.13", t_cell)],
        [Paragraph("<b>Inaccurate Route, ETA & GPS Tracking</b>", t_cell), Paragraph("<b>~15.0%</b> (Route 9.0% + GPS 6.3%)", t_cell), Paragraph("Backend Routing & Product", t_cell), Paragraph("+0.08 to +0.16", t_cell)],
        [Paragraph("<b>Self-Booking Failures</b>", t_cell), Paragraph("7.4% (Roster sync / cutoffs)", t_cell), Paragraph("Backend Roster Systems", t_cell), Paragraph("+0.04 to +0.08", t_cell)],
        [Paragraph("<b>Late Cab / Driver No-Show</b>", t_cell), Paragraph("5.5% (Dispatch delays)", t_cell), Paragraph("Fleet Operations", t_cell), Paragraph("+0.03 to +0.06", t_cell)],
        [Paragraph("<b>Support Helpdesk Unresponsive</b>", t_cell), Paragraph("5.1% (Ticket resolution)", t_cell), Paragraph("Support Team", t_cell), Paragraph("+0.02 to +0.05", t_cell)],
        [Paragraph("<b>Vague Frustration</b> ('worst app')", t_cell), Paragraph("17.7% (General venting)", t_cell), Paragraph("Unclassified / Noise", t_cell), Paragraph("Baseline residual", t_cell)]
    ]
    t_breakdown = Table(breakdown_data, colWidths=[140, 140, 115, 109])
    t_breakdown.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_breakdown)
    story.append(Spacer(1, 6))

    # Clean monochrome key takeaway box
    takeaway_data = [
        [Paragraph(
            "<b>Key Takeaway for Leadership:</b> Crashes and Login failures together represent <b>over 27% of all low-star reviews</b>. "
            "These are not subjective design complaints—they completely lock employees out of their work commute. "
            "Fixing these two issues alone delivers an immediate estimated lift of <b>+0.14 to +0.30</b> on written reviews.",
            body_style
        )]
    ]
    t_takeaway = Table(takeaway_data, colWidths=[504])
    t_takeaway.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_takeaway)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: WHAT TO FIX FIRST - 3 CONCRETE ENGINEERING TICKETS
    # =========================================================================
    story.append(Paragraph("Actionable Engineering Plan: What We Should Fix First", sec_heading))
    story.append(Paragraph(
        "Store reviews capture real user symptoms rather than verified server logs. Because of this, every fix below "
        "is structured like a production ticket: starting with telemetry validation, leading to concrete engineering steps, and closing with measurable targets.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # --- TICKET 1 ---
    story.append(Paragraph("Ticket 1: App Won't Open & Startup Crashes (Priority #1)", sub_heading))
    story.append(Paragraph("<b>Primary Team:</b> Mobile App Engineering | <b>Complaint Share:</b> 15.7% (spiked to 31.7% in last 30d) | <b>Expected Lift:</b> +0.08 to +0.17", bullet_style))
    story.append(Paragraph("• <b>Direct User Evidence:</b> <i>'whenever i update this app, i am not able to open the app again, I need to uninstall and reinstall again'</i> (9 Oct 2026); <i>'Doesn't Open, always gets stuck... tried all options reinstall, upgrade'</i> (12 Aug 2026, v12.17.0).", bullet_style))
    story.append(Paragraph("• <b>Working Hypothesis:</b> Corrupted local SQLite cache or broken schema migration on app update, clustering on specific Android OEM flavors (MIUI/ColorOS) or background task limits in Android 14+.", bullet_style))
    story.append(Paragraph("• <b>Validation Step:</b> Pull crash traces and ANR logs from Google Play Console Android Vitals filtered by releases 12.18-12.20 and device models.", bullet_style))
    story.append(Paragraph("• <b>What to Ship:</b> Fix top 3 crash signatures; wrap startup migrations in defensive try-catch fallbacks with local reset; enforce staged rollouts (10% -> 25% -> 100%) with automated pause on crash spikes.", bullet_style))
    story.append(Paragraph("• <b>Success Criteria:</b> Crash-free session rate > 99.5% on Android Vitals; <code>crash_lag</code> drops to <b>under 8%</b> of low-star reviews within 60 days.", bullet_style))
    story.append(Spacer(1, 5))

    # --- TICKET 2 ---
    story.append(Paragraph("Ticket 2: Login & OTP Failures / Session Dropouts (Priority #2)", sub_heading))
    story.append(Paragraph("<b>Primary Team:</b> App Eng, Backend Auth & Enterprise IT | <b>Complaint Share:</b> 11.7% | <b>Expected Lift:</b> +0.06 to +0.13", bullet_style))
    story.append(Paragraph("• <b>Direct User Evidence:</b> <i>'Didn't get any otp to login'</i> (3 Jun 2026); <i>'I am not receiving the OTP even after trying multiple times'</i> (24 Sep 2026); <i>'email otp system don't work everyday have to login via otp'</i> (2 Jun 2026).", bullet_style))
    story.append(Paragraph("• <b>Working Hypothesis:</b> SMS gateway timeouts across specific telecom carriers, corporate mail spam filtering for OTPs, and overly aggressive session invalidation forcing daily re-logins.", bullet_style))
    story.append(Paragraph("• <b>Validation Step:</b> Instrument an end-to-end OTP funnel (Request -> Gateway Sent -> Delivered -> Verified) segmented by SMS provider, carrier, and corporate email domain.", bullet_style))
    story.append(Paragraph("• <b>What to Ship:</b> Multi-gateway automatic SMS failover (switch provider if unconfirmed after 25s); add instant WhatsApp/Email backup channels; introduce biometrics to extend refresh token lifetimes safely.", bullet_style))
    story.append(Paragraph("• <b>Success Criteria:</b> P95 OTP delivery under 15 seconds; delivery success > 98.5%; <code>login_otp</code> complaints fall to <b>under 6%</b> within 60 days.", bullet_style))
    story.append(Spacer(1, 5))

    # --- TICKET 3 ---
    story.append(Paragraph("Ticket 3: Route Inefficiency & Live Tracking Jumps (Priority #3)", sub_heading))
    story.append(Paragraph("<b>Primary Team:</b> Backend Routing Engine & Product | <b>Complaint Share:</b> ~15.0% combined | <b>Expected Lift:</b> +0.08 to +0.16", bullet_style))
    story.append(Paragraph("• <b>Direct User Evidence:</b> <i>'Terrible tracking, the ETA keeps increasing until the vehicle is 2-3 stops away. Then it decreases suddenly'</i> (3 Jun 2026); <i>'terrible routing - picks the wrong and longer route'</i> (14 Aug 2026).", bullet_style))
    story.append(Paragraph("• <b>Working Hypothesis:</b> Gaps in driver phone GPS pings (battery saver throttling), unbuffered ETA recalculations causing jumping arrival estimates, and detours that feel excessive to riders.", bullet_style))
    story.append(Paragraph("• <b>Validation Step:</b> Benchmark predicted ETA against actual GPS arrival time across a sample of 1,000 live commuter trips; audit driver app location heartbeat frequency.", bullet_style))
    story.append(Paragraph("• <b>What to Ship:</b> Display confidence windows (e.g. '8-12 mins' instead of jumpy exact times); show a clear 'Last updated X secs ago' status; enforce driver GPS ping intervals during active trips.", bullet_style))
    story.append(Paragraph("• <b>Success Criteria:</b> Mean Absolute Error on arrival ETA under 3 minutes; combined route/tracking complaints drop to <b>under 10%</b> within 90 days.", bullet_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: METHODOLOGY, REPRODUCIBILITY & TOOLS USED
    # =========================================================================
    story.append(Paragraph("How I Built This & The Tools I Used", sec_heading))
    story.append(Paragraph("A transparent summary of my methodology, validation steps, and reproducibility pipeline.", subtitle_style))

    story.append(Paragraph("My Analytical Workflow", sub_heading))
    story.append(Paragraph(
        "1. <b>Full Dataset Scraping & Reconciliation:</b> I scraped all 24,318 historical reviews (2014 to Oct 2026) for <code>com.moveinsync.ets</code> using <code>google-play-scraper</code>. "
        "I verified that the weighted average of the store star histogram matched 4.6389, perfectly reconciling with the Play Store headline score. Data was stored in a local SQLite database (<code>data/reviews.db</code>) with deduplication on review ID.",
        body_style
    ))
    story.append(Paragraph(
        "2. <b>Cleaning & Taxonomy Design:</b> I filtered 3,178 eligible reviews (last 24 months, >=3 words). To prevent distortion, I isolated 190 short negative reviews (like <i>'worst app'</i>) as <code>low_no_detail</code> so they wouldn't artificially inflate specific engineering buckets. "
        "I then built a 19-label mutually exclusive taxonomy mapped across 9 commuter journey stages.",
        body_style
    ))
    story.append(Paragraph(
        "3. <b>LLM Classification with Schema Validation:</b> I classified the recent cohort using Claude 3.5 Haiku via OpenRouter at temperature 0. I used strict Pydantic schema validation to reliably extract the primary theme, secondary themes, severity (1-5), suspected team owner, and exact evidence quotes.",
        body_style
    ))
    story.append(Paragraph(
        "4. <b>Ground Truth Validation:</b> I benchmarked model outputs against an independently audited gold standard dataset (n = 27). The classifier achieved <b>Cohen’s Kappa = 0.87</b> (89.0% theme agreement), <b>= 0.67</b> (81.0% owner agreement), and <b>100% agreement</b> on distinguishing complaints from positive feedback.",
        body_style
    ))
    story.append(Paragraph(
        "5. <b>Statistical Testing & Lift Modeling:</b> An initial inspection suggested version 12.19.0 might be a severe regression. I ran a pooled two-proportion hypothesis test, which yielded <b>z = 1.40 (p approx 0.16)</b>—confirming it was within normal sample variation rather than an isolated release disaster. "
        "I then built a mathematical simulation to estimate rating lifts across conservative (+0.23) and optimistic (+0.49) resolution scenarios.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Tools Used Across the Stack", sub_heading))
    story.append(Paragraph("• <b>Data Scraping & Storage:</b> Python 3.13, <code>google-play-scraper</code>, SQLite 3, CSV snapshots.", bullet_style))
    story.append(Paragraph("• <b>Data Processing & Statistical Analysis:</b> <code>pandas</code>, <code>numpy</code>, <code>scipy</code> (hypothesis testing, weighting).", bullet_style))
    story.append(Paragraph("• <b>Classification & Validation:</b> OpenRouter API (Claude 3.5 Haiku), <code>pydantic</code>, <code>scikit-learn</code> (Cohen's Kappa).", bullet_style))
    story.append(Paragraph("• <b>Interactive Dashboard:</b> <code>streamlit</code>, <code>plotly</code> (multi-view operational interface with cached loaders).", bullet_style))
    story.append(Paragraph("• <b>Automation & CI/CD:</b> GitHub Actions (<code>.github/workflows/weekly.yml</code>), Git, PyYAML.", bullet_style))

    story.append(Spacer(1, 5))
    story.append(Paragraph("Answering 'How Are Our Ratings?' on a Regular Basis", sub_heading))
    story.append(Paragraph(
        "Because this is an ongoing question rather than a one-time exercise, I automated the entire pipeline with a GitHub Actions workflow (<code>weekly.yml</code>). "
        "Every Monday at 03:00 UTC (or on manual trigger), it captures daily store snapshots, scrapes new reviews, cleans text, and updates analytical tables. "
        "It supports both a free, zero-key baseline mode and an automated LLM classification mode whenever an API key is supplied.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: DASHBOARD & SUBMISSION DETAILS (CLEAN BLANK PAGE FOR SCREENSHOTS)
    # =========================================================================
    story.append(Paragraph("Interactive Ratings Intelligence Dashboard", sec_heading))
    story.append(Paragraph(
        "To allow product managers, engineers, and leadership to slice and inspect the data firsthand, "
        "I built a clean, read-only Streamlit dashboard (<code>app/dashboard.py</code>). "
        "It loads directly from the local SQLite database and provides instant visibility into rolling windows, friction trends, and the engineering backlog.",
        body_style
    ))
    story.append(Spacer(1, 8))

    meta_table_data = [
        [Paragraph("Repository URL", t_header), Paragraph("https://github.com/jhanvi-11/moveinsync-ratings", t_cell)],
        [Paragraph("Dashboard Command", t_header), Paragraph("streamlit run app/dashboard.py", t_cell)],
        [Paragraph("Core Views", t_header), Paragraph("1. Overview & Rolling Timeline (2014-2026)<br/>2. Complaint Taxonomy Pareto & Suspected Ownership<br/>3. Rating Lift Simulator & Prioritized Action Tickets", t_cell)],
        [Paragraph("Data Storage", t_header), Paragraph("Local SQLite (data/reviews.db) with 24,318 deduplicated reviews", t_cell)]
    ]
    t_meta = Table(meta_table_data, colWidths=[120, 384])
    t_meta.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Dashboard Visual Walkthrough", sub_heading))
    story.append(Paragraph(
        "The space below is reserved for inserting screenshots of the local Streamlit dashboard (Overview Timeline and Complaint/Backlog views) prior to final distribution.",
        body_style
    ))

    doc.build(story, canvasmaker=MonochromeCanvas)
    print(f"Monochrome clean PDF successfully created at {filename}")


if __name__ == "__main__":
    build_pdf()
