# Repo Cleanup Log

> **Maintenance policy:** this file tracks the *current* cleanup state only.
> When a new cleanup pass happens, **update this file in place** — replace the
> log below with the latest activity. Do not append historical passes; git
> history is the archive, this file is the snapshot.

## Last cleanup: 2026-07-25 (merged-branch sweep + simulation history scrub)

### What was done

**Branches**
- Deleted 5 merged branches (local + origin): `chore/complete-legacy-baseline-removal`,
  `feat/amex-f11-stack-packing`, `feat/amex-f4-pill-packing`,
  `feat/amex-n3-signed-paren-chips`, `feat/amex-p3-polish`.
- Remaining: `main`, `gnhf/objective-produce-a-9c5007` (sim worktree branch),
  `assets/issue-evidence` (orphan, see below), local-only `backup/pre-scrub-main`.

**Simulation history scrub (the big one)**
- `git filter-repo --refs main --path simulation/ --invert-paths` removed all
  sim PNG history from main; main force-pushed (`a508795 → ecc697e`, forced).
  **All pre-scrub commit SHAs on main are rewritten.**
- Issue evidence preserved first: 11 round-3 ticket screenshots moved to the
  orphan branch `assets/issue-evidence` (11 PNGs + EVIDENCE.md, ~824KB), and
  the 11 close comments on #96–#103 repinned from `7c66284` →
  `assets/issue-evidence` URLs (verified HTTP 200).
- Local safety net: `backup/pre-scrub-main` branch points at pre-scrub main;
  delete once the rewritten history is trusted.
- Remote size: GitHub still retains sim blobs because `gnhf/objective-produce-a-9c5007`
  (the v4 sim baseline) intentionally keeps them per the sim-evidence policy.
  The remote shrink completes when that branch is eventually deleted.
  Local `.git` likewise keeps old objects while the backup + gnhf refs exist.

### Environment notes (for future cleanups)
- `git filter-repo` installed via `pip install git-filter-repo`; executable lives
  in `%APPDATA%\Python\Python314\Scripts` (not on default PATH).
- Orphan-branch recipe: `git checkout --orphan <b>` → `git rm -rfq --cached .`
  → commit ONLY evidence (`git add -f` needed since `simulation/` is gitignored)
  → push. Do NOT `git reset` before committing (undoes the index clear).
- `filter-repo --refs main` limits rewriting to main — essential so the gnhf
  sim branch and backup refs are untouched.
- The `no-mistakes` remote is a local bare mirror (`~/.no-mistakes/repos/`);
  branch deletion and even main force-push are safe — custody lives in the mirror.
- `gh api` comment PATCH needs the *numeric* comment id (node ids 404);
  read gh output with `encoding="utf-8"` on this machine.

### Deferred (conscious, re-check next pass)
- `step4_builder_validator.py` consolidation (real refactor, not a sweep).
- `tests/test_renderer_v2_charts_js.py` split (~2,100 lines, grows every ticket).
- Delete `backup/pre-scrub-main` + `gnhf/objective-produce-a-9c5007` when v4
  sims wrap → then `git gc` for the actual local/remote size win.

### Standing policies
- `simulation/` evidence lives only in GNHF worktrees, never on main
  (commit 1628633). Do not path-merge it back.
- Screenshot/evidence links in issues: pin to a commit SHA or the
  `assets/issue-evidence` orphan branch — never a mutable branch.
- Delete feature branches after PR merge (no-mistakes-safe once merged).
