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
const modules = files.map((file) => ({ file, data: JSON.parse(fs.readFileSync(file, 'utf8')) }));

const byCategory = new Map();
for (const item of modules) {
  const cat = item.data.category || '';
  const lvl = item.data.level || '';
  const mod = item.data.module || '';
  if (!byCategory.has(cat)) byCategory.set(cat, []);
  (item.data.questions || []).forEach((q, idx) => {
    byCategory.get(cat).push({ item, qIndex: idx, key: norm(q.question), level: lvl, module: mod });
  });
}

let changed = 0;
for (const [, records] of byCategory) {
  const groups = new Map();
  for (const r of records) {
    if (!r.key) continue;
    if (!groups.has(r.key)) groups.set(r.key, []);
    groups.get(r.key).push(r);
  }

  for (const [key, arr] of groups) {
    if (arr.length < 2) continue;
    // Keep first occurrence unchanged, rewrite others with level/module context.
    for (let i = 1; i < arr.length; i += 1) {
      const r = arr[i];
      const q = r.item.data.questions[r.qIndex];
      const original = String(q.question || '');
      q.question = `[${r.level} - ${r.module}] ${original}`;
      if (norm(q.question) === key) {
        q.question = `${original} (${r.level} ${i + 1})`;
      }
      changed += 1;
    }
  }
}

for (const { file, data } of modules) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

console.log(JSON.stringify({ changed }, null, 2));
