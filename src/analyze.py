import math, os, sqlite3
import pandas as pd

os.makedirs("data/out", exist_ok=True)
c = sqlite3.connect("data/reviews.db")

rev = pd.read_sql("SELECT * FROM reviews", c)
rev["date"] = pd.to_datetime(rev["date"], utc=True)
rev["low"] = rev.rating <= 2
now = rev.date.max()

llm = pd.read_sql("SELECT * FROM reviews_llm", c)
d = llm.merge(rev[["review_id", "rating", "date", "app_version", "text", "reply_text"]], on="review_id")
d["low"] = d.rating <= 2

# ---- Reweighting by star (send-set share / classified share)
send = pd.read_sql("""SELECT r.rating FROM reviews r JOIN reviews_clean c USING(review_id)
                      WHERE c.send_to_llm=1""", c)
w = (send.rating.value_counts(normalize=True) / d.rating.value_counts(normalize=True)).to_dict()
d["w"] = d.rating.map(w)

def share(df, col, weighted=False):
    s = df.groupby(col)["w"].sum() if weighted else df.groupby(col).size()
    return (s / s.sum()).sort_values(ascending=False)

# ---- 1. Themes among 1-2 star reviews
low = d[d.low]
t = pd.DataFrame({"n": low.groupby("primary_theme").size(),
                  "raw_share": share(low, "primary_theme"),
                  "weighted_share": share(low, "primary_theme", True),
                  "avg_severity": low.groupby("primary_theme").severity.mean()}).fillna(0)
t = t.sort_values("n", ascending=False).round(3)
print(f"== Themes among 1-2 star classified reviews (n={len(low)}) ==")
print(t.to_string())
t.to_csv("data/out/themes_low.csv")

# ---- 2. Owner split
o = low.suspected_owner.value_counts(normalize=True).round(3)
print("\n== Suspected owner, 1-2 star ==")
print(o.to_string())
o.to_csv("data/out/owner_low.csv")

# ---- 3. Rating-lift simulation on the last 90 days (all reviews, theme shares from classified sample)
r90 = rev[rev.date >= now - pd.Timedelta(days=90)]
base = r90.rating.mean()
low90 = r90[r90.low]
n_low90 = len(low90)
nonlow_avg = r90[~r90.low].rating.mean()
print(f"\n== Rating-lift simulation, last 90d (n={len(r90)}, avg {base:.3f}, 1-2 star n={n_low90}) ==")
print("Assumption: each theme's share of 1-2 star reviews is taken from the classified sample.")
rows = []
for theme, sh in t.weighted_share.items():
    k = sh * n_low90                           # estimated affected reviews
    cur = low90.rating.mean()
    cons = (r90.rating.sum() + k * (3 - cur)) / len(r90)           # affected become 3 stars
    opt = (r90.rating.sum() + k * (nonlow_avg - cur)) / len(r90)   # affected become avg of non-low
    rows.append((theme, round(sh, 3), round(k, 1), round(cons - base, 3), round(opt - base, 3)))
sim = pd.DataFrame(rows, columns=["theme", "share_of_low", "est_reviews", "lift_conservative", "lift_optimistic"])
print(sim.head(10).to_string(index=False))
sim.to_csv("data/out/lift_sim.csv", index=False)

# ---- 4. Version check on update_issue and rating_prompt (classified sample)
d["is_update"] = (d.primary_theme == "update_issue")
d["is_prompt"] = (d.primary_theme == "rating_prompt")
v = (d.dropna(subset=["app_version"]).groupby("app_version")
      .agg(n=("rating", "size"), avg=("rating", "mean"), low=("low", "mean"),
           update_issue=("is_update", "mean"), rating_prompt=("is_prompt", "mean")))
v = v[v.n >= 20].round(3)
print("\n== Classified-sample versions (n>=20) ==")
print(v.to_string())
v.to_csv("data/out/versions_llm.csv")

# ---- 5. Emerging themes: last 30d vs prior 90d (1-2 star, classified)
a = low[low.date >= now - pd.Timedelta(days=30)]
b = low[(low.date < now - pd.Timedelta(days=30)) & (low.date >= now - pd.Timedelta(days=120))]
em = pd.DataFrame({"last30_share": a.primary_theme.value_counts(normalize=True),
                   "prior90_share": b.primary_theme.value_counts(normalize=True),
                   "last30_n": a.primary_theme.value_counts()}).fillna(0)
em["change"] = em.last30_share - em.prior90_share
print(f"\n== Emerging themes (last30 n={len(a)}, prior90 n={len(b)}; small samples, hints only) ==")
print(em.sort_values("change", ascending=False).round(3).head(8).to_string())

# ---- 6. Evidence quotes (3 per top theme)
print("\n== Example quotes, top 5 low-star themes ==")
for theme in t.index[:5]:
    ex = low[low.primary_theme == theme].sort_values("confidence", ascending=False).head(3)
    print(f"\n[{theme}]")
    for _, r in ex.iterrows():
        print(f"  {r.date.date()} v{r.app_version} {r.rating}* | {r.text[:160]!r}")

# ---- 7. Reply analysis (all reviews, 1-2 star)
lowall = rev[rev.low]
rep = lowall[lowall.reply_text.notna()]
print("\n== Replies to 1-2 star (all reviews) ==")
print("reply rate:", round(len(rep) / len(lowall), 3), "| unique texts:", rep.reply_text.nunique(), "of", len(rep))
print(rep.reply_text.str.slice(0, 140).value_counts().head(5).to_string())

# ---- 8. 90-day trend, all reviews
p90 = rev[(rev.date < now - pd.Timedelta(days=90)) & (rev.date >= now - pd.Timedelta(days=180))]
print(f"\n== 90d avg {r90.rating.mean():.2f} (low {r90.low.mean():.3f}) vs prior 90d {p90.rating.mean():.2f} (low {p90.low.mean():.3f}) ==")

# ---- 9. Confidence and 12.19.0 update_issue check
print("\nlow confidence (<0.5):", round((d.confidence < 0.5).mean(), 3))
a = d[d.app_version == "12.19.0"]; b = d[d.app_version != "12.19.0"]
print(f"update_issue share: 12.19.0 {a.is_update.mean():.3f} (n={len(a)}) vs others {b.is_update.mean():.3f} (n={len(b)})")