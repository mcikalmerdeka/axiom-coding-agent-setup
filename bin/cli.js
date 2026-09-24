#!/usr/bin/env node

/**
 * AXIOM Coding Agent Setup CLI
 * 
 * Downloads AGENTS.md and .agents/ folder (core docs, templates, skills)
 * from the GitHub repository into the current project directory.
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const REPO_OWNER = 'mcikalmerdeka';
const REPO_NAME = 'axiom-coding-agent-setup';
const BRANCH = 'main';

// Skills from the mattpocock/skills collection.
// These are optionally excluded when the user declines the
// "Do you want to install Mattpocock skill collection?" prompt.
const MATTCOCK_SKILL_DIRS = [
  '.agents/skills/domain-modeling',
  '.agents/skills/grill-with-docs',
  '.agents/skills/grilling',
  '.agents/skills/to-spec',
  '.agents/skills/to-tickets',
  '.agents/skills/triage',
  '.agents/skills/wayfinder'
];

function isMattPocockSkillFile(filePath) {
  return MATTCOCK_SKILL_DIRS.some((dir) => filePath.startsWith(dir + '/'));
}

const FILES_TO_DOWNLOAD = [
  // Main instructions
  'AGENTS.md',
  // OpenCode configuration
  'opencode.json',
  // Environment variables template
  '.env.axiom',
  // Core agent documents (on-demand reference docs)
  '.agents/STACK.md',
  '.agents/SECURITY.md',
  '.agents/DEBUGGING.md',
  '.agents/PERFORMANCE.md',
  // Templates (project-type conventions)
  '.agents/templates/ai-engineering-python.md',
  '.agents/templates/fullstack-ai-nextjs.md',
  // Skills (generated recursively from .agents/skills)
  '.agents/skills/ai-integration/SKILL.md',
  '.agents/skills/deployment-patterns/SKILL.md',
  '.agents/skills/developing-with-streamlit/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/building-streamlit-chat-ui/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/building-streamlit-custom-components-v2/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/building-streamlit-custom-components-v2/references/packaged-components.md',
  '.agents/skills/developing-with-streamlit/skills/building-streamlit-custom-components-v2/references/state-sync.md',
  '.agents/skills/developing-with-streamlit/skills/building-streamlit-custom-components-v2/references/theme-css-variables.md',
  '.agents/skills/developing-with-streamlit/skills/building-streamlit-custom-components-v2/references/troubleshooting.md',
  '.agents/skills/developing-with-streamlit/skills/building-streamlit-dashboards/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/building-streamlit-multipage-apps/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/choosing-streamlit-selection-widgets/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/connecting-streamlit-to-snowflake/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/creating-streamlit-themes/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/displaying-streamlit-data/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/improving-streamlit-design/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/optimizing-streamlit-performance/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/organizing-streamlit-code/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/setting-up-streamlit-environment/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/using-streamlit-cli/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/using-streamlit-custom-components/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/using-streamlit-layouts/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/using-streamlit-markdown/SKILL.md',
  '.agents/skills/developing-with-streamlit/skills/using-streamlit-session-state/SKILL.md',
  '.agents/skills/developing-with-streamlit/templates/.gitattributes',
  '.agents/skills/developing-with-streamlit/templates/apps/.gitignore',
  '.agents/skills/developing-with-streamlit/templates/apps/README.md',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-companies/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-companies/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-compute-snowflake/.gitignore',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-compute-snowflake/.streamlit/secrets.toml.example',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-compute-snowflake/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-compute-snowflake/snowflake.yml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-compute-snowflake/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-compute/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-compute/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-feature-usage/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-feature-usage/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-metrics-snowflake/.gitignore',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-metrics-snowflake/.streamlit/secrets.toml.example',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-metrics-snowflake/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-metrics-snowflake/snowflake.yml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-metrics-snowflake/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-metrics/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-metrics/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-seattle-weather/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-seattle-weather/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-stock-peers-snowflake/.gitignore',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-stock-peers-snowflake/.streamlit/secrets.toml.example',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-stock-peers-snowflake/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-stock-peers-snowflake/snowflake.yml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-stock-peers-snowflake/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-stock-peers/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/apps/dashboard-stock-peers/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/themes/.gitignore',
  '.agents/skills/developing-with-streamlit/templates/themes/README.md',
  '.agents/skills/developing-with-streamlit/templates/themes/_configs/dracula.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/_configs/github.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/_configs/minimal.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/_configs/nord.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/_configs/snowflake.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/_configs/solarized-light.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/_configs/spotify.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/_configs/stripe.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/_shared/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/themes/_templates/pyproject.toml.tmpl',
  '.agents/skills/developing-with-streamlit/templates/themes/dracula/.streamlit/config.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/dracula/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/dracula/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/themes/github/.streamlit/config.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/github/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/github/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/themes/manage.py',
  '.agents/skills/developing-with-streamlit/templates/themes/minimal/.streamlit/config.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/minimal/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/minimal/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/themes/nord/.streamlit/config.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/nord/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/nord/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/themes/snowflake/.streamlit/config.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/snowflake/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/snowflake/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/themes/solarized-light/.streamlit/config.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/solarized-light/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/solarized-light/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/themes/spotify/.streamlit/config.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/spotify/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/spotify/streamlit_app.py',
  '.agents/skills/developing-with-streamlit/templates/themes/stripe/.streamlit/config.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/stripe/pyproject.toml',
  '.agents/skills/developing-with-streamlit/templates/themes/stripe/streamlit_app.py',
  '.agents/skills/domain-modeling/ADR-FORMAT.md',
  '.agents/skills/domain-modeling/CONTEXT-FORMAT.md',
  '.agents/skills/domain-modeling/SKILL.md',
  '.agents/skills/domain-modeling/agents/openai.yaml',
  '.agents/skills/fastapi-templates/SKILL.md',
  '.agents/skills/fastapi/SKILL.md',
  '.agents/skills/fastapi/references/dependencies.md',
  '.agents/skills/fastapi/references/other-tools.md',
  '.agents/skills/fastapi/references/streaming.md',
  '.agents/skills/frontend-design/LICENSE.txt',
  '.agents/skills/frontend-design/SKILL.md',
  '.agents/skills/gradio/SKILL.md',
  '.agents/skills/gradio/references/api-signatures.md',
  '.agents/skills/gradio/references/event-listeners.md',
  '.agents/skills/gradio/references/examples.md',
  '.agents/skills/grill-with-docs/SKILL.md',
  '.agents/skills/grill-with-docs/agents/openai.yaml',
  '.agents/skills/grilling/SKILL.md',
  '.agents/skills/grilling/agents/openai.yaml',
  '.agents/skills/huggingface-deployment/SKILL.md',
  '.agents/skills/mcp-builder/SKILL.md',
  '.agents/skills/project-design/SKILL.md',
  '.agents/skills/project-design/references/ARCHITECTURE.md',
  '.agents/skills/project-design/references/PROJECT_PLAN.md',
  '.agents/skills/prompt-creation/SKILL.md',
  '.agents/skills/to-spec/SKILL.md',
  '.agents/skills/to-spec/agents/openai.yaml',
  '.agents/skills/to-tickets/SKILL.md',
  '.agents/skills/to-tickets/agents/openai.yaml',
  '.agents/skills/triage/AGENT-BRIEF.md',
  '.agents/skills/triage/OUT-OF-SCOPE.md',
  '.agents/skills/triage/SKILL.md',
  '.agents/skills/triage/agents/openai.yaml',
  '.agents/skills/wayfinder/SKILL.md',
  '.agents/skills/wayfinder/agents/openai.yaml'
];

const GITHUB_RAW_URL = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${BRANCH}`;

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

/**
 * Interactive Yes/No prompt.
 *
 * On an interactive terminal the options are rendered as a selectable list
 * (up/down arrows to highlight, Enter to confirm). The Y/N keys also work
 * as shortcuts. When stdin is not a TTY (piped input, CI, etc.) it falls
 * back to a plain text prompt where typing "y"/"yes" means Yes and anything
 * else (including just pressing Enter) uses the default answer.
 *
 * @param {string} questionText - The question to display.
 * @param {boolean} defaultYes  - Preselected option (default: No).
 * @returns {Promise<boolean>} true when the user selected Yes.
 */
function promptYesNo(questionText, defaultYes = false) {
  return new Promise((resolve) => {
    const options = ['Yes', 'No'];
    let selected = defaultYes ? 0 : 1;

    const render = (final = false) => {
      const lines = [`\r\x1b[K${questionText}`];
      options.forEach((opt, i) => {
        lines.push(
          i === selected
            ? `\r\x1b[K  ${colors.cyan}${colors.bold}❯ ${opt}${colors.reset}`
            : `\r\x1b[K    ${opt}`
        );
      });
      if (final) {
        process.stdout.write(lines.join('\n') + '\n');
      } else {
        process.stdout.write('\x1b[?25l' + lines.join('\n') + `\x1b[${options.length}A`);
      }
    };

    // Fallback for non-interactive terminals (piped input, CI runners, etc.)
    if (!process.stdin.isTTY || typeof process.stdin.setRawMode !== 'function') {
      const defaultHint = defaultYes ? 'Y/n' : 'y/N';
      const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
      rl.question(`${questionText} (${defaultHint}): `, (answer) => {
        rl.close();
        const normalized = (answer || '').trim().toLowerCase();
        if (normalized === 'n' || normalized === 'no') resolve(false);
        else if (normalized === 'y' || normalized === 'yes') resolve(true);
        else resolve(defaultYes);
      });
      return;
    }

    const stdin = process.stdin;
    readline.emitKeypressEvents(stdin);

    const onKey = (str, key) => {
      if (key) {
        if (key.name === 'up' || (key.name === 'k' && !key.ctrl)) {
          selected = 0;
          render();
          return;
        }
        if (key.name === 'down' || (key.name === 'j' && !key.ctrl)) {
          selected = 1;
          render();
          return;
        }
        if (key.name === 'return' || key.name === 'enter') {
          stdin.setRawMode(false);
          stdin.removeListener('keypress', onKey);
          stdin.pause();
          process.stdout.write('\x1b[?25h'); // restore cursor
          render(true);
          resolve(selected === 0);
          return;
        }
        if (key.ctrl && key.name === 'c') {
          stdin.setRawMode(false);
          stdin.removeListener('keypress', onKey);
          stdin.pause();
          process.stdout.write('\x1b[?25h\n');
          process.exit(1);
        }
      }
      const letter = (str || '').toLowerCase();
      if (letter === 'y') {
        selected = 0;
        render();
      } else if (letter === 'n') {
        selected = 1;
        render();
      }
    };

    stdin.setRawMode(true);
    stdin.resume();
    stdin.on('keypress', onKey);
    render();
  });
}

function downloadFile(filePath) {
  return new Promise((resolve, reject) => {
    const url = `${GITHUB_RAW_URL}/${filePath}`;
    const localPath = path.join(process.cwd(), filePath);
    const dir = path.dirname(localPath);

    // Create directory if it doesn't exist
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const file = fs.createWriteStream(localPath);
    
    https.get(url, (response) => {
      if (response.statusCode === 200) {
        response.pipe(file);
        file.on('finish', () => {
          file.close();
          resolve(filePath);
        });
      } else if (response.statusCode === 301 || response.statusCode === 302) {
        // Handle redirects
        https.get(response.headers.location, (redirectResponse) => {
          if (redirectResponse.statusCode === 200) {
            redirectResponse.pipe(file);
            file.on('finish', () => {
              file.close();
              resolve(filePath);
            });
          } else {
            fs.unlinkSync(localPath);
            reject(new Error(`Failed to download ${filePath}: ${redirectResponse.statusCode}`));
          }
        }).on('error', reject);
      } else {
        file.close();
        fs.unlinkSync(localPath);
        reject(new Error(`Failed to download ${filePath}: ${response.statusCode}`));
      }
    }).on('error', (err) => {
      fs.unlinkSync(localPath);
      reject(err);
    });
  });
}

async function main() {
  log('\n' + '='.repeat(60), 'cyan');
  log('AXIOM Coding Agent Setup', 'bold');
  log('='.repeat(60) + '\n', 'cyan');

  log(`Target directory: ${process.cwd()}\n`, 'yellow');

  const includeMattPocockSkills = await promptYesNo(
    'Do you want to install Mattpocock skill collection?'
  );
  log('');

  const filesToDownload = includeMattPocockSkills
    ? FILES_TO_DOWNLOAD
    : FILES_TO_DOWNLOAD.filter((file) => !isMattPocockSkillFile(file));

  if (!includeMattPocockSkills) {
    log('Skipping Mattpocock skill collection skills.\n', 'yellow');
  }

  let successCount = 0;
  let failCount = 0;

  for (const file of filesToDownload) {
    try {
      process.stdout.write(`Downloading ${file}... `);
      await downloadFile(file);
      log('✓', 'green');
      successCount++;
    } catch (error) {
      log(`✗ (${error.message})`, 'red');
      failCount++;
    }
  }

  log('\n' + '='.repeat(60), 'cyan');
  log(`Setup complete! ${successCount} files downloaded, ${failCount} failed.`, successCount > 0 ? 'green' : 'red');
  log('='.repeat(60) + '\n', 'cyan');

  if (successCount > 0) {
    log('Your project now has AXIOM coding agent instructions:', 'bold');
    log('  - AGENTS.md                          → Main agent instructions', 'cyan');
    log('  - opencode.json                      → OpenCode IDE configuration', 'cyan');
    log('  - .env.axiom                         → Environment variables template', 'cyan');
    log('  - .agents/STACK.md                   → Tech stack reference (on demand)', 'cyan');
    log('  - .agents/SECURITY.md                → Security principles & checklist (on demand)', 'cyan');
    log('  - .agents/DEBUGGING.md               → Systematic debugging methodology (on demand)', 'cyan');
    log('  - .agents/PERFORMANCE.md             → Performance awareness & optimization (on demand)', 'cyan');
    log('  - .agents/templates/                 → Project-type conventions', 'cyan');
    log('  - .agents/skills/                    → Domain-specific skills\n', 'cyan');
  }

  process.exit(failCount > 0 ? 1 : 0);
}

main().catch((error) => {
  log(`\nUnexpected error: ${error.message}`, 'red');
  process.exit(1);
});