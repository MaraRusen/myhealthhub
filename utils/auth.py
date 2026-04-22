"""Simulated Face ID authentication gate."""
import time
import streamlit as st


def face_id_gate(section_name: str = "Finances") -> bool:
    """Render a Face ID button. Returns True once the user is authenticated for this session."""
    key = f"auth_{section_name.lower()}"

    if st.session_state.get(key, False):
        return True

    st.markdown(
        f"""
        <div style="text-align:center; padding:3rem 1rem; background:#FFFFFF;
                    border-radius:16px; border:1px solid #D9E8D9; margin:2rem 0;">
            <div style="font-size:4rem;">🔒</div>
            <h2 style="color:#4A7C4A; margin:0.5rem 0;">{section_name} is protected</h2>
            <p style="color:#6B7F6B; font-size:0.95rem;">
                This section contains sensitive financial information.<br>
                Authenticate with Face ID to continue.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔐  Authenticate with Face ID", use_container_width=True, type="primary"):
            with st.spinner("Scanning face..."):
                progress = st.progress(0)
                for pct in range(0, 101, 10):
                    time.sleep(0.08)
                    progress.progress(pct)
                progress.empty()
            st.session_state[key] = True
            st.success("✅ Authentication successful — access granted")
            time.sleep(0.6)
            st.rerun()

    return False


def logout(section_name: str = "Finances") -> None:
    """Clear authentication for a section."""
    key = f"auth_{section_name.lower()}"
    if key in st.session_state:
        st.session_state[key] = False
