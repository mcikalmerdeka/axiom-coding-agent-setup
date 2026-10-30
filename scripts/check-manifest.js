#!/usr/bin/env node

/**
 * Pre-publish guard for the vendored file manifest.
 *
 * The CLI downloads a hard-coded list of files from GitHub (FILES_TO_DOWNLOAD
 * in bin/cli.js). That list is maintained by hand, so it silently drifts when
 * skills are added or removed — which is how data-science-utils shipped in the
 * npm tarball but could never be installed. This script fails the publish if
 * the manifest, the files on disk, and the README disagree.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const CLI_PATH = path.join(ROOT, 'bin', 'cli.js');
const README_PATH = path.join(ROOT, 'README.md');
const LOCK_PATH = path.join(ROOT, 'skills-lock.json');
const VENDORED_DIRS = ['.agents/skills', '.agents/templates'];

const errors = [];
const warnings = [];

function toPosix(filePath) {
  return filePath.split(path.sep).join('/');
}

function walk(dir, base = dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(full, base) : [toPosix(path.relative(base, full))];
  });
}

function readManifest() {
  const source = fs.readFileSync(CLI_PATH, 'utf8');
  const match = source.match(/const FILES_TO_DOWNLOAD = \[([\s\S]*?)\n\];/);
  if (!match) {
    throw new Error('Could not locate FILES_TO_DOWNLOAD in bin/cli.js');
  }
  return [...match[1].matchAll(/'([^']+)'/g)].map((m) => m[1]);
}

function checkManifest(manifest) {
  const listed = new Set(manifest);

  for (const file of listed) {
    if (!fs.existsSync(path.join(ROOT, file))) {
      errors.push(`manifest lists a file that does not exist: ${file}`);
    }
  }

  for (const dir of VENDORED_DIRS) {
    for (const rel of walk(path.join(ROOT, dir))) {
      const repoPath = toPosix(path.join(dir, rel));
      if (!listed.has(repoPath)) {
        errors.push(`file on disk is missing from the manifest: ${repoPath}`);
      }
    }
  }

  const duplicates = manifest.filter((file, i) => manifest.indexOf(file) !== i);
  for (const dup of new Set(duplicates)) {
    errors.push(`manifest lists a file twice: ${dup}`);
  }
}

function checkReadme() {
  const readme = fs.readFileSync(README_PATH, 'utf8');
  const skillsDir = path.join(ROOT, '.agents', 'skills');
  const skillNames = fs
    .readdirSync(skillsDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);

  for (const name of skillNames) {
    if (!readme.includes(`\`${name}/\``)) {
      errors.push(`skill is not listed in README.md: ${name}`);
    }
  }

  for (const match of readme.matchAll(/^- `([a-z0-9-]+)\/`/gm)) {
    if (!skillNames.includes(match[1])) {
      errors.push(`README.md lists a skill that does not exist: ${match[1]}`);
    }
  }
}

function checkLockfile() {
  if (!fs.existsSync(LOCK_PATH)) return;

  const tracked = Object.keys(JSON.parse(fs.readFileSync(LOCK_PATH, 'utf8')).skills || {});
  const skillsDir = path.join(ROOT, '.agents', 'skills');
  const untracked = fs
    .readdirSync(skillsDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .filter((name) => !tracked.includes(name));

  if (untracked.length > 0) {
    warnings.push(
      `not in skills-lock.json (locally authored, no upstream source): ${untracked.join(', ')}`
    );
  }
}

function main() {
  const manifest = readManifest();
  checkManifest(manifest);
  checkReadme();
  checkLockfile();

  for (const warning of warnings) {
    console.warn(`warning: ${warning}`);
  }

  if (errors.length > 0) {
    for (const error of errors) {
      console.error(`error: ${error}`);
    }
    console.error(`\n${errors.length} manifest problem(s). Publish aborted.`);
    process.exit(1);
  }

  console.log(`Manifest OK: ${manifest.length} files, all present and documented.`);
}

main();
