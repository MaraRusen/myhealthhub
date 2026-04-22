"""Finances — insurance tariff, claims, and coverage. Protected by Face ID."""
import pandas as pd
import streamlit as st

from utils.auth import face_id_gate, logout
from utils.chatbot import render_chatbot_sidebar
from utils.data_loader import load_celina, load_finances
from utils.database import get_submitted_claims, init_db, mark_claim_submitted

init_db()

st.set_page_config(page_title="Finances · MyHealthHub", page_icon="💶", layout="wide")

st.markdown(
    """
    <style>
        .stApp { background-color: #FFFBF5; }
        section[data-testid="stSidebar"] { background-color: #F5F9F2; }
        h1, h2, h3 { color: #3A5F3A; }
        .fin-kpi {
            background: #FFFFFF;
            padding: 1.25rem 1.5rem;
            border-radius: 14px;
            border: 1px solid #E3EDE0;
            height: 100%;
        }
        .fin-kpi .label {
            font-size: 0.75rem; color: #6B7F6B; text-transform: uppercase;
            letter-spacing: 0.05em; margin: 0;
        }
        .fin-kpi .value {
            font-size: 1.7rem; font-weight: 600; color: #3A5F3A; margin: 0.3rem 0 0 0;
        }
        .fin-kpi .sub { font-size: 0.85rem; color: #8FA68F; margin: 0.3rem 0 0 0; }
        .tariff-box {
            background: linear-gradient(135deg, #D9E8D9 0%, #F5F9F2 100%);
            padding: 1.5rem; border-radius: 14px; margin: 1rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

render_chatbot_sidebar()

# ---------------------------------------------------------------- auth gate
if not face_id_gate("Finances"):
    st.stop()

# ---------------------------------------------------------------- content (authenticated)
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.title("💶 Finances & Insurance")
    st.caption("Your claims, coverage, and tariff details.")
with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔓 Lock", use_container_width=True):
        logout("Finances")
        st.rerun()

celina = load_celina()
finances = load_finances()
summary = finances["summary"]
ins = celina["insurance"]

# ---------------------------------------------------------------- KPI row
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""<div class="fin-kpi">
            <p class="label">Total Billed {summary['year']}</p>
            <p class="value">€{summary['total_billed_eur']:.2f}</p>
            <p class="sub">across {len(finances['claims'])} claims</p>
        </div>""",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""<div class="fin-kpi">
            <p class="label">Covered by Debeka</p>
            <p class="value">€{summary['total_covered_eur']:.2f}</p>
            <p class="sub">{int(100*summary['total_covered_eur']/summary['total_billed_eur'])}% of total</p>
        </div>""",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""<div class="fin-kpi">
            <p class="label">Out of Pocket</p>
            <p class="value">€{summary['total_out_of_pocket_eur']:.2f}</p>
            <p class="sub">your share</p>
        </div>""",
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""<div class="fin-kpi">
            <p class="label">⏳ Open Balance</p>
            <p class="value">€{summary['pending_submission_eur'] + summary['pending_reimbursement_eur']:.2f}</p>
            <p class="sub">pending submit/reimburse</p>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------- tariff box
st.markdown(
    f"""
    <div class="tariff-box">
        <h3 style="margin:0;">🛡️ Your Tariff: {ins['provider']} · {ins['tariff']}</h3>
        <p style="color:#4A6B4A; margin:0.3rem 0 0 0;">
            Member since {ins['member_since']} · Policy #{ins['policy_number']}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("#### 💳 Premium & Deductible")
    st.metric("Monthly premium", f"€{ins['monthly_premium_eur']:.2f}")
    st.metric(
        "Annual deductible used",
        f"€{ins['deductible_used_eur']:.2f} / €{ins['annual_deductible_eur']:.0f}",
    )
    st.progress(ins["deductible_used_eur"] / ins["annual_deductible_eur"])

with col_b:
    st.markdown("#### 📋 Coverage Details")
    for service, pct in ins["coverage"].items():
        st.markdown(
            f"<div style='display:flex; justify-content:space-between; "
            f"padding:0.35rem 0; border-bottom:1px solid #F0F4EE;'>"
            f"<span style='color:#4A6B4A;'>{service.replace('_', ' ').title()}</span>"
            f"<strong style='color:#3A5F3A;'>{pct}</strong></div>",
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------- claims table
st.markdown("### 🧾 Claims & Reimbursements")

status_filter = st.radio(
    "Filter by status",
    ["All", "Reimbursed", "Pending reimbursement", "Not yet submitted"],
    horizontal=True,
)

# Overlay DB state: any claim marked as submitted in the DB moves from "Not yet submitted" to "Pending reimbursement"
submitted_ids = get_submitted_claims()
claims = []
for c in finances["claims"]:
    c = dict(c)
    if c["id"] in submitted_ids and c["status"] == "Not yet submitted":
        c["status"] = "Pending reimbursement"
    claims.append(c)

if status_filter != "All":
    claims = [c for c in claims if c["status"] == status_filter]

df = pd.DataFrame(claims)
if not df.empty:
    display_df = df[
        ["date", "service", "doctor", "amount_eur", "covered_eur", "out_of_pocket_eur", "status"]
    ].rename(
        columns={
            "date": "Date",
            "service": "Service",
            "doctor": "Provider",
            "amount_eur": "Billed (€)",
            "covered_eur": "Covered (€)",
            "out_of_pocket_eur": "Your share (€)",
            "status": "Status",
        }
    )
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Billed (€)": st.column_config.NumberColumn(format="€%.2f"),
            "Covered (€)": st.column_config.NumberColumn(format="€%.2f"),
            "Your share (€)": st.column_config.NumberColumn(format="€%.2f"),
        },
    )

    unsubmitted = [
        c for c in finances["claims"]
        if c["status"] == "Not yet submitted" and c["id"] not in submitted_ids
    ]
    if unsubmitted:
        st.warning(
            f"⚠️ You have **{len(unsubmitted)} claim(s)** not yet submitted "
            f"(€{sum(c['out_of_pocket_eur'] for c in unsubmitted):.2f}). "
            f"Submit them to get reimbursed.",
            icon="📤",
        )
        if st.button("📤 Submit all pending claims to Debeka"):
            for c in unsubmitted:
                mark_claim_submitted(c["id"])
            st.toast(
                f"✉️ {len(unsubmitted)} claim(s) submitted to Debeka — confirmation in 2-3 days.",
                icon="✅",
            )
            st.rerun()
else:
    st.info("No claims match this filter.")
