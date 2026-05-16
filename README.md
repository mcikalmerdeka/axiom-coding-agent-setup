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
- `opencode.json` — OpenCode IDE configuration (MCP servers, plugins)
- `.env.axiom` — Environment variables template for AXIOM credentials
- `.agents/ENGINEERING.md` — Engineering principles & code standards
- `.agents/STACK.md` — Technology stack knowledge
- `.agents/WORKFLOW.md` — Workflow guidelines & verification protocol
- `.agents/SECURITY.md` — Security-first principles & attack vector checklist
- `.agents/DEBUGGING.md` — Systematic debugging methodology & anti-patterns
- `.agents/PERFORMANCE.md` — Performance awareness & optimization hierarchy
- `.agents/CONTEXT-MANAGEMENT.md` — Context budget & session discipline
- `.agents/templates/` — Project-type specific conventions
- `.agents/skills/` — Domain-specific skills for specialized tasks

## Files Included

### AGENTS.md
The main instruction file that coding agents (Claude, Cursor, OpenCode, etc.) read first when working on your project.

### opencode.json
OpenCode IDE configuration including:
- MCP server definitions (remote tools like n8n, Neon, Gradio, etc.)
- Plugin configuration
- Environment variable references for secure credential management

### .agents/ENGINEERING.md
Core engineering principles including:
- KISS, YAGNI, DRY principles
- Decision framework for code reviews
- Architecture guidelines
- Anti-patterns to avoid
- AI-assisted development ground rules

### .agents/STACK.md
Technology stack knowledge covering:
- Languages (TypeScript, Python, Go, Rust, SQL)
- Frontend (React, Next.js, Tailwind, shadcn/ui)
- Backend (Hono, FastAPI, tRPC, etc.)
- Databases (PostgreSQL, Redis, Vector DBs)
- AI/ML stack (LLM APIs, orchestration, observability)
- Infrastructure & DevOps

### .agents/WORKFLOW.md
Workflow guidelines including:
- Verification protocol (read files before claiming, test before declaring done)
- Git discipline
- Communication style
- Code review stance
- Context management for agentic sessions
- Error recovery & anti-loop patterns

### .agents/SECURITY.md
Security-first principles including:
- Input validation & secrets management checklist
- Authentication & authorization patterns
- Common attack vectors & prevention
- When to escalate security decisions to humans

### .agents/DEBUGGING.md
Systematic debugging methodology including:
- The 4-phase debugging protocol (Reproduction → Observation → Hypothesis → Fix)
- Debugging techniques (binary search, git bisect, rubber duck)
- Common bug categories & symptoms
- Anti-patterns to avoid (shotgun debugging, print-driven development)

### .agents/PERFORMANCE.md
Performance awareness including:
- The performance hierarchy (algorithm → database → I/O → memory → micro)
- Caching strategies & when (not) to cache
- Database query optimization
- Frontend Core Web Vitals
- Profiling & measurement tools

### .agents/CONTEXT-MANAGEMENT.md
Context management discipline including:
- The 50% rule for context compaction
- Session lifecycle & handoff documentation
- Parallel execution & context isolation
- Codebase navigation without context bloat
- Context anti-patterns

### .agents/templates/
Project-type specific convention files:
- `ai-engineering-python.md` — FastAPI + AI/ML stack patterns
- `fullstack-ai-nextjs.md` — Next.js + Vercel AI SDK patterns

### .agents/skills/
Domain-specific skills that can be loaded on-demand:
- `agent-browser/` — Web browser automation skill
- `ai-integration/` — LLM/AI integration patterns
- `deployment-patterns/` — Deployment and infrastructure guide
- `developing-with-streamlit/` — Streamlit app development guides
- `fastapi/` — FastAPI best practices and patterns
- `fastapi-templates/` — FastAPI project templates
- `frontend-design/` — Frontend UI/UX design patterns
- `git-commit/` — Conventional commit message generation
- `gradio/` — Gradio UI framework guides
- `mcp-builder/` — MCP server development guide
- `n8n-patterns/` — n8n workflow automation patterns
- `project-design/` — Project planning & architecture documentation
- `ui-ux-pro-max/` — Advanced UI/UX design skill

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