import argparse, json, os, re, sqlite3, time
from datetime import datetime, timezone
from typing import List, Literal

import yaml
from openai import OpenAI
from pydantic import BaseModel, Field

Theme = Literal[
    "login_otp", "booking_failure", "cab_late_no_show", "wrong_route_eta",
    "live_tracking_gps", "boarding_verification", "crash_lag", "notifications",
    "driver_behavior", "safety", "support_unresponsive", "billing_payment",
    "ui_confusion", "rating_prompt", "update_issue", "feature_request",
    "praise", "misdirected_review", "other"
]

Stage = Literal[
    "onboarding", "booking", "assignment", "pickup", "tracking",
    "boarding", "drop", "issue_raising", "whole_app"
]

Owner = Literal[
    "app_engineering", "backend_routing", "operations", "client_policy",
    "support_process", "unclear"
]



from pydantic import BaseModel, Field, field_validator

class Item(BaseModel):
    id: str
    primary_theme: Theme
    secondary_themes: List[Theme] = []
    journey_stage: Stage
    sentiment: Literal["neg", "neu", "pos"]
    severity: int = Field(ge=1, le=5)
    suspected_owner: Owner
    evidence_quote: str
    confidence: float = Field(ge=0, le=1)
    needs_internal_validation: bool = True

    @field_validator("sentiment", mode="before")
    @classmethod
    def normalize_sentiment(cls, v: str) -> str:
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("pos", "positive"):
                return "pos"
            if v_lower in ("neg", "negative"):
                return "neg"
            if v_lower in ("neu", "neutral"):
                return "neu"
        return v


DB, BATCH = "data/reviews.db", 15
cfg = yaml.safe_load(open("config.yaml"))
MODEL, PV = cfg["llm_model"], cfg["prompt_version"]
TAXONOMY = open("prompts/taxonomy.md", encoding="utf-8").read()
SYSTEM = (
    "You classify Play Store reviews of an employee commute app (self-booked cabs and "
    "shuttles, live tracking, OTP boarding). Follow this taxonomy exactly.\n\n" + TAXONOMY +
    "\n\nReturn ONLY a JSON array, one object per review, with keys: id, primary_theme, "
    "secondary_themes, journey_stage, sentiment (must be 'neg', 'neu', or 'pos'), severity, suspected_owner, "
    "evidence_quote, confidence, needs_internal_validation. No prose, no code fences."
)


api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    raise SystemExit("Set OPENROUTER_API_KEY first.")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={"X-Title": "moveinsync-ratings"},   # optional, shows in OpenRouter logs
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews_llm (
  review_id TEXT PRIMARY KEY, primary_theme TEXT, secondary_themes TEXT,
  journey_stage TEXT, sentiment TEXT, severity INTEGER, suspected_owner TEXT,
  evidence_quote TEXT, confidence REAL, needs_internal_validation INTEGER,
  model TEXT, prompt_version TEXT, classified_at TEXT);
"""


def extract_json_array(raw: str):
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    return json.loads(raw[raw.index("["): raw.rindex("]") + 1])


def call_llm(batch):
    payload = [{"id": f"r{i}", "stars": r["rating"], "text": r["text"][:1200]}
               for i, r in enumerate(batch)]
    resp = client.chat.completions.create(
        model=MODEL, temperature=0, max_tokens=4000,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    raw = resp.choices[0].message.content
    return [Item(**x) for x in extract_json_array(raw)]


def classify_batch(batch):
    for attempt in range(3):
        try:
            by_id = {it.id: it for it in call_llm(batch)}
            return [(r, by_id.get(f"r{i}")) for i, r in enumerate(batch)]
        except Exception as e:
            print(f"  retry {attempt + 1}: {type(e).__name__}: {str(e)[:150]}")
            time.sleep(2 ** attempt)
    return [(r, None) for r in batch]


def main(limit):
    conn = sqlite3.connect(DB)
    conn.executescript(SCHEMA)
    conn.row_factory = sqlite3.Row
    todo = [dict(r) for r in conn.execute("""
        SELECT r.review_id, r.rating, r.text FROM reviews r
        JOIN reviews_clean c USING(review_id)
        WHERE c.send_to_llm = 1
          AND r.review_id NOT IN (SELECT review_id FROM reviews_llm)""")]
    if limit:
        todo = todo[:limit]
    print(f"{len(todo)} reviews to classify with {MODEL}")
    done = failed = 0
    for i in range(0, len(todo), BATCH):
        for r, it in classify_batch(todo[i:i + BATCH]):
            if it is None:
                failed += 1
                continue
            conn.execute(
                "INSERT OR REPLACE INTO reviews_llm VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r["review_id"], it.primary_theme, json.dumps(it.secondary_themes),
                 it.journey_stage, it.sentiment, it.severity, it.suspected_owner,
                 it.evidence_quote, it.confidence, int(it.needs_internal_validation),
                 MODEL, PV, datetime.now(timezone.utc).isoformat()))
            done += 1
        conn.commit()
        print(f"  {min(i + BATCH, len(todo))}/{len(todo)} (ok {done}, failed {failed})")
    print("Done. Rerun to retry failures.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="classify only N reviews (test run)")
    main(ap.parse_args().limit)