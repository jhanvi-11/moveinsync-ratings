# Taxonomy v1

## Themes (primary_theme, choose ONE; secondary_themes optional)
- login_otp: cannot log in, login OTP/SMS not arriving, account or registration problems
- booking_failure: cannot book, booking not confirmed, cancelled, waitlist/confirmation not communicated
- cab_late_no_show: cab late, no show, trip not assigned, long waits
- wrong_route_eta: wrong or long route, ETA or pickup time inaccurate
- live_tracking_gps: vehicle location wrong, not updating, map issues
- boarding_verification: boarding OTP, seatbelt/safety pop-ups at boarding, driver verification, QR flow
- crash_lag: crashes, freezes, slowness, app will not open
- notifications: missing, late, excessive or irrelevant alerts
- driver_behavior: rude driver, rash driving, refusal, calls/messages from driver
- safety: women's safety, unsafe driving, SOS, medical or night-shift risk
- support_unresponsive: no help from app support, transport desk or helpline
- billing_payment: charges, cost, payment, penalty fees
- ui_confusion: hard to navigate or understand, confusing new screens or flows
- rating_prompt: forced or repeated requests to rate or review, no skip option
- update_issue: complaint tied to an update (broke after updating, "bring back old version")
- feature_request: asks for a feature that doesn't exist
- praise: positive, no complaint
- misdirected_review: written by a driver, vendor or admin about their own role, not an employee rider
- other: relevant but fits none of the above

## Rules
1. Classify what the reviewer REPORTS. Never state a confirmed root cause.
2. If a review mentions an update AND a specific problem (confusing UI after update), primary = the specific problem; add update_issue to secondary_themes.
3. suspected_owner is a suspicion: app_engineering | backend_routing | operations | client_policy | support_process | unclear. Use "unclear" when the review does not say.
   - client_policy: company rules the user blames on the app (shift timings, eligibility, mandatory steps set by employer)
   - operations: vendor, driver or fleet behaviour
   - backend_routing: allocation, ETA, route planning
4. severity: 1 = minor annoyance ... 3 = blocks a task ... 5 = safety or total loss of service.
5. evidence_quote: shortest exact span from the review (max 20 words) that supports the theme. Keep the original language.
6. confidence: 0 to 1. Use below 0.5 if the review is vague.
7. journey_stage: onboarding | booking | assignment | pickup | tracking | boarding | drop | issue_raising | whole_app