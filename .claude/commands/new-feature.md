---
description: Start (and later wrap up) a feature branch using this project's standard git workflow
---

The user wants to work through this project's standard feature-branch workflow for a feature named: $ARGUMENTS

If no name was given, ask for one before doing anything (e.g. "database-setup", "expense-crud").

Walk through these phases. Do not skip ahead — check with the user between phases using AskUserQuestion or a plain question, since git state changes are visible/shared and some steps (push, merge) are not easily reversible.

## Phase 1 — Start the branch
1. `git status` — confirm the working tree is clean before switching branches. If there are uncommitted changes, stop and ask the user how to handle them (stash, commit, discard) rather than guessing.
2. `git checkout master` (if not already on it), then `git pull origin master` — sync local master with remote.
3. `git checkout -b feature/<name>` — create and switch to the new branch, using the feature name given (prefix with `feature/` if not already).

Then stop and hand control back to the user for the actual implementation work (this command is only for the git scaffolding, not the feature code itself).

## Phase 2 — Commit (only when the user asks to commit)
- Stage the relevant files (ask which, or use `git status`/`git diff` to identify them — avoid `git add .` / `git add -A` blindly).
- **Do not run `git commit` yourself.** This user prefers to write and run the commit themselves. Show them `git status`/`git diff --stat` of what's staged and let them run the commit command. Only draft a suggested commit message if they ask for one.

## Phase 3 — Push and PR (only when the user asks)
1. `git push origin feature/<name>` — pushes the branch; GitHub will return a "create a pull request" link in the output.
2. Ask the user whether they want you to open the PR with `gh pr create`, or whether they'll do it themselves on GitHub. Don't create the PR without asking.

## Phase 4 — Merge back to master (only after the user confirms the PR is merged)
1. `git checkout master`
2. `git pull origin master` — this should fast-forward and pull in the merged feature commit(s).
3. Optionally ask if they want the now-merged local feature branch deleted (`git branch -d feature/<name>`) — don't delete it without asking.

Keep responses in each phase short — state what command you're about to run and why, run it, report the result. Don't narrate the whole workflow up front; move phase by phase as the user is ready for each.
