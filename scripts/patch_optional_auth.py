from pathlib import Path

TARGETS = [Path("app.py"), *sorted(Path("pages").glob("*.py"))]
IMPORT = "from meetinglens_auth import require_user\n"
CALL = "identity = require_user()\n"


def patch(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    if IMPORT.strip() not in text:
        marker = "import streamlit as st\n"
        if marker not in text:
            raise SystemExit(f"streamlit import not found in {path}")
        text = text.replace(marker, marker + IMPORT, 1)

    if CALL.strip() not in text:
        lines = text.splitlines(keepends=True)
        output = []
        inserted = False
        in_config = False
        balance = 0
        for line in lines:
            output.append(line)
            if not inserted and not in_config and "st.set_page_config(" in line:
                in_config = True
                balance = line.count("(") - line.count(")")
                if balance <= 0:
                    output.append("\n" + CALL)
                    inserted = True
                    in_config = False
            elif in_config:
                balance += line.count("(") - line.count(")")
                if balance <= 0:
                    output.append("\n" + CALL)
                    inserted = True
                    in_config = False
        if not inserted:
            raise SystemExit(f"set_page_config not found or incomplete in {path}")
        text = "".join(output)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


changed = []
for target in TARGETS:
    if patch(target):
        changed.append(str(target))
print("Patched:", ", ".join(changed) if changed else "nothing")
