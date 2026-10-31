#!/usr/bin/env python3
"""Preview and export a reviewed Recall deck, without network or app access."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import sys

from export_deck import encode, strings, MAX_INPUT_BYTES

DEFAULTS = {
    "level": "matchSource", "difficulty": "mixed", "targetCards": 50,
    "answerLength": "brief", "questionPercent": 100, "cardForm": "basic",
    "coverage": "core", "sourcePolicy": "lectureOnly", "language": "matchSource",
}
CHOICES = {
    "difficulty": {"foundation", "application", "integration", "mixed"},
    "answerLength": {"brief", "balanced", "detailed"},
    "cardForm": {"basic", "cloze", "mixed"},
    "coverage": {"core", "objectives", "comprehensive", "selected"},
    "sourcePolicy": {"lectureOnly", "supplemented"},
}
ANSWER_RANGES = {"brief": (15, 30), "balanced": (30, 60), "detailed": (60, 100)}


def object_with_keys(value, allowed, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    if set(value) - set(allowed):
        raise ValueError(f"{label} contains unsupported fields")


def short_text(value, label, limit=200):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or "\x00" in value:
        raise ValueError(f"{label} must be nonempty text of at most {limit} characters")
    return value.strip()


def normalize_preferences(value):
    object_with_keys(value, DEFAULTS, "preferences")
    result = {**DEFAULTS, **value}
    for key, allowed in CHOICES.items():
        if not isinstance(result[key], str) or result[key] not in allowed:
            raise ValueError(f"preferences.{key} must be one of {', '.join(sorted(allowed))}")
    for key in ("level", "language"):
        result[key] = short_text(result[key], f"preferences.{key}")
    for key, lower, upper in (("targetCards", 1, 2000), ("questionPercent", 0, 100)):
        if type(result[key]) is not int or not lower <= result[key] <= upper:
            raise ValueError(f"preferences.{key} must be an integer from {lower} to {upper}")
    return result


def normalize_coverage(value):
    object_with_keys(value, {"included", "omitted", "limitations"}, "coverageReport")
    result = {}
    for key in ("included", "omitted", "limitations"):
        items = value.get(key, [])
        if not isinstance(items, list) or len(items) > 128:
            raise ValueError(f"coverageReport.{key} must be an array of at most 128 strings")
        result[key] = [short_text(item, f"coverageReport.{key}", 500) for item in items]
    return result


def prepare(request):
    object_with_keys(request, {"draftSchemaVersion", "preferences", "coverageReport", "draft"}, "request")
    if type(request.get("draftSchemaVersion")) is not int or request["draftSchemaVersion"] != 1:
        raise ValueError("draftSchemaVersion must be 1")
    preferences = normalize_preferences(request.get("preferences", {}))
    coverage = normalize_coverage(request.get("coverageReport", {}))
    draft = request.get("draft")
    payload, document = encode(draft)
    # A consistency check, never proof of human approval or source accuracy.
    digest = hashlib.sha256(payload).hexdigest()
    canonical = json.dumps({"schema": 1, "sha256": digest, "preferences": preferences,
                            "coverageReport": coverage}, ensure_ascii=False,
                           sort_keys=True, separators=(",", ":")).encode("utf-8")
    preview_hash = hashlib.sha256(canonical).hexdigest()
    cards = document["decks"][0]["cards"]
    notes = draft["cards"]
    warnings = []
    if len(cards) != preferences["targetCards"]:
        warnings.append(f"Requested {preferences['targetCards']} cards; draft contains {len(cards)} after cloze expansion. Review coverage rather than add unsupported filler.")
    upper = ANSWER_RANGES[preferences["answerLength"]][1]
    long_answers = sum(len(note.get("back", "").split()) > upper for note in notes)
    if long_answers:
        warnings.append(f"{long_answers} note answers exceed the {upper}-word {preferences['answerLength']} target. Sources are excluded; text has not been truncated.")
    without_sources = sum(not note.get("sources") for note in notes)
    if without_sources:
        warnings.append(f"{without_sources} notes have no source locations. Do not invent references.")
    cloze_notes = sum(note.get("cloze", False) for note in notes)
    if preferences["cardForm"] == "basic" and cloze_notes:
        warnings.append("Draft contains cloze notes despite the basic-only preference.")
    if preferences["cardForm"] == "cloze" and cloze_notes != len(notes):
        warnings.append("Draft contains basic notes despite the cloze-only preference.")
    if not coverage["included"]:
        warnings.append("No coverage inventory supplied; do not claim comprehensive coverage.")
    if coverage["omitted"] or coverage["limitations"]:
        warnings.append("Review the stated omissions and extraction limitations before using this deck.")
    indices = sorted({0, len(cards) // 2, len(cards) - 1})
    result = {
        "name": document["decks"][0]["name"], "noteCount": len(notes),
        "cardCount": len(cards), "sourceReferenceCount": sum(len(strings(n.get("sources", []), "sources", 20)) for n in notes),
        "bytes": len(payload), "sha256": digest, "previewHash": preview_hash,
        "preferences": preferences, "coverageReport": coverage, "warnings": warnings,
        "sample": [{"cardNumber": n + 1, **{k: cards[n][k] for k in
                    ("front", "back", "tags", "clozeIndex") if k in cards[n]}} for n in indices],
        "qualityNotice": "Validation checks structure and consistency, not educational accuracy, cognitive difficulty, or source truth. Review the lecture and draft.",
    }
    return payload, result


def reject_constant(_):
    raise ValueError("JSON must not contain NaN or Infinity")


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("JSON must not contain duplicate fields")
        value[key] = item
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Request JSON file, or - for stdin")
    parser.add_argument("output", nargs="?", help="New .recall file; existing files are never replaced")
    parser.add_argument("--preview", action="store_true", help="Validate and report without creating an artifact")
    parser.add_argument("--preview-hash", help="Hash from preview of the same final request; required to export")
    args = parser.parse_args()
    try:
        if args.preview and (args.output or args.preview_hash):
            raise ValueError("preview takes no output or preview hash")
        if not args.preview and (not args.output or Path(args.output).suffix != ".recall"):
            raise ValueError("output must have the .recall extension")
        if not args.preview and (not args.preview_hash or not re.fullmatch(r"[a-f0-9]{64}", args.preview_hash)):
            raise ValueError("preview the final request and pass its --preview-hash before exporting")
        if args.input == "-":
            raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        else:
            with open(args.input, "rb") as source:
                raw = source.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("request exceeds the 2 MB input limit; split the deck")
        request = json.loads(raw, parse_constant=reject_constant, object_pairs_hook=unique_object)
        payload, result = prepare(request)
        if not args.preview:
            if not hmac.compare_digest(args.preview_hash, result["previewHash"]):
                raise ValueError("request changed after preview; preview it again before exporting")
            with open(args.output, "xb") as destination:
                destination.write(payload)
            result["output"] = str(Path(args.output).resolve())
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as error:
        print(f"Deck build failed: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
