# Delegated Workflow Token Audit

> Research archive — 2026-08-11. Live contract: root `AGENTS.md` bullets and `docs/agents/delegated-delivery.md` (Follow-up token economy). If this doc disagrees with those, they win.

Findings from auditing every token-consuming surface of the ticket-wave setup (supervisor session, implementer panes, no-mistakes pipeline agents, watcher/scripts), after wave `d383c963` (#183/#187/#192/#195) demonstrated the failure modes: implementer panes reaching 534k cumulative tokens / 99.4% context, and ~90k supervisor input tokens spent on watcher follow-ups.

## Where tokens flow

| Surface | Mechanism | Cost shape |
|---|---|---|
| Supervisor session | watcher follow-up events delivered by `ticket-wave-followups.ts` | per event: full JSON payload into context |
| Implementer panes | ticket work + gate driving | per model turn: entire accumulated context |
| Pipeline step agents | review/test/document/lint/ci + fix agents | cold-start ramp-up per round (AGENTS chain + repo exploration, ~30–80k) |
| Watcher / wave scripts | PowerShell processes | zero model tokens |
| Idle panes | open pi TUI with no active turn | zero |

## Fixed leaks (2026-08-11)

1. **Implementer sleep-poll gates.** Implementers waited at gates with `sleep 180 && axi status` agent-level loops; each poll paid a full model turn over the entire context plus ~1–2k of status blob. Fix: `~/.agents/skills/no-mistakes/SKILL.md` now mandates blocking — `axi run` and `axi respond` block until the next gate or outcome, a plain `axi run` re-attaches to an active run, and sleep-poll loops are explicitly forbidden. `axi status` is for one-off checks only. Liveness remains the watcher's job (free).
2. **Supervisor follow-up volume.** Fix in two parts:
   - Payload compression in `watch-visible-implementers.ps1` `Return-Event`/`Compress-AxiStatus`: `branch_sync` dropped unless anomalous (diverged/behind/local_ahead), `help[...]` boilerplate stripped, `steps[...]`/`active_steps[...]` tables collapsed to one line, raw pane output capped to 15 lines × 200 chars with a `herdr pane read` pointer. Gate/ask-user content always survives.
   - Decision-relevance routing in `ticket-wave-followups.ts`: only `ask-user`, `pr-ready`, `loop-limit`, implementer `done`, and events carrying `outcome`/`error`/`status: failed` reach the session; the rest are suppressed as `informational` in `actions.jsonl`. Desktop notifications still fire for every event.
   - Supervisor consumption discipline (root `AGENTS.md`): passive between events, no timer polling, probe only on decision-relevant events / pre-merge / loop-limit / user request.
   - Measured on wave `d383c963`: 41 events / 296KB feed (~80–90k tokens); projected ~75% reduction on the next wave.
3. **Root AGENTS.md per-session tax.** Every pi session in a worktree auto-loads root `AGENTS.md`; mechanical watcher details were moved out of it into `docs/agents/delegated-delivery.md` (Follow-up token economy), keeping rules in root per DOX style.

## Remaining structural costs

1. **Cold step agents (biggest remaining whale).** no-mistakes `session_reuse: true` persists one reviewer session across re-reviews only for claude/codex; pi runs cold, so every review/fix round pays full context ramp-up again (~20 rounds/wave ≈ 1M+ tokens). Needs upstream no-mistakes support for pi session reuse. **Update (later same day):** implemented locally — the installed daemon is a custom build `v1.46.0-pi-session-reuse` of upstream `kunchenguid/no-mistakes` v1.46.0 that adds pi to `session_reuse` (source: `C:\Users\Ag1Le\Documents\no-mistakes`, branches `pi-session-reuse` / `pi-session-reuse-v1.46`). Scope correction found during implementation: `session_reuse` covers the review-**fixer** role only; review/rereview turns run cold by design so the certifier never resumes the session that prescribed its fixes. The saving is therefore the fixer skipping re-ramp-up on fix rounds 2–5, not the full whale estimated above.
2. **Thinking level is global.** `agent_args_override` in `~/.no-mistakes/config.yaml` pins all pipeline agents to `openrouter/~x-ai/grok-latest:high`; no per-step knob exists, so mechanical steps (lint/document/ci) think as hard as review. Lowering globally also softens review; per-step effort needs upstream support.
3. **Review-fix round count.** Controlled at the gate: from round ≥2, fix consents should carry `--instructions` demanding a whole-class audit (e.g. all measure/paint parity in one pass) so the next round cannot surface another one-off finding.

## Rejected ideas

- **Stale-event TTL in the extension** — redundant once decision-relevance routing landed: stale events were overwhelmingly informational, and signature dedup covers decision-relevant repeats. Add only if a stale decision-relevant event ever bites.
- **Ending implementer panes at pr-ready** — idle panes cost nothing; keeping them open enables cheap recovery re-engagement (demonstrated on #183/#195).
