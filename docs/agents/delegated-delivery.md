# Delegated ticket delivery

Use this workflow for parallel issue implementation, adversarial host review, no-mistakes correction, and approved PR merging.

## External prerequisites

This process depends on user-global tools and configuration, not files vendored in this repository:

- Pi Extensible Workflows (PEW)
- Herdr
- `no-mistakes axi`
- `gh` authenticated for `xryptox/Impact_Slides`
- workflow roles in `~/.pi/agent/pi-extensible-workflows/roles/`
- model aliases in `~/.pi/agent/pi-extensible-workflows/settings.json`

Expected roles:

- `implementer` — implements one issue in an isolated feature worktree
- `gate-driver` — recovery-only driver for an existing no-mistakes run; Kimi `review` model, `bash` only, all skills/extensions disabled (the role invokes the installed `no-mistakes` CLI directly)
- `reviewer` — Kimi read-only correctness/data-loss review with project/cwd DOX context, CodeMapper only, and no unrelated extensions
- `merger` — cheap-model, approval-gated merge of one exact PR head; `bash` only with all skills/extensions disabled

The current aliases use `dev` for implementation work, `review` for Kimi review, and `cheap` for merging. Inspect the live settings rather than copying remembered provider names.

## Why Herdr wraps implementation

PEW's native child runtime resolves models before dynamically registered providers are loaded. A provider registered by an extension, such as SuperGrok, may therefore work in normal Pi but fail in native `agent(...)` calls with `UNKNOWN_MODEL`.

When that applies, use PEW for orchestration and isolated worktrees, but launch a full interactive Pi process in a visible Herdr tab for each implementer. Do not use `pi --print`: progress must remain observable. Close a temporary tab only after collecting its final report and Git/no-mistakes state.

Durable workflow scripts:

- `~/.pi/agent/pi-extensible-workflows/scripts/launch-visible-implementer.ps1` — starts the lean interactive Pi child
- `~/.pi/agent/pi-extensible-workflows/scripts/orchestrate-herdr-repair-visible.ps1` — repair/report lifecycle built on that launcher
- `~/.pi/agent/pi-extensible-workflows/scripts/cleanup-merged-workflow.ps1` — dry-run-first cleanup of merged workflow worktrees/branches after exact PR-head verification

The lean child starts with `--no-extensions --no-skills` and explicitly loads only SuperGrok, the skill-command extension, Ponytail, CodeMapper, and the `implement` skill. Its tool allowlist is `read,bash,edit,write,map,search,outline,expand,path`. Observational memory, RTK, fork/subagent, handoff, TSCG, and PEW are excluded from the child. A workflow may create ticket briefs and result artifacts under `%TEMP%`, but must not depend on temporary launcher copies.

## Delivery sequence

### 1. Prepare a dependency wave

- Read the root and applicable child `AGENTS.md` files.
- Fetch each issue and its comments/labels.
- Group only independent tickets in the same parallel wave.
- Give every ticket its own branch and worktree.
- Record the starting SHA, issue number, worktree, branch, and expected changed paths.

### 2. Implement in visible tabs

Each implementer must:

- launch through `launch-visible-implementer.ps1` (directly or through the repair orchestrator), not a bare full-profile `pi` command;
- invoke/read the `implement` skill explicitly;
- use TDD where practical and perform the required code review;
- change only its issue scope;
- run focused checks, mutation/adversarial proof, one final full suite, and `python scripts/gen_layout_index.py --check` when relevant;
- complete the DOX pass;
- commit on the feature branch;
- run the full no-mistakes gate itself;
- report commits, tests, mutations, review results, no-mistakes run ID/findings/fixes, PR URL, CI state, and blockers.

`ask-user` findings are escalation points. An implementer must not decide them without explicit standing consent.

### 3. Respect no-mistakes custody

A live no-mistakes pipeline owns unpublished correction commits.

- Never edit, reset, rebase, or start a duplicate run while it owns the branch.
- Inspect with `no-mistakes axi status`.
- If local and pipeline heads differ, use `no-mistakes axi sync`; use `sync --recover` only when AXI explicitly reports recoverable divergence.
- Preserve pipeline commits and rerun affected checks after reconciliation.
- The CI stage normally remains active until its PR is merged or closed.

Treat update notices on stderr as notices, not task failures. Verify GitHub, Git, and `no-mistakes axi status` directly when a wrapper reports `BLOCKED`.

### 4. Host verification

A green suite is not sufficient in this repository. The supervising host must inspect the final pipeline head and use the smallest relevant combination of:

- mutation testing;
- same-worktree before/after output comparison;
- Playwright geometry on the real archived handoff;
- facade/registry identity checks;
- malformed-input sweeps;
- focused tests plus the full suite and layout-index gate.

Return real defects to the same implementer and existing no-mistakes run. Do not patch pipeline-owned branches from the host.

### 5. Prepare merge metadata

Before approval, verify that every PR:

- targets `main`;
- is open and non-draft;
- is clean/mergeable;
- has green required checks;
- has the reviewed exact head SHA;
- contains `Closes #N` (or equivalent).

Record the exact head SHA presented for approval.

### 6. Approval and merge

The user may approve one exact PR or a named batch. Batch approval is conditional and serial:

1. Launch the `merger` role once per PR.
2. Supply PR number, reviewed head SHA, and literal `HUMAN_APPROVAL: true`.
3. Recheck against current `main` after every preceding merge.
4. Squash-merge and delete the remote branch only when all role checks pass.
5. Stop the batch on a changed head, conflict, pending/failed check, missing closing reference, or changed scope.

A feature-head change invalidates approval and requires fresh host review and approval. A `main` change caused only by an earlier approved merge does not invalidate the batch, but the next PR must still be recalculated and clean.

The merger role must not edit code/metadata, force, use admin bypass, update local `main`, or clean worktrees.

### 7. Closeout

After merges:

- fetch and fast-forward/reconcile the root checkout without discarding local commits;
- confirm linked issues closed;
- let no-mistakes monitors reach terminal state;
- run `cleanup-merged-workflow.ps1` without `-Apply`, review its exact plan, then rerun with `-Apply`; pass safety refs explicitly because unrelated or non-ancestor refs are rejected;
- delete the terminal run from `/workflow` after script cleanup to remove persisted metadata;
- report merge SHAs, unresolved PRs, and any cleanup intentionally deferred.

## Windows failure modes

- PEW journal persistence can fail with `EPERM` during atomic rename after an external merge succeeded. Query the PR before retrying; never assume exactly-once external effects.
- PowerShell native stderr can be promoted to an exception. Classify using exit code and authoritative state, not stderr text alone.
- Herdr marks a completed interactive Pi as `done`; `herdr wait agent-status --status idle` does not accept/observe that terminal state. Poll `herdr pane list` for `done` or `idle`, then collect the report and close the tab.
- Quote Git revision ranges as one normal argument (`base..head`); malformed nested quoting can make Git treat the range as a filename.
- PEW workflow JavaScript is sandboxed: do not assume `Date.now()` or Bash shell syntax is available; `shell()` uses the host Windows shell.
- A local branch deletion may fail while its linked worktree exists even though the GitHub merge and remote branch deletion succeeded.
