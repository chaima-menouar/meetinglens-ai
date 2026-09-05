from training.ami_dataset import _collect_summary_link_labels, extract_ref_ids, infer_label


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


def test_summary_links_map_dialogue_acts_to_sections(tmp_path):
    abstractive = tmp_path / "abstractive"
    extractive = tmp_path / "extractive"
    abstractive.mkdir()
    extractive.mkdir()

    (abstractive / "ES2002a.abssumm.xml").write_text(
        '''<?xml version="1.0"?>
<nite:root xmlns:nite="http://nite.sourceforge.net/">
  <decisions nite:id="decisions.1"><sentence nite:id="s.dec">Ship Friday.</sentence></decisions>
  <actions nite:id="actions.1"><sentence nite:id="s.act">Maya validates analytics.</sentence></actions>
  <problems nite:id="problems.1"><sentence nite:id="s.risk">Release dependency is open.</sentence></problems>
</nite:root>''',
        encoding="utf-8",
    )
    (extractive / "ES2002a.summlink.xml").write_text(
        '''<?xml version="1.0"?>
<nite:root xmlns:nite="http://nite.sourceforge.net/">
  <summlink nite:id="l1"><nite:pointer role="extractive" href="ES2002a.A.dialog-act.xml#id(da.dec)"/><nite:pointer role="abstractive" href="ES2002a.abssumm.xml#id(s.dec)"/></summlink>
  <summlink nite:id="l2"><nite:pointer role="extractive" href="ES2002a.B.dialog-act.xml#id(da.act)"/><nite:pointer role="abstractive" href="ES2002a.abssumm.xml#id(s.act)"/></summlink>
  <summlink nite:id="l3"><nite:pointer role="extractive" href="ES2002a.C.dialog-act.xml#id(da.risk)"/><nite:pointer role="abstractive" href="ES2002a.abssumm.xml#id(s.risk)"/></summlink>
</nite:root>''',
        encoding="utf-8",
    )

    labels = _collect_summary_link_labels(tmp_path)
    assert labels["da.dec"] == "decision"
    assert labels["da.act"] == "action"
    assert labels["da.risk"] == "risk"
