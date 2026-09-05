---
name: sprint-planning
description: Sprint planning procedure (Steps 1-4) — BA User Story generation, Architect Technical Design, task breakdown, and PO Plan Approval gate.
---

# sprint-planning — Sprint Ingestion, Story & Design, PO Approval

Follow this procedure to plan a sprint before writing code or creating worktrees.

## Procedure

### Step 1: Raw Feature Ingestion
1. Receive raw feature description, requirements, or sprint scope from the Product Owner (PO).
2. Initialize or update `.agile-pm/sprint.json` to record:
   - Sprint metadata (`sprint_id`, `name`, `status: "planning"`)
   - High-level business goal and raw feature description
   - Initial backlog item records.

### Step 2: User Story & Acceptance Criteria Generation
1. Dispatch the Business Analyst (`ba`) sub-agent via `sys_session_send`:
   ```yaml
   sys_session_send(
     agent="ba",
     title="story-<feature_slug>",
     args={
       purpose: "story",
       input: "<Raw feature description and requirements. Draft user stories in standard format with exhaustive Gherkin Given/When/Then acceptance criteria and UAT scenarios.>"
     }
   )
   ```
2. Emit the dispatch call in the SAME turn you announce it; then end your turn.
3. Collect the BA story report with `sys_read_inbox`.
4. Update `.agile-pm/sprint.json` with user story IDs and Gherkin Acceptance Criteria.

### Step 3: Technical Architecture & Design Breakdown
1. Dispatch the Software Architect (`architect`) sub-agent via `sys_session_send`:
   ```yaml
   sys_session_send(
     agent="architect",
     title="design-<feature_slug>",
     args={
       purpose: "design",
       input: "<BA User Stories and Acceptance Criteria. Inspect the codebase, design technical architecture/schemas/interfaces, and break down implementation into Developer Task Packets.>"
     }
   )
   ```
2. Emit the dispatch in the SAME turn; then end your turn.
3. Collect the Architect design report with `sys_read_inbox`.
4. Update `.agile-pm/sprint.json` with task breakdown packets, file scopes, and verification criteria.

### Step 4: PO Plan Approval Gate
1. Synthesize the complete sprint plan proposal:
   - User Stories & Gherkin Acceptance Criteria (from BA)
   - Technical Architecture, Schemas, and Developer Task Breakdown (from Architect)
   - Proposed sprint backlog and task assignments.
2. Present the consolidated proposal to the Product Owner (PO).
3. **MANDATORY GATE**: Wait for explicit PO approval before proceeding to Step 5.
   - Do NOT create git worktrees or dispatch `dev` before PO approval is granted.
   - If the PO requests revisions, route feedback back to `ba` or `architect` as appropriate.
   - Once approved, transition `.agile-pm/sprint.json` status to `"in_progress"` and proceed with `sprint-execution`.
