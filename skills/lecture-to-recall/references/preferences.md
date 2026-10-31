# Preferences and request contract

Apply user choices independently. These options guide Claude's drafting;
the script validates the contract and reports observable issues. It cannot
prove that a question has a particular cognitive difficulty or is correct.

| JSON key | Values/default | Drafting behavior |
| --- | --- | --- |
| `level` | Nonempty text; `matchSource` | Vocabulary/assumed knowledge; e.g. medical student |
| `difficulty` | `foundation`, `application`, `integration`, `mixed` (default) | Facts, applied cases, combining concepts, or a mix; not Recall grading |
| `targetCards` | Integer 1–2000; 50 | Expanded native cards, including distinct cloze indices; split above note/byte limits |
| `answerLength` | `brief` (default), `balanced`, `detailed` | Soft answer targets: 15–30, 30–60, 60–100 words, excluding citations; shorter correct answers are fine |
| `questionPercent` | Integer 0–100; 100 | Percent of prompts written as questions; remainder structured topic/fact prompts. Apply to basic notes; cloze sentences retain native syntax |
| `cardForm` | `basic` (default), `cloze`, `mixed` | Representation, separate from difficulty and prompt style |
| `coverage` | `core` (default), `objectives`, `comprehensive`, `selected` | Balance coverage and size honestly; name selected objectives/pages in the coverage report |
| `sourcePolicy` | `lectureOnly` (default), `supplemented` | Use only supplied sources unless user requests supplements; label supplemental content and real sources |
| `language` | Nonempty text; `matchSource` | Output language; retain technical terms/units and disclose uncertain translation |

Interpret “questions vs details” as `questionPercent`, then confirm any separate
answer-length preference from the user's language. Interpret “harder” as cognitive
difficulty, not a grading/scheduling change. Do not silently discard source
facts or truncate answers to meet a word limit. If a source cannot support the
target count, export fewer cards and disclose the difference.

For application cards, use source-supported situations requiring a prediction,
comparison or mechanism. For integration cards, combine supported concepts in
one reasoning task. Do not add an unsupported diagnosis or fact to make a card
look harder. Every cloze index produces one card; basic notes produce one each.

Build an object with only these keys:

```json
{
  "draftSchemaVersion": 1,
  "preferences": {
    "level": "medical student",
    "difficulty": "application",
    "targetCards": 50,
    "answerLength": "brief",
    "questionPercent": 80,
    "cardForm": "mixed",
    "coverage": "objectives",
    "sourcePolicy": "lectureOnly",
    "language": "matchSource"
  },
  "coverageReport": {
    "included": ["Objective 1: cell structures"],
    "omitted": [],
    "limitations": []
  },
  "draft": {
    "name": "Lecture title",
    "tags": ["Biology"],
    "cards": [
      {
        "front": "Question supported by the lecture?",
        "back": "Source-supported answer.",
        "tags": ["Objective 1"],
        "sources": ["Lecture title, slide 3"]
      },
      {
        "front": "{{c1::Mitochondria}} produce {{c2::ATP}}.",
        "back": "Optional supported context.",
        "cloze": true,
        "sources": ["Lecture title, slide 3"]
      }
    ]
  }
}
```

`preferences` and `coverageReport` can be omitted; missing preference fields
receive defaults. Always supply an honest coverage report when generating from
a lecture. Each coverage field is an array of at most 128 nonempty strings of
at most 500 characters. The example is a three-card deck, not fifty cards.
The model's full draft should match the selected source, not copy this example.

The strict `draft` accepts only `name`, `tags`, `cards`; each note accepts only
`front`, `back`, `cloze`, `tags`, `sources`. Basic cards need both sides; cloze
cards need valid positive deletion indices from 1 to 99, with no nesting.
Names: 200 characters; each side: 20,000; each tag/source: 500. Maximum 50 tags
per deck/note and 20 source locations per note. Unknown fields are errors.

Preview returns actual note/expanded-card counts, selected beginning/middle/end
samples, normalized preferences, warnings, coverage, archive bytes/digest and
a `previewHash`. Export requires that same request and hash and refuses to
overwrite existing files. No preview hash proves source truth or user approval.
Warnings flag issues without silently rewriting the user's content.
