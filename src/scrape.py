import argparse, json, os, sqlite3, time
from datetime import datetime, timezone

import yaml
from google_play_scraper import reviews, Sort

DB = "data/reviews.db"
RAW_DIR = "data/raw"
BATCH = 200

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
  review_id      TEXT PRIMARY KEY,
  app_id         TEXT NOT NULL,
  rating         INTEGER,
  text           TEXT,
  date           TEXT,      -- UTC ISO-8601
  thumbs_up      INTEGER,
  app_version    TEXT,      -- may be NULL
  reply_text     TEXT,
  reply_date     TEXT,
  lang_requested TEXT,
  fetched_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_reviews_app_date ON reviews(app_id, date);
"""

UPSERT = """
INSERT INTO reviews (review_id, app_id, rating, text, date, thumbs_up,
                     app_version, reply_text, reply_date, lang_requested, fetched_at)
VALUES (:review_id, :app_id, :rating, :text, :date, :thumbs_up,
        :app_version, :reply_text, :reply_date, :lang_requested, :fetched_at)
ON CONFLICT(review_id) DO UPDATE SET
  rating=excluded.rating, text=excluded.text, thumbs_up=excluded.thumbs_up,
  reply_text=excluded.reply_text, reply_date=excluded.reply_date
"""


def utc_iso(dt):
    # google-play-scraper returns naive local datetimes; astimezone() treats them as local
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def to_row(r, app_id, lang, fetched_at):
    return {
        "review_id": r["reviewId"],
        "app_id": app_id,
        "rating": r["score"],
        "text": (r.get("content") or "").strip(),
        "date": utc_iso(r.get("at")),
        "thumbs_up": r.get("thumbsUpCount"),
        "app_version": r.get("appVersion") or r.get("reviewCreatedVersion"),
        "reply_text": r.get("replyContent"),
        "reply_date": utc_iso(r.get("repliedAt")),
        "lang_requested": lang,
        "fetched_at": fetched_at,
    }


def fetch(app_id, lang, country, token):
    for attempt in range(5):
        try:
            return reviews(app_id, lang=lang, country=country, sort=Sort.NEWEST,
                           count=BATCH, continuation_token=token)
        except Exception as e:
            wait = 2 ** attempt
            print(f"  fetch failed ({e}); retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError("Giving up after 5 failed attempts")


def existing_ids(conn, ids):
    q = ",".join("?" * len(ids))
    return {x[0] for x in conn.execute(
        f"SELECT review_id FROM reviews WHERE review_id IN ({q})", ids)}


def save_raw(batch, app_id, lang, stamp, page):
    os.makedirs(RAW_DIR, exist_ok=True)
    path = f"{RAW_DIR}/{app_id}_{lang}_{stamp}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        for r in batch:
            r = {k: v for k, v in r.items() if k not in ("userName", "userImage")}
            f.write(json.dumps(r, default=str, ensure_ascii=False) + "\n")


def scrape(conn, app_id, lang, country, full):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    fetched_at = datetime.now(timezone.utc).isoformat()
    token, new_total, pages = None, 0, 0
    while True:
        batch, token = fetch(app_id, lang, country, token)
        if not batch:
            break
        known = existing_ids(conn, [r["reviewId"] for r in batch])
        n_new = sum(r["reviewId"] not in known for r in batch)
        conn.executemany(UPSERT, [to_row(r, app_id, lang, fetched_at) for r in batch])
        conn.commit()
        save_raw(batch, app_id, lang, stamp, pages)
        new_total += n_new
        pages += 1
        oldest = utc_iso(batch[-1]["at"])[:10]
        print(f"  [{lang}] page {pages}: {len(batch)} fetched, {n_new} new, oldest {oldest}")
        if not full and n_new == 0:
            break               # incremental: caught up
        if token is None:
            break               # reached the end of available history
        time.sleep(1)
    return new_total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="ignore the early-stop rule")
    args = ap.parse_args()

    cfg = yaml.safe_load(open("config.yaml"))
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.executescript(SCHEMA)

    for app in cfg["apps"]:
        for lang in cfg["languages"]:
            print(f"Scraping {app['name']} ({app['id']}) lang={lang}")
            n = scrape(conn, app["id"], lang, cfg["country"], args.full)
            print(f"  -> {n} new reviews")

    total = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    print(f"Total in DB: {total}")