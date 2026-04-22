"""Records — historical medical visits grouped by specialty."""
import streamlit as st

from utils.chatbot import render_chatbot_sidebar
from utils.data_loader import load_records

st.set_page_config(page_title="Records · MyHealthHub", page_icon="📋", layout="wide")

st.markdown(
    """
    <style>
        .stApp { background-color: #FFFBF5; }
        section[data-testid="stSidebar"] { background-color: #F5F9F2; }
        h1, h2, h3 { color: #3A5F3A; }
        .rec-card {
            background: #FFFFFF;
            padding: 1.2rem 1.4rem;
            border-radius: 12px;
            border: 1px solid #E3EDE0;
            margin-bottom: 0.8rem;
        }
        .rec-title { font-size: 1.05rem; font-weight: 600; color: #2F4F2F; margin: 0; }
        .rec-meta { color: #6B7F6B; font-size: 0.88rem; margin: 0.3rem 0; }
        .rec-findings {
            background: #F5F9F2; padding: 0.8rem 1rem; border-radius: 8px;
            color: #3A5F3A; font-size: 0.92rem; margin: 0.6rem 0;
        }
        .rec-result-row {
            display: flex; justify-content: space-between;
            padding: 0.3rem 0; border-bottom: 1px dashed #E3EDE0;
            font-size: 0.9rem;
        }
        .timeline-rail {
            position: relative;
            padding-left: 2rem;
            border-left: 3px solid #8FBC8F;
            margin-left: 1rem;
        }
        .timeline-dot {
            position: absolute;
            left: -0.7rem;
            width: 1.2rem;
            height: 1.2rem;
            background: #FFFFFF;
            border: 3px solid #4A7C4A;
            border-radius: 50%;
            margin-top: 0.4rem;
        }
        .timeline-item {
            position: relative;
            background: #FFFFFF;
            padding: 1rem 1.3rem;
            border-radius: 12px;
            border: 1px solid #E3EDE0;
            margin-bottom: 1.2rem;
        }
        .timeline-year {
            color: #4A7C4A;
            font-weight: 700;
            font-size: 1.1rem;
            margin: 1.5rem 0 0.8rem -0.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📋 Medical Records")
st.caption("Your complete health history — switch between specialty tabs or a chronological timeline.")

records = load_records()["history"]

# ---------------------------------------------------------------- view toggle
view = st.radio(
    "View",
    ["🗂️ By Specialty", "⏳ Timeline"],
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("<br>", unsafe_allow_html=True)


def _render_record_card(rec: dict) -> None:
    st.markdown(
        f"""
        <div class="rec-card">
            <div style="display:flex; justify-content:space-between;">
                <p class="rec-title">{rec['icon']} {rec['type']}</p>
                <span style="color:#4A7C4A; font-weight:600;">{rec['date']}</span>
            </div>
            <p class="rec-meta">👨‍⚕️ {rec['doctor']} · {rec['specialty']}</p>
            <div class="rec-findings">💡 <strong>Summary:</strong> {rec['findings']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("🔬 View detailed results"):
        for key, val in rec["key_results"].items():
            st.markdown(
                f"<div class='rec-result-row'>"
                f"<span style='color:#6B7F6B;'>{key}</span>"
                f"<strong style='color:#3A5F3A;'>{val}</strong></div>",
                unsafe_allow_html=True,
            )
        st.caption(f"📎 Attached file: `{rec['file']}`")


if view == "🗂️ By Specialty":
    # group by specialty
    by_spec: dict[str, list] = {}
    for rec in records:
        by_spec.setdefault(rec["specialty"], []).append(rec)
    for spec in by_spec:
        by_spec[spec].sort(key=lambda r: r["date"], reverse=True)

    spec_order = sorted(by_spec.keys(), key=lambda s: -len(by_spec[s]))

    st.markdown("### 🗂️ By specialty")
    cols = st.columns(len(spec_order))
    for col, spec in zip(cols, spec_order):
        with col:
            icon = by_spec[spec][0]["icon"]
            st.markdown(
                f"""
                <div style="background:#FFFFFF; padding:1rem; border-radius:12px;
                            border:1px solid #E3EDE0; text-align:center;">
                    <div style="font-size:1.8rem;">{icon}</div>
                    <div style="font-weight:600; color:#3A5F3A; margin-top:0.3rem;">{spec}</div>
                    <div style="color:#8FA68F; font-size:0.85rem;">{len(by_spec[spec])} records</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    tabs = st.tabs([f"{by_spec[s][0]['icon']} {s}" for s in spec_order])
    for tab, spec in zip(tabs, spec_order):
        with tab:
            for rec in by_spec[spec]:
                _render_record_card(rec)

else:
    st.markdown("### ⏳ Chronological timeline")
    st.caption("All medical events in reverse chronological order — newest at the top.")

    chrono = sorted(records, key=lambda r: r["date"], reverse=True)
    current_year = None

    st.markdown('<div class="timeline-rail">', unsafe_allow_html=True)
    for rec in chrono:
        year = rec["date"][:4]
        if year != current_year:
            st.markdown(f'<div class="timeline-year">📆 {year}</div>', unsafe_allow_html=True)
            current_year = year
        st.markdown('<div class="timeline-dot"></div>', unsafe_allow_html=True)
        _render_record_card(rec)
    st.markdown("</div>", unsafe_allow_html=True)

render_chatbot_sidebar()
