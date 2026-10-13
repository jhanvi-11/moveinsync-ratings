# """Data cleaning and language detection module for MoveInSync reviews."""

# import re
# import html
# import sqlite3
# import logging
# from typing import Optional, Tuple
# from langdetect import detect, DetectorFactory

# # Set seed for deterministic language detection
# DetectorFactory.seed = 0

# logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
# logger = logging.getLogger(__name__)

# HINGLISH_KEYWORDS = {
#     "bekar", "bura", "achha", "accha", "bahut", "gaadi", "gadi", "chalak",
#     "kuch", "nahi", "karte", "der", "samay", "paise", "kaam", "bakwas",
#     "dhoka", "ganda", "chor", "chahiye", "kar", "rahe", "hota", "galti"
# }


# def clean_text(text: Optional[str]) -> str:
#     """Clean raw review text: unescape HTML, normalize whitespaces, preserve semantics."""
#     if not text:
#         return ""

#     # Unescape HTML entities (&amp;, &lt;, etc.)
#     text = html.unescape(text)

#     # Replace multiple newlines or tabs with a single space
#     text = re.sub(r"[\r\n\t]+", " ", text)

#     # Normalize multiple consecutive spaces
#     text = re.sub(r"\s{2,}", " ", text)

#     # Strip leading and trailing whitespace
#     return text.strip()


# def detect_review_language(text: str) -> str:
#     """
#     Detect language of review text.
#     Handles English ('en'), Hindi ('hi'), Hinglish / code-mixed ('hinglish'), or 'unknown'.
#     """
#     if not text or len(text.strip()) < 3:
#         return "unknown"

#     # Check for Romanized Hindi (Hinglish) keyword heuristic
#     words = set(re.findall(r"\b[a-zA-Z]{3,}\b", text.lower()))
#     hinglish_matches = words.intersection(HINGLISH_KEYWORDS)
#     if len(hinglish_matches) >= 2:
#         return "hinglish"

#     try:
#         lang = detect(text)
#         return lang
#     except Exception:
#         return "unknown"


# def clean_and_enrich_reviews(db_path: str = "data/reviews.db") -> int:
#     """Clean uncleaned reviews and populate cleaned_content and language columns."""
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()

#     cursor.execute("""
#         SELECT review_id, content
#         FROM reviews
#         WHERE cleaned_content IS NULL OR language IS NULL
#     """)
#     rows = cursor.fetchall()

#     if not rows:
#         logger.info("No uncleaned reviews found.")
#         conn.close()
#         return 0

#     logger.info(f"Cleaning {len(rows)} reviews...")
#     update_data = []
#     for review_id, content in rows:
#         cleaned = clean_text(content)
#         lang = detect_review_language(cleaned)
#         update_data.append((cleaned, lang, review_id))

#     cursor.executemany("""
#         UPDATE reviews
#         SET cleaned_content = ?,
#             language = ?,
#             updated_at = CURRENT_TIMESTAMP
#         WHERE review_id = ?
#     """, update_data)

#     conn.commit()
#     conn.close()
#     logger.info(f"Successfully cleaned and updated {len(update_data)} reviews.")
#     return len(update_data)


# if __name__ == "__main__":
#     clean_and_enrich_reviews()

import re, sqlite3
import pandas as pd

DB = "data/reviews.db"

DEVANAGARI = re.compile(r"[\u0900-\u097F]")
LETTER = re.compile(r"[A-Za-z\u0900-\u097F]")
# Distinctive Romanised-Hindi tokens. Ambiguous English words (to, me, hi) left out on purpose.
HINGLISH = {"hai", "nahi", "nhi", "nahin", "bhot", "bahut", "bohot", "kya", "kyun",
            "kyu", "bekar", "bakwas", "kharab", "accha", "acha", "achha", "bhai",
            "karo", "raha", "rahi", "hota", "hoti", "abhi", "sahi", "bilkul",
            "mera", "meri", "kaam", "paisa", "ghanta", "jaldi"}


def lang_tag(text: str) -> str:
    if not LETTER.search(text):
        return "no_text"          # emoji-only or empty
    if DEVANAGARI.search(text):
        return "hindi"
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    return "hinglish" if tokens & HINGLISH else "english"


def main():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT review_id, rating, text, date, app_version, reply_text FROM reviews", conn)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["text"] = df["text"].fillna("").str.strip()

    out = pd.DataFrame({"review_id": df.review_id})
    out["lang_tag"] = df.text.map(lang_tag)
    out["word_count"] = df.text.str.split().str.len()
    out["too_short"] = out.word_count < 3
    out["has_reply"] = df.reply_text.notna()

    now = df.date.max()
    out["in_24m"] = df.date >= now - pd.DateOffset(months=24)
    out["in_90d"] = df.date >= now - pd.Timedelta(days=90)
    out["version_known"] = df.app_version.notna()

    # What goes to the LLM: recent, enough words, has real text
    out["send_to_llm"] = out.in_24m & ~out.too_short & (out.lang_tag != "no_text")
    # 1-2 star short reviews, counted separately as "no detail"
    out["low_no_detail"] = out.in_24m & out.too_short & (df.rating <= 2)

    out.to_sql("reviews_clean", conn, if_exists="replace", index=False)

    print("language mix (last 24m):")
    print(out[out.in_24m].lang_tag.value_counts().to_string())
    print("\nsend to LLM:", int(out.send_to_llm.sum()))
    print("1-2 star, no detail:", int(out.low_no_detail.sum()))
    print("short reviews, other:", int((out.in_24m & out.too_short).sum() - out.low_no_detail.sum()))


if __name__ == "__main__":
    main()