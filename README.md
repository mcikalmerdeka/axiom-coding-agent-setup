# AXIOM Coding Agent Setup

CLI tool to quickly set up AXIOM coding agent instructions in your projects.

## Usage

Run the CLI using npx (no installation required):

```bash
npx axiom-coding-agent-setup
```

Or use the shorter alias:

```bash
npx axiom-setup
```

## What It Does

This command downloads the following files from the [axiom-coding-agent-setup](https://github.com/mcikalmerdeka/axiom-coding-agent-setup) repository into your current project directory:

- `AGENTS.md` — Main agent instructions
- `.agents/engineering.md` — Engineering principles & code standards
- `.agents/stack.md` — Technology stack knowledge
- `.agents/workflow.md` — Workflow guidelines & verification protocol
- `.agents/templates/` — Project-type specific conventions
- `.agents/skills/` — Domain-specific skills for specialized tasks

## Files Included

### AGENTS.md
The main instruction file that coding agents (Claude, Cursor, etc.) read first when working on your project.

### .agents/engineering.md
Core engineering principles including:
- KISS, YAGNI, DRY principles
- Decision framework for code reviews
- Architecture guidelines
- Anti-patterns to avoid
- AI-assisted development ground rules

### .agents/stack.md
Technology stack knowledge covering:
- Languages (TypeScript, Python, Go, Rust, SQL)
- Frontend (React, Next.js, Tailwind, shadcn/ui)
- Backend (Hono, FastAPI, tRPC, etc.)
- Databases (PostgreSQL, Redis, Vector DBs)
- AI/ML stack (LLM APIs, orchestration, observability)
- Infrastructure & DevOps

### .agents/workflow.md
Workflow guidelines including:
- Verification protocol (read files before claiming, test before declaring done)
- Git discipline
- Communication style
- Code review stance
- Context management for agentic sessions

### .agents/templates/
Project-type specific convention files:
- `ai-engineering-python.md` — FastAPI + AI/ML stack patterns
- `fullstack-ai-nextjs.md` — Next.js + Vercel AI SDK patterns

### .agents/skills/
Domain-specific skills that can be loaded on-demand:
- `mcp-builder/` — MCP server development guide
- `n8n-patterns/` — n8n workflow automation patterns
- `ai-integration/` — LLM/AI integration patterns
- `deployment-patterns/` — Deployment and infrastructure guide

## Development

To test the CLI locally:

```bash
node bin/cli.js
```

## Publishing to npm

1. Login to npm:
   ```bash
   npm login
   ```

2. Publish the package:
   ```bash
   npm publish
   ```

## License

MIT