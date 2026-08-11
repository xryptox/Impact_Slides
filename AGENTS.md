## Agent skills

### Issue tracker

GitHub Issues via `gh` on `xryptox/Impact_Slides`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary matches tracker strings (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.

# DOX framework

- DOX is highly performant AGENTS.md hierarchy installed here
- Agent must follow DOX instructions across any edits

## Core Contract

- AGENTS.md files are binding work contracts for their subtrees
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable AGENTS.md plus every parent AGENTS.md above it

## Read Before Editing

1. Read the root AGENTS.md
2. Identify every file or folder you expect to touch
3. Walk from the repository root to each target path
4. Read every AGENTS.md found along each route
5. If a parent AGENTS.md lists a child AGENTS.md whose scope contains the path, read that child and continue from there
6. Use the nearest AGENTS.md as the local contract and parent docs for repo-wide rules
7. If docs conflict, the closer doc controls local work details, but no child doc may weaken DOX

Do not rely on memory. Re-read the applicable DOX chain in the current session before editing.

## Update After Editing

Every meaningful change requires a DOX pass before the task is done.

Update the closest owning AGENTS.md when a change affects:

- purpose, scope, ownership, or responsibilities
- durable structure, contracts, workflows, or operating rules
- required inputs, outputs, permissions, constraints, side effects, or artifacts
- user preferences about behavior, communication, process, organization, or quality
- AGENTS.md creation, deletion, move, rename, or index contents

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. Small edits that do not change behavior or contracts may leave docs unchanged, but the DOX pass still must happen.

## Hierarchy

- Root AGENTS.md is the DOX rail: project-wide instructions, global preferences, durable workflow rules, and the top-level Child DOX Index
- Child AGENTS.md files own domain-specific instructions and their own Child DOX Index
- Each parent explains what its direct children cover and what stays owned by the parent
- The closer a doc is to the work, the more specific and practical it must be

## Child Doc Shape

- Create a child AGENTS.md when a folder becomes a durable boundary with its own purpose, rules, responsibilities, workflow, materials, or quality standards
- Work Guidance must reflect the current standards of the project or user instructions; if there are no specific standards or instructions yet, leave it empty
- Verification must reflect an existing check; if no verification framework exists yet, leave it empty and update it when one exists

Default section order:
- Purpose
- Ownership
- Local Contracts
- Work Guidance
- Verification
- Child DOX Index

## Style

- Keep docs concise, current, and operational
- Document stable contracts, not diary entries
- Put broad rules in parent docs and concrete details in child docs
- Prefer direct bullets with explicit names
- Do not duplicate rules across many files unless each scope needs a local version
- Delete stale notes instead of explaining history
- Trim obvious statements, repeated rules, misplaced detail, and warnings for risks that no longer exist

## Closeout

1. Re-check changed paths against the DOX chain
2. Update nearest owning docs and any affected parents or children
3. Refresh every affected Child DOX Index
4. Remove stale or contradictory text
5. Run existing verification when relevant
6. Report any docs intentionally left unchanged and why

## User Preferences

When the user requests a durable behavior change, record it here or in the relevant child AGENTS.md.

- Delegated ticket implementers run the `code-review` skill's parallel Standards and Spec subagents before the full `no-mistakes axi` gate and report both review axes plus no-mistakes findings, fixes, run ID, push/PR/CI outcome, and unresolved decisions to the supervising workflow. Escalate `ask-user` findings verbatim instead of deciding them without explicit standing consent. Parked gates (review/rebase/document) are escalation points: report, end the turn, and run `axi respond` only after the supervisor relays a decision; execute relayed decisions exactly, with the complete finding set named in the relay. Mechanics live in `docs/agents/delegated-delivery.md`.
- Parallel ticket workflows launch full interactive Pi TUI sessions through the durable Herdr scripts in `~/.pi/agent/pi-extensible-workflows/scripts/`, as visible tabs in the supervising session's current workspace; no separate Herdr workspace, manual launches, RPC, or `pi --print`. Each wave runs exactly one manifest-scoped deduplicating watcher that surfaces decision-relevant events (`ask-user` gates, parked auto-fix gates, `pr-ready` handoffs, `loop-limit`) to the supervising session while informational events stay notification-only; loop limits stop further fixing and require controlled recovery with pipeline custody preserved; cleanup runs automatically only after all run-owned PRs are merged, linked issues closed, and implementers terminal. Supervisor consumption discipline: stay passive between watcher events — never poll `axi status` or read panes on a timer; probe only on a decision-relevant event, before merge approval, on loop-limit/failure investigation, or on user request; interrupt a pane only to deliver a decision, approval, or instruction. Mechanics live in `docs/agents/delegated-delivery.md`.
- Delegated-wave supervisors and implementers must read `wiki/AGENT_LEARNINGS.md` before starting wave work and update it after every wave that produces durable lessons (verified measurement, pipeline mechanics, supervision, renderer fit/paint parity). It is live and binding despite living in the wiki archive.
- Delegated workflow development and general-purpose Standards/Spec subagents use `openrouter/~x-ai/grok-latest` with high thinking; no Terra model remains in the active workflow configuration. no-mistakes pipeline agents are pinned the same way: `~/.no-mistakes/config.yaml` sets `agent: pi` plus an `agent_args_override` of `--model openrouter/~x-ai/grok-latest:high`; after config changes, restart the daemon (`no-mistakes daemon restart`, or `--force` only when no active runs remain) so step agents pick up the new model. The daemon binary is a custom local build `v1.46.0-pi-session-reuse` (source checkout `C:\Users\Ag1Le\Documents\no-mistakes`, branch `pi-session-reuse-v1.46`, upstream `kunchenguid/no-mistakes`) that adds pi to `session_reuse` support: the review-fixer keeps one durable session across fix rounds of a run, review turns remain session-free by design; the official binary is backed up as `%LOCALAPPDATA%\no-mistakes\no-mistakes.exe.v1.46.0.bak4` and rollback is swap-back plus daemon restart. Never run `no-mistakes update` while the custom build is installed: the CLI shows a false `new version available` banner and updating would overwrite the feature. Revert to the official binary once upstream ships pi session reuse.
- Follow `docs/agents/delegated-delivery.md` for the manifest-driven PEW → run-owned worktree → visible Herdr implementer + host watcher → no-mistakes → verification → approved merger workflow. Start new waves through `start-ticket-wave.ps1`; use its `wave.json` for inspection, repair, watching, partial cleanup, and exact-head merge preflight instead of manually feeding RunIds, branches, worktrees, panes, or PRs. `start-ticket-wave.ps1` automatically launches `watch-ticket-wave.ps1` for repeated polling; the global `ticket-wave-followups.ts` extension forwards every queued event into the supervising Pi session without manual rearm. Use `Invoke-ApprovedMerge.ps1` for approved exact-head merges when PEW journal persistence is unreliable. Do not substitute manual branches or tab launches.

## Child DOX Index

- `impact_slides/AGENTS.md` — Python package (preprocessor v4 + shared modules); child covers renderer
- `impact_slides/renderer_v2/AGENTS.md` — legacy Step 4 renderer v2 (current layouts, charts, recipes, validation)
- `impact_slides/renderer_v3/AGENTS.md` — schema-v1 canonical rendering kernel (typed validation, plan freeze, chart/table/card composition families, format registry, legacy→v1 migrator, generated JSON Schema, deterministic artifact publication); remaining chart/card families in later tickets
- `docs/AGENTS.md` — agent operating docs (`docs/agents/`) and ADRs
- `tests/AGENTS.md` — pytest suite, fixtures, CI expectations
- `wiki/AGENTS.md` — historical archive + stale-doc marker policy; generated layout index; live `AGENT_LEARNINGS.md` pointer
- `scripts/AGENTS.md` — repo tooling (`gen_layout_index.py`, helpers)
- `artifacts/AGENTS.md` — committed reproducible capture evidence; child covers the #156 slide-27 recapture
- Root-owned: `CONTEXT.md`, `README.md`, `AGENTS.md`, `pytest.ini`, `requirements-ci.txt`, `.github/`, root `step*.py` entry shims, `config.example.yaml`
