import sqlite3, pandas as pd

df = pd.read_sql("SELECT * FROM reviews", sqlite3.connect("data/reviews.db"))
df["date"] = pd.to_datetime(df["date"], utc=True)
df["low"] = df.rating <= 2
df["replied"] = df.reply_text.notna()
df["words"] = df.text.fillna("").str.split().str.len()

print("== by year ==")
y = df.groupby(df.date.dt.year).agg(n=("rating", "size"),
        avg=("rating", "mean"), low_share=("low", "mean"))
print(y.round(2))

now = df.date.max()
for label, days in [("last 90d", 90), ("prior 90d", 180)]:
    pass
r90 = df[df.date >= now - pd.Timedelta(days=90)]
p90 = df[(df.date < now - pd.Timedelta(days=90)) & (df.date >= now - pd.Timedelta(days=180))]
print("\n== last 90d vs prior 90d ==")
for name, d in [("last 90d", r90), ("prior 90d", p90)]:
    print(name, "n =", len(d), "| avg =", round(d.rating.mean(), 2),
          "| 1-2 star share =", round(d.low.mean(), 3))

print("\n== volume to classify ==")
last24 = df[df.date >= now - pd.DateOffset(months=24)]
print("last 24 months:", len(last24), "| of which 1-3 star:", (last24.rating <= 3).sum())
print("too short (<3 words), last 24m:", round((last24.words < 3).mean() * 100, 1), "%")

print("\n== replies ==")
low = df[df.low]
print("reply rate on 1-2 star:", round(low.replied.mean() * 100, 1), "%")
rep = df[df.replied]
print("unique reply texts:", rep.reply_text.nunique(), "of", len(rep))
print(rep.reply_text.value_counts().head(5).to_string())
rep_t = (pd.to_datetime(rep.reply_date, utc=True) - rep.date).dt.total_seconds() / 86400
print("median reply delay (days):", round(rep_t.median(), 1))

print("\n== recent versions (n >= 20) ==")
v = (last24.dropna(subset=["app_version"]).groupby("app_version")
     .agg(n=("rating", "size"), avg=("rating", "mean"),
          low_share=("low", "mean"), first=("date", "min")))
print(v[v.n >= 20].sort_values("first").round(2).to_string())