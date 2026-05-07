---
name: changelog
description: Create Towncrier changelog fragments based on changes in the current branch
disable-model-invocation: true
---

# Create Changelog Fragments

Create Towncrier changelog fragment(s) for the current branch's changes.

## Steps

1. **Understand the changes.** Run `git diff main...HEAD` and `git log main..HEAD --oneline` to see what changed on this branch.

2. **Determine fragment type(s) and descriptions.** Choose one or more of the following types based on the changes:
   - `security` — Security fixes
   - `removed` — Removed features or APIs
   - `deprecated` — Newly deprecated features
   - `added` — New features, classes, functions, or modules
   - `changed` — Changes to existing behavior or APIs (including breaking changes)
   - `improved` — Performance improvements or non-breaking enhancements to existing features
   - `fixed` — Bug fixes

   Write a one-sentence description for each fragment. Follow these conventions from existing fragments:
   - Use backticks for code references (class names, function names, etc.)
   - Start with a past-tense verb (e.g. "Added...", "Fixed...", "Updated...")
   - End with a period
   - Be concise — one sentence is typical

   If multiple types apply (e.g. both `added` and `changed`), create separate fragments.

3. **Ask the user for the PR number.** Use `AskUserQuestion` to ask: "What is the PR number for these changelog entries?"

4. **Create the fragments.** For each fragment, run:
   ```
   towncrier create -c "Description here." <PR#>.<type>.md
   ```
   For example: `towncrier create -c "Added \`UniformLocalC1\` distribution." 307.added.md`
