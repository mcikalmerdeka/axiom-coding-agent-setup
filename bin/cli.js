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
  '.agents/skills/implement',
  '.agents/skills/setup-matt-pocock-skills',
  '.agents/skills/tdd',
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
  // Core agent documents
  '.agents/ENGINEERING.md',
  '.agents/STACK.md',
  '.agents/WORKFLOW.md',
  '.agents/SECURITY.md',
  '.agents/DEBUGGING.md',
  '.agents/PERFORMANCE.md',
  '.agents/CONTEXT-MANAGEMENT.md',
  // Templates (project-type conventions)
  '.agents/templates/ai-engineering-python.md',
  '.agents/templates/fullstack-ai-nextjs.md',
  // Skills (domain-specific guides)
  '.agents/skills/agent-browser/SKILL.md',
  '.agents/skills/ai-integration/SKILL.md',
  '.agents/skills/deployment-patterns/SKILL.md',
  '.agents/skills/developing-with-streamlit/SKILL.md',
  '.agents/skills/domain-modeling/SKILL.md',
  '.agents/skills/domain-modeling/ADR-FORMAT.md',
  '.agents/skills/domain-modeling/CONTEXT-FORMAT.md',
  '.agents/skills/fastapi/SKILL.md',
  '.agents/skills/fastapi-templates/SKILL.md',
  '.agents/skills/frontend-design/SKILL.md',
  '.agents/skills/git-commit/SKILL.md',
  '.agents/skills/gradio/SKILL.md',
  '.agents/skills/grill-with-docs/SKILL.md',
  '.agents/skills/grilling/SKILL.md',
  '.agents/skills/huggingface-deployment/SKILL.md',
  '.agents/skills/implement/SKILL.md',
  '.agents/skills/mcp-builder/SKILL.md',
  '.agents/skills/project-design/SKILL.md',
  '.agents/skills/setup-matt-pocock-skills/SKILL.md',
  '.agents/skills/setup-matt-pocock-skills/domain.md',
  '.agents/skills/setup-matt-pocock-skills/issue-tracker-github.md',
  '.agents/skills/setup-matt-pocock-skills/issue-tracker-gitlab.md',
  '.agents/skills/setup-matt-pocock-skills/issue-tracker-local.md',
  '.agents/skills/setup-matt-pocock-skills/triage-labels.md',
  '.agents/skills/tdd/SKILL.md',
  '.agents/skills/tdd/mocking.md',
  '.agents/skills/tdd/tests.md',
  '.agents/skills/to-spec/SKILL.md',
  '.agents/skills/to-tickets/SKILL.md',
  '.agents/skills/triage/SKILL.md',
  '.agents/skills/triage/AGENT-BRIEF.md',
  '.agents/skills/triage/OUT-OF-SCOPE.md',
  '.agents/skills/wayfinder/SKILL.md',
  '.agents/skills/ui-ux-pro-max/SKILL.md'
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
    log('  - .agents/ENGINEERING.md             → Engineering principles', 'cyan');
    log('  - .agents/STACK.md                   → Tech stack knowledge', 'cyan');
    log('  - .agents/WORKFLOW.md                → Workflow guidelines', 'cyan');
    log('  - .agents/SECURITY.md                → Security principles & checklist', 'cyan');
    log('  - .agents/DEBUGGING.md               → Systematic debugging methodology', 'cyan');
    log('  - .agents/PERFORMANCE.md             → Performance awareness & optimization', 'cyan');
    log('  - .agents/CONTEXT-MANAGEMENT.md      → Context budget & session discipline', 'cyan');
    log('  - .agents/templates/                 → Project-type conventions', 'cyan');
    log('  - .agents/skills/                    → Domain-specific skills\n', 'cyan');
  }

  process.exit(failCount > 0 ? 1 : 0);
}

main().catch((error) => {
  log(`\nUnexpected error: ${error.message}`, 'red');
  process.exit(1);
});