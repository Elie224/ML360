const replacements: Array<[RegExp, string]> = [
  [/\bCategories\b/g, 'Catégories'],
  [/\bcategories\b/g, 'catégories'],
  [/\bCategorie\b/g, 'Catégorie'],
  [/\bcategorie\b/g, 'catégorie'],
  [/\bDebutant\b/g, 'Débutant'],
  [/\bdebutant\b/g, 'débutant'],
  [/\bMaitrise\b/g, 'Maîtrise'],
  [/\bmaitrise\b/g, 'maîtrise'],
  [/\bDeveloppe\b/g, 'Développe'],
  [/\bdeveloppe\b/g, 'développe'],
  [/\btheorie\b/g, 'théorie'],
  [/\breflexes\b/g, 'réflexes'],
  [/\bmetier\b/g, 'métier'],
  [/\bcachee\b/g, 'cachée'],
  [/\bdonnees\b/g, 'données'],
  [/\brecompense\b/g, 'récompense'],
  [/\bstrategie\b/g, 'stratégie'],
  [/\bscenarios\b/g, 'scénarios'],
  [/\bscenario\b/g, 'scénario'],
  [/\bselection\b/g, 'sélection'],
  [/\bprecedent\b/g, 'précédent'],
  [/\bprecedente\b/g, 'précédente'],
  [/\bReponses\b/g, 'Réponses'],
  [/\breponses\b/g, 'réponses'],
  [/\bReponse\b/g, 'Réponse'],
  [/\breponse\b/g, 'réponse'],
  [/\bResultat\b/g, 'Résultat'],
  [/\bresultat\b/g, 'résultat'],
  [/\bverrouille\b/g, 'verrouillé'],
  [/\bverrouillee\b/g, 'verrouillée'],
  [/\bdebloque\b/g, 'débloqué'],
  [/\bdebloquee\b/g, 'débloquée'],
  [/\bsemi supervise\b/gi, 'semi-supervisé'],
  [/\bnon supervise\b/gi, 'non supervisé'],
  [/\bsupervise\b/gi, 'supervisé'],
  [/\bAucune categorie\b/g, 'Aucune catégorie'],
]

export function normalizeFrenchText(text: string | null | undefined) {
  if (!text) {
    return text ?? ''
  }

  let value = text
  for (const [pattern, replacement] of replacements) {
    value = value.replace(pattern, replacement)
  }
  return value
}
