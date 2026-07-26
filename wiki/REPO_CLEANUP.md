# Repo Cleanup Log

> **Maintenance policy:** this file tracks the *current* cleanup state only.
> When a new cleanup pass happens, **update this file in place** — replace the
> log below with the latest activity. Do not append historical passes; git
> history is the archive, this file is the snapshot.

## Last cleanup: 2026-07-25 (sim history purge completed — .git 60MB → 25MB)

### What was done

**Endgame of the sim-scrub (previous pass rewrote main; this pass reclaimed the space)**
- User deleted the v4 GNHF worktree; deleted branch `gnhf/objective-produce-a-9c5007`
  and local safety net `backup/pre-scrub-main`.
- Fixed local `assets/issue-evidence` branch still pointing at the botched
  full-tree orphan commit (`4894224`) — repointed to `origin/assets/issue-evidence`
  (`9e3aa27`, the 11-PNG-only orphan).
- Found the real space-pinners: **no-mistakes custody refs**
  (`refs/no-mistakes/sync/*` anchors + `refs/remotes/no-mistakes/*` stale feature
  branches) held the entire pre-scrub chain. Deleted the local refs (the
  pipeline's own bare mirror at `~/.no-mistakes/repos/` keeps its copies —
  merged runs need no recovery).
- `git reflog expire --expire=now --all` + `git gc --prune=now`:
  **`.git` 60MB → 25MB** (pack 54.6 → 24.2 MiB).
- Remaining sim refs are exactly the intentional two: `gnhf/objective-produce-a-11b7c0`
  (active v5 sim run) and `assets/issue-evidence` (orphan screenshots for #96–#103).
- GitHub side: origin refs no longer reach the old sim chain; GitHub's GC
  reclaims it in due course.

### Environment notes (for future cleanups)
- **no-mistakes pins history twice**: `refs/remotes/no-mistakes/*` (mirror
  tracking) AND `refs/no-mistakes/sync/*` (run sync anchors). After any history
  rewrite, both must be deleted locally before `gc` can reclaim. The mirror
  repo keeps custody, so this is safe for terminal/merged runs.
- After force-pushing rewritten history, check `git for-each-ref --contains
  <old-sha>` to find every ref still pinning old objects before running gc.
- Orphan-branch recipe: `git checkout --orphan <b>` → `git rm -rfq --cached .`
  → commit ONLY evidence (`git add -f` since `simulation/` is gitignored) →
  push `HEAD:<branch>`. Verify the LOCAL branch points at the clean commit
  afterward (a botched first attempt keeps the full tree alive locally).
- `git filter-repo` via `pip install git-filter-repo`; executable in
  `%APPDATA%\Python\Python314\Scripts`.
- `gh api` comment PATCH needs the *numeric* comment id; read gh output with
  `encoding="utf-8"` on this machine.

### Deferred (conscious, re-check next pass)
- `step4_builder_validator.py` consolidation (real refactor, not a sweep).
- `tests/test_renderer_v2_charts_js.py` split (~2,100 lines, grows every ticket).
- When the v5 GNHF run wraps: delete its branch/worktree + gc again for the
  last few MB.

### Standing policies
- `simulation/` evidence lives only in GNHF worktrees, never on main
  (commit 1628633). Do not path-merge it back.
- Screenshot/evidence links in issues: pin to a commit SHA or the
  `assets/issue-evidence` orphan branch — never a mutable branch.
- Delete feature branches after PR merge (no-mistakes-safe once merged).
