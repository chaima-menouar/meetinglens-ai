from __future__ import annotations

from typing import Any

import streamlit as st


def auth_enabled() -> bool:
    """Return True only when a Streamlit OIDC configuration is present."""
    try:
        auth = st.secrets.get("auth", {})
    except Exception:
        return False
    if not auth:
        return False
    try:
        return bool(auth.get("redirect_uri") and auth.get("cookie_secret"))
    except Exception:
        return False


def current_identity() -> dict[str, Any]:
    if not auth_enabled():
        return {
            "mode": "disabled",
            "authenticated": False,
            "name": "Local user",
            "email": "",
            "subject": "local",
        }
    try:
        logged_in = bool(st.user.is_logged_in)
    except Exception:
        logged_in = False
    if not logged_in:
        return {
            "mode": "oidc",
            "authenticated": False,
            "name": "",
            "email": "",
            "subject": "",
        }
    try:
        values = st.user.to_dict()
    except Exception:
        values = {}
    subject = str(values.get("sub") or values.get("email") or values.get("name") or "user")
    return {
        "mode": "oidc",
        "authenticated": True,
        "name": str(values.get("name") or values.get("email") or "User"),
        "email": str(values.get("email") or ""),
        "subject": subject,
    }


def require_user() -> dict[str, Any]:
    """Gate a page only when OIDC is configured; otherwise preserve public/single-user mode."""
    identity = current_identity()
    if identity["mode"] == "disabled":
        return identity
    if not identity["authenticated"]:
        st.markdown("## MeetingLens AI")
        st.caption("This deployment requires an authenticated account.")
        st.button("Sign in", type="primary", on_click=st.login)
        st.stop()
    with st.sidebar:
        st.caption(f"Signed in · {identity['name']}")
        st.button("Sign out", on_click=st.logout, use_container_width=True)
    return identity
