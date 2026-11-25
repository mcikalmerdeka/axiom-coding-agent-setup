---
name: installing-powerbi-skills
description: Use when a project needs Power BI semantic-model or report-authoring skills, when the user asks to install powerbi-modeling or powerbi-report-cli, or when working with PBIP/TMDL files, Fabric semantic models, or local Power BI reports.
---

# Installing Power BI Skills

## Overview

The full Power BI skills are large external packages. Do not vendor them into
AXIOM. Install them into the target project on demand, then let the agent load
them from the project's skills directory.

## When to Use

- The user asks to install `powerbi-modeling` or `powerbi-report-cli`.
- The task needs Power BI semantic modeling: DAX, star schemas, relationships,
  RLS, calculation groups, or model performance.
- The task needs Power BI report lifecycle work: PBIR/PBIP editing, preview,
  publish, rebind, or Fabric upload/download.
- The project contains PBIP/TMDL files or a local Power BI Desktop model.

Do not use this skill for generic Fabric data engineering, pipelines, or
warehouse work.

## Install Into the Target Project

Run these from the target project root. Project scope is the default; do not
pass `-g`.

```bash
npx -y skills add https://github.com/github/awesome-copilot --skill powerbi-modeling -y
npx -y skills add https://github.com/microsoft/skills-for-fabric --skill powerbi-report-cli -y
```

- The first `-y` skips the npx install prompt; the trailing `-y` skips the
  skills CLI confirmation.
- The CLI detects the project's agent and installs into its project-level skills
  directory. For OpenCode that is `.agents/skills/`.
- Add `--agent opencode` if detection picks the wrong agent.
- GitHub access and Node/npx are required.

## Verify

```bash
npx -y skills list
```

Expect both skills in the project list. For OpenCode, also check:

```powershell
Test-Path .agents/skills/powerbi-modeling/SKILL.md
Test-Path .agents/skills/powerbi-report-cli/SKILL.md
```

If the project uses another agent directory, trust `npx skills list` and the CLI
output instead of assuming `.agents/`.

## Use the Installed Skills

### powerbi-modeling

Semantic models in Fabric workspaces, Power BI Desktop, or PBIP/TMDL files:
DAX, star schemas, relationships, RLS, naming, documentation, and performance.

Use the local `powerbi-modeling` MCP server configured in `opencode.json`:

```text
npx -y @microsoft/powerbi-modeling-mcp@latest --start
```

Connect to the target model first. Use only this server for a given authoring
task; do not combine it with the hosted Power BI Authoring server.

If the target project's `opencode.json` does not contain the server yet, copy
the `powerbi-modeling` block from AXIOM's `opencode.json`.

### powerbi-report-cli

Report lifecycle: requirements, page design, PBIR/PBIP edits, validation,
screenshots, Fabric upload/download, and rebinding. For model or DAX changes,
use `powerbi-modeling`; for natural-language questions over an existing model,
use `fabriciq`.

## Update or Remove

```bash
npx -y skills update -p
npx -y skills remove powerbi-modeling powerbi-report-cli -y
```

If they were installed globally by mistake:

```bash
npx -y skills remove -g powerbi-modeling powerbi-report-cli -y
```

Then reinstall without `-g`.

## Common Mistakes

- Passing `-g`: installs user-level instead of project-level.
- Omitting the trailing `-y`: the command blocks in non-interactive runs.
- Assuming every agent uses `.agents/skills/`; verify with `npx skills list`.
- Vendoring the full external skills into AXIOM; install them per project.
- Combining the local `powerbi-modeling` MCP server with the hosted Power BI
  Authoring server for the same task.
- Using the modeling skill for PBIR/PBIP report lifecycle work; use
  `powerbi-report-cli`.
