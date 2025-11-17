# Multi-Environment Development Workflow

This document describes the multi-environment development workflow for Polylog6.

## Overview

The project uses a multi-environment development approach:
- **Cursor**: Primary implementation engine
- **Windsurf**: Fallback IDE
- **Claude**: Architect (planning and design)

## Workflow Modes

### MODE A — BUILD (default)
Used when credits are healthy. Cursor implements features, refactors, updates docs, and commits changes.

### MODE B — CONSOLIDATE
Used when credits are low or a major unit is complete. Cursor summarizes work, updates state files, and prepares for handoff.

### MODE C — HANDOFF
Used when Cursor cannot continue. Cursor generates detailed handoff documentation for Windsurf.

## State Management

All state is tracked in the `/state` directory:
- `checkpoint.md` - Current system checkpoint
- `next-steps.md` - Immediate actionable items
- `progress-log.md` - Development timeline
- `credits.md` - Credit status tracking
- `handoff-windsurf.md` - Handoff documentation

## Repository Structure

- `/docs/architecture` - Claude's high-level planning
- `/docs/system` - System-level documentation
- `/state` - State management files
- `/cursor` - Cursor-specific files (plan, tasks, notes)

## Checkpoint System

Checkpoints are created:
- After major coding sessions
- Before switching modes
- When preparing for handoff
- On demand via GitHub Actions workflow

See `cursor/plan.md` for full workflow details.

