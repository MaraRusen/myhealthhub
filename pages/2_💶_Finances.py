"""Finances — insurance tariff, claims, and coverage. Protected by Face ID."""
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.auth import face_id_gate, logout
from utils.chatbot import render_chatbot_sidebar
from utils.data_loader import load_celina, load_finances
from utils.database import get_submitted_claims, init_db, mark_claim_submitted

EXAMPLE_RECEIPT = Path(__file__).parent.parent / "example_doctor_$.png"

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
        .receipt-box {
            background: #FFFFFF;
            padding: 1.5rem;
            border-radius: 14px;
            border: 2px dashed #8FBC8F;
            margin: 1.5rem 0;
        }
        .extract-row {
            display: flex; justify-content: space-between;
            padding: 0.45rem 0; border-bottom: 1px dashed #E3EDE0;
        }
        .extract-row span.key { color:#6B7F6B; font-size:0.9rem; }
        .extract-row span.val { color:#2F4F2F; font-weight:600; }
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

# ---------------------------------------------------------------- receipt upload / camera
st.markdown("### 📸 Add a new claim by receipt")
st.caption("Snap a photo of your doctor's invoice, upload one from files, or try the example image.")

with st.container():
    st.markdown('<div class="receipt-box">', unsafe_allow_html=True)

    method = st.radio(
        "How would you like to add the receipt?",
        ["📁 Upload from files", "📷 Take a photo", "🖼️ Use example receipt"],
        horizontal=True,
        key="receipt_method",
    )

    image_source = None
    if method == "📁 Upload from files":
        uploaded = st.file_uploader(
            "Choose an invoice image",
            type=["png", "jpg", "jpeg"],
            key="receipt_upload",
        )
        if uploaded:
            image_source = uploaded

    elif method == "📷 Take a photo":
        snap = st.camera_input("Take a photo of your receipt", key="receipt_camera")
        if snap:
            image_source = snap

    else:  # Example receipt
        if EXAMPLE_RECEIPT.exists():
            image_source = str(EXAMPLE_RECEIPT)
        else:
            st.warning("Example receipt not found.")

    if image_source is not None:
        col_img, col_extract = st.columns([1, 1])
        with col_img:
            st.image(
                image_source,
                caption="📄 Uploaded receipt",
                use_container_width=True,
            )
        with col_extract:
            st.markdown("#### 🤖 AI extraction")
            if "receipt_extracted" not in st.session_state:
                with st.spinner("Scanning receipt with AI..."):
                    time.sleep(1.2)
                st.session_state.receipt_extracted = True

            st.success("✅ Extraction complete")
            st.markdown(
                """
                <div class="extract-row"><span class="key">Doctor</span><span class="val">Dr. Markus Huber</span></div>
                <div class="extract-row"><span class="key">Specialty</span><span class="val">General Practitioner</span></div>
                <div class="extract-row"><span class="key">Date</span><span class="val">2026-04-15</span></div>
                <div class="extract-row"><span class="key">Services</span><span class="val">Consultation + Lab test</span></div>
                <div class="extract-row"><span class="key">Amount</span><span class="val">€142.50</span></div>
                <div class="extract-row"><span class="key">Expected coverage</span><span class="val">€142.50 (100%)</span></div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)
            col_submit, col_reset = st.columns([2, 1])
            with col_submit:
                if st.button("📤 Submit this claim to Debeka", type="primary", use_container_width=True):
                    st.toast(
                        "✉️ Claim submitted — expected reimbursement in 10-14 days.",
                        icon="✅",
                    )
                    st.balloons()
            with col_reset:
                if st.button("🔄 Scan another", use_container_width=True):
                    st.session_state.pop("receipt_extracted", None)
                    st.session_state.pop("receipt_upload", None)
                    st.session_state.pop("receipt_camera", None)
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

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
