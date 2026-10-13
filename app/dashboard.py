"""MoveInSync Play App ratings dashboard.

Run:  streamlit run app/dashboard.py
Read-only: reads data/reviews.db, data/rating_snapshots.csv. No LLM or network calls.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st

import charts
import loaders as L
from theme import CSS, NON_ACTIONABLE, OWNER_LABELS, THEME_LABELS

st.set_page_config(page_title="MoveInSync ratings", page_icon="🚕", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

if not L.DB.exists():
    st.error("data/reviews.db not found. Run the pipeline first: baseline, scrape, clean, classify.")
    st.stop()

stamp = L.db_stamp()
rev = L.load_reviews(stamp)
cls = L.load_classified(stamp)
send = L.load_send_set(stamp)
snaps = L.load_snapshots(stamp)
notes = L.load_backlog_notes()

if rev.empty:
    st.warning("The reviews table is empty.")
    st.stop()

hl = L.headline(rev)
hist = L.latest_histogram(snaps)
weights = L.star_weights(cls, send)

# ------------------------------------------------------------------ header
st.markdown(
    """<div class="hero"><h1>🚕 MoveInSync Play App ratings</h1>
    <p>How are our ratings, why are they where they are, and what should we fix first?</p></div>""",
    unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
if hist:
    c1.metric("Store score", f"{hist['score']:.2f} ⭐", f"{hist['ratings']:,} ratings",
              delta_color="off")
else:
    c1.metric("Store score", "n/a", "run baseline.py", delta_color="off")
c2.metric("Written average, last 90 days", f"{hl['avg90']:.2f}",
          f"{hl['avg90'] - hl['avgprev']:+.2f} vs prior 90 days")
c3.metric("1-2 star share, last 90 days", f"{hl['low90']:.0%}",
          f"{(hl['low90'] - hl['lowprev']) * 100:+.1f} pts vs prior 90 days",
          delta_color="inverse")
c4.metric("Written reviews, last 90 days", f"{hl['n90']:,}",
          f"as of {hl['now']:%d %b %Y}", delta_color="off")

st.markdown(
    '<div class="note">Written reviews skew negative: people who write are far less happy than '
    'people who just tap a star. These figures describe <b>reviewers</b>, not all users.</div>',
    unsafe_allow_html=True)

tab_trend, tab_themes, tab_versions, tab_backlog = st.tabs(
    ["📈 Rating trend", "🏷️ Top themes and owners", "🔢 Versions", "🧾 Prioritized backlog"])

# ------------------------------------------------------------------ 1. rating trend
with tab_trend:
    st.subheader("Rating trend")
    windows = {"Last 90 days": 90, "Last 12 months": 365, "Last 3 years": 1095,
               "All history": None}
    choice = st.radio("Window", list(windows), index=1, horizontal=True)
    monthly = L.trend_by_month(rev, windows[choice])
    if len(monthly) < 2:
        st.info("Not enough months in this window to draw a trend. Pick a wider window.")
    else:
        a, b = st.columns(2)
        a.plotly_chart(charts.trend_average(monthly), width="stretch")
        b.plotly_chart(charts.trend_low_share(monthly), width="stretch")
        st.caption("Months with few reviews are noisy. Compare the bars (volume) with the line "
                   "before reading anything into a single month.")

    a, b = st.columns(2)
    a.plotly_chart(charts.yearly_average(L.trend_by_year(rev)), width="stretch")
    with b:
        if hist:
            st.plotly_chart(charts.star_histogram(hist["stars"]), width="stretch")
        else:
            st.info("No store snapshot yet. Run `python src/baseline.py`.")
    if len(snaps) >= 3:
        st.plotly_chart(charts.store_score_history(snaps), width="stretch")
    else:
        st.caption(f"Store-score history builds up with every `baseline.py` run "
                   f"({len(snaps)} snapshot(s) so far). The Play Store shows no public history, "
                   f"so this is how one gets built.")

# ------------------------------------------------------------------ 2. themes and owners
with tab_themes:
    st.subheader("Top themes with owner split")
    if cls.empty or not cls["low"].any():
        st.info("No classified reviews yet. Run `python src/classify.py`.")
    else:
        themes = L.theme_table(cls, weights)
        n_low = int(cls["low"].sum())
        weighted = st.toggle("Reweight by star rating to match the full eligible set", value=False,
                             help="Corrects for the classified sample's star mix differing from "
                                  "the full eligible set. The two views usually differ by about a point.")
        st.markdown(
            f'<div class="note">Based on <b>{n_low}</b> classified 1-2 star reviews from '
            f'{cls["date"].min():%b %Y} to {cls["date"].max():%b %Y}. Owners are '
            f'<b>suspicions from review text</b>, not verified root causes.</div>',
            unsafe_allow_html=True)

        a, b = st.columns([3, 2])
        a.plotly_chart(charts.themes_bar(themes, weighted), width="stretch")
        b.plotly_chart(charts.owner_donut(L.owner_overall(cls)), width="stretch")

        top_themes = [t for t in themes["primary_theme"] if t not in {"praise"}][:10]
        st.plotly_chart(charts.owner_stack(L.owner_by_theme(cls, top_themes)), width="stretch")
        st.caption("Read across: a theme that is mostly 'Unclear' needs internal data to place; "
                   "one that is mostly 'Operations' will not be fixed by an app release alone.")

        st.markdown("#### What reviewers actually wrote")
        pick = st.selectbox("Theme", top_themes, format_func=lambda t: THEME_LABELS.get(t, t))
        q = L.theme_quotes(cls, pick)
        for _, r in q.iterrows():
            ver = f" v{r['app_version']}" if pd.notna(r["app_version"]) else ""
            st.markdown(f"> {r['text']}\n\n"
                        f"<small>{r['date']:%d %b %Y}{ver} · {int(r['rating'])}★ · "
                        f"owner: {OWNER_LABELS.get(r['suspected_owner'], r['suspected_owner'])} · "
                        f"confidence {r['confidence']:.2f}</small>", unsafe_allow_html=True)

# ------------------------------------------------------------------ 3. versions
with tab_versions:
    st.subheader("Versions")
    vt = L.version_table(rev, cls)
    if vt.empty:
        st.info("No versions with enough reviews in the last 24 months.")
    else:
        overall_low = rev[rev["date"] >= rev["date"].max() - pd.DateOffset(months=24)]["low"].mean()
        st.plotly_chart(charts.versions_chart(vt, overall_low), width="stretch")

        versions = vt["app_version"].tolist()
        default = versions.index("12.19.0") if "12.19.0" in versions else len(versions) - 1
        sel = st.selectbox("Is this version worse than the five before it?", versions, index=default)
        t = L.version_test(rev, sel)
        if t is None:
            st.info("Not enough earlier versions to compare against.")
        else:
            verdict = ("a statistically significant difference" if abs(t["z"]) >= 1.96
                       else "**not statistically significant**")
            st.markdown(
                f'<div class="warn"><b>{t["version"]}</b>: {t["p1"]:.0%} of {t["n1"]} reviews are '
                f'1-2 star, against {t["p2"]:.0%} of {t["n2"]} reviews for the previous five versions '
                f'({", ".join(t["prev"])}). Two-proportion z = <b>{t["z"]:.2f}</b>, so this is '
                f'{verdict} (threshold 1.96). Small-sample dips appear in other versions too, so '
                f're-test as reviews accumulate.</div>', unsafe_allow_html=True)

        show = vt.copy()
        show["first_seen"] = show["first_seen"].dt.strftime("%Y-%m-%d")
        cols = {"app_version": "Version", "first_seen": "First seen", "n_reviews": "Reviews",
                "avg": "Avg rating", "low_share": "1-2 star share"}
        for c, name in [("n_classified", "Classified"), ("crash_share", "Crash share"),
                        ("login_share", "Login share"), ("update_share", "Update-issue share")]:
            if c in show.columns:
                cols[c] = name
        show = show[list(cols)].rename(columns=cols)
        fmt = {"Avg rating": "{:.2f}", "1-2 star share": "{:.0%}", "Crash share": "{:.0%}",
               "Login share": "{:.0%}", "Update-issue share": "{:.0%}"}
        st.dataframe(show.style.format({k: v for k, v in fmt.items() if k in show.columns},
                                       na_rep="-"), width="stretch", hide_index=True)
        st.caption("Review counts and rating come from all reviews in the last 24 months. Theme "
                   "shares come from the classified subset only, so they are indicative.")

# ------------------------------------------------------------------ 4. prioritized backlog
with tab_backlog:
    st.subheader("Prioritized backlog")
    if cls.empty or not cls["low"].any():
        st.info("No classified reviews yet. Run `python src/classify.py`.")
    else:
        themes = L.theme_table(cls, weights)
        lift = L.lift_table(rev, themes)
        backlog = L.build_backlog(themes, lift, notes)
        if backlog.empty:
            st.info("Could not build the backlog from the current data.")
        else:
            st.markdown(
                '<div class="note"><b>How the ranking works:</b> themes are ordered by estimated '
                'lift on the last-90-day written average (midpoint of the conservative and '
                'optimistic case), then by average severity. Lift assumes the classified theme mix '
                'holds for the last 90 days and overlap between themes is ignored, so do not sum '
                'the rows. Vague, praise and misdirected reviews are left out.</div>',
                unsafe_allow_html=True)

            table = pd.DataFrame({
                "Rank": backlog["rank"],
                "Theme": backlog["primary_theme"].map(lambda t: THEME_LABELS.get(t, t)),
                "Ticket": backlog["ticket"],
                "Action": backlog["action"],
                "Likely owner": backlog["top_owner"].map(lambda o: OWNER_LABELS.get(o, o)),
                "Share of 1-2 star": backlog["weighted_share"] * 100,
                "Avg severity": backlog["avg_severity"],
                "Est. lift (low)": backlog["lift_low"],
                "Est. lift (high)": backlog["lift_high"],
                "n": backlog["n"],
            })
            st.dataframe(
                table, width="stretch", hide_index=True,
                column_config={
                    "Share of 1-2 star": st.column_config.ProgressColumn(
                        "Share of 1-2 star", format="%.1f%%", min_value=0, max_value=25),
                    "Avg severity": st.column_config.NumberColumn(format="%.2f"),
                    "Est. lift (low)": st.column_config.NumberColumn(format="+%.3f"),
                    "Est. lift (high)": st.column_config.NumberColumn(format="+%.3f"),
                })

            st.plotly_chart(charts.lift_chart(backlog), width="stretch")

            st.markdown("#### Ticket details")
            for _, r in backlog.iterrows():
                n = notes.get(r["primary_theme"])
                if not n:
                    continue
                label = THEME_LABELS.get(r["primary_theme"], r["primary_theme"])
                with st.expander(f"#{r['rank']}  {label}  ·  {n.get('ticket', '')}  ·  "
                                 f"{r['weighted_share']:.1%} of 1-2 star"):
                    st.markdown(f"**Team:** {n.get('team', '-')}  \n"
                                f"**Effort and impact:** {n.get('effort', '-')}")
                    st.markdown(f"**Hypothesis (unverified):** {n.get('hypothesis', '-')}")
                    st.markdown(f"**Validation step:** {n.get('validate', '-')}")
                    st.markdown(f"**Proposed change:** {n.get('change', '-')}")
                    st.markdown(f"**Acceptance criteria:** {n.get('accept', '-')}")
                    st.markdown(f"**Success metric:** {n.get('metric', '-')}")
                    st.markdown("**Evidence**")
                    for _, q in L.theme_quotes(cls, r["primary_theme"]).iterrows():
                        ver = f" v{q['app_version']}" if pd.notna(q["app_version"]) else ""
                        st.markdown(f"> {q['text'][:400]}\n\n"
                                    f"<small>{q['date']:%d %b %Y}{ver} · {int(q['rating'])}★</small>",
                                    unsafe_allow_html=True)

            st.download_button("Download backlog as CSV", table.to_csv(index=False).encode("utf-8"),
                               "backlog.csv", "text/csv")

# ------------------------------------------------------------------ footer
with st.expander("About this data and its limits"):
    n_cls = len(cls)
    n_elig = len(send)
    st.markdown(
        f"- **Reviews in database:** {len(rev):,} ({rev['date'].min():%Y} to {rev['date'].max():%d %b %Y}).\n"
        f"- **Classified:** {n_cls:,} of {n_elig:,} eligible reviews "
        f"({(n_cls / n_elig if n_elig else 0):.0%}), newest first. Themes are indicative.\n"
        f"- **Owners** are suspicions from review text. Public data cannot confirm root causes.\n"
        f"- **Validation:** see the method note for agreement with hand-checked labels (small sample).\n"
        f"- **Refresh:** the app re-reads the database whenever the pipeline updates it.")
    if not cls.empty and "model" in cls.columns:
        mix = cls["model"].value_counts()
        st.markdown("**Classifier model mix:**")
        st.dataframe(mix.rename("reviews").reset_index().rename(columns={"model": "model"}),
                     hide_index=True, width="content")
