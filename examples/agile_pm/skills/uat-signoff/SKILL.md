---
name: uat-signoff
description: Business Acceptance & UAT sign-off procedure (Step 7) — BA black-box Given/When/Then validation against PR diff and SIT evidence, sprint completion, and PO handoff.
---

# uat-signoff — Business Acceptance, Sprint Completion, PO Handoff

Follow this procedure for the final business acceptance validation and PO deliverable handoff.

## Procedure

### Step 7: Business AC Review & UAT Sign-off
1. Dispatch Business Analyst (`ba`) via `sys_session_send`:
   ```yaml
   sys_session_send(
     agent="ba",
     title="uat-<feature_slug>",
     args={
       purpose: "uat",
       input: "<PR diff, SIT verification evidence, and original Gherkin Given/When/Then Acceptance Criteria. Perform black-box acceptance validation and render an explicit ACCEPTED or REJECTED verdict.>"
     }
   )
   ```
2. Emit the dispatch in the SAME turn; then end your turn.
3. Collect the BA UAT report with `sys_read_inbox`.
4. Evaluate verdict:
   - If `REJECTED`:
     - Record discrepancies in `.agile-pm/sprint.json`.
     - Route defects back to `sprint-execution` Defect Loop for remediation.
   - If `ACCEPTED`:
     - Update `.agile-pm/sprint.json` with `status: "completed"`, UAT sign-off evidence, and completion timestamp.
     - Generate a final Sprint Summary Report containing:
       - Summary of delivered user stories and acceptance criteria.
       - Architecture and implementation notes.
       - Unit test and SIT verification results.
       - UAT sign-off confirmation.
       - Link to open PR(s).
     - Present the completed deliverable and PR to the Product Owner (PO) for final review and merge.
     - **REMINDER**: The Agile PM orchestrator never merges PRs directly; merging is reserved for the PO.
     - Once the PO confirms the merge, clean up: `git worktree remove <repo>/.worktrees/<task_id> --force`, `git worktree prune`, and delete the merged task branch. Never remove a worktree whose PR is still open.
