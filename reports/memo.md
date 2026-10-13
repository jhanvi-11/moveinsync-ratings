# MoveInSync Play Store Ratings: Recommendation Memo

**Date**: 13 October 2026  
**Scope**: MoveInSync employee app (`com.moveinsync.ets`)  

---

## The Answer in One Minute

### What is happening
The public store rating is **4.64 from 114,881 ratings** (85.5% are 5-star, 7.1% are 1-2 star). People who take the time to write reviews are far less happy: the **last-90-day written-review average is 3.81**, with **28% rated at 1-2 stars**. This is essentially flat against the prior 90 days (3.82 average, 27% low-star). 

This is a **chronic pattern**, not a sudden collapse: the written average has crept up gradually from 3.45 in 2022 to 3.85 in 2026. Because written reviews naturally skew toward negative feedback, these figures describe vocal reviewers rather than the entire passive user base.

### Why
Among **434 classified 1-2 star reviews** from the last ~8 months (February to October 2026), the primary complaint drivers are:

| Cause | Share of 1-2 Star Reviews |
| :--- | :--- |
| **App will not open / crashes / lags** | **15.7%** |
| **Login and OTP failures** | **11.7%** |
| **Wrong route, bad ETA, inaccurate live tracking** | **~15.0%** (9.0% + 6.3%) |
| **Bookings failing** | **7.4%** |
| **Cab late or no-show** | **5.5%** |
| **Support unresponsive** | **5.1%** |
| **Vague or unclassifiable** (*"worst app"*, permissions) | **17.7%** |

- **Crash and login problems together account for ~27% of complaints.** 
- **Crash complaints rose to 31.7% of 1-2 star reviews in the last 30 days** compared to 15.8% in the prior 90 days — the single theme showing a sharp recent surge (*note: small monthly sample, treat as a strong directional signal*).
- **Suspected ownership breakdown**:
  - **48%** App Engineering
  - **12%** Backend Routing
  - **8%** Fleet Operations
  - **5%** Support
  - **2%** Client Policy
  - **26%** Unclear / Vague  
  *(Note: Owners reflect reported user experience, not verified backend root causes).*

### What happens tomorrow
Three targeted technical investigations, each beginning with internal telemetry MoveInSync already holds and ending in an operational fix:
1. **Crash & Won't-Open Triage**: Analyze Google Play Console Android Vitals and crash telemetry by device and OS.
2. **OTP & Login Delivery Audit**: Audit delivery success rates across SMS gateways, email providers, and corporate SSO paths.
3. **ETA & Route Accuracy Audit**: Benchmark predicted vs. actual pickup timings on a representative sample of real trips.

*Booking failures represent the fourth priority and should be tackled as soon as engineering capacity permits.*

---

## Evidence and Actionable Tickets

Fixes are conditional on internal validation, as app store reviews report user-side symptoms rather than confirmed server root causes.

### Ticket 1: App won't open or crashes (Engineering)
- **Problem**: 15.7% of classified 1-2 star reviews (68 of 434). Last-30-day share surged to 31.7%.
- **Evidence**:
  - *2026-10-09*: "whenever i update this app, i am not able to open the app again, I need to uninstall and reinstall again. facing this issue since 3 months"
  - *2026-08-12 (v12.17.0)*: "Doesn't Open, always gets stuck. tried all options reinstall, upgrade, different networks."
  - *2026-06-02 (v12.13.0)*: "sometimes the app is not working plz fix the bug"
- **Hypothesis (unverified)**: Startup or update-path failure, likely clustering on specific OEM devices, custom Android builds, or corrupted local cache during version migration.
- **Validation step**: Pull crash and ANR rates from Play Console by app version, Android OS version, and device model. Verify if crash spikes correlate with recent releases (`12.19.0`, `12.20.0`).
- **Proposed change**: Ship targeted hotfixes for top 3 crash/ANR clusters. Implement staged rollouts (10% -> 25% -> 100%) with automated halt thresholds on ANR/crash regressions.
- **Acceptance criteria**: Top 3 crash clusters resolved in production; crash-free user rate target established (>99.5%).
- **Effort & Impact**: Medium effort, High impact. Estimated lift on the 90-day written review average: **+0.08 to +0.17**.
- **Success metric**: `crash_lag` drops from ~16% to **under 8%** of 1-2 star reviews within 60 days.

---

### Ticket 2: Login and OTP failures (Engineering, Backend, Client IT)
- **Problem**: 11.7% of 1-2 star reviews (52 of 434), average severity 2.98 / 5. Completely blocks the user journey.
- **Evidence**:
  - *2026-06-03 (v12.13.0)*: "Didn't get any otp to login"
  - *2026-09-24 (v12.19.0)*: "I am not receiving the OTP even after trying multiple times"
  - *2026-06-02 (v12.13.0)*: "email otp system don't work everyday have to login via otp"
- **Hypothesis (unverified)**: SMS gateway delivery latency/dropouts, email OTP spam filtering, aggressive session invalidation forcing daily re-logins, and corporate SSO token mismatches.
- **Validation step**: Measure OTP send-to-verify conversion rates by channel (SMS vs. Email) and telecom provider; audit token refresh policies and SSO failure logs by corporate domain.
- **Proposed change**: Introduce multi-gateway SMS failover; offer alternate fallback channels (WhatsApp / Email resend after 30s); replace blank white screens with explicit error states. *(Session token lifetime adjustments require security sign-off).*
- **Acceptance criteria**: End-to-end OTP delivery tracked per provider with SLAs; failure states clearly inform users of next steps.
- **Effort & Impact**: Medium effort, High impact. Estimated lift: **+0.06 to +0.13**.
- **Success metric**: `login_otp` falls to **under 6%** of 1-2 star reviews within 60 days.

---

### Ticket 3: Route, ETA, and live-tracking accuracy (Backend Routing, Product)
- **Problem**: `wrong_route_eta` (9.0%) + `live_tracking_gps` (6.3%): 66 of 434 combined complaints.
- **Evidence**:
  - *2026-06-03 (v12.9.4)*: "Terrible tracking, the ETA keeps increasing until the vehicle is 2-3 stops away. Then it decreases suddenly."
  - *2026-08-14 (v12.16.0)*: "This has terrible routing - picks the wrong and longer route"
- **Hypothesis (unverified)**: Map service telematics latency, routing engine sequencing inefficiency (excessive pool detours), or unsanctioned driver route deviations.
- **Validation step**: Compare predicted ETA vs. actual GPS arrival on a sample of 1,000 real trips; audit vehicle telemetry ping intervals during active pickups.
- **Proposed change**: Implement an ETA confidence range (e.g., "7–10 mins" instead of static "5 mins"); show a transparent "Last updated Xs ago" indicator on map view.
- **Acceptance criteria**: Baseline ETA error quantified and product variance threshold agreed upon.
- **Effort & Impact**: High effort, Medium-to-High impact. Estimated lift: **+0.08 to +0.16**.
- **Success metric**: Combined tracking and route complaints drop to **under 10%** of 1-2 star reviews within 90 days.

---

### Next in Queue: Booking Failures
- **Problem**: 7.4% of 1-2 star reviews, average severity 2.94 / 5. Estimated lift: **+0.04 to +0.08**.
- **Context**: As one commuter highlighted: *"I have not been able to book for pickup for 2 weeks. I have reported the issue, but no feedback"*. Self-booking is the foundation of the commute experience; resolve roster sync and booking cut-off bugs immediately after Tickets 1–3.

---

## Expected Impact & Mathematical Lift

Lift estimates apply to the **90-day written-review average (3.81)**:
- **Conservative case**: Assumes affected low-star reviews improve to 3 stars.
- **Optimistic case**: Assumes affected reviews improve to match the non-complaint average (~4.3 stars).
- **Combined impact**: Remedying the top 3 themes yields a projected lift of **+0.20 to +0.40** on the written review average.
- **Store rating context**: Because public written reviews represent only ~20% of total ratings, and the cumulative score (4.64) is anchored by 114,881 ratings, the overall store score will move incrementally. The rolling 90-day window provides the accurate measure of progress.

---

## Action Plan by Horizon

### Quick Wins (Weeks 1–2)
1. **Theme-Specific Developer Replies**: The team already replies to **54.6% of 1-2 star reviews** with a fast median response time of **0.9 days**. However, generic templates redirecting riders to support emails or facilities desks provide little value. Replace boilerplate with targeted self-help paths (e.g., OTP troubleshooting, reinstall advice for update freezes).
2. **Neutral, Unbiased Rating Prompt**: Trigger the store rating prompt solely after a successful trip completion. Ensure it is easily skippable, offered to all riders, and paired with an in-app feedback channel for issues. Never gate store reviews based on sentiment.
3. **Audit App Permissions**: Investigate the subset of complaints citing invasive or repetitive permission requests to ensure only necessary runtime location access is requested.

### Mid-Term (Months 1–2)
- Execute Tickets 1, 2, and 3 validation steps, deploy production fixes, and address booking failures.

### Structural Governance (Ongoing)
- **Unified Weekly Triage**: Establish a joint weekly triage linking Play Store review themes, customer care tickets, and transport desk operational incidents to a single prioritization backlog with assigned engineering and ops owners.

---

## What NOT to Do (Anti-Patterns)
- ❌ **Do not roll back or redesign the UI**: `ui_confusion` is only 5.3% and `update_issue` is only 1.6% of complaints.
- ❌ **Do not sentiment-gate the rating prompt**: Filtering unhappy users away from Google Play violates store guidelines and blinds the team to genuine bugs.
- ❌ **Do not declare version 12.19.0 a confirmed regression**: While 12.19.0 had a lower average (2.66, n=53) and 34% negative reviews vs. 27% historically, a two-proportion test yields **z = 1.40 (not statistically significant)**.
- ❌ **Do not attempt to solve operational fleet issues in client app code**: Driver no-shows and vehicle cleanliness demand vendor SLA enforcement, not mobile UI adjustments.

---

## The Repeatable Intelligence Engine
Whenever leadership asks *"How are our Play Store ratings trending?"*, this repository provides the automated answer:
- [`src/baseline.py`](file:///d:/moveinsync-ratings/src/baseline.py): Captures public ratings and histogram snapshots.
- [`src/scrape.py`](file:///d:/moveinsync-ratings/src/scrape.py): Pulls incoming reviews incrementally.
- [`src/clean.py`](file:///d:/moveinsync-ratings/src/clean.py): Filters and normalizes text and languages.
- [`src/classify.py`](file:///d:/moveinsync-ratings/src/classify.py): Classifies complaints using the validated 19-label taxonomy.
- [`src/analyze.py`](file:///d:/moveinsync-ratings/src/analyze.py): Produces weekly cohort distributions, suspected ownership splits, and rating-lift models.
