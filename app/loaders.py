"""Cached data loaders and metric calculations for the dashboard (read-only)."""

import math
import os
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "reviews.db"
SNAPSHOTS = ROOT / "data" / "rating_snapshots.csv"
BACKLOG_YAML = Path(__file__).resolve().parent / "backlog.yaml"

LOW_MAX = 2  # 1-2 star = "low"


def db_stamp() -> float:
    """Modified time of the DB, used as a cache key so pipeline reruns refresh the app."""
    return os.path.getmtime(DB) if DB.exists() else 0.0


def _version_key(v: str):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return (0,)


# ---------------------------------------------------------------- loaders
@st.cache_data(show_spinner=False)
def load_reviews(stamp: float) -> pd.DataFrame:
    conn = sqlite3.connect(DB)
    df = pd.read_sql(
        "SELECT review_id, rating, text, date, app_version, reply_text FROM reviews", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["low"] = df["rating"] <= LOW_MAX
    return df


@st.cache_data(show_spinner=False)
def load_classified(stamp: float) -> pd.DataFrame:
    conn = sqlite3.connect(DB)
    try:
        df = pd.read_sql(
            """SELECT l.*, r.rating, r.date, r.app_version, r.text
               FROM reviews_llm l JOIN reviews r USING(review_id)""", conn)
    except Exception:
        conn.close()
        return pd.DataFrame()
    conn.close()
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["low"] = df["rating"] <= LOW_MAX
    return df


@st.cache_data(show_spinner=False)
def load_send_set(stamp: float) -> pd.DataFrame:
    conn = sqlite3.connect(DB)
    try:
        df = pd.read_sql(
            """SELECT r.rating FROM reviews r JOIN reviews_clean c USING(review_id)
               WHERE c.send_to_llm = 1""", conn)
    except Exception:
        df = pd.DataFrame({"rating": []})
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_snapshots(stamp: float) -> pd.DataFrame:
    if not SNAPSHOTS.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(SNAPSHOTS)
    except Exception:
        return pd.DataFrame()
    df["snapshot_at"] = pd.to_datetime(df["snapshot_at"], utc=True)
    return df.sort_values("snapshot_at")


@st.cache_data(show_spinner=False)
def load_backlog_notes() -> dict:
    if not BACKLOG_YAML.exists():
        return {}
    return yaml.safe_load(open(BACKLOG_YAML, encoding="utf-8")) or {}


# ---------------------------------------------------------------- rating trend
def headline(rev: pd.DataFrame) -> dict:
    now = rev["date"].max()
    r90 = rev[rev["date"] >= now - pd.Timedelta(days=90)]
    p90 = rev[(rev["date"] < now - pd.Timedelta(days=90)) &
              (rev["date"] >= now - pd.Timedelta(days=180))]
    return {
        "now": now,
        "n90": len(r90), "avg90": r90["rating"].mean(), "low90": r90["low"].mean(),
        "nprev": len(p90), "avgprev": p90["rating"].mean(), "lowprev": p90["low"].mean(),
    }


def trend_by_month(rev: pd.DataFrame, days: int | None) -> pd.DataFrame:
    d = rev if days is None else rev[rev["date"] >= rev["date"].max() - pd.Timedelta(days=days)]
    d = d.assign(month=d["date"].dt.tz_localize(None).dt.to_period("M").dt.to_timestamp())
    out = d.groupby("month").agg(n=("rating", "size"), avg=("rating", "mean"),
                                 low=("low", "mean")).reset_index()
    return out


def trend_by_year(rev: pd.DataFrame) -> pd.DataFrame:
    d = rev.assign(year=rev["date"].dt.year)
    return d.groupby("year").agg(n=("rating", "size"), avg=("rating", "mean"),
                                 low=("low", "mean")).reset_index()


def latest_histogram(snaps: pd.DataFrame):
    if snaps.empty:
        return None
    row = snaps.iloc[-1]
    return {
        "score": float(row["score"]), "ratings": int(row["ratings_count"]),
        "stars": [int(row[f"star{i}"]) for i in range(1, 6)],
        "at": row["snapshot_at"],
    }


# ---------------------------------------------------------------- themes and owners
def star_weights(cls: pd.DataFrame, send: pd.DataFrame) -> dict:
    """Weight = eligible-set star share / classified-set star share."""
    if cls.empty or send.empty:
        return {}
    s = send["rating"].value_counts(normalize=True)
    c = cls["rating"].value_counts(normalize=True)
    return (s / c).dropna().to_dict()


def theme_table(cls: pd.DataFrame, weights: dict) -> pd.DataFrame:
    low = cls[cls["low"]].copy()
    if low.empty:
        return pd.DataFrame()
    low["w"] = low["rating"].map(weights).fillna(1.0)
    g = low.groupby("primary_theme")
    out = pd.DataFrame({
        "n": g.size(),
        "raw_share": g.size() / len(low),
        "weighted_share": g["w"].sum() / low["w"].sum(),
        "avg_severity": g["severity"].mean(),
    })
    owner = pd.crosstab(low["primary_theme"], low["suspected_owner"])
    out["top_owner"] = owner.idxmax(axis=1)
    return out.sort_values("n", ascending=False).reset_index()


def owner_by_theme(cls: pd.DataFrame, themes: list[str]) -> pd.DataFrame:
    low = cls[cls["low"] & cls["primary_theme"].isin(themes)]
    return pd.crosstab(low["primary_theme"], low["suspected_owner"]).reindex(themes).fillna(0)


def owner_overall(cls: pd.DataFrame) -> pd.Series:
    low = cls[cls["low"]]
    return low["suspected_owner"].value_counts(normalize=True)


def theme_quotes(cls: pd.DataFrame, theme: str, k: int = 3) -> pd.DataFrame:
    d = cls[cls["low"] & (cls["primary_theme"] == theme)]
    return d.sort_values(["confidence", "date"], ascending=[False, False]).head(k)


# ---------------------------------------------------------------- versions
def version_table(rev: pd.DataFrame, cls: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    now = rev["date"].max()
    recent = rev[(rev["date"] >= now - pd.DateOffset(months=24)) & rev["app_version"].notna()]
    g = recent.groupby("app_version")
    out = pd.DataFrame({
        "n_reviews": g.size(), "avg": g["rating"].mean(), "low_share": g["low"].mean(),
        "first_seen": g["date"].min(),
    })
    if not cls.empty:
        c = cls[cls["app_version"].notna()]
        cg = c.groupby("app_version")
        out["n_classified"] = cg.size()
        out["crash_share"] = cg["primary_theme"].apply(lambda s: (s == "crash_lag").mean())
        out["login_share"] = cg["primary_theme"].apply(lambda s: (s == "login_otp").mean())
        out["update_share"] = cg["primary_theme"].apply(lambda s: (s == "update_issue").mean())
    out = out[out["n_reviews"] >= min_n].reset_index()
    out["small_sample"] = out["n_reviews"] < 60
    out["_k"] = out["app_version"].map(_version_key)
    return out.sort_values("_k").drop(columns="_k").reset_index(drop=True)


def version_test(rev: pd.DataFrame, version: str, n_prev: int = 5) -> dict | None:
    """Two-proportion z-test: `version` vs. the n_prev versions released just before it."""
    versions = sorted(rev["app_version"].dropna().unique(), key=_version_key)
    if version not in versions:
        return None
    idx = versions.index(version)
    prev = versions[max(0, idx - n_prev):idx]
    if not prev:
        return None
    a = rev[rev["app_version"] == version]
    b = rev[rev["app_version"].isin(prev)]
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return None
    p1, p2 = a["low"].mean(), b["low"].mean()
    p = (a["low"].sum() + b["low"].sum()) / (n1 + n2)
    denom = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if 0 < p < 1 else float("nan")
    z = (p1 - p2) / denom if denom and not math.isnan(denom) else float("nan")
    return {"version": version, "prev": prev, "n1": n1, "n2": n2, "p1": p1, "p2": p2, "z": z}


# ---------------------------------------------------------------- impact + backlog
def lift_table(rev: pd.DataFrame, themes: pd.DataFrame) -> pd.DataFrame:
    """Rating-lift simulation on the last 90 days, same method as src/analyze.py."""
    now = rev["date"].max()
    r90 = rev[rev["date"] >= now - pd.Timedelta(days=90)]
    low90 = r90[r90["low"]]
    if r90.empty or low90.empty or themes.empty:
        return pd.DataFrame()
    cur = low90["rating"].mean()
    nonlow_avg = r90[~r90["low"]]["rating"].mean()
    total = r90["rating"].sum()
    k = themes["weighted_share"] * len(low90)
    out = themes[["primary_theme"]].copy()
    out["est_reviews"] = k.values
    out["lift_low"] = ((total + k * (3 - cur)) / len(r90) - r90["rating"].mean()).values
    out["lift_high"] = ((total + k * (nonlow_avg - cur)) / len(r90) - r90["rating"].mean()).values
    out["lift_mid"] = (out["lift_low"] + out["lift_high"]) / 2
    return out


def build_backlog(themes: pd.DataFrame, lift: pd.DataFrame, notes: dict) -> pd.DataFrame:
    from theme import NON_ACTIONABLE
    if themes.empty or lift.empty:
        return pd.DataFrame()
    d = themes.merge(lift, on="primary_theme")
    d = d[~d["primary_theme"].isin(NON_ACTIONABLE)].copy()
    d["ticket"] = d["primary_theme"].map(lambda t: notes.get(t, {}).get("ticket", "-"))
    d["action"] = d["primary_theme"].map(lambda t: notes.get(t, {}).get("action", "Investigate"))
    d = d.sort_values(["lift_mid", "avg_severity"], ascending=False).reset_index(drop=True)
    d.insert(0, "rank", np.arange(1, len(d) + 1))
    return d
