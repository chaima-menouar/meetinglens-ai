from training.ami_dataset import extract_ref_ids, infer_label


def test_extract_ref_ids_handles_range():
    href = "ES2008a.A.words.xml#id(ES2008a.A.words12)..id(ES2008a.A.words18)"
    assert extract_ref_ids(href) == ["ES2008a.A.words12", "ES2008a.A.words18"]


def test_decision_reference_has_priority():
    assert infer_label("statement", "we discussed the launch", decision_ref=True) == "decision"


def test_commit_maps_to_action():
    assert infer_label("commit", "I will send the notes tomorrow") == "action"


def test_risk_weak_label_uses_lexical_signal():
    assert infer_label("statement", "the dependency is blocking the release") == "risk"


def test_plain_statement_is_other():
    assert infer_label("statement", "the prototype is on the table") == "other"
