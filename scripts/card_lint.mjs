#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const ROOT_DIRS = [
  path.join(process.cwd(), 'data', 'cards'),
];
const INCLUDE_DOTDATA = process.argv.includes('--include-dotdata');
if (INCLUDE_DOTDATA) {
  ROOT_DIRS.push(path.join(process.cwd(), '.data', 'cards'));
}

const HTTPS_SCHEMA = 'https://adaptivecards.io/schemas/adaptive-card.json';
const args = process.argv.slice(2);
const DO_FIX = args.includes('--fix');
const INCLUDE_SAMPLES = args.includes('--include-samples');

function isJsonFile(file) {
  return file.toLowerCase().endsWith('.json');
}

function* walk(dir) {
  if (!fs.existsSync(dir)) return;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (!INCLUDE_SAMPLES && e.name.toLowerCase() === 'samples') continue;
      yield* walk(full);
    } else if (isJsonFile(e.name)) {
      yield full;
    }
  }
}

function readJson(file) {
  try {
    const raw = fs.readFileSync(file, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    return { __parseError: String(err) };
  }
}

function writeJson(file, obj) {
  const content = JSON.stringify(obj, null, 2) + '\n';
  fs.writeFileSync(file, content, 'utf8');
}

function altFromImage(el) {
  if (typeof el.altText === 'string' && el.altText.trim()) return el.altText;
  if (typeof el.id === 'string' && el.id.trim()) return `${el.id} image`;
  if (typeof el.url === 'string') {
    try {
      const u = new URL(el.url);
      const last = path.basename(u.pathname);
      if (last) return last;
    } catch {}
    const segs = el.url.split('/');
    const last = segs[segs.length - 1] || 'Image';
    return last;
  }
  return 'Image';
}

function lintElement(el, issues, fixApplied) {
  if (!el || typeof el !== 'object') return fixApplied;

  // Rule: Image elements should have altText
  if (el.type === 'Image') {
    if (!('altText' in el) || !String(el.altText || '').trim()) {
      issues.push({ level: 'warn', msg: 'Image missing altText' });
      if (DO_FIX) {
        el.altText = altFromImage(el);
        fixApplied = true;
      }
    }
  }

  // Recurse known collections
  const arrays = ['items', 'columns', 'actions', 'targetElements'];
  for (const key of arrays) {
    if (Array.isArray(el[key])) {
      for (const child of el[key]) {
        fixApplied = lintElement(child, issues, fixApplied) || fixApplied;
      }
    }
  }

  // Recurse selectAction if present
  if (el.selectAction && typeof el.selectAction === 'object') {
    fixApplied = lintElement(el.selectAction, issues, fixApplied) || fixApplied;
  }

  // Check minHeight formatting if present
  if ('minHeight' in el) {
    const v = el.minHeight;
    if (typeof v === 'number') {
      issues.push({ level: 'warn', msg: 'minHeight should be a string with px units' });
      if (DO_FIX) {
        el.minHeight = `${v}px`;
        fixApplied = true;
      }
    } else if (typeof v === 'string') {
      const s = v.trim();
      if (!s.endsWith('px')) {
        issues.push({ level: 'info', msg: 'minHeight without px units' });
      }
    }
  }

  return fixApplied;
}

function lintCard(file, card) {
  const issues = [];
  let fixed = false;

  if (card.__parseError) {
    issues.push({ level: 'error', msg: `JSON parse error: ${card.__parseError}` });
    return { issues, fixed };
  }

  if (card.type !== 'AdaptiveCard') {
    issues.push({ level: 'error', msg: 'Root.type must be AdaptiveCard' });
  }
  if (!card.version || typeof card.version !== 'string') {
    issues.push({ level: 'error', msg: 'Root.version must be a string (e.g., 1.3 or 1.5)' });
  }

  if (!card['$schema'] || typeof card['$schema'] !== 'string') {
    issues.push({ level: 'warn', msg: 'Missing $schema; adding https adaptivecards schema' });
    if (DO_FIX) {
      card['$schema'] = HTTPS_SCHEMA;
      fixed = true;
    }
  } else if (String(card['$schema']).startsWith('http://')) {
    issues.push({ level: 'warn', msg: 'Using http schema; switching to https' });
    if (DO_FIX) {
      card['$schema'] = HTTPS_SCHEMA;
      fixed = true;
    }
  }

  if (!card.fallbackText) {
    issues.push({ level: 'info', msg: 'Missing fallbackText on root' });
    if (DO_FIX) {
      card.fallbackText = 'Content unavailable. Try chat commands or refresh.';
      fixed = true;
    }
  }

  if (Array.isArray(card.body)) {
    for (const el of card.body) {
      const f = lintElement(el, issues, false);
      fixed = fixed || f;
    }
  } else {
    issues.push({ level: 'error', msg: 'Root.body must be an array' });
  }

  return { issues, fixed };
}

function main() {
  const files = [];
  for (const dir of ROOT_DIRS) {
    for (const f of walk(dir)) files.push(f);
  }
  if (files.length === 0) {
    console.log('No card JSON files found in data/cards (or .data/cards when opting in).');
    process.exit(0);
  }

  let errorCount = 0;
  let warnCount = 0;
  let infoCount = 0;
  const fixedFiles = [];

  for (const file of files) {
    const card = readJson(file);
    const { issues, fixed } = lintCard(file, card);
    if (issues.length === 0) continue;

    console.log(`\n${file}`);
    for (const i of issues) {
      if (i.level === 'error') errorCount++;
      else if (i.level === 'warn') warnCount++;
      else infoCount++;
      console.log(` - [${i.level}] ${i.msg}`);
    }

    if (DO_FIX && fixed && !card.__parseError) {
      writeJson(file, card);
      fixedFiles.push(file);
    }
  }

  console.log('\nSummary:');
  console.log(` Errors: ${errorCount}`);
  console.log(` Warnings: ${warnCount}`);
  console.log(` Info: ${infoCount}`);
  if (DO_FIX) {
    if (fixedFiles.length) {
      console.log(' Fixed files:');
      for (const f of fixedFiles) console.log(`  - ${f}`);
    } else {
      console.log(' No auto-fixes applied.');
    }
  } else {
    console.log(' Run with --fix to auto-apply safe fixes.');
  }
}

main();
