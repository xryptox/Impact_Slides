# Delegated workflow determinism assessment

> **Reference snapshot — not the live workflow contract.** The binding operating rules are in root `AGENTS.md` and `docs/agents/delegated-delivery.md`. Update or supersede this assessment when the scripts materially change.

## Canonical workflow structure

```text
start-ticket-wave.ps1 -Issue 150,154,...
│
├─ Generate RunId
├─ Detect focused Herdr workspace
├─ Resolve configured dev model
├─ Fetch origin/main
├─ For each issue:
│  ├─ create-run-owned-worktree.ps1
│  ├─ orchestrate-herdr-implement-visible.ps1
│  └─ launch-visible-implementer.ps1
├─ Persist wave.json + targets.json
└─ Auto-start watch-ticket-wave.ps1
       │
       ▼
watch-ticket-wave.ps1
└─ Repeatedly run watch-visible-implementers.ps1
   ├─ Poll all panes
   ├─ Bind no-mistakes state by exact branch
   ├─ Deduplicate events in watcher-state.json
   ├─ Append every event to the session follow-up queue
   └─ Rearm automatically until terminal cleanup
       │
       ├─ ticket-wave-followups.ts → supervising Pi session
       ├─ ask-user → human decision → same pane
       ├─ repair → authoritative repair-prompt.md
       └─ complete → PR/CI and closing-keyword checks
                         │
                         ▼
              approved exact-head merge
              Invoke-ApprovedMerge.ps1
                         │
                         ▼
cleanup-ticket-wave.ps1
└─ cleanup-merged-workflow.ps1
   ├─ Verify selected PRs merged at reviewed heads
   ├─ Tolerate GitHub-auto-deleted remote branches
   ├─ Dry-run before apply
   ├─ Remove selected worktrees/branches/no-mistakes refs
   └─ Rewrite wave.json + targets.json for remaining tickets
```

## Determinism by component

Percentages are approximate assessments of the control plane, not measured reliability guarantees.

| Component | Approx. deterministic | Remaining dependency |
|---|---:|---|
| `resolve-dev-model.ps1` | **98%** | Reads one configured `dev` alias. |
| `create-run-owned-worktree.ps1` | **98%** | Needs issue number, RunId, repository, and base. Names are generated predictably. |
| `start-ticket-wave.ps1` | **93%** | Normally needs only issue numbers. It derives RunId, workspace, model, branches, paths, tabs, panes, manifests, and starts supervision automatically. |
| Implementer brief generation | **90%** | The standard contract is generated; the agent must read the issue for issue-specific scope. |
| `launch-visible-implementer.ps1` | **85%** | Launch mechanics are deterministic; LLM and tool behavior are inherently variable. |
| Implementer coding | **40–70%** | Issue ambiguity, model decisions, tests, review findings, and repairs vary. |
| Standards/Spec reviews | **70%** | Invocation is fixed and parallel, but findings are model-generated. |
| No-mistakes gate | **80%** | Stage order and custody are deterministic; findings and conflict resolution may need decisions. |
| `watch-visible-implementers.ps1` | **92%** | Binds pane, worktree, PR, and exact-branch no-mistakes state. Parsing still depends on stable Herdr and no-mistakes output formats. |
| `watch-ticket-wave.ps1` + follow-up extension | **95%** | Automatically rearms and delivers an append-only event queue to the originating Pi session. |
| `inspect-ticket-wave.ps1` | **96%** | Read-only derivation from `wave.json`, Git, GitHub, exact-branch no-mistakes state, and PR closing metadata. |
| Repair launcher | **80%** | IDs and launch are derived; validated host findings are copied into an authoritative repair prompt that supersedes the original prompt. |
| `Invoke-ApprovedMerge.ps1` | **97%** | Requires explicit exact-head human approval, then performs deterministic preflight and merge outside PEW journal persistence. |
| Cleanup scripts | **98%** | Dry-run-first exact ownership checks support selected-ticket cleanup and already-absent remote branches without disturbing active wave members. |

## Inputs the scripts derive

For a new canonical wave, the supervisor should not manually relay:

- RunId
- branch names
- worktree paths
- Herdr workspace ID
- model and provider
- tab or pane IDs
- artifact directories
- PR numbers during cleanup
- no-mistakes branch refs
- cleanup branch lists

These are generated or derived from `wave.json`.

Normal startup should be approximately:

```powershell
start-ticket-wave.ps1 -Issue 150,154,156,159
```

The generated `targets.json` drives watching. `wave.json` drives inspection, repair, merge preflight, and cleanup. Startup launches the outer watcher automatically; `-SkipWatcherStart` exists only for deterministic tests.

## Deliberately human-controlled decisions

These inputs should not be automated:

1. Ticket selection and dependency grouping.
2. Product decisions at `ask-user` gates.
3. Approval of scope expansion.
4. Trust of recovered dirty or partial work.
5. Exceptional abort, reset, or rebase authorization.
6. Exact-head merge approval.
7. Destructive cleanup when automatic safety checks cannot prove ownership.

## Hardened exception paths

The August 2026 automation pass added and smoke-tested:

1. Automatic watcher startup and rearming through `watch-ticket-wave.ps1`.
2. Append-only session follow-up delivery so adjacent events are not overwritten.
3. Exact-branch no-mistakes run selection instead of repository-global latest-run selection.
4. Authoritative repair prompts that copy validated host findings and supersede the original brief.
5. PR closing-keyword inspection and merge blocking for missing `Closes`, `Fixes`, or `Resolves` references.
6. Deterministic exact-head merge preflight outside PEW journal persistence for Windows `EPERM` recovery.
7. Partial-wave cleanup plus idempotent handling of GitHub-auto-deleted remote branches.

Smoke coverage includes PowerShell 5.1 parsing, queued follow-up delivery, stale-event suppression, two-event automatic rearming, exact-branch run selection, repair-prompt precedence, closing-reference boundaries, already-merged merge rejection, selected-ticket cleanup, preservation of another active worktree, and cleanup with an already-absent origin branch.

## Current limitations

- The inner watcher still returns after one unseen event, but `watch-ticket-wave.ps1` now rearms it automatically; `watcher-state.json` prevents duplicate delivery and the append-only follow-up file prevents event overwrite.
- The watcher enforces operational loop ceilings: more than 5 no-mistakes review-fix rounds, more than 90 minutes in review fixing, or more than 10 minutes without agent/log activity emits `loop-limit` and requires controlled recovery. These are orchestration safety limits, not native PEW budgets.
- PEW aggregate budgets (`tokens`, `costUsd`, `durationMs`, `agentLaunches`) constrain workflow-owned `agent()` work, but visible Herdr Pi and no-mistakes subprocesses run outside those agent budgets; the watcher limits cover that gap.
- Herdr and no-mistakes state is parsed from CLI output, so upstream output-format changes can break detection.
- LLM implementation and review cannot be made fully deterministic.
- A wave created before the manifest architecture may have manual branch names, no valid `wave.json`, and no automatic cleanup path.
- The #151/#155 production wave completed the manifest-driven implementation-to-cleanup lifecycle, but the latest exception-path hardening above has isolated smoke proof rather than a second full production wave.

## Overall assessment

- **Future manifest-driven waves:** approximately **90–95% deterministic control plane**.
- **Grandfathered/manual waves:** approximately **60–70% deterministic control plane** because recovery and cleanup require manual reconciliation.
- **Implementation behavior:** inherently less deterministic than orchestration because it depends on issue quality, model behavior, review findings, and test evidence.
