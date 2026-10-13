"""Streamlit Dashboard for MoveInSync Ratings & Reviews Intelligence."""

import os
import sys
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add workspace root to sys.path so src imports work reliably
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analyze import (
    load_reviews_df,
    calculate_weekly_metrics,
    get_category_breakdown,
    get_top_pain_points
)
from src.alerts import run_alert_checks
from src.classify import evaluate_classifier_against_gold

st.set_page_config(
    page_title="MoveInSync Commute Intelligence",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 5px solid #2563eb;
    }
    .badge-critical {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .badge-positive {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def fetch_data():
    """Fetch reviews dataframe from SQLite."""
    df = load_reviews_df("data/reviews.db")
    return df


def main():
    st.title("🚕 MoveInSync Commute Intelligence Dashboard")
    st.markdown("Real-time sentiment, taxonomy analysis, fleet safety alerts, and weekly cohort tracking for Google Play reviews.")

    df = fetch_data()

    if df.empty:
        st.warning("⚠️ No reviews currently in `data/reviews.db`. Run `python src/scrape.py` or populate sample reviews.")
        # Provide option to load gold labels as preview
        if os.path.exists("data/gold_labels.csv"):
            if st.button("Load Gold Labels as Sample Dataset"):
                gold_df = pd.read_csv("data/gold_labels.csv")
                st.info(f"Loaded {len(gold_df)} gold label benchmark reviews.")
                st.dataframe(gold_df)
        return

    # Sidebar Filters
    st.sidebar.header("🔍 Filter Reviews")

    # Date / Week Filter
    all_weeks = sorted(df["week"].dropna().unique().tolist(), reverse=True)
    selected_weeks = st.sidebar.multiselect("Filter Weekly Cohorts", all_weeks, default=all_weeks)

    # Category Filter
    all_categories = sorted(df["primary_category"].dropna().unique().tolist())
    selected_cats = st.sidebar.multiselect("Primary Categories", all_categories, default=all_categories)

    # Sentiment Filter
    all_sentiments = ["positive", "neutral", "negative"]
    selected_sents = st.sidebar.multiselect("Sentiment", all_sentiments, default=all_sentiments)

    # Urgency Filter
    all_urgencies = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    selected_urgencies = st.sidebar.multiselect("Urgency Level", all_urgencies, default=all_urgencies)

    # Rating Filter
    selected_ratings = st.sidebar.slider("Star Rating Range", 1, 5, (1, 5))

    # Search Box
    search_query = st.sidebar.text_input("Keyword Search", "")

    # Apply Filters
    filtered_df = df[
        (df["week"].isin(selected_weeks)) &
        (df["primary_category"].isin(selected_cats)) &
        (df["sentiment"].isin(selected_sents)) &
        (df["urgency"].isin(selected_urgencies)) &
        (df["score"] >= selected_ratings[0]) &
        (df["score"] <= selected_ratings[1])
    ]

    if search_query:
        filtered_df = filtered_df[filtered_df["content"].str.contains(search_query, case=False, na=False)]

    # Alert Banner
    alerts = run_alert_checks()
    if alerts:
        with st.expander(f"⚠️ Active Alerts ({len(alerts)} Triggered)", expanded=True):
            for a in alerts:
                sev = a.get("severity", "INFO")
                if sev == "CRITICAL":
                    st.error(f"{a['title']}: {a['message']}")
                else:
                    st.warning(f"{a['title']}: {a['message']}")

    # KPI Scorecards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    total_reviews = len(filtered_df)
    avg_rating = filtered_df["score"].mean() if total_reviews else 0.0
    pos_count = (filtered_df["sentiment"] == "positive").sum()
    neg_count = (filtered_df["sentiment"] == "negative").sum()
    nss = ((pos_count - neg_count) / total_reviews * 100) if total_reviews else 0.0
    critical_count = (filtered_df["urgency"] == "CRITICAL").sum()
    actionable_count = (filtered_df["is_actionable"] == 1).sum()

    kpi1.metric("Total Reviews", f"{total_reviews:,}")
    kpi2.metric("Mean Rating", f"{avg_rating:.2f} ⭐")
    kpi3.metric("Net Sentiment (NSS)", f"{nss:+.1f}%")
    kpi4.metric("🚨 Critical Issues", f"{critical_count}")
    kpi5.metric("Actionable Feedback", f"{actionable_count}")

    st.markdown("---")

    # Main Visualizations Tab Layout
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Trends & Cohorts", "🏷️ Taxonomy & Issues", "📋 Review Explorer", "🎯 Benchmark & Accuracy"])

    with tab1:
        st.subheader("Weekly Rating & Volume Trends")
        weekly_metrics = calculate_weekly_metrics(filtered_df)

        if not weekly_metrics.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=weekly_metrics["week"],
                y=weekly_metrics["total_reviews"],
                name="Review Volume",
                marker_color="#93c5fd",
                yaxis="y2"
            ))
            fig.add_trace(go.Scatter(
                x=weekly_metrics["week"],
                y=weekly_metrics["avg_rating"],
                name="Avg Rating",
                mode="lines+markers",
                marker=dict(color="#1d4ed8", size=8),
                line=dict(color="#1d4ed8", width=3)
            ))
            fig.update_layout(
                title="Weekly Rating (Line) vs Volume (Bars)",
                xaxis_title="Cohort Week",
                yaxis=dict(title="Average Star Rating", range=[1, 5]),
                yaxis2=dict(title="Review Volume", overlaying="y", side="right"),
                legend=dict(x=0.01, y=0.99),
                template="plotly_white",
                height=420
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient weekly data for trends.")

    with tab2:
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            st.subheader("Volume by Primary Category")
            cat_df = get_category_breakdown(filtered_df)
            if not cat_df.empty:
                fig_cat = px.bar(
                    cat_df,
                    x="review_count",
                    y="primary_category",
                    orientation="h",
                    color="primary_category",
                    text="review_count",
                    title="Reviews per Category",
                    template="plotly_white"
                )
                fig_cat.update_layout(showlegend=False, height=380)
                st.plotly_chart(fig_cat, use_container_width=True)

        with col_cat2:
            st.subheader("Sentiment Distribution by Category")
            if not cat_df.empty and "positive" in cat_df.columns:
                fig_sent = px.bar(
                    cat_df,
                    x="primary_category",
                    y=["positive", "neutral", "negative"],
                    title="Sentiment Share per Category",
                    color_discrete_map={"positive": "#22c55e", "neutral": "#f59e0b", "negative": "#ef4444"},
                    template="plotly_white"
                )
                fig_sent.update_layout(height=380)
                st.plotly_chart(fig_sent, use_container_width=True)

        st.subheader("Top Negative Friction Subcategories")
        pain_df = get_top_pain_points(filtered_df, top_n=6)
        if not pain_df.empty:
            st.dataframe(pain_df, use_container_width=True)

    with tab3:
        st.subheader(f"Review Explorer ({len(filtered_df)} items)")
        display_cols = ["at", "score", "primary_category", "primary_subcategory", "sentiment", "urgency", "content", "summary"]
        st.dataframe(
            filtered_df[[c for c in display_cols if c in filtered_df.columns]],
            use_container_width=True,
            height=450
        )

    with tab4:
        st.subheader("Classifier Ground Truth Benchmark")
        st.markdown("Evaluates classification engine against human-curated benchmark dataset `data/gold_labels.csv`.")
        if st.button("Run Evaluation Benchmark"):
            with st.spinner("Calculating precision, recall, and F1 metrics..."):
                metrics = evaluate_classifier_against_gold()
                b1, b2, b3, b4 = st.columns(4)
                b1.metric("Category Accuracy", f"{metrics['category_accuracy']*100:.1f}%")
                b2.metric("Category F1 (Weighted)", f"{metrics['category_weighted_f1']*100:.1f}%")
                b3.metric("Category Precision", f"{metrics['category_weighted_precision']*100:.1f}%")
                b4.metric("Sentiment Accuracy", f"{metrics['sentiment_accuracy']*100:.1f}%")
                st.success("Benchmark calculation completed.")


if __name__ == "__main__":
    main()
