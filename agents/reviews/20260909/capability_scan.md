# Capability Scan

Date: 2026-09-09

## Platform

Claude Code (Opus 5) running inside the Claude desktop app, Code tab, on
Windows 11 Pro. Both a PowerShell tool and a Git Bash tool are available.

Work is taking place in a git worktree at
`H:\worktreesclaude\algaewatch-villarrica\workshop-code-orientation-75c650`,
branch `claude/workshop-code-orientation-75c650`. The main checkout at
`H:\algaewatch-villarrica` shares the same git configuration and remotes.

## Agent Capabilities

| Capability | Available | Evidence / Notes |
|---|---|---|
| File read/write | yes | Read, Write, Edit tools plus shell redirection; used throughout this mount |
| Shell commands | yes | Git Bash and PowerShell; Python 3 with pandas, numpy and scikit-learn confirmed present by running the audit scripts |
| Subagents | yes | `cavecrew-investigator`, `cavecrew-builder`, `cavecrew-reviewer`, `Explore`, `Plan`, `general-purpose`, `claude` |
| Parallel tool calls | yes | Independent calls issued in a single message |
| Browser/UI inspection | yes, unused so far | In-app browser tools available; no frontend verification performed during mounting |
| Network access | yes | `WebFetch` available; git over HTTPS verified by cloning a private repository |
| GitHub/PR tooling | partial | `gh` CLI is **not installed**. The GitHub MCP server requires authorization and this session is non-interactive, so it cannot be authorized here. Git over HTTPS works through the Windows credential manager |
| Google Docs/Drive export | no | MCP server present but unauthorized; cannot be authorized in a non-interactive session |
| Image/PDF/doc generation | partial | Artifact publishing available. The pdf-viewer MCP server disconnected and reconnected during this session and is unreliable |

## Verified During This Mount

- Private repository access through the existing git credential helper: cloned
  `agent-harness-kernel` branch `testing` at commit `a5f428d`, without handling
  any credential directly.
- The cloned kernel is byte-identical to the copies installed at
  `/h/game-colab/.harness` and `/h/solar-energy-contractor-simulator-(4.6)/.harness`,
  so no version divergence risk applies to this mount.
- Fork reachable and consistent: `StrawberryFrappe/algaewatch-villarrica` at
  `4b37bea`, the same commit as the original repository, so history and
  authorship are preserved.
- Remotes rewired: `origin` now points at the owner's fork, `upstream` at
  `Luchosqi/algaewatch-villarrica`. Local `main` retargeted to `origin/main`.
- Python audit scripts execute and reproduce every figure quoted in
  `EVIDENCE_INDEX.md`.

## Subagent Policy

- If subagents are available, use them for plan review, implementation review,
  adversarial verification, research, and parallel read-only inspection where
  appropriate.
- If subagents are not available, document the downgrade and perform a labeled
  single-agent review.
- Never pretend a simulated role is an autonomous subagent.

### Application to this mount

Harness documents were written by the main agent rather than delegated. This was
deliberate: their content encodes an audit conducted across a long interactive
session, and delegating would have required re-transmitting that context with
attendant loss. The harness mount review is delegated to a subagent, which is
where independent judgement carries real value and where both the kernel's
review protocol and the user's global orchestration rules require it.

## Downgrades

| Downgrade | Effect on harness strength |
|---|---|
| No `gh` CLI; GitHub MCP unauthorized | Pull requests and issues cannot be created from this session. Git push, fetch and clone are unaffected. Any PR must be opened by the user through the GitHub web interface |
| Several MCP servers unauthorized, one endpoint unreachable | No effect on this project. None of them are needed |
| No frontend verification performed | GATE-PQ has not been exercised. No screenshot evidence exists yet, so no visual claim is currently supported |
| No test runner present | GATE-TEST cannot pass until BL-002 lands. Audit findings rest on reproducible scripts rather than on a regression suite |
