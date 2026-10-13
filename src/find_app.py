from google_play_scraper import search

for r in search("MoveInSync", lang="en", country="in", n_hits=10):
    print(r["appId"], "|", r["title"], "|", r["developer"], "|", r["score"])