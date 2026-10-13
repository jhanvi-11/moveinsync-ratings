"""Shared look and labels for the dashboard."""

ACCENT = "#4F46E5"
INK = "#1F2937"
MUTED = "#6B7280"
GRID = "#E5E7EB"
GOOD = "#10B981"
BAD = "#EF4444"
WARN = "#F59E0B"

OWNER_COLORS = {
    "app_engineering": "#4F46E5",
    "backend_routing": "#0EA5E9",
    "operations": "#F59E0B",
    "support_process": "#10B981",
    "client_policy": "#EC4899",
    "unclear": "#9CA3AF",
}
OWNER_LABELS = {
    "app_engineering": "App engineering",
    "backend_routing": "Backend routing",
    "operations": "Operations / fleet",
    "support_process": "Support process",
    "client_policy": "Client policy",
    "unclear": "Unclear",
}

THEME_LABELS = {
    "login_otp": "Login / OTP",
    "booking_failure": "Booking failures",
    "cab_late_no_show": "Cab late / no-show",
    "wrong_route_eta": "Wrong route / ETA",
    "live_tracking_gps": "Live tracking / GPS",
    "boarding_verification": "Boarding verification",
    "crash_lag": "Crashes / won't open / lag",
    "notifications": "Notifications",
    "driver_behavior": "Driver behaviour",
    "safety": "Safety",
    "support_unresponsive": "Support unresponsive",
    "billing_payment": "Billing / payment",
    "ui_confusion": "UI confusion",
    "rating_prompt": "Rating prompt",
    "update_issue": "Update issue",
    "feature_request": "Feature request",
    "praise": "Praise",
    "misdirected_review": "Misdirected review",
    "other": "Other / vague",
}

# Themes that are not actionable fixes
NON_ACTIONABLE = {"praise", "other", "misdirected_review"}

CSS = f"""
<style>
.block-container {{ padding-top: 2rem; max-width: 1250px; }}
h1, h2, h3 {{ color: {INK}; letter-spacing: -0.01em; }}
.hero {{
  background: linear-gradient(120deg, #4F46E5 0%, #7C3AED 55%, #0EA5E9 100%);
  border-radius: 18px; padding: 1.6rem 2rem; color: white; margin-bottom: 1.2rem;
}}
.hero h1 {{ color: white; margin: 0 0 .25rem 0; font-size: 2rem; }}
.hero p {{ margin: 0; opacity: .92; font-size: 1.02rem; }}
div[data-testid="stMetric"] {{
  background: #FFFFFF; border: 1px solid {GRID}; border-left: 5px solid {ACCENT};
  border-radius: 12px; padding: .8rem 1rem; box-shadow: 0 1px 3px rgba(0,0,0,.05);
}}
.note {{
  background: #EEF2FF; border-left: 4px solid {ACCENT}; border-radius: 8px;
  padding: .7rem 1rem; color: {INK}; margin: .4rem 0 1rem 0; font-size: .95rem;
}}
.warn {{
  background: #FFFBEB; border-left: 4px solid {WARN}; border-radius: 8px;
  padding: .7rem 1rem; color: {INK}; margin: .4rem 0 1rem 0; font-size: .95rem;
}}
.stTabs [data-baseweb="tab"] {{ font-weight: 600; }}
</style>
"""
