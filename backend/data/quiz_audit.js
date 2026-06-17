const fs = require('fs');
const path = require('path');

const root = path.join(process.cwd(), 'backend', 'data', 'modules');

function walk(dir) {
  let out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out = out.concat(walk(p));
    else if (e.isFile() && p.endsWith('.json')) out.push(p);
  }
  return out;
}

function norm(s) {
  return String(s || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

const files = walk(root);
const issues = [];
const byCatLevel = new Map();
const byCategory = new Map();

for (const file of files) {
  let data;
  try {
    data = JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (e) {
    issues.push({ type: 'json_parse', file, msg: e.message });
    continue;
  }

  const cat = data.category || '';
  const lvl = data.level || '';
  const mod = data.module || '';
  const qArr = Array.isArray(data.questions) ? data.questions : [];
  const clKey = `${cat}||${lvl}`;
  const cKey = cat;

  const seenInModule = new Map();

  qArr.forEach((q, idx) => {
    const qn = idx + 1;
    const prompt = String(q.question || '');
    const key = norm(prompt);

    if (!prompt) issues.push({ type: 'missing_prompt', file, q: qn });

    if (seenInModule.has(key)) {
      issues.push({ type: 'dup_in_module', file, q: qn, other: seenInModule.get(key) });
    } else {
      seenInModule.set(key, qn);
    }

    if (!byCatLevel.has(clKey)) byCatLevel.set(clKey, []);
    byCatLevel.get(clKey).push({ file, module: mod, q: qn, key, prompt });

    if (!byCategory.has(cKey)) byCategory.set(cKey, []);
    byCategory.get(cKey).push({ file, module: mod, level: lvl, q: qn, key, prompt });

    const choices = q.choices || {};
    const letters = ['A', 'B', 'C', 'D'];
    const missing = letters.filter((l) => !(l in choices));
    if (missing.length) issues.push({ type: 'missing_choices', file, q: qn, missing });

    const ca = q.correct_answer;
    if (!letters.includes(ca)) issues.push({ type: 'invalid_correct_answer', file, q: qn, correct: ca });

    const explanation = String(q.explanation || '').toLowerCase();
    if (/first option|premiere option|premier choix/.test(explanation) && ca !== 'A') {
      issues.push({
        type: 'explanation_conflict_first_option',
        file,
        q: qn,
        correct: ca,
        explanation: q.explanation,
      });
    }
  });
}

function findDuplicates(records, includeCrossCheck) {
  const grouped = new Map();
  for (const r of records) {
    if (!r.key) continue;
    if (!grouped.has(r.key)) grouped.set(r.key, []);
    grouped.get(r.key).push(r);
  }

  const dups = [];
  for (const [k, arr] of grouped) {
    if (arr.length < 2) continue;
    if (!includeCrossCheck(arr)) continue;
    dups.push({ key: k, count: arr.length, examples: arr.slice(0, 3) });
  }
  return dups;
}

function formatIssuesByType(issuesByType) {
  const entries = Object.entries(issuesByType || {}).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return '- None';
  return entries.map(([k, v]) => `- ${k}: ${v}`).join('\n');
}

function formatIssueTable(issuesSample) {
  if (!issuesSample || !issuesSample.length) {
    return 'No issues in sample.';
  }

  const rows = issuesSample.slice(0, 20).map((it) => {
    const where = `${it.file || ''}${it.q ? `#Q${it.q}` : ''}`;
    const detail = it.msg || it.explanation || JSON.stringify(it);
    return `| ${it.type || ''} | ${where.replace(/\|/g, '\\|')} | ${String(detail).replace(/\|/g, '\\|')} |`;
  });

  return [
    '| Type | Location | Detail |',
    '|---|---|---|',
    ...rows,
  ].join('\n');
}

function formatDuplicateScopes(items, scopeName) {
  if (!items || !items.length) return `- No duplicate sets for ${scopeName}.`;

  const lines = [];
  for (const scopeItem of items.slice(0, 8)) {
    lines.push(`- Scope: ${scopeItem.scope}`);
    for (const dup of (scopeItem.duplicates || []).slice(0, 3)) {
      lines.push(`  - key: ${dup.key} (count: ${dup.count})`);
    }
  }
  return lines.join('\n');
}

function buildMarkdownReport(report) {
  return [
    '# Quiz QA Audit Report',
    '',
    `Generated: ${new Date().toISOString()}`,
    '',
    '## Summary',
    '',
    `- Files scanned: ${report.fileCount}`,
    `- Total issues: ${report.issueCount}`,
    `- Duplicate sets by category+level: ${report.duplicateQuestionSetsByCategoryLevel}`,
    `- Duplicate sets by category: ${report.duplicateQuestionSetsByCategory}`,
    '',
    '## Issues By Type',
    '',
    formatIssuesByType(report.issuesByType),
    '',
    '## Issues Sample',
    '',
    formatIssueTable(report.issuesSample),
    '',
    '## Duplicate Sample By Category+Level',
    '',
    formatDuplicateScopes(report.duplicateSampleByCategoryLevel, 'category+level'),
    '',
    '## Duplicate Sample By Category',
    '',
    formatDuplicateScopes(report.duplicateSampleByCategory, 'category'),
    '',
  ].join('\n');
}

const dupCatLevel = [];
for (const [scope, records] of byCatLevel) {
  const d = findDuplicates(records, (arr) => new Set(arr.map((x) => x.module)).size > 1);
  if (d.length) dupCatLevel.push({ scope, duplicates: d.slice(0, 20) });
}

const dupCategory = [];
for (const [scope, records] of byCategory) {
  const d = findDuplicates(records, (arr) => new Set(arr.map((x) => `${x.level}::${x.module}`)).size > 1);
  if (d.length) dupCategory.push({ scope, duplicates: d.slice(0, 20) });
}

const report = {
  fileCount: files.length,
  issueCount: issues.length,
  issuesByType: issues.reduce((acc, it) => {
    acc[it.type] = (acc[it.type] || 0) + 1;
    return acc;
  }, {}),
  issuesSample: issues.slice(0, 50),
  duplicateQuestionSetsByCategoryLevel: dupCatLevel.length,
  duplicateQuestionSetsByCategory: dupCategory.length,
  duplicateSampleByCategoryLevel: dupCatLevel.slice(0, 8),
  duplicateSampleByCategory: dupCategory.slice(0, 8),
};

const outFile = path.join(process.cwd(), 'backend', 'data', 'quiz_audit_report.json');
fs.writeFileSync(outFile, JSON.stringify(report, null, 2), 'utf8');
const outMarkdown = path.join(process.cwd(), 'backend', 'data', 'quiz_audit_report.md');
fs.writeFileSync(outMarkdown, buildMarkdownReport(report), 'utf8');
console.log(`Report written: ${outFile}`);
console.log(`Report written: ${outMarkdown}`);
console.log(JSON.stringify({
  fileCount: report.fileCount,
  issueCount: report.issueCount,
  issuesByType: report.issuesByType,
  duplicateQuestionSetsByCategoryLevel: report.duplicateQuestionSetsByCategoryLevel,
  duplicateQuestionSetsByCategory: report.duplicateQuestionSetsByCategory,
}, null, 2));
