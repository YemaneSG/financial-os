# AI Development Governance Kit

This directory contains the model-agnostic operating rules for AI-assisted product development in Financial OS and reusable templates for other projects.

## Canonical project policy

- `ai-development-operating-model.md` — approved Financial OS roles, evidence rules, review protocol, quality gates, and orchestration strategy

## Reusable templates

- `templates/ai-development-operating-model.template.md` — adapt the operating model to another project
- `templates/execution-packet.template.md` — hand one bounded vertical slice to an implementation lead
- `templates/independent-review.template.md` — require an evidence-backed, independent plan or release review
- `templates/session-bootstrap.template.md` — start a new Codex, Claude Code, or other capable agent session from repository state rather than conversation memory

## Design rule

Canonical product and governance rules must remain tool- and model-agnostic. Tool-specific files such as `AGENTS.md`, `CLAUDE.md`, agent definitions, skills, commands, and hooks should point to these documents and implement them without silently changing their meaning.

## Reuse in another project

1. Copy the files under `templates/` into the new repository.
2. Rename each file by removing `.template` when it becomes active.
3. Replace every `{{PLACEHOLDER}}`.
4. Remove roles, gates, or procedures that do not fit the project; do not retain ceremony without a demonstrated purpose.
5. Have the project owner approve the operating model.
6. Create concise adapters for the AI development tools used by that project.
7. Use an execution packet for each meaningful vertical slice.
8. Run independent review only at the risk and decision points defined in the operating model.

## Reuse in a fresh chat session

Use `templates/session-bootstrap.template.md` as the first prompt. The new session should read the canonical repository artifacts, produce a brief, identify missing context, and wait for a confirmed session outcome before changing project state.

Conversation history is supporting context, not the source of truth. Accepted decisions must be recoverable from versioned repository artifacts.
