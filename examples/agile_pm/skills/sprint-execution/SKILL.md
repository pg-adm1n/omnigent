---
name: sprint-execution
description: Sprint execution procedure (Steps 5-6) — Git worktree creation, Dev implementation & unit tests, SIT cross-vendor review & integration tests, and the Defect Loop.
---

# sprint-execution — Development, SIT Verification & Defect Loop

Follow this procedure for implementing approved sprint tasks and running the SIT defect loop.

## Procedure

### Step 5: Development & Unit Testing
1. For each approved Developer Task Packet from the sprint backlog:
   - Create an isolated git worktree for the task:
     `git worktree add .worktrees/<task_id> -b task/<task_id>`
2. Dispatch Developer (`dev` — Teammate A) via `sys_session_send`:
   ```yaml
   sys_session_send(
     agent="dev",
     title="dev-<task_id>",
     args={
       purpose: "implement",
       input: "<Task packet details, worktree path .worktrees/<task_id>, Architect technical design, and BA acceptance criteria. Implement code and unit tests, drive unit tests to green, commit with 'Co-authored-by: omnigent <noreply@omnigent.ai>', and open PR via gh pr create.>"
     }
   )
   ```
3. Emit the dispatch in the SAME turn; then end your turn.
4. Collect the Dev completion report with `sys_read_inbox`.
5. Update `.agile-pm/sprint.json` with the PR URL and task implementation status.

### Step 6: Peer Review & SIT Verification (Defect Loop)
1. Dispatch SIT / Peer Reviewer (`sit` — Teammate B) via `sys_session_send`:
   ```yaml
   sys_session_send(
     agent="sit",
     title="sit-<task_id>",
     args={
       purpose: "review",
       input: "<Dev PR diff, Architect specification, and BA Acceptance Criteria. Run system integration test suites, verify end-to-end flows, and report structured defects (blocking, non-blocking, test_failures). Do not edit code.>"
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
     - If all integration tests are green and 0 blocking defects remain:
       - Mark task technical verification passed in `.agile-pm/sprint.json`.
       - Proceed to Step 7 (`uat-signoff`).
