import meetinglens_auth


def test_auth_defaults_to_public_mode_without_oidc_secrets(monkeypatch):
    monkeypatch.setattr(meetinglens_auth, "auth_enabled", lambda: False)
    identity = meetinglens_auth.current_identity()
    assert identity["mode"] == "disabled"
    assert identity["authenticated"] is False
    assert identity["subject"] == "local"


def test_require_user_does_not_gate_when_auth_disabled(monkeypatch):
    monkeypatch.setattr(meetinglens_auth, "auth_enabled", lambda: False)
    identity = meetinglens_auth.require_user()
    assert identity["mode"] == "disabled"
    assert identity["name"] == "Local user"
