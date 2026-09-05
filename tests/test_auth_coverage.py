from pathlib import Path


def test_main_and_all_pages_use_auth_gate():
    targets = [Path("app.py"), *sorted(Path("pages").glob("*.py"))]
    assert targets
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "from meetinglens_auth import require_user" in text, f"Missing auth import in {path}"
        assert "require_user()" in text, f"Missing auth gate in {path}"
