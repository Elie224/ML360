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

const replacements = [
  [/\bApprentissage non supervise\b/g, 'Apprentissage non supervisé'],
  [/\bApprentissage semi supervise\b/g, 'Apprentissage semi-supervisé'],
  [/\bApprentissage supervise\b/g, 'Apprentissage supervisé'],
  [/\bapprentissage non supervise\b/g, 'apprentissage non supervisé'],
  [/\bapprentissage semi supervise\b/g, 'apprentissage semi-supervisé'],
  [/\bapprentissage supervise\b/g, 'apprentissage supervisé'],
  [/\bdeploiement\b/gi, 'déploiement'],
  [/\bdonnees\b/gi, 'données'],
  [/\brarete\b/gi, 'rareté'],
  [/\bconformite\b/gi, 'conformité'],
  [/\bsecurite\b/gi, 'sécurité'],
  [/\bregularisation\b/gi, 'régularisation'],
  [/\bgeneralisation\b/gi, 'généralisation'],
  [/\bpenalite\b/gi, 'pénalité'],
  [/\bcategorie\b/gi, 'catégorie'],
  [/\bcontrole\b/gi, 'contrôle'],
  [/\bpreparation\b/gi, 'préparation'],
  [/\bdesiquilibre\b/gi, 'déséquilibre'],
  [/\binterpretabilite\b/gi, 'interprétabilité'],
  [/\bingenierie\b/gi, 'ingénierie'],
  [/\bderivees\b/gi, 'dérivées'],
  [/\bmodeles\b/gi, 'modèles'],
  [/\blever\b/gi, 'levier'],
  [/\bd anomalies\b/gi, "d'anomalies"],
  [/\bd anomalie\b/gi, "d'anomalie"],
  [/\bd appartenance\b/gi, "d'appartenance"],
  [/\bd alerte\b/gi, "d'alerte"],
  [/\bd activation\b/gi, "d'activation"],
  [/\bd erreur\b/gi, "d'erreur"],
  [/\bd entree\b/gi, "d'entrée"],
  [/\bd etat\b/gi, "d'état"],
  [/\bd exploration\b/gi, "d'exploration"],
  [/\bd exploitation\b/gi, "d'exploitation"],
  [/\bd apprentissage\b/gi, "d'apprentissage"],
  [/\bd optimisation\b/gi, "d'optimisation"],
  [/\bd inference\b/gi, "d'inférence"],
  [/\bd images\b/gi, "d'images"],
  [/\bd image\b/gi, "d'image"],
  [/\bd utilisation\b/gi, "d'utilisation"],
  [/\bd evaluation\b/gi, "d'évaluation"],
  [/\bd etiquetage\b/gi, "d'étiquetage"],
  [/\bd observations\b/gi, "d'observations"],
  [/\bd une\b/gi, "d'une"],
  [/\bd un\b/gi, "d'un"],
];

function fixString(text) {
  let out = text;
  for (const [pattern, value] of replacements) {
    out = out.replace(pattern, value);
  }
  return out
    .replace(/\s+'/g, " '")
    .replace(/\s{2,}/g, ' ')
    .trim();
}

function transform(node) {
  if (typeof node === 'string') {
    return fixString(node);
  }

  if (Array.isArray(node)) {
    return node.map(transform);
  }

  if (node && typeof node === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(node)) {
      out[k] = transform(v);
    }
    return out;
  }

  return node;
}

const files = walk(root);
let changedFiles = 0;

for (const file of files) {
  const data = JSON.parse(fs.readFileSync(file, 'utf8'));
  const next = transform(data);
  const before = JSON.stringify(data);
  const after = JSON.stringify(next);

  if (before !== after) {
    fs.writeFileSync(file, JSON.stringify(next, null, 2) + '\n', 'utf8');
    changedFiles += 1;
  }
}

console.log(JSON.stringify({ fileCount: files.length, changedFiles }, null, 2));
