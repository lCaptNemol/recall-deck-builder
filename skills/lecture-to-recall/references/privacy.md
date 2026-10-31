# Data boundary

This plugin makes files and does not connect to Recall. It never reads the
Recall library, study history, CloudKit, backups, or account credentials, and
never imports or publishes a deck. Its scripts make no AI API or other network
calls.

Claude processes material the user shares under that Claude account's or
organization's policies. Running the scripts on the user's own computer, as
Claude Code does, does not make Claude's reasoning local. In the Claude apps,
code runs in a cloud sandbox, so drafts and export files also exist in that
environment. The plugin supplies no developer-operated server, upload
endpoint, analytics, or content log. Anthropic still processes the
conversation and its tool use.

Use only user-selected material. Do not save private lectures into shared
plugin resources, project knowledge, or memory. Do not claim that disabling or
removing this plugin deletes conversations or files, or changes retention or
training settings. Direct the user to Claude's privacy settings for
provider-side choices, and to Anthropic's privacy policy and Privacy Center:
https://www.anthropic.com/legal/privacy and https://privacy.claude.com

Generated decks and temporary drafts may contain lecture content. Save them
only in the task's allowed output location and let the user decide where to
import or share them. This architecture adds no recurring Recall inference,
hosting or API bill; the user's Claude plan, features and usage limits apply.
