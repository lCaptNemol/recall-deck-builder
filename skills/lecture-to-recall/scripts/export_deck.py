#!/usr/bin/env python3
"""Content-only Recall v2 ZIP encoder, verified by native RecallDocument tests."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import unicodedata
import uuid
import zipfile

MAX_INPUT_BYTES = 2_000_000
NAMESPACE = uuid.UUID("a1ed57b0-229a-5fd9-9d68-7b0be4b4b358")
# Mirrors RecallDomain.ClozeSyntax.pattern (multiline answers and hints).
CLOZE = re.compile(r"\{\{c(\d+)::(.*?)(?:::(.*?))?\}\}", re.DOTALL)


def text(value, label, limit=20_000, required=False):
    if not isinstance(value, str) or len(value) > limit or "\x00" in value:
        raise ValueError(f"{label} must be text of at most {limit} characters")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{label} cannot be empty")
    return value


def strings(value, label, limit=50):
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError(f"{label} must be an array of at most {limit} strings")
    result, seen = [], set()
    for item in value:
        item = text(item, label, 500, True)
        key = "".join(c for c in unicodedata.normalize("NFD", item.casefold())
                      if not unicodedata.combining(c))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def only_keys(value, allowed, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"{label} has unsupported fields: {', '.join(sorted(unknown))}")


def manifest(draft):
    only_keys(draft, {"name", "tags", "cards"}, "deck")
    name = text(draft.get("name"), "name", 200, True)
    tags = strings(draft.get("tags", []), "deck tags")
    notes = draft.get("cards")
    if not isinstance(notes, list) or not 1 <= len(notes) <= 500:
        raise ValueError("cards must contain 1 to 500 notes")
    normalized = []
    for number, note in enumerate(notes, 1):
        label = f"card {number}"
        only_keys(note, {"front", "back", "cloze", "tags", "sources"}, label)
        front = text(note.get("front"), f"{label} front", required=True)
        back = text(note.get("back", ""), f"{label} back")
        cloze = note.get("cloze", False)
        if type(cloze) is not bool:
            raise ValueError(f"{label} cloze must be a boolean")
        matches = list(CLOZE.finditer(front))
        if cloze:
            if not matches or "{{c" in CLOZE.sub("", front):
                raise ValueError(f"{label} needs complete {{{{c1::answer}}}} cloze syntax")
            for match in matches:
                if not 1 <= int(match[1]) <= 99 or not match[2].strip() or any(
                    marker in match[2] + (match[3] or "") for marker in ("{{", "}}")
                ):
                    raise ValueError(f"{label} has an invalid, empty, or nested cloze")
        elif matches or "{{c" in front:
            raise ValueError(f"{label} contains cloze markup; set cloze to true")
        elif not back:
            raise ValueError(f"{label} back cannot be empty for a basic card")
        normalized.append({"front": front, "back": back, "cloze": cloze,
                           "tags": strings(note.get("tags", []), f"{label} tags"),
                           "sources": strings(note.get("sources", []), f"{label} sources", 20)})
    canonical = json.dumps({"name": name, "tags": tags, "cards": normalized},
                           ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    deck_id = uuid.uuid5(NAMESPACE, canonical)
    cards = []
    for number, note in enumerate(normalized):
        group = uuid.uuid5(deck_id, f"note:{number}")
        back = note["back"]
        if note["sources"]:
            back += ("\n\n" if back else "") + "Sources:\n" + "\n".join("- " + s for s in note["sources"])
        indices = sorted({int(m[1]) for m in CLOZE.finditer(note["front"])}) if note["cloze"] else [None]
        for index in indices:
            card = {"id": str(uuid.uuid5(group, f"card:{index}")), "front": note["front"],
                    "back": back, "tags": note["tags"]}
            if index is not None:
                card.update(clozeIndex=index, clozeGroupID=str(group))
            cards.append(card)
    if len(cards) > 2_000:
        raise ValueError("cloze expansion exceeds the 2,000-card limit; split this deck")
    # Scheduling, curation, device transfer, settings, and media are deliberately
    # absent. Native decoders apply defaults and clean import mints fresh IDs.
    return {"format": "recall", "version": 2, "kind": "deck", "quizzes": [],
            "decks": [{"id": str(deck_id), "name": name, "tags": tags, "cards": cards}]}


def encode(draft):
    document = manifest(draft)
    data = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    output = io.BytesIO()
    # Fixed ZIP metadata makes repeated exports byte-for-byte identical.
    entry = zipfile.ZipInfo("data.json", date_time=(1980, 1, 1, 0, 0, 0))
    entry.compress_type = zipfile.ZIP_DEFLATED
    entry.external_attr = 0o600 << 16
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(entry, data)
    return output.getvalue(), document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON draft path, or - for stdin")
    parser.add_argument("output", nargs="?", help="Output .recall path (never a Recall library)")
    parser.add_argument("--preview", action="store_true", help="Validate and report without writing a file")
    args = parser.parse_args()
    try:
        if not args.preview and (not args.output or Path(args.output).suffix != ".recall"):
            raise ValueError("output must have the .recall extension")
        if args.input == "-":
            raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        else:
            with open(args.input, "rb") as source:
                raw = source.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("draft exceeds the 2 MB input limit")
        payload, document = encode(json.loads(raw))
        # Exclusive create avoids overwriting somebody's existing deck.
        if not args.preview:
            with open(args.output, "xb") as destination:
                destination.write(payload)
        print(json.dumps({"name": document["decks"][0]["name"],
                          "cardCount": len(document["decks"][0]["cards"]),
                          "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
                          "noteCount": len(draft_cards := json.loads(raw)["cards"]),
                          "sourceReferenceCount": sum(len(strings(n.get("sources", []), "sources", 20)) for n in draft_cards),
                          "sample": [{k: c[k] for k in ("front", "back", "tags", "clozeIndex") if k in c}
                                     for c in document["decks"][0]["cards"][:5]]}))
    except (OSError, ValueError, TypeError) as error:
        print(f"Export failed: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
