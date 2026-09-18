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

- Delegated ticket waves: load `.agents/skills/delegated-delivery/SKILL.md` (supervise/implement procedure). Contract and script catalog remain `docs/agents/delegated-delivery.md`. Lesson log remains `wiki/AGENT_LEARNINGS.md` — read it before a wave; harvest durable reflexes into the skill (do not diary already-fixed script bugs). Start waves with `start-ticket-wave.ps1`; inspect/repair/watch/cleanup/teardown from its `wave.json`. New waves write `cleanupOnAllMerged: false`.
- Delegated workflow development and general-purpose Standards/Spec subagents use `supergrok/grok-4.6` with high thinking (dev alias in `~/.pi/agent/pi-extensible-workflows/settings.json` `modelAliases.dev`, general-purpose agent in `~/.pi/agent/agents/general-purpose.md`); no Terra model remains in the active workflow configuration. no-mistakes pipeline agents are pinned the same way: `~/.no-mistakes/config.yaml` sets `agent: pi` plus an `agent_args_override` of `--model supergrok/grok-4.6:high`; after config changes, restart the daemon (`no-mistakes daemon restart`, or `--force` only when no active runs remain) so step agents pick up the new model. The daemon binary is a custom local build `v1.46.0-pi-session-reuse` (source checkout `C:\Users\Ag1Le\Documents\no-mistakes`, branch `pi-session-reuse-v1.46`, upstream `kunchenguid/no-mistakes`) with two local patches: pi `session_reuse` support (the review-fixer keeps one durable session across fix rounds of a run, review turns remain session-free by design) and a deterministic `Closes #<n>` append in the PR step when the branch name matches `issue-<n>` (fork commit `ca9e2e0`; watcher compensation stays as second layer). The official binary is backed up as `%LOCALAPPDATA%\no-mistakes\no-mistakes.exe.v1.46.0.bak4` and the pre-closing-ref custom binary as `.bak5`; rollback is swap-back plus daemon restart. Rebuilds use portable Go at `C:\Users\Ag1Le\go-portable\go\bin` (`go build -o ./bin/no-mistakes.exe ./cmd/no-mistakes`); the fork steps suite is green except environment-bound CI-timer tests that exceed the default package timeout on this machine (run with `-skip TestCIStep` or a long `-timeout`). Never run `no-mistakes update` while the custom build is installed: the CLI shows a false `new version available` banner and updating would overwrite the feature. Revert to the official binary once upstream ships pi session reuse. Model pinning across pi default, the `dev` alias (implementer sessions), general-purpose subagent, no-mistakes, and GNHF is switched together via `~/.pi/agent/bin/switch-pi-model.ps1` (menu or `-Model provider/model -Thinking level`); it backs up each file, restarts the no-mistakes daemon, and warns when docs still pin the old model.

## Child DOX Index

- `impact_slides/AGENTS.md` — Python package (preprocessor v4 + shared modules); child covers renderer
- `impact_slides/renderer_v2/AGENTS.md` — legacy Step 4 renderer v2 (current layouts, charts, recipes, validation)
- `impact_slides/renderer_v3/AGENTS.md` — schema-v1 canonical rendering kernel (typed validation, plan freeze, chart/table/card + dual/hero/metric + chart_grouped_annex + strategy_board compositions incl. combo charts, format registry, legacy→v1 migrator, generated JSON Schema, deterministic artifact publication); D314 canonical Amex corpus
- `docs/AGENTS.md` — agent operating docs (`docs/agents/`) and ADRs
- `tests/AGENTS.md` — pytest suite, fixtures, CI expectations
- `wiki/AGENTS.md` — historical archive + stale-doc marker policy; generated layout index; live `AGENT_LEARNINGS.md` pointer
- `scripts/AGENTS.md` — repo tooling (`gen_layout_index.py`, helpers)
- `artifacts/AGENTS.md` — committed reproducible capture evidence; children cover the #156 slide-27 recapture, the #354 linear wrap recapture, the D315 renderer-3.0.0 release bundle, and renderer_v3 Archify diagrams
- Root-owned: `CONTEXT.md`, `README.md`, `AGENTS.md`, `pytest.ini`, `requirements-ci.txt`, `.github/`, root `step*.py` entry shims, `config.example.yaml`, `.agents/skills/delegated-delivery/` (Pi ticket-wave procedure; references synthesize `wiki/AGENT_LEARNINGS.md`)
