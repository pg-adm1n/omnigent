---
name: sprint-execution
description: Sprint execution procedure (Steps 5-6) — Git worktree creation, Dev implementation & unit tests, SIT cross-vendor review & integration tests, and the Defect Loop.
---

# sprint-execution — Development, SIT Verification & Defect Loop

Follow this procedure for implementing approved sprint tasks and running the SIT defect loop.

## Procedure

### Step 5: Development & Unit Testing
1. For each approved Developer Task Packet from the sprint backlog:
   - Create an isolated git worktree at an ABSOLUTE path:
     `git worktree add <repo>/.worktrees/<task_id> -b task/<task_id>`
     (run `git rev-parse --show-toplevel` first so `<repo>` is absolute).
   - Create ALL worktrees first (one `sys_os_shell` per packet, same turn),
     then dispatch. Never interleave one worktree + one dispatch per turn —
     that serializes the sprint for no reason.
2. Dispatch one Developer (`dev` — Teammate A) per packet — IN PARALLEL,
   all in the SAME turn (up to 4 packets per turn; the per-turn dispatch cap
   is 6, so keep headroom for inbox/repair calls):
   ```yaml
   sys_session_send(
     agent="dev",
     title="dev-<task_id>",
     args={
       purpose: "implement",
       input: "<Task packet details, ABSOLUTE worktree path <repo>/.worktrees/<task_id> (cd there first and verify with pwd), Architect technical design, and BA acceptance criteria. Implement code and unit tests, drive unit tests to green, commit with 'Co-authored-by: omnigent <noreply@omnigent.ai>', and open PR via gh pr create.>"
     }
   )
   ```
   Dev shares your cwd by default — a relative worktree path WILL pollute
   the main checkout.
3. Emit ALL dispatches in the SAME turn you announce them; then end your turn.
4. Collect completions with `sys_read_inbox` — parallel workers finish OUT OF
   ORDER. Track per-task status in `.agile-pm/sprint.json` keyed by `task_id`
   and advance each task only on ITS dev's green report + PR URL. A task that
   fails or stalls NEVER blocks the others; handle it in its own
   (`agent="dev"`, `title="dev-<task_id>"`) session.
5. Update `.agile-pm/sprint.json` with each PR URL and task implementation status.

### Step 6: Peer Review & SIT Verification (Defect Loop)
1. Dispatch SIT / Peer Reviewer (`sit` — Teammate B) via `sys_session_send`:
   ```yaml
   sys_session_send(
     agent="sit",
     title="sit-<task_id>",
     args={
       purpose: "review",
       input: "<Dev PR URL + branch, ABSOLUTE worktree path <repo>/.worktrees/<task_id>, Architect specification, and BA Acceptance Criteria. cd to the worktree path FIRST (it has the PR branch checked out) and run the system integration test suites THERE — the main checkout does not contain the unmerged code. Verify end-to-end flows and report structured defects (blocking, non-blocking, test_failures). Do not edit code.>"
     }
   )
   ```
2. Emit the dispatch in the SAME turn; then end your turn.
3. Collect the SIT report with `sys_read_inbox`.
4. **Defect Loop**:
   - Inspect the SIT findings:
     - If `blocking` defects > 0 or `test_failures` > 0:
       - Record defects in `.agile-pm/sprint.json`.
       - Re-dispatch `dev` in the existing worktree session (`agent="dev"`, `title="dev-<task_id>"`, `args={purpose: "implement", input: "<Defect details and failure logs to fix>"}`).
       - Dev applies fixes, re-runs unit tests to green, commits with the co-authored trailer, and pushes updates.
       - Re-dispatch `sit` to re-verify integration tests.
       - Repeat until SIT reports 0 blocking defects and 0 test failures.
   - SIT dispatches parallelize the same way as dev (one `sit-<task_id>` per
     finished task, same turn, up to 4); each task's defect loop stays
     independent in its own (`dev-<task_id>` / `sit-<task_id>`) sessions.
     - **Loop cap (anti-spin)**: at most 3 dev→sit rounds per task. If the
       3rd SIT re-verification still reports blocking defects, STOP looping:
       record the deadlock in `.agile-pm/sprint.json` and escalate to the PO
       with the defect list, dev's fix attempts, and options (descope, send
       back to `architect` for redesign, or accept with follow-ups). Never
       burn a 4th round without explicit PO approval.
     - If all integration tests are green and 0 blocking defects remain:
       - Mark task technical verification passed in `.agile-pm/sprint.json`.
       - Proceed to Step 7 (`uat-signoff`).
