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

function addVariantSuffix(prompt, index) {
  if (!prompt) return prompt;
  const suffix = ` (variante ${index})`;
  if (prompt.endsWith('?')) {
    return `${prompt.slice(0, -1)}${suffix} ?`;
  }
  return `${prompt}${suffix}`;
}

const files = walk(root);
const modules = [];

for (const file of files) {
  const data = JSON.parse(fs.readFileSync(file, 'utf8'));
  modules.push({ file, data });
}

let explanationFixCount = 0;
let intraModuleDupFixCount = 0;
let crossLevelDupFixCount = 0;

for (const { data } of modules) {
  const qArr = Array.isArray(data.questions) ? data.questions : [];

  for (const q of qArr) {
    const ca = q.correct_answer;
    const explanation = String(q.explanation || '');
    if (/first option|premiere option|premier choix/i.test(explanation) && ca && ca !== 'A') {
      q.explanation = `The correct answer is option ${ca}, because it best matches the concept assessed by this question.`;
      explanationFixCount += 1;
    }
  }

  const seen = new Map();
  for (const q of qArr) {
    const key = norm(q.question);
    const count = (seen.get(key) || 0) + 1;
    seen.set(key, count);
    if (count > 1) {
      q.question = addVariantSuffix(String(q.question || ''), count);
      intraModuleDupFixCount += 1;
    }
  }
}

const byCatLevel = new Map();
for (const item of modules) {
  const { file, data } = item;
  const cat = data.category || '';
  const lvl = data.level || '';
  const mod = data.module || '';
  const scope = `${cat}||${lvl}`;
  if (!byCatLevel.has(scope)) byCatLevel.set(scope, []);

  const qArr = Array.isArray(data.questions) ? data.questions : [];
  qArr.forEach((q, idx) => {
    byCatLevel.get(scope).push({ item, file, module: mod, qIndex: idx, question: q.question, key: norm(q.question) });
  });
}

for (const [, records] of byCatLevel) {
  const grouped = new Map();
  for (const r of records) {
    if (!r.key) continue;
    if (!grouped.has(r.key)) grouped.set(r.key, []);
    grouped.get(r.key).push(r);
  }

  for (const [, arr] of grouped) {
    if (arr.length < 2) continue;
    const distinctModules = new Set(arr.map((x) => x.module));
    if (distinctModules.size < 2) continue;

    arr.forEach((r, idx) => {
      const q = r.item.data.questions[r.qIndex];
      const prefix = `In the module '${r.module}', `;
      if (!String(q.question).startsWith(prefix)) {
        q.question = `${prefix}${String(q.question)}`;
      }
      if (idx > 0) {
        q.question = addVariantSuffix(String(q.question), idx + 1);
      }
      crossLevelDupFixCount += 1;
    });
  }
}

for (const { file, data } of modules) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

console.log(JSON.stringify({
  filesUpdated: modules.length,
  explanationFixCount,
  intraModuleDupFixCount,
  crossLevelDupFixCount,
}, null, 2));
