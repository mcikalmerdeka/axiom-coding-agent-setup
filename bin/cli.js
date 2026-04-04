#!/usr/bin/env node

/**
 * AXIOM Coding Agent Setup CLI
 * 
 * Downloads AGENTS.md and .axiom/ folder files from the GitHub repository
 * into the current project directory.
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const REPO_OWNER = 'mcikalmerdeka';
const REPO_NAME = 'axiom-coding-agent-setup';
const BRANCH = 'main';

const FILES_TO_DOWNLOAD = [
  'AGENTS.md',
  '.axiom/engineering.md',
  '.axiom/stack.md',
  '.axiom/workflow.md'
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

  let successCount = 0;
  let failCount = 0;

  for (const file of FILES_TO_DOWNLOAD) {
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
    log('  - AGENTS.md         → Main agent instructions', 'cyan');
    log('  - .axiom/engineering.md → Engineering principles', 'cyan');
    log('  - .axiom/stack.md       → Tech stack knowledge', 'cyan');
    log('  - .axiom/workflow.md    → Workflow guidelines\n', 'cyan');
  }

  process.exit(failCount > 0 ? 1 : 0);
}

main().catch((error) => {
  log(`\nUnexpected error: ${error.message}`, 'red');
  process.exit(1);
});