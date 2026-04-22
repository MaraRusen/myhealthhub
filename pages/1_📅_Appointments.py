"""Appointments — upcoming medical appointments for Celina."""
from datetime import date, datetime

import streamlit as st

from utils.chatbot import render_chatbot_sidebar
from utils.data_loader import load_appointments, load_celina
from utils.database import init_db, set_reminder, get_reminders, clear_reminder

init_db()

st.set_page_config(page_title="Appointments · MyHealthHub", page_icon="📅", layout="wide")

st.markdown(
    """
    <style>
        .stApp { background-color: #FFFBF5; }
        section[data-testid="stSidebar"] { background-color: #F5F9F2; }
        h1, h2, h3 { color: #3A5F3A; }
        .appt-card {
            background: #FFFFFF;
            padding: 1.25rem 1.5rem;
            border-radius: 14px;
            border: 1px solid #E3EDE0;
            margin-bottom: 1rem;
            border-left: 5px solid #8FBC8F;
        }
        .appt-card.high { border-left-color: #E8A87C; }
        .appt-title { font-size: 1.15rem; font-weight: 600; color: #2F4F2F; margin: 0; }
        .appt-meta { color: #6B7F6B; font-size: 0.9rem; margin: 0.3rem 0; }
        .appt-date-badge {
            display: inline-block;
            background: #D9E8D9;
            color: #2F4F2F;
            padding: 0.3rem 0.7rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📅 Upcoming Appointments")
st.caption("All your scheduled medical appointments in one place.")

appointments = load_appointments()["upcoming"]
today = date(2026, 4, 22)
appointments_sorted = sorted(
    appointments,
    key=lambda a: datetime.strptime(a["date"], "%Y-%m-%d").date(),
)

reminders_set = get_reminders()
celina_email = load_celina()["email"]

# ---------------------------------------------------------------- filter bar
specialties = sorted({a["specialty"] for a in appointments_sorted})
selected = st.multiselect(
    "Filter by specialty",
    options=specialties,
    default=specialties,
)

filtered = [a for a in appointments_sorted if a["specialty"] in selected]

st.markdown(f"**{len(filtered)}** upcoming appointments")
st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------- cards
for appt in filtered:
    appt_date = datetime.strptime(appt["date"], "%Y-%m-%d").date()
    days = (appt_date - today).days
    days_text = f"in {days} days" if days > 0 else ("today" if days == 0 else f"{-days} days ago")
    priority_class = "high" if appt["priority"] == "high" else ""

    with st.container():
        st.markdown(
            f"""
            <div class="appt-card {priority_class}">
                <div style="display:flex; justify-content:space-between; align-items:start; gap:1rem;">
                    <div style="flex:1;">
                        <p class="appt-title">{appt['icon']} {appt['type']}</p>
                        <p class="appt-meta">👨‍⚕️ <strong>{appt['doctor']}</strong> · {appt['specialty']}</p>
                        <p class="appt-meta">📍 {appt['location']}<br>
                            <span style="color:#8FA68F; font-size:0.85rem;">{appt['address']}</span>
                        </p>
                        <p class="appt-meta">📝 {appt['notes']}</p>
                    </div>
                    <div style="text-align:right; min-width:140px;">
                        <span class="appt-date-badge">{appt['date']}</span>
                        <p class="appt-meta" style="margin-top:0.4rem;">🕐 {appt['time']}</p>
                        <p class="appt-meta" style="color:#4A7C4A; font-weight:600;">{days_text}</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_a, col_b, col_c = st.columns([1.2, 1, 3])
        with col_a:
            reminder_key = f"reminder_{appt['id']}"
            if appt["id"] in reminders_set:
                if st.button("🔕 Cancel reminder", key=f"cancel_{appt['id']}"):
                    clear_reminder(appt["id"])
                    st.toast(f"Reminder for {appt['type']} cancelled.", icon="🔕")
                    st.rerun()
            else:
                if st.button("🔔 Remind me by email", key=reminder_key):
                    set_reminder(appt["id"], celina_email)
                    st.toast(
                        f"✉️ Email reminder set for {appt['type']} — we'll notify {celina_email} 2 days before.",
                        icon="🔔",
                    )
                    st.rerun()
        with col_b:
            st.caption(
                f"💰 €{appt['estimated_cost_eur']:.0f} · covered €{appt['estimated_coverage_eur']:.0f}"
            )

render_chatbot_sidebar()
