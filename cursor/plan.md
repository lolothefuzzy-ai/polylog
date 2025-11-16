# CURSOR COMPOSER PLAN

Project: Polyform Generator

Authoring AI: Cursor

Purpose: Stable, credit-aware multi-environment development workflow

## 1. GLOBAL WORKFLOW RULES

Cursor should always follow these principles:

- **GitHub is the single source of truth.** All states, checkpoints, docs, and code changes go into the repo.
- **Cursor is the primary implementation engine.** Full backend feature development, refactoring, multi-file changes, data structures, complex logic.
- **Claude is the architect.** Cursor should read Claude's plans from `/docs/architecture`, translate them into code, and summarize blockers back into `/state/next-steps.md`.
- **Windsurf is the fallback IDE.** Cursor must write detailed checkpoints when credits run low so Windsurf can seamlessly continue.
- **Manus is removed from workflow.** Replaced by lightweight free prototyping tools (this is documented, no actions needed).
- **Every major coding session ends with a checkpoint commit.**

## 2. REPO STRUCTURE

```
/docs
  /architecture        ← Claude's high-level planning
  /system              ← System-level docs Cursor maintains
  /api                 ← Swagger/OpenAPI if relevant
  /diagrams            ← Sequence/state diagrams

/state
  checkpoint.md        ← Cursor auto-updates
  next-steps.md        ← Immediate actionable items
  progress-log.md      ← Append-only development timeline
  credits.md           ← Cursor writes last-known credit status

/src
  ... project code ...

/cursor
  plan.md              ← This master file
  tasks.md             ← Cursor-generated task lists
  session-notes.md     ← Scratchpad notes during dev

/tools
  github-actions       ← non-aggressive checkpoint workflows
```

## 3. CURSOR WORKING MODES (State Machine)

Cursor should maintain these modes through `state/checkpoint.md`:

### MODE A — BUILD (default)
Used when credits are healthy.
- Implement backend features
- Refactor
- Update docs
- Commit meaningful changes

### MODE B — CONSOLIDATE (credits low or major unit complete)
Cursor must:
- Summarize all work in `/state/checkpoint.md`
- Update `/state/next-steps.md`
- Update `/docs/system/*`
- Push all changes
- Prepare repo for Windsurf handoff

### MODE C — HANDOFF (Cursor cannot continue)
Cursor generates:
- Detailed report for Windsurf in `/state/handoff-windsurf.md`
- Step-by-step instructions
- File references
- Known bugs
- Code patterns to follow
- Open TODO items

💡 Cursor should automatically switch to MODE C when it detects it cannot complete tasks due to remaining credits.

## 4. CHECKPOINT FILE TEMPLATE

See `/state/checkpoint.md` for template structure.

## 5. NEXT-STEPS TEMPLATE

See `/state/next-steps.md` for template structure.

## 6. WINDSURF HANDOFF TEMPLATE

See `/state/handoff-windsurf.md` for template structure.

## 7. GITHUB ACTION (Light Touch)

See `.github/workflows/checkpoint-on-demand.yml` for manual checkpoint workflow.

## 8. CURSOR SESSION RULES

- After any major change: Update checkpoint.md, next-steps.md, commit & push
- Before refusing work due to credits: Finalize docs, generate Windsurf handoff file, commit & push
- At session start: Read checkpoint.md, next-steps.md, /docs/system/*, recent commits
- Every significant operation: Log to /state/progress-log.md

## 9. CURSOR TODO LIST FORMAT

See `/cursor/tasks.md` for task tracking format.

## 10. PROMPT FOR CURSOR

You are Cursor operating within a multi-environment workflow (Cursor primary, Windsurf fallback, Claude architect).

Follow the repository structure and state system defined in `/cursor/plan.md`.

Your responsibilities:
1. Always update checkpoints in `/state/checkpoint.md`
2. Always write next steps in `/state/next-steps.md`
3. When credits run low, switch to CONSOLIDATE mode and prepare Handoff to Windsurf
4. Maintain accurate system documentation in `/docs/system`
5. Keep commits atomic and descriptive
6. Use `/cursor/tasks.md` to track your work
7. ALWAYS ensure the repo is stable, consistent, and ready for another tool to continue

Your first action in any session:
- Read `/state/checkpoint.md`
- Read `/state/next-steps.md`
- Read the most recent commit messages
- Then announce what you understand about the current state before making changes.

