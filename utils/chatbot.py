"""Claude-powered chatbot with Celina's data as context. Falls back to demo mode if no API key."""
import json
import streamlit as st

from utils.data_loader import load_all
from utils.database import (
    clear_chat_history,
    init_db,
    load_chat_history,
    save_chat_message,
)

SYSTEM_PROMPT = """You are HealthBuddy, a friendly health assistant inside MyHealthHub — a personal health dashboard for Celina Becker.

You have full access to Celina's health data below and should use it to answer her questions accurately and concisely. Always respond in English. Be warm, practical, and brief (2-4 sentences unless she asks for more).

You can help with:
- Upcoming appointments (dates, doctors, what to bring, what to expect)
- Medical records (past visits, test results, vaccinations)
- Finances (what insurance covered, what's pending, tariff details)
- General health questions based on her profile

Never invent medical advice. If asked something clinical you can't answer from her records, suggest she ask her doctor.

--- CELINA'S DATA ---
{data}
--- END DATA ---

Today's date: 2026-04-22.
"""

DEMO_RESPONSES = {
    "appointment": "Your next appointment is a **Dental Cleaning with Dr. Schmidt on May 5, 2026 at 09:30**. It's fully covered by your Premium Plus tariff. 🦷",
    "next": "Your next appointment is a **Dental Cleaning with Dr. Schmidt on May 5, 2026 at 09:30**. 🦷",
    "dentist": "Your last dental visit was on Nov 20, 2025 (cleaning + X-ray, no cavities). Next cleaning is scheduled for May 5, 2026 with Dr. Schmidt.",
    "blood": "Your last blood test was on Jan 15, 2026. Everything normal except **Vitamin D was low (18 ng/mL)** — Dr. Bauer recommended supplementation.",
    "vitamin": "Your Vitamin D was low (18 ng/mL) in your January 2026 blood test. You're currently taking a D3 supplement.",
    "insurance": "You're with **Debeka, Tarif Premium Plus** (private). Monthly premium: €487.50. Your deductible of €500 is €312.50 used for 2026.",
    "covered": "In 2026 so far, €2,420 of €2,847.50 has been covered by Debeka. €215 from physio hasn't been submitted yet — want me to remind you?",
    "pending": "You have one claim pending reimbursement (€180 dermatology follow-up from March 18) and €215 in physio costs not yet submitted.",
    "allerg": "You're allergic to **Penicillin** and have **pollen-triggered hay fever**. Always mention Penicillin when prescribed antibiotics.",
    "vaccin": "Your vaccinations are up to date: COVID booster (May 2023), HPV series complete (Feb 2022), flu shot (Oct 2024). Next flu shot is scheduled for Oct 8, 2026. 💉",
    "skin": "Your last skin check was June 5, 2025 — one mole on your upper back is being monitored (benign). Next screening: June 12, 2026 with Dr. Müller.",
    "gyn": "Your last gynecology check was July 18, 2025 — all results normal (pap smear clear, HPV negative). Next check: July 20, 2026 with Dr. Weber.",
    "default": "I can help with your appointments, medical records, insurance claims, or general health questions. What would you like to know?",
}


def _demo_reply(user_msg: str) -> str:
    """Lightweight keyword-matching fallback when no API key is set."""
    msg = user_msg.lower()
    for keyword, reply in DEMO_RESPONSES.items():
        if keyword in msg:
            return reply
    return DEMO_RESPONSES["default"]


def _get_api_key() -> str | None:
    try:
        return st.secrets.get("ANTHROPIC_API_KEY")
    except (FileNotFoundError, KeyError, AttributeError):
        return None


def ask_claude(user_msg: str, history: list[dict]) -> str:
    """Send a message to Claude with Celina's data as system context.

    Falls back to demo responses if no API key is configured.
    """
    api_key = _get_api_key()

    if not api_key:
        return _demo_reply(user_msg)

    try:
        from anthropic import Anthropic
    except ImportError:
        return "⚠️ `anthropic` package not installed. Run: `pip install anthropic`"

    client = Anthropic(api_key=api_key)
    data = load_all()

    messages = history + [{"role": "user", "content": user_msg}]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=SYSTEM_PROMPT.format(data=json.dumps(data, indent=2)),
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Claude API error: {e}\n\nFalling back to demo mode:\n\n{_demo_reply(user_msg)}"


def render_chatbot_sidebar() -> None:
    """Render the persistent chatbot in the sidebar. History persists in SQLite."""
    init_db()
    with st.sidebar:
        st.markdown("### 💬 HealthBuddy")
        st.caption("Ask me anything about your health data.")

        if not _get_api_key():
            st.info("🔑 Running in **demo mode** — add your Claude API key to `.streamlit/secrets.toml` for full AI responses.", icon="ℹ️")

        history = load_chat_history()

        chat_container = st.container(height=320)
        with chat_container:
            if not history:
                st.markdown(
                    "<div style='color:#8FA68F; font-size:0.85rem; padding:0.5rem;'>"
                    "Try: <i>\"When is my next appointment?\"</i> or <i>\"What did my last blood test show?\"</i>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            for msg in history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if prompt := st.chat_input("Ask HealthBuddy..."):
            save_chat_message("user", prompt)
            with st.spinner("Thinking..."):
                reply = ask_claude(prompt, history)
            save_chat_message("assistant", reply)
            st.rerun()

        if history:
            if st.button("🧹 Clear chat", use_container_width=True):
                clear_chat_history()
                st.rerun()
