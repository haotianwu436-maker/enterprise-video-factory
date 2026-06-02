# AGENT.md

<!-- repo-init:managed -->

## Source Of Truth

- `README.md`: human-facing repository summary
- `AGENT.md`: agent operating rules
- `PROJECT.md`: project definition or compatibility snapshot
- `STATUS.md`: current state, latest feedback, task impact, replan suggestions, blockers, and next step
- `DECISIONS.md`: durable accepted decisions only
- `tasks/*.md`: execution work items

## Reading Order

1. `PROJECT.md`
2. `STATUS.md`
3. `DECISIONS.md`
4. the coordinating task in `tasks/` when one exists
5. the relevant child task in `tasks/`

## Operating Rules

- Preserve user-authored source plans by default.
- Keep all updates consistent with the current source confidence.
- Treat low-confidence intake as a clarification problem, not an implementation license.
- Treat initialization as complete once the collaboration files, first task, and initialization report exist.
- Do not begin implementation after initialization unless the user explicitly asks for post-init execution.
- When a coordinating master task exists, use it to sequence child tasks and keep `STATUS.md` pointed at the master task until a child task is explicitly chosen.
- When a task reaches a milestone, blocker change, acceptance change, assumption invalidation, or user-directed change, update that task's `Assumption Checks` and `Downstream Impact` before closing the execution batch.
- When task-local feedback affects unfinished work, update the coordinating master task `Feedback Ledger` plus `STATUS.md` `Latest Feedback`, `Task Impact`, and `Recommended Replan`.
- For single-task work, let `STATUS.md` carry the current feedback and replan suggestion without inventing a coordinating task.
- Treat `Recommended Replan` as suggestion space until downstream changes are explicitly accepted.
- Do not rewrite untouched task status or acceptance criteria from a single unconfirmed feedback cycle.
- Run `uv run validate-contracts --repo .` and `uv run pytest` before review or acceptance when contract/schema/OpenAPI/tooling files change.
- Append to the task `Execution Log` only after a meaningful execution batch or milestone.
- Add to `DECISIONS.md` only when a real durable decision or explicitly accepted replan outcome exists.

## Update Rules

Update `STATUS.md` when:

- the active task changes
- latest feedback changes
- task impact or recommended replan changes
- a blocker appears or is removed
- the next recommended step changes

Update `DECISIONS.md` when:

- a non-trivial technical choice is accepted
- a replan decision is explicitly accepted and should become durable
- an option is rejected for a concrete reason
- a previous decision is reversed

Update a task file when:

- the task is created
- acceptance criteria change
- assumption validation state changes
- downstream impact changes
- implementation notes materially affect execution
- the task status changes
- a blocker appears or is removed
- a meaningful batch of related repository changes completes

Update the task `Execution Log` when:

- a milestone is reached
- a task status changes
- a blocker appears or is removed
- a meaningful batch of related repository changes completes
- a user decision materially changes the execution path
- a downstream impact or replan recommendation becomes material to future tasks

If an `Execution Log` entry changes downstream work, also update `Downstream Impact`; do not leave that impact only in the log.

Do not update the task `Execution Log` for:

- every file save
- every small refactor or formatting-only edit
- every micro-step inside the same execution batch
- changes that are already obvious from git history and do not affect execution understanding

## Anti-Patterns

- Do not rewrite the source plan unless the user explicitly requests it.
- Do not invent implementation details just to make files look complete.
- Do not use ad hoc temp directories when `.repo-init/` already exists.
- Do not turn the task `Execution Log` into a file-by-file or save-by-save change ledger.
- Do not store temporary feedback notes or unaccepted replan suggestions in `DECISIONS.md`.
- Do not rewrite not-yet-started task status or acceptance criteria from a single unconfirmed feedback cycle.
