from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


ACTION_TYPES = {
    "commit", "directive", "suggest", "offer", "option", "action-directive",
}
DECISION_TYPES = {
    "decision", "decide", "agree", "accept", "confirm", "approved",
}
RISK_WORDS = {
    "risk", "blocked", "blocking", "blocker", "delay", "delayed", "issue",
    "problem", "concern", "dependency", "fail", "failure", "not ready",
}


@dataclass
class Example:
    meeting_id: str
    speaker: str
    text: str
    label: str
    dialogue_act: str = ""
    source_id: str = ""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _get_id(element: ET.Element) -> str:
    for key, value in element.attrib.items():
        if key.endswith("}id") or key in {"id", "nite:id"}:
            return value
    return ""


def _meeting_id(path: Path) -> str:
    name = path.name
    match = re.search(r"([A-Z]{2}\d{4}[a-z]?)", name)
    return match.group(1) if match else name.split(".")[0]


def _speaker_from_filename(path: Path) -> str:
    match = re.search(r"\.([A-Z])\.", path.name)
    return match.group(1) if match else "Speaker"


def extract_ref_ids(href: str) -> list[str]:
    """Extract NXT ids from href/xpointer expressions.

    Handles common forms such as #id(foo), id(foo)..id(bar), and
    xpointer(id(foo)). For ranges we return both endpoints; the builder
    expands the interval using the word-order index from the referenced file.
    """
    if not href:
        return []
    return re.findall(r"id\(([^)]+)\)", href)


def _token_text(element: ET.Element) -> str:
    text = " ".join(part.strip() for part in element.itertext() if part and part.strip())
    return re.sub(r"\s+", " ", text).strip()


def load_words(corpus_root: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    word_text: dict[str, str] = {}
    order_by_file: dict[str, list[str]] = {}
    candidates = list(corpus_root.rglob("*.words.xml")) + list(corpus_root.rglob("*words*.xml"))
    for path in sorted(set(candidates)):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        order: list[str] = []
        for el in root.iter():
            ident = _get_id(el)
            if not ident:
                continue
            text = _token_text(el)
            if text:
                word_text[ident] = text
                order.append(ident)
        if order:
            order_by_file[path.name] = order
    return word_text, order_by_file


def _expand_ref_ids(href: str, order_by_file: dict[str, list[str]]) -> list[str]:
    ids = extract_ref_ids(href)
    if len(ids) < 2:
        return ids
    file_match = re.search(r"([^/#]+\.xml)#", href)
    if not file_match:
        return ids
    order = order_by_file.get(file_match.group(1), [])
    try:
        start, end = order.index(ids[0]), order.index(ids[-1])
    except ValueError:
        return ids
    lo, hi = sorted((start, end))
    return order[lo : hi + 1]


def infer_label(dialogue_act: str, text: str, decision_ref: bool = False) -> str:
    da = (dialogue_act or "").lower().replace("_", "-")
    low = (text or "").lower()
    if decision_ref or any(token in da for token in DECISION_TYPES):
        return "decision"
    if any(token in da for token in ACTION_TYPES):
        return "action"
    if any(token in low for token in RISK_WORDS):
        return "risk"
    return "other"


def _dialogue_act_type(element: ET.Element) -> str:
    for key in ("niteType", "type", "da-type", "dialogue_act", "dialogue-act"):
        if key in element.attrib:
            return element.attrib[key]
    for key, value in element.attrib.items():
        if key.endswith("}type"):
            return value
    return ""


def _collect_decision_refs(corpus_root: Path) -> set[str]:
    refs: set[str] = set()
    for path in corpus_root.rglob("*.xml"):
        low = path.name.lower()
        if "decision" not in low:
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for el in root.iter():
            for value in el.attrib.values():
                if "href" in value or "id(" in value:
                    refs.update(extract_ref_ids(value))
            if _local_name(el.tag).lower() in {"child", "pointer"}:
                refs.update(extract_ref_ids(el.attrib.get("href", "")))
    return refs


def build_examples(corpus_root: str | Path) -> list[Example]:
    root_path = Path(corpus_root)
    word_text, order_by_file = load_words(root_path)
    decision_refs = _collect_decision_refs(root_path)
    examples: list[Example] = []

    files = [p for p in root_path.rglob("*.xml") if "dialog" in p.name.lower() or ".da" in p.name.lower()]
    for path in sorted(files):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        meeting = _meeting_id(path)
        speaker = _speaker_from_filename(path)
        for el in root.iter():
            da_type = _dialogue_act_type(el)
            if not da_type:
                continue
            source_id = _get_id(el)
            refs: list[str] = []
            for child in el.iter():
                href = child.attrib.get("href", "")
                if href:
                    refs.extend(_expand_ref_ids(href, order_by_file))
            tokens = [word_text[x] for x in refs if x in word_text]
            text = re.sub(r"\s+", " ", " ".join(tokens)).strip()
            if not text:
                text = _token_text(el)
            if not text or len(text) < 2:
                continue
            label = infer_label(da_type, text, decision_ref=source_id in decision_refs)
            examples.append(Example(meeting, speaker, text, label, da_type, source_id))
    return examples


def write_csv(examples: Iterable[Example], output_path: str | Path) -> None:
    rows = [asdict(x) for x in examples]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(Example.__annotations__.keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build MeetingLens training rows from AMI NXT annotations")
    parser.add_argument("corpus_root", help="Path to the extracted AMI manual annotations directory")
    parser.add_argument("--output", default="data/processed/ami_events.csv")
    args = parser.parse_args()

    data = build_examples(args.corpus_root)
    write_csv(data, args.output)
    counts: dict[str, int] = {}
    for row in data:
        counts[row.label] = counts.get(row.label, 0) + 1
    print(f"wrote {len(data)} examples to {args.output}")
    print("label distribution:", counts)
