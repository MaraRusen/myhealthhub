"""MyHealthHub — Home Dashboard."""
from datetime import date, datetime

import streamlit as st

from utils.chatbot import render_chatbot_sidebar
from utils.data_loader import load_all

st.set_page_config(
    page_title="MyHealthHub",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------- styling
st.markdown(
    """
    <style>
        .stApp { background-color: #FFFBF5; }
        section[data-testid="stSidebar"] { background-color: #F5F9F2; }
        h1, h2, h3 { color: #3A5F3A; }
        .kpi-card {
            background: #FFFFFF;
            padding: 1.25rem 1.5rem;
            border-radius: 14px;
            border: 1px solid #E3EDE0;
            box-shadow: 0 1px 3px rgba(74,124,74,0.05);
            height: 100%;
        }
        .kpi-label {
            font-size: 0.8rem;
            color: #6B7F6B;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 0 0 0.4rem 0;
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 600;
            color: #3A5F3A;
            margin: 0;
            line-height: 1.2;
        }
        .kpi-sub {
            font-size: 0.85rem;
            color: #8FA68F;
            margin: 0.3rem 0 0 0;
        }
        .hero {
            background: linear-gradient(135deg, #D9E8D9 0%, #F5F9F2 100%);
            padding: 2rem 2rem 1.5rem 2rem;
            border-radius: 18px;
            margin-bottom: 1.5rem;
        }
        .hero h1 { margin: 0; color: #2F4F2F; }
        .hero p { color: #4A6B4A; margin: 0.4rem 0 0 0; }
        .quick-card {
            background: #FFFFFF;
            padding: 1rem 1.2rem;
            border-radius: 12px;
            border-left: 4px solid #8FBC8F;
            margin-bottom: 0.6rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- data
data = load_all()
celina = data["celina"]
appointments = data["appointments"]["upcoming"]
records = data["records"]["history"]
finances = data["finances"]

today = date(2026, 4, 22)
upcoming_sorted = sorted(
    appointments,
    key=lambda a: datetime.strptime(a["date"], "%Y-%m-%d").date(),
)
next_appt = next(
    (a for a in upcoming_sorted if datetime.strptime(a["date"], "%Y-%m-%d").date() >= today),
    None,
)
last_record = max(records, key=lambda r: r["date"])

days_since_last = (today - datetime.strptime(last_record["date"], "%Y-%m-%d").date()).days
days_until_next = (
    (datetime.strptime(next_appt["date"], "%Y-%m-%d").date() - today).days if next_appt else None
)

# ---------------------------------------------------------------- hero
st.markdown(
    f"""
    <div class="hero">
        <h1>🌿 Welcome back, {celina['name'].split()[0]}</h1>
        <p>Your personal health overview — everything in one place.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <p class="kpi-label">📅 Next Appointment</p>
            <p class="kpi-value">{next_appt['type'] if next_appt else '—'}</p>
            <p class="kpi-sub">{'in ' + str(days_until_next) + ' days' if days_until_next is not None else 'none scheduled'}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <p class="kpi-label">💶 Open Balance (2026)</p>
            <p class="kpi-value">€{finances['summary']['total_out_of_pocket_eur']:.2f}</p>
            <p class="kpi-sub">€{finances['summary']['pending_submission_eur']:.0f} not yet submitted</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <p class="kpi-label">📋 Records on File</p>
            <p class="kpi-value">{len(records)}</p>
            <p class="kpi-sub">last visit {days_since_last} days ago</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    coverage_pct = int(
        100
        * finances["summary"]["total_covered_eur"]
        / finances["summary"]["total_billed_eur"]
    )
    st.markdown(
        f"""
        <div class="kpi-card">
            <p class="kpi-label">🛡️ Insurance Coverage</p>
            <p class="kpi-value">{coverage_pct}%</p>
            <p class="kpi-sub">{celina['insurance']['provider']} · {celina['insurance']['tariff']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------- quick views
left, right = st.columns([1.1, 1])

with left:
    st.markdown("### 📅 Coming up next")
    for appt in upcoming_sorted[:3]:
        appt_date = datetime.strptime(appt["date"], "%Y-%m-%d").date()
        days = (appt_date - today).days
        when = f"in {days} days" if days > 0 else "today" if days == 0 else "past"
        st.markdown(
            f"""
            <div class="quick-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="color:#3A5F3A;">{appt['icon']} {appt['type']}</strong><br>
                        <span style="color:#6B7F6B; font-size:0.9rem;">
                            {appt['doctor']} · {appt['specialty']}
                        </span>
                    </div>
                    <div style="text-align:right;">
                        <strong style="color:#4A7C4A;">{appt['date']}</strong><br>
                        <span style="color:#8FA68F; font-size:0.85rem;">{when} · {appt['time']}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with right:
    st.markdown("### 📋 Recent records")
    for rec in sorted(records, key=lambda r: r["date"], reverse=True)[:3]:
        st.markdown(
            f"""
            <div class="quick-card">
                <strong style="color:#3A5F3A;">{rec['icon']} {rec['type']}</strong><br>
                <span style="color:#6B7F6B; font-size:0.9rem;">
                    {rec['doctor']} · {rec['date']}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------- nav hint
st.info(
    "💡 Use the sidebar to explore **Appointments**, **Finances**, and **Records** — "
    "or ask **HealthBuddy** anything about your data.",
    icon="🌿",
)

# ---------------------------------------------------------------- sidebar chatbot
render_chatbot_sidebar()
