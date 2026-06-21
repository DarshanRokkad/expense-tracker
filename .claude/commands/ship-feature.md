---
description: Ships the current feature branch end-to-end — stage, commit, push, open PR (GitHub MCP), merge (GitHub MCP), delete remote+local branches, sync master. Usage: /ship-feature [optional PR title]
argument-hint: "[optional PR title — defaults to a title derived from the branch name]"
allowed-tools: Bash(git:*), mcp__github__list_pull_requests, mcp__github__create_pull_request, mcp__github__get_pull_request_status, mcp__github__merge_pull_request
---

Ship the current feature branch for this repo, end to end. Follow
the steps below **in order**. If any step fails or returns something
unexpected, stop immediately and report it to the user — do not
skip ahead, retry blindly, or improvise a workaround for a
destructive step (force-push, force-delete, etc.).

PR creation, status checks, and merging go through the **GitHub
MCP server** (`mcp__github__*` tools). Plain `git`/Bash is used only
for the parts that are inherently local-git or that the GitHub MCP
server has no tool for (staging/committing, pushing a branch's full
commit history, deleting a branch ref, checkout, pull) — there is
no MCP tool for any of those.

## Step 0 — Preflight checks

1. `git branch --show-current` — if this is already the default
   branch (see point 3), stop and say there's nothing to ship.
2. Resolve `owner` and `repo` from the remote:
   ```bash
   git remote get-url origin | sed -E 's#.*[:/]([^/]+)/([^/]+)\.git#\1 \2#'
   ```
3. Resolve the default base branch:
   ```bash
   git symbolic-ref refs/remotes/origin/HEAD | sed 's#refs/remotes/origin/##'
   ```
   Fall back to `master` if this fails.

## Step 2 — Stage and commit

Run `git status --porcelain` to see what's unstaged/untracked.

**Before staging anything**, scan the untracked entries (lines
starting with `??`) for unwanted files — things that slipped past
`.gitignore` but shouldn't be committed. Treat any of the following
as unwanted and **stop, listing them, instead of staging**:
- Media/binaries: `*.mp3`, `*.mp4`, `*.mov`, `*.wav`, `*.zip`, `*.tar.gz`
- Editor/IDE noise: `.idea/`, `.vscode/`, `.DS_Store`, `*.swp`, `*~`
- Secrets: `.env`, `*.pem`, `*.key`, `credentials*.json`
- Build/dependency artifacts: `__pycache__/`, `*.pyc`, `node_modules/`,
  `.venv/`, `venv/`, `*.egg-info/`

If any of these show up, do not run `git add`. Tell the user exactly
which files were flagged and ask whether to add them to `.gitignore`,
delete them, or stage them anyway — never decide silently.

If nothing unwanted is found:
- If there's nothing to stage at all (`git status --porcelain` is
  empty) and the branch has no commits ahead of the default branch
  either, stop and say there's nothing to ship.
- Otherwise stage everything: `git add -A`.
- Commit with: `git commit -m "<branch>: <short description>"`,
  where `<branch>` is the current branch name from Step 0 (this
  repo's branches are named `feat/<feature-slug>`, so the message
  naturally comes out as `feat/<feature-slug>: <short description>`,
  matching this repo's existing commit history, e.g.
  `feat/profile: dynamic expense and profile from backedn`). The
  description must be a concise (1 sentence) summary of *why* the
  change was made, based on the staged diff — not a restatement of
  file names.
- If there's nothing left to stage/commit (e.g. the branch's changes
  were already committed earlier in the session) skip the commit
  and continue — this isn't a failure.

## Step 3 — Push the branch

```bash
git push -u origin <branch>
```

## Step 4 — Create the pull request (GitHub MCP)

First call `mcp__github__list_pull_requests` with `head: "<owner>:<branch>"`,
`state: "open"` to avoid opening a duplicate. If an open PR already
exists for this branch, reuse it and skip to Step 5.

Otherwise call `mcp__github__create_pull_request`:
- `owner`, `repo` — from Step 0
- `head` — `<branch>`
- `base` — `<default branch>`
- `title` — `$ARGUMENTS` if provided; otherwise derive Title Case from
  the branch name (strip a leading `feat/`/`fix/`/`chore/` prefix,
  replace `-` with spaces, title-case each word — e.g.
  `feat/profile-date-filtering` → "Profile Date Filtering")
- `body` — a short 1-2 sentence summary based on
  `git log <default branch>..<branch> --oneline`, not a raw commit dump

Report the PR URL and number to the user.

## Step 5 — Check PR status before merging (GitHub MCP)

Call `mcp__github__get_pull_request_status` for the PR number from
Step 4. If any check is in a **failing** state, stop and tell the
user — never merge over a failing check. Pending or no checks
configured (this repo has no CI today) is fine to proceed past.

## Step 6 — Merge the pull request (GitHub MCP)

Call `mcp__github__merge_pull_request` with `merge_method: "squash"`
(matches this repo's existing merge history, e.g.
`Feat/profile date filtering (#7)`). Confirm the response has
`merged: true` before continuing. If it doesn't, stop and report why.

## Step 7 — Delete the remote branch

```bash
git push origin --delete <branch>
```
(No GitHub MCP tool exposes branch deletion — this is the only
git-native way to do it.)

## Step 8 — Checkout and sync the default branch

```bash
git checkout <default branch>
git pull origin <default branch>
```

## Step 9 — Delete the local feature branch

```bash
git branch -D <branch>
```

This must be `-D` (force), not `-d`: GitHub's squash merge creates a
brand-new commit on the default branch, so the local branch's
original commits are never literal ancestors of it — `git branch -d`
will refuse with "not fully merged" even though the PR genuinely
merged. Only run this after Step 6 confirmed `merged: true`.

## Step 10 — Report

Print a short summary in this format:
```
Shipped:    <branch>
PR:         <PR URL> (#<number>)
Merged to:  <default branch>
Local:      back on <default branch>, up to date, <branch> deleted
```
