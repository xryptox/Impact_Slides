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
├─ Persist wave.json
└─ Persist targets.json
       │
       ▼
PEW watcher workflow
└─ watch-visible-implementers.ps1
   ├─ Poll all panes
   ├─ Read branch-specific no-mistakes state
   ├─ Deduplicate events in watcher-state.json
   ├─ Return first unseen idle/done/blocked event
   └─ Host rearms after each delivered event
       │
       ├─ ask-user → human decision → same pane
       ├─ repair → orchestrate-herdr-repair-visible.ps1
       └─ complete → PR/CI monitoring
                         │
                         ▼
                 approved serial merger
                         │
                         ▼
cleanup-ticket-wave.ps1
└─ cleanup-merged-workflow.ps1
   ├─ Verify every PR merged
   ├─ Verify exact run-owned branches/heads
   ├─ Verify issues closed and gates passed
   ├─ Dry-run
   └─ Remove worktrees, branches, and no-mistakes refs
```

## Determinism by component

Percentages are approximate assessments of the control plane, not measured reliability guarantees.

| Component | Approx. deterministic | Remaining dependency |
|---|---:|---|
| `resolve-dev-model.ps1` | **98%** | Reads one configured `dev` alias. |
| `create-run-owned-worktree.ps1` | **98%** | Needs issue number, RunId, repository, and base. Names are generated predictably. |
| `start-ticket-wave.ps1` | **90%** | Normally needs only issue numbers. It derives RunId, workspace, model, branches, paths, tabs, panes, and manifests. |
| Implementer brief generation | **90%** | The standard contract is generated; the agent must read the issue for issue-specific scope. |
| `launch-visible-implementer.ps1` | **85%** | Launch mechanics are deterministic; LLM and tool behavior are inherently variable. |
| Implementer coding | **40–70%** | Issue ambiguity, model decisions, tests, review findings, and repairs vary. |
| Standards/Spec reviews | **70%** | Invocation is fixed and parallel, but findings are model-generated. |
| No-mistakes gate | **80%** | Stage order and custody are deterministic; findings and conflict resolution may need decisions. |
| `watch-visible-implementers.ps1` | **90%** | Binds pane, worktree, gate, PR, and state. Parsing still depends on stable Herdr and no-mistakes output formats. |
| `inspect-ticket-wave.ps1` | **95%** | Read-only derivation from `wave.json`, Git, GitHub, and no-mistakes. |
| Repair launcher | **70%** | IDs and launch are derived, but it needs validated host findings or an ask-user answer. |
| Merger role | **95%** | Requires explicit exact-head human approval; checks and the merge command are then fixed. |
| Cleanup scripts | **97%** | Dry-run-first with exact ownership, head, and merge checks; destructive actions are not inferred. |

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

The generated `targets.json` drives watching. `wave.json` drives inspection, repair, and cleanup.

## Deliberately human-controlled decisions

These inputs should not be automated:

1. Ticket selection and dependency grouping.
2. Product decisions at `ask-user` gates.
3. Approval of scope expansion.
4. Trust of recovered dirty or partial work.
5. Exceptional abort, reset, or rebase authorization.
6. Exact-head merge approval.
7. Destructive cleanup when automatic safety checks cannot prove ownership.

## Current limitations

- The watcher returns after the first unseen event so PEW can deliver a real supervising-session follow-up. The host must rearm it while work remains; `watcher-state.json` prevents immediate duplicate delivery.
- Herdr and no-mistakes state is parsed from CLI output, so upstream output-format changes can break detection.
- LLM implementation and review cannot be made fully deterministic.
- A wave created before the manifest architecture may have manual branch names, no valid `wave.json`, and no automatic cleanup path.
- The canonical components have isolated parsing and safety checks, but the complete `start → implementation → PR → merge → automatic cleanup` lifecycle has not yet completed one production wave end to end.

## Overall assessment

- **Future manifest-driven waves:** approximately **85–90% deterministic control plane**.
- **Grandfathered/manual waves:** approximately **60–70% deterministic control plane** because recovery and cleanup require manual reconciliation.
- **Implementation behavior:** inherently less deterministic than orchestration because it depends on issue quality, model behavior, review findings, and test evidence.
