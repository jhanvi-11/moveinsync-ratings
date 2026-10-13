import os, yaml
from datetime import datetime, timezone
import pandas as pd
from google_play_scraper import app

cfg = yaml.safe_load(open("config.yaml"))
pkg = cfg["apps"][0]["id"]

d = app(pkg, lang="en", country=cfg["country"])
h = d["histogram"]  # [1,2,3,4,5 stars]
row = {
    "snapshot_at": datetime.now(timezone.utc).isoformat(),
    "app_id": pkg,
    "title": d["title"],
    "developer": d["developer"],
    "score": d["score"],
    "ratings_count": d["ratings"],
    "reviews_count": d["reviews"],
    "star1": h[0], "star2": h[1], "star3": h[2], "star4": h[3], "star5": h[4],
    "installs": d["installs"],
    "version": d["version"],
    "last_updated": datetime.fromtimestamp(d["updated"], tz=timezone.utc).isoformat() if d.get("updated") else None,
}
df = pd.DataFrame([row])
df["pct_1_2_star"] = ((df.star1 + df.star2) / df.ratings_count).round(3)
df["hist_total"] = df[["star1","star2","star3","star4","star5"]].sum(axis=1)
df["hist_avg"] = ((df.star1 + 2*df.star2 + 3*df.star3 + 4*df.star4 + 5*df.star5) / df.hist_total).round(4)

path = "data/rating_snapshots.csv"
df.to_csv(path, mode="a", header=not os.path.exists(path), index=False)
print(df.T)