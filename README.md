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

## Interactive Setup

During installation you will be asked:

> **Do you want to install Mattpocock skill collection?**

- **Yes** — installs all skills, including the Mattpocock skill collection
  (`domain-modeling`, `grill-with-docs`, `grilling`,
  `to-spec`, `to-tickets`, `triage`, `wayfinder`).
- **No** — installs everything except the Mattpocock skill collection skills.

Use the arrow keys (or `Y`/`N`) to select and press Enter to confirm.

## What It Does

This command downloads the following files from the [axiom-coding-agent-setup](https://github.com/mcikalmerdeka/axiom-coding-agent-setup) repository into your current project directory:

- `AGENTS.md` — Main agent instructions
- `opencode.json` — OpenCode IDE configuration (MCP servers, plugins)
- `.env.axiom` — Environment variables template for AXIOM credentials
- `.agents/STACK.md` — Technology stack knowledge (loaded on demand)
- `.agents/SECURITY.md` — Security-first principles & attack vector checklist (loaded on demand)
- `.agents/DEBUGGING.md` — Systematic debugging methodology & anti-patterns (loaded on demand)
- `.agents/PERFORMANCE.md` — Performance awareness & optimization hierarchy (loaded on demand)
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

### .agents/STACK.md
Reference catalog loaded on demand: languages, frameworks, databases, AI/ML stack, infra & DevOps recommendations.

### .agents/SECURITY.md
Loaded on demand: checklist, common attack vectors, defensive patterns, escalation rules.

### .agents/DEBUGGING.md
Loaded on demand: the 4-phase debugging protocol, techniques (git bisect, binary search), anti-patterns.

### .agents/PERFORMANCE.md
Loaded on demand: performance hierarchy, caching strategy, database & frontend tuning, profiling tools.

*(Engineering principles, workflow, git discipline, and communication guidelines are merged directly into AGENTS.md.)*

### .agents/templates/
Project-type specific convention files:
- `ai-engineering-python.md` — FastAPI + AI/ML stack patterns
- `fullstack-ai-nextjs.md` — Next.js + Vercel AI SDK patterns

### .agents/skills/
Domain-specific skills that can be loaded on-demand:
- `ai-integration/` — LLM/AI integration patterns
- `deployment-patterns/` — Deployment and infrastructure guide
- `developing-with-streamlit/` — Streamlit app development guides
- `domain-modeling/` — Domain model, glossary & ADR documentation
- `fastapi/` — FastAPI best practices and patterns
- `fastapi-templates/` — FastAPI project templates
- `frontend-design/` — Frontend UI/UX design patterns
- `gradio/` — Gradio UI framework guides
- `grill-with-docs/` — Design interview that sharpens plans into ADRs & glossary
- `grilling/` — Stress-test plans with relentless questioning
- `huggingface-deployment/` — Deploy apps to Hugging Face Spaces
- `mcp-builder/` — MCP server development guide
- `project-design/` — Project planning & architecture documentation
- `prompt-creation/` — Generate implementation prompts for AI handoff
- `to-spec/` — Turn a conversation into a published spec
- `to-tickets/` — Break plans/specs into tracer-bullet tickets
- `triage/` — Issue & PR triage workflow
- `wayfinder/` — Plan large work as a map of decision tickets

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
