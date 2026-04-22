"""Insights — interactive analytics on Celina's health & finance data.

New in MyHealthHub v2: data visualisation tab with 4 interactive Plotly charts.
"""
from collections import Counter, defaultdict
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.chatbot import render_chatbot_sidebar
from utils.data_loader import load_appointments, load_celina, load_finances, load_records

st.set_page_config(page_title="Insights · MyHealthHub", page_icon="📊", layout="wide")

# ---------------------------------------------------------------- palette (mint + cream)
MINT = "#8FBC8F"
MINT_DARK = "#4A7C4A"
MINT_LIGHT = "#D9E8D9"
PEACH = "#E8A87C"
CREAM = "#FFFBF5"
TEXT = "#2F4F2F"

st.markdown(
    f"""
    <style>
        .stApp {{ background-color: {CREAM}; }}
        section[data-testid="stSidebar"] {{ background-color: #F5F9F2; }}
        h1, h2, h3 {{ color: {TEXT}; }}
        .insight-card {{
            background: #FFFFFF;
            padding: 1rem 1.25rem;
            border-radius: 14px;
            border: 1px solid #E3EDE0;
            margin-bottom: 1rem;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Health & Finance Insights")
st.caption("Interactive analytics across your appointments, records, and claims.")

# ---------------------------------------------------------------- data
celina = load_celina()
finances = load_finances()
records = load_records()["history"]
appointments = load_appointments()["upcoming"]

# ---------------------------------------------------------------- top row: 3 KPIs
col_a, col_b, col_c = st.columns(3)

total_visits = len(records)
total_spent = finances["summary"]["total_billed_eur"]
total_reimbursed = finances["summary"]["total_covered_eur"]
reimbursement_rate = int(100 * total_reimbursed / total_spent) if total_spent else 0

# preventive care score: % of recommended annual screenings up to date
recommended = ["Dentist", "Dermatologist", "Gynecologist", "General Practitioner", "Ophthalmologist"]
today = date(2026, 4, 22)
up_to_date = 0
for spec in recommended:
    latest = max(
        (datetime.strptime(r["date"], "%Y-%m-%d").date() for r in records if r["specialty"] == spec),
        default=None,
    )
    if latest and (today - latest).days <= 365:
        up_to_date += 1
preventive_score = int(100 * up_to_date / len(recommended))

with col_a:
    st.metric("🩺 Total visits (all time)", total_visits)
with col_b:
    st.metric("💶 Reimbursement rate", f"{reimbursement_rate}%",
              help=f"€{total_reimbursed:.0f} covered of €{total_spent:.0f} billed")
with col_c:
    st.metric("🛡️ Preventive-care score", f"{preventive_score}%",
              help=f"{up_to_date} of {len(recommended)} annual screenings up to date")

st.markdown("---")

# ---------------------------------------------------------------- chart 1: spending over time
st.markdown("### 💸 Healthcare spending over time")

claims = finances["claims"]
df_claims = pd.DataFrame(claims)
df_claims["date"] = pd.to_datetime(df_claims["date"])
df_claims = df_claims.sort_values("date")
df_claims["cumulative_billed"] = df_claims["amount_eur"].cumsum()
df_claims["cumulative_covered"] = df_claims["covered_eur"].cumsum()
df_claims["cumulative_out_of_pocket"] = df_claims["out_of_pocket_eur"].cumsum()

fig_spending = go.Figure()
fig_spending.add_trace(
    go.Scatter(
        x=df_claims["date"], y=df_claims["cumulative_billed"],
        mode="lines+markers", name="Total billed",
        line=dict(color=MINT_DARK, width=3),
        fill="tozeroy", fillcolor="rgba(143,188,143,0.15)",
    )
)
fig_spending.add_trace(
    go.Scatter(
        x=df_claims["date"], y=df_claims["cumulative_covered"],
        mode="lines+markers", name="Covered by Debeka",
        line=dict(color=MINT, width=3, dash="dot"),
    )
)
fig_spending.add_trace(
    go.Scatter(
        x=df_claims["date"], y=df_claims["cumulative_out_of_pocket"],
        mode="lines+markers", name="Your share (out of pocket)",
        line=dict(color=PEACH, width=3),
    )
)
fig_spending.update_layout(
    plot_bgcolor="#FFFFFF", paper_bgcolor=CREAM,
    xaxis=dict(title="Date", showgrid=True, gridcolor="#F0F4EE"),
    yaxis=dict(title="Cumulative € (EUR)", showgrid=True, gridcolor="#F0F4EE"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=30, b=20),
    height=380,
)
st.plotly_chart(fig_spending, use_container_width=True)

# ---------------------------------------------------------------- row: donut + gauge
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🩺 Visits by specialty")
    spec_counts = Counter(r["specialty"] for r in records)
    fig_donut = go.Figure(
        data=[
            go.Pie(
                labels=list(spec_counts.keys()),
                values=list(spec_counts.values()),
                hole=0.55,
                marker=dict(
                    colors=["#8FBC8F", "#4A7C4A", "#D9E8D9", "#E8A87C", "#B8D8B8", "#6DAB6D"]
                ),
                textinfo="label+percent",
                textfont=dict(color=TEXT, size=12),
            )
        ]
    )
    fig_donut.update_layout(
        plot_bgcolor="#FFFFFF", paper_bgcolor=CREAM,
        showlegend=False,
        margin=dict(l=20, r=20, t=10, b=20),
        height=350,
        annotations=[
            dict(
                text=f"<b>{total_visits}</b><br><span style='font-size:0.75rem;color:#6B7F6B'>visits</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=22, color=MINT_DARK),
            )
        ],
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with col2:
    st.markdown("### 🛡️ Preventive-care coverage")
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=preventive_score,
            number={"suffix": "%", "font": {"size": 42, "color": MINT_DARK}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#6B7F6B"},
                "bar": {"color": MINT_DARK},
                "bgcolor": "#FFFFFF",
                "steps": [
                    {"range": [0, 50], "color": "#FFE4D1"},
                    {"range": [50, 80], "color": "#FFF4E0"},
                    {"range": [80, 100], "color": MINT_LIGHT},
                ],
                "threshold": {
                    "line": {"color": MINT_DARK, "width": 3},
                    "thickness": 0.8, "value": 80,
                },
            },
        )
    )
    fig_gauge.update_layout(
        paper_bgcolor=CREAM, margin=dict(l=20, r=20, t=30, b=20), height=350,
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    missing = [
        spec for spec in recommended
        if not any(
            r["specialty"] == spec
            and (today - datetime.strptime(r["date"], "%Y-%m-%d").date()).days <= 365
            for r in records
        )
    ]
    if missing:
        st.info(f"📌 Overdue: {', '.join(missing)}", icon="⏰")

# ---------------------------------------------------------------- chart 4: coverage by service
st.markdown("### 📋 Reimbursement rate by service")

service_totals: dict[str, dict[str, float]] = defaultdict(lambda: {"billed": 0.0, "covered": 0.0})
for c in claims:
    service_totals[c["service"]]["billed"] += c["amount_eur"]
    service_totals[c["service"]]["covered"] += c["covered_eur"]

rows = []
for service, totals in service_totals.items():
    pct = int(100 * totals["covered"] / totals["billed"]) if totals["billed"] else 0
    rows.append({
        "Service": service,
        "Billed (€)": totals["billed"],
        "Covered (€)": totals["covered"],
        "Coverage %": pct,
    })
df_cov = pd.DataFrame(rows).sort_values("Coverage %")

fig_bar = px.bar(
    df_cov,
    x="Coverage %",
    y="Service",
    orientation="h",
    text="Coverage %",
    color="Coverage %",
    color_continuous_scale=[[0, PEACH], [0.5, "#F5D5B0"], [1, MINT]],
    range_color=[0, 100],
)
fig_bar.update_traces(
    texttemplate="%{text}%",
    textposition="outside",
    textfont=dict(color=TEXT),
)
fig_bar.update_layout(
    plot_bgcolor="#FFFFFF", paper_bgcolor=CREAM,
    xaxis=dict(title="Covered (%)", range=[0, 110], showgrid=True, gridcolor="#F0F4EE"),
    yaxis=dict(title=""),
    margin=dict(l=20, r=20, t=20, b=20),
    height=380,
    coloraxis_showscale=False,
)
st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------------- footer summary
st.markdown(
    f"""
    <div class="insight-card">
        <strong style="color:{MINT_DARK};">🌿 Summary:</strong>
        {celina['name'].split()[0]} has had <b>{total_visits} medical visits</b> across
        <b>{len(spec_counts)} specialties</b>, with <b>{reimbursement_rate}% of costs</b>
        reimbursed by her {celina['insurance']['provider']} Premium Plus tariff.
        She's up to date on <b>{up_to_date} of {len(recommended)}</b> recommended annual screenings.
    </div>
    """,
    unsafe_allow_html=True,
)

render_chatbot_sidebar()
