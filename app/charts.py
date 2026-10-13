"""Plotly figure builders for the dashboard."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from theme import (ACCENT, BAD, GOOD, GRID, INK, MUTED, OWNER_COLORS, OWNER_LABELS,
                   THEME_LABELS, WARN)

STAR_COLORS = ["#EF4444", "#F97316", "#FACC15", "#84CC16", "#10B981"]


def _base(fig: go.Figure, height: int = 380, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, template="plotly_white", font=dict(color=INK),
        margin=dict(l=10, r=10, t=40, b=10), showlegend=legend,
        legend=dict(orientation="h", y=-0.2),
    )
    fig.update_xaxes(gridcolor=GRID)
    fig.update_yaxes(gridcolor=GRID)
    return fig


def trend_average(monthly: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=monthly["month"], y=monthly["n"], name="Reviews (right axis)",
                marker_color="#E0E7FF", secondary_y=True)
    fig.add_scatter(x=monthly["month"], y=monthly["avg"], name="Average rating",
                    mode="lines+markers", line=dict(color=ACCENT, width=3), secondary_y=False)
    fig.update_yaxes(title_text="Average rating", range=[1, 5], secondary_y=False)
    fig.update_yaxes(title_text="Reviews", showgrid=False, secondary_y=True)
    fig.update_layout(title="Written-review average by month")
    return _base(fig)


def trend_low_share(monthly: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=monthly["month"], y=monthly["low"] * 100, mode="lines+markers", fill="tozeroy",
        line=dict(color=BAD, width=3), fillcolor="rgba(239,68,68,0.12)", name="1-2 star %"))
    fig.update_yaxes(title_text="1-2 star share (%)", rangemode="tozero")
    fig.update_layout(title="Share of 1-2 star reviews by month")
    return _base(fig, legend=False)


def yearly_average(yearly: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=yearly["year"].astype(str), y=yearly["avg"], marker_color=ACCENT,
        text=[f"{a:.2f}<br>n={n:,}" for a, n in zip(yearly["avg"], yearly["n"])],
        textposition="outside"))
    fig.update_yaxes(range=[1, 5], title_text="Average rating")
    fig.update_layout(title="Written-review average by year")
    return _base(fig, legend=False)


def star_histogram(stars: list[int]) -> go.Figure:
    total = sum(stars)
    fig = go.Figure(go.Bar(
        x=[f"{i}★" for i in range(1, 6)], y=stars, marker_color=STAR_COLORS,
        text=[f"{s / total:.1%}" for s in stars], textposition="outside"))
    fig.update_yaxes(title_text="Ratings")
    fig.update_layout(title="App rating distribution (all ratings)")
    return _base(fig, legend=False)


def store_score_history(snaps: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(x=snaps["snapshot_at"], y=snaps["score"], mode="lines+markers",
                               line=dict(color=ACCENT, width=3)))
    fig.update_yaxes(title_text="Store score", range=[snaps["score"].min() - 0.05,
                                                     snaps["score"].max() + 0.05])
    fig.update_layout(title="Store score over time (from baseline snapshots)")
    return _base(fig, legend=False)


def themes_bar(table: pd.DataFrame, weighted: bool, top: int = 12) -> go.Figure:
    col = "weighted_share" if weighted else "raw_share"
    d = table.sort_values(col, ascending=False).head(top).iloc[::-1]
    labels = [THEME_LABELS.get(t, t) for t in d["primary_theme"]]
    fig = go.Figure(go.Bar(
        y=labels, x=d[col] * 100, orientation="h", marker_color=ACCENT,
        text=[f"{s:.1%}  (n={n})" for s, n in zip(d[col], d["n"])], textposition="outside"))
    fig.update_xaxes(title_text="Share of 1-2 star reviews (%)", range=[0, d[col].max() * 130])
    fig.update_layout(title="What 1-2 star reviewers complain about")
    return _base(fig, height=460, legend=False)


def owner_donut(owner_share: pd.Series) -> go.Figure:
    labels = [OWNER_LABELS.get(o, o) for o in owner_share.index]
    colors = [OWNER_COLORS.get(o, "#9CA3AF") for o in owner_share.index]
    fig = go.Figure(go.Pie(labels=labels, values=owner_share.values, hole=0.55,
                           marker=dict(colors=colors), textinfo="label+percent",
                           sort=False))
    fig.update_layout(title="Suspected owner, all 1-2 star reviews")
    return _base(fig, height=420, legend=False)


def owner_stack(cross: pd.DataFrame) -> go.Figure:
    pct = cross.div(cross.sum(axis=1).replace(0, 1), axis=0) * 100
    labels = [THEME_LABELS.get(t, t) for t in pct.index]
    fig = go.Figure()
    for owner in OWNER_COLORS:
        if owner in pct.columns:
            fig.add_bar(y=labels, x=pct[owner], name=OWNER_LABELS[owner], orientation="h",
                        marker_color=OWNER_COLORS[owner])
    fig.update_layout(barmode="stack", title="Which owner each theme points to (% of theme)")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title_text="% of reviews in theme", range=[0, 100])
    return _base(fig, height=460)


def versions_chart(vt: pd.DataFrame, overall_low: float) -> go.Figure:
    colors = [("#CBD5E1" if s else ACCENT) for s in vt["small_sample"]]
    fig = go.Figure(go.Bar(
        x=vt["app_version"], y=vt["low_share"] * 100, marker_color=colors,
        text=[f"{v:.0%}<br>n={n}" for v, n in zip(vt["low_share"], vt["n_reviews"])],
        textposition="outside"))
    fig.add_hline(y=overall_low * 100, line_dash="dash", line_color=WARN,
                  annotation_text=f"overall {overall_low:.0%}", annotation_position="top left")
    fig.update_yaxes(title_text="1-2 star share (%)", rangemode="tozero")
    fig.update_xaxes(title_text="App version (release order)", type="category")
    fig.update_layout(title="1-2 star share by app version (grey = fewer than 60 reviews)")
    return _base(fig, height=420, legend=False)


def lift_chart(backlog: pd.DataFrame, top: int = 8) -> go.Figure:
    d = backlog.head(top)
    labels = [THEME_LABELS.get(t, t) for t in d["primary_theme"]]
    fig = go.Figure()
    fig.add_bar(x=labels, y=d["lift_low"], name="Conservative (affected become 3★)",
                marker_color="#A5B4FC")
    fig.add_bar(x=labels, y=d["lift_high"], name="Optimistic (affected match non-complaint avg)",
                marker_color=ACCENT)
    fig.update_yaxes(title_text="Lift on 90-day average (stars)")
    fig.update_layout(barmode="group", title="Estimated lift if the theme were fixed")
    return _base(fig, height=420)
