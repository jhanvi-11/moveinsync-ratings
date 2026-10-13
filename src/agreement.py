import sqlite3
from collections import Counter
import pandas as pd

c = sqlite3.connect("data/reviews.db")
gold = pd.read_csv("data/gold_overlap.csv")
gold = gold[gold.primary_theme.notna() & (gold.primary_theme != "")]
llm = pd.read_sql("SELECT review_id, primary_theme AS llm_theme, suspected_owner AS llm_owner, confidence FROM reviews_llm", c)
d = gold.merge(llm, on="review_id", how="inner")
print("rows compared:", len(d))

def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")

for name, g_col, l_col in [("primary_theme", "primary_theme", "llm_theme"),
                           ("suspected_owner", "suspected_owner", "llm_owner")]:
    a, b = d[g_col].tolist(), d[l_col].tolist()
    agree = sum(x == y for x, y in zip(a, b)) / len(a)
    print(f"{name}: agreement {agree:.2f} | kappa {kappa(a, b):.2f}")

# Coarse view: complaint vs not (praise/other/misdirected)
non = {"praise", "other", "misdirected_review"}
a = ["non" if x in non else "complaint" for x in d.primary_theme]
b = ["non" if x in non else "complaint" for x in d.llm_theme]
print("complaint-vs-not agreement:", round(sum(x == y for x, y in zip(a, b)) / len(a), 2))

print("\nDisagreements (yours -> model):")
bad = d[d.primary_theme != d.llm_theme]
for _, r in bad.iterrows():
    print(f"- {r.primary_theme} -> {r.llm_theme} | {str(r.text)[:90]}")
print("\nconfusion pairs:")
print(Counter(zip(bad.primary_theme, bad.llm_theme)).most_common(8))