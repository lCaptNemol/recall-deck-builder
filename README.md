# Recall Deck Builder

Recall Deck Builder is a Claude plugin that turns a lecture, slide deck,
transcript or set of notes you share with Claude into a reviewed flashcard
deck for the Recall app. Claude drafts the cards, checks them against the
material, and saves a `.recall` file that you open or import in Recall on Mac
or iOS. Recall does not need to be installed to make the file.

## Install

**Claude chat and Cowork.** In claude.ai or the Claude desktop app, open
**Customize > Plugins**, choose **Add > Add marketplace**, enter
`https://github.com/lCaptNemol/recall-deck-builder`, and install Recall Deck
Builder. To install
from a file instead, choose **Add > Upload plugin** and select
`recall-deck-builder-0.2.2.zip` from the
[latest release](https://github.com/lCaptNemol/recall-deck-builder/releases/latest).
Turn on code execution and file creation in Settings so Claude can write the
deck file. A plugin installed on your account also loads in Claude Code.

**Claude Code.** In your terminal, run:

```sh
claude plugin marketplace add lCaptNemol/recall-deck-builder
claude plugin install recall-deck-builder@recall-app
```

Inside a session, `/plugin marketplace add lCaptNemol/recall-deck-builder`
followed by `/plugin install recall-deck-builder@recall-app` does the same.

**Skill only.** If your plan offers custom skills but not plugins, upload
`lecture-to-recall-skill-0.2.2.zip` from the same release in the Skills
section of Settings, with code execution turned on.

Plugins, skills and code execution depend on your Claude plan and, in a
workspace, on what its administrators allow.

## Use

Share your lecture: attach a PDF, slides or a transcript, paste notes, or (in
Claude Code) name the file. Then ask, for example:

> Make 40 Recall cards for a medical student. Use mostly application
> questions, short answers, and a mix of basic and cloze cards. Cover the
> learning objectives and cite the slide numbers.

In Claude Code you can also start with `/recall-deck-builder:lecture-to-recall`.

Other controls include foundational versus integration questions, question
versus structured-fact prompts, detailed explanations, selected sections,
language, and card count. You can revise the draft in the conversation.

Claude previews and validates the draft, then creates a `.recall` file. Claude
Code saves it in the folder you name, or the current folder; Claude chat and
Cowork offer it as a download. Open or import it in Recall on Mac or iOS
Standalone. Existing Synced iOS libraries receive decks through the Mac's
normal publication flow. The plugin does not open your library, import
automatically, or enable sync.

## What it runs, sends and stores

- **Runs:** one skill, `lecture-to-recall`, and its two bundled Python
  scripts, `build_deck.py` and `export_deck.py`. They use only Python's
  standard library and run in Claude's code-execution sandbox, or on your
  computer in Claude Code. They read the draft that Claude writes as JSON and
  write one `.recall` file, a ZIP archive that holds a single `data.json`.
- **Sends and fetches:** nothing. The scripts make no network requests, and
  the plugin has no server, API key, analytics, connector or hook.
- **Stores:** only the deck you ask for and a temporary JSON draft in a
  working folder. An existing file is never replaced. The plugin never reads
  your Recall library, study history, backups or account.

Anthropic processes your lecture and the conversation under your Claude
account's or organization's settings; running the scripts on your own
computer does not make Claude's reasoning local. See the
[privacy notes](skills/lecture-to-recall/references/privacy.md),
[Anthropic's privacy policy](https://www.anthropic.com/legal/privacy) and the
[Privacy Center](https://privacy.claude.com).

## Limits

Difficulty and length choices guide AI drafting, so review the resulting
facts, sources and coverage before studying. This version supports basic and
native cloze cards, tags and source locations; images, occlusion, quizzes,
study progress and direct app connections are outside it. The scripts need
Python 3.9 or later: Claude Code uses the Python on your computer, and Claude
chat and Cowork use the code-execution sandbox. Without code execution,
Claude can supply a structured draft but not an importable deck.

The plugin costs nothing beyond your Claude plan, whose features and usage
limits apply.

## License

The plugin's code and documentation are available under the
[MIT License](LICENSE). The Recall name and app icon are not licensed for
other uses.
