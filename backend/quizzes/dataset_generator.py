import json
import re
from pathlib import Path

from django.utils.text import slugify


LETTERS = ['A', 'B', 'C', 'D']

FRENCH_POLISH_REPLACEMENTS = [
	('scenario', 'scénario'),
	('Scenario', 'Scénario'),
	('metier', 'métier'),
	('Metier', 'Métier'),
	('donnees', 'données'),
	('Donnees', 'Données'),
	('donnee', 'donnée'),
	('Donnee', 'Donnée'),
	('etiquetee', 'étiquetée'),
	('Etiquetee', 'Étiquetée'),
	('etiquetees', 'étiquetées'),
	('Etiquetees', 'Étiquetées'),
	('labelise', 'labellisé'),
	('Labelise', 'Labellisé'),
	('labelisee', 'labellisée'),
	('Labelisee', 'Labellisée'),
	('reel', 'réel'),
	('Reel', 'Réel'),
	('reelle', 'réelle'),
	('Reelle', 'Réelle'),
	('fiabilite', 'fiabilité'),
	('Fiabilite', 'Fiabilité'),
	('coherence', 'cohérence'),
	('Coherence', 'Cohérence'),
	('coherent', 'cohérent'),
	('Coherent', 'Cohérent'),
	('qualite', 'qualité'),
	('Qualite', 'Qualité'),
	('methode', 'méthode'),
	('Methode', 'Méthode'),
	('strategie', 'stratégie'),
	('Strategie', 'Stratégie'),
	('securite', 'sécurité'),
	('Securite', 'Sécurité'),
	('precision', 'précision'),
	('Precision', 'Précision'),
	('decision', 'décision'),
	('Decision', 'Décision'),
	('evaluation', 'évaluation'),
	('Evaluation', 'Évaluation'),
	('generalisation', 'généralisation'),
	('Generalisation', 'Généralisation'),
	('regression', 'régression'),
	('Regression', 'Régression'),
	('derive', 'dérive'),
	('Derive', 'Dérive'),
	('probleme', 'problème'),
	('Probleme', 'Problème'),
	('completement', 'complètement'),
	('Completement', 'Complètement'),
	('coeur', 'cœur'),
	('Coeur', 'Cœur'),
	('equipe', 'équipe'),
	('Equipe', 'Équipe'),
	('plutot', 'plutôt'),
	('Plutot', 'Plutôt'),
	('debut', 'début'),
	('Debut', 'Début'),
	('decisions', 'décisions'),
	('Decisions', 'Décisions'),
	('aligne', 'aligné'),
	('Aligne', 'Aligné'),
	('credible', 'crédible'),
	('Credible', 'Crédible'),
	('finalite', 'finalité'),
	('Finalite', 'Finalité'),
	('ameliorer', 'améliorer'),
	('Ameliorer', 'Améliorer'),
	('reelles', 'réelles'),
	('Reelles', 'Réelles'),
	('premiere', 'première'),
	('Premiere', 'Première'),
	('intermediaire', 'intermédiaire'),
	('Intermediaire', 'Intermédiaire'),
	('regressions', 'régressions'),
	('Regressions', 'Régressions'),
	('idee', 'idée'),
	('Idee', 'Idée'),
	('demarrer', 'démarrer'),
	('Demarrer', 'Démarrer'),
	('verifiable', 'vérifiable'),
	('Verifiable', 'Vérifiable'),
	('decider', 'décider'),
	('Decider', 'Décider'),
	('enonce', 'énoncé'),
	('Enonce', 'Énoncé'),
	('decrit', 'décrit'),
	('Decrit', 'Décrit'),
	('precisement', 'précisément'),
	('Precisement', 'Précisément'),
	('definition', 'définition'),
	('Definition', 'Définition'),
	('stabilite', 'stabilité'),
	('Stabilite', 'Stabilité'),
]


def _polish_french_text(text):
	if not text:
		return text
	polished = text
	for source, target in FRENCH_POLISH_REPLACEMENTS:
		polished = re.sub(rf'\b{re.escape(source)}\b', target, polished)

	phrase_replacements = [
		('des le debut', 'dès le début'),
		('ce qu on', "ce qu'on"),
		('ce qu on te demande', "ce qu'on te demande"),
		("dans un atelier de cadrage de évaluation", "dans un atelier de cadrage d'évaluation"),
		("d'une intuition a une action", "d'une intuition à une action"),
		('davantage a ', 'davantage à '),
		('problème pose', 'problème posé'),
		('concept central demande', 'concept central demandé'),
	]
	for source, target in phrase_replacements:
		polished = polished.replace(source, target)

	# Common contractions in generated French prose.
	polished = re.sub(r"\bde ([aeiouhAEIOUHéèêàîïôùûÉÈÊÀÎÏÔÙÛ])", r"d'\1", polished)
	polished = re.sub(r"\b([dDlL]) ([aeiouhAEIOUH])", r"\1'\2", polished)
	polished = re.sub(r"\b([jJ]) ai\b", r"\1'ai", polished)
	polished = re.sub(r"\bc est\b", "c'est", polished)
	polished = re.sub(r"\bC est\b", "C'est", polished)
	polished = re.sub(r'\s{2,}', ' ', polished).strip()
	return polished

LEVEL_SPECS = {
	'Beginner': {'difficulty': 'easy', 'question_counts': [10, 11, 12, 13, 15]},
	'Intermediate': {'difficulty': 'medium', 'question_counts': [12, 14, 15, 16, 18, 20, 22]},
	'Advanced': {'difficulty': 'hard', 'question_counts': [15, 17, 18, 20, 22, 24, 26, 28, 30, 32]},
}

MODULE_LIBRARY = {
	'apprentissage-supervise': {
		'category': 'Apprentissage supervise',
		'levels': {
			'Beginner': [
				('Fondamentaux du supervise', ['donnee etiquetee', 'feature', 'target', 'modele predictif']),
				('Preparation des donnees', ['nettoyage', 'normalisation', 'encodage categoriel', 'split train-test']),
				('Bases de la regression', ['variable continue', 'residu', 'erreur quadratique', 'regression lineaire']),
				('Bases de la classification', ['classe', 'frontiere de decision', 'regression logistique', 'matrice de confusion']),
				('Evaluation initiale', ['accuracy', 'precision', 'recall', 'overfitting']),
			],
			'Intermediate': [
				('Ingenierie des features', ['standardisation', 'selection de variables', 'variables derivees', 'prevention de fuite']),
				('Modeles lineaires avances', ['coefficient', 'regularisation', 'log-odds', 'interpretabilite']),
				('Arbres de decision', ['split', 'profondeur maximale', 'random forest', 'importance des variables']),
				('Strategie de validation', ['cross-validation', 'validation set', 'stratification', 'early stopping']),
				('Desiquilibre de classes', ['F1 score', 'ROC-AUC', 'class weights', 'resampling']),
				('Controle de generalisation', ['penalite L1', 'penalite L2', 'compromis biais-variance', 'underfitting']),
				('Pipelines et experimentation', ['pipeline', 'modele baseline', 'recherche d hyperparametres', 'reproductibilite']),
			],
			'Advanced': [
				('Diagnostic biais-variance', ['biais eleve', 'variance elevee', 'courbe d apprentissage', 'decomposition de l erreur']),
				('Conception d ensembles', ['bagging', 'boosting', 'stacking', 'weak learner']),
				('Optimisation d hyperparametres', ['grid search', 'random search', 'optimisation bayesienne', 'espace de recherche']),
				('Calibration et seuils', ['courbe de calibration', 'seuil de decision', 'Brier score', 'calibration des probabilites']),
				('Explicabilite', ['SHAP', 'partial dependence', 'permutation importance', 'explication locale']),
				('Drift et monitoring', ['data drift', 'concept drift', 'monitoring de performance', 'seuil d alerte']),
				('Decisions sensibles au cout', ['cout faux positif', 'cout faux negatif', 'matrice de cout', 'ajustement du seuil']),
				('Robustesse au bruit', ['bruit de labels', 'loss robuste', 'filtrage d anomalies', 'controle de coherence']),
				('Fairness et conformite', ['parite demographique', 'equal opportunity', 'attribut sensible', 'audit de biais']),
				('Production des systemes supervises', ['feature store', 'evaluation offline', 'inference online', 'strategie de rollback']),
			],
		},
	},
	'apprentissage-non-supervise': {
		'category': 'Apprentissage non supervise',
		'levels': {
			'Beginner': [
				('Fondamentaux du non supervise', ['donnee non etiquetee', 'structure cachee', 'similarite', 'segmentation']),
				('Mesures de proximite', ['distance euclidienne', 'distance cosinus', 'normalisation', 'voisinage']),
				('Introduction au clustering', ['cluster', 'centroide', 'inertie', 'assignation']),
				('Reduction de dimension', ['projection', 'variance expliquee', 'PCA', 'visualisation']),
				('Evaluation initiale', ['silhouette score', 'cohesion', 'separation', 'stabilite']),
			],
			'Intermediate': [
				('Preparation des donnees non supervisees', ['scaling', 'gestion des outliers', 'selection de variables', 'curse of dimensionality']),
				('K-means en pratique', ['initialisation', 'mise a jour des centroides', 'convergence', 'choix de k']),
				('Clustering hierarchique', ['liaison simple', 'liaison complete', 'dendrogramme', 'coupe de clusters']),
				('Clustering par densite', ['DBSCAN', 'epsilon', 'min_samples', 'points bruit']),
				('PCA et transformations', ['composante principale', 'decorrelation', 'compression', 'reconstruction']),
				('Regles d association', ['support', 'confiance', 'lift', 'market basket']),
				('Validation de clusters', ['Davies-Bouldin', 'Calinski-Harabasz', 'stabilite inter-runs', 'interpretation metier']),
			],
			'Advanced': [
				('Modeles de melange', ['Gaussian mixture', 'probabilite d appartenance', 'EM', 'covariance']),
				('Clustering spectral', ['graphe de similarite', 'laplacien', 'valeurs propres', 'embedding spectral']),
				('Factorisation matricielle', ['decomposition', 'facteurs latents', 'recommandation', 'approximation basse dimension']),
				('Detection d anomalies', ['isolation', 'score d anomalie', 'contamination', 'seuil d alerte']),
				('Selection de modeles non supervises', ['AIC', 'BIC', 'selection de k', 'compromis complexite']),
				('Donnees de grande dimension', ['malediction dimensionnelle', 'sparsity', 'distance degradee', 'reduction prealable']),
				('Segmentation metier', ['persona', 'micro-segments', 'action marketing', 'priorisation']),
				('Robustesse des clusters', ['bootstrap', 'sensibilite au bruit', 'stabilite temporelle', 'reassignation']),
				('Monitoring non supervise', ['drift de segments', 'evolution des centroides', 'qualite de partition', 'alerting']),
				('Industrialisation', ['pipeline batch', 'rafraichissement periodique', 'versioning de segments', 'rollback analytique']),
			],
		},
	},
	'apprentissage-semi-supervise': {
		'category': 'Apprentissage semi supervise',
		'levels': {
			'Beginner': [
				('Fondamentaux du semi supervise', ['petit jeu labelise', 'grand jeu non labelise', 'hypothese de continuite', 'gain de labels']),
				('Valeur des donnees non etiquetees', ['structure des donnees', 'proximite', 'coherence locale', 'pseudo-information']),
				('Pseudo-labeling initial', ['pseudo-label', 'confiance', 'filtrage', 'iteration']),
				('Propagation simple', ['voisinage', 'graphe', 'transfert de labels', 'consistance']),
				('Evaluation initiale', ['jeu de validation labelise', 'precision des pseudo-labels', 'drift des labels', 'surapprentissage']),
			],
			'Intermediate': [
				('Self-training', ['enseignant initial', 're-entrainement', 'selection confiante', 'accumulation d erreurs']),
				('Label propagation', ['graphe de similarite', 'propagation iterative', 'lissage', 'voisins fiables']),
				('Co-training', ['vues complementaires', 'independance conditionnelle', 'echange de labels', 'accord entre modeles']),
				('Seuils de confiance', ['score de confiance', 'precision attendue', 'trade-off couverture', 'rejet']),
				('Augmentation de donnees', ['transformation stable', 'consistance', 'robustesse', 'regularisation']),
				('Validation sous rarete de labels', ['petit validation set', 'cross-validation restreinte', 'selection prudente', 'biais d estimation']),
				('Qualite des pseudo-labels', ['bruit de labels', 'correction', 'reponderation', 'ensemble teacher-student']),
			],
			'Advanced': [
				('Controle du bruit de pseudo-labels', ['filtre de confiance', 'temperature', 'label sharpening', 'correction iterative']),
				('Mismatch de distribution', ['shift domaine', 'covariate shift', 'alignement de distributions', 'adaptation']),
				('Graphes avances', ['graphe k-NN', 'poids d aretes', 'harmonic function', 'regularisation sur graphe']),
				('Teacher-student', ['modele enseignant', 'modele etudiant', 'consistency loss', 'mise a jour EMA']),
				('Active learning hybride', ['requete de labels', 'incertitude', 'budget annotation', 'boucle humaine']),
				('Calibration en semi supervise', ['surconfiance', 'temperature scaling', 'selection prudente', 'fiabilite']),
				('Robustesse et generalisation', ['augmentation forte', 'stabilite', 'domain shift', 'regularisation']),
				('Fairness sous labels rares', ['biais d echantillonnage', 'groupes sous-representes', 'audit', 'mitigation']),
				('Monitoring en production', ['degradation des pseudo-labels', 'drift de confiance', 'erreurs silencieuses', 'alerte']),
				('Boucles de production', ['rafraichissement de labels', 'versioning', 'validation humaine', 'rollback']),
			],
		},
	},
	'apprentissage-par-renforcement': {
		'category': 'Apprentissage par renforcement',
		'levels': {
			'Beginner': [
				('Fondamentaux du RL', ['agent', 'environnement', 'etat', 'action']),
				('Recompense et objectif', ['reward', 'retour cumule', 'objectif long terme', 'signal sparse']),
				('Episodes et transitions', ['episode', 'step', 'transition', 'terminal state']),
				('Politique et decision', ['policy', 'choix d action', 'comportement', 'strategie']),
				('Evaluation initiale', ['score cumule', 'random baseline', 'stabilite d apprentissage', 'exploration']),
			],
			'Intermediate': [
				('MDP', ['etat de Markov', 'dynamique de transition', 'reward immediate', 'horizon']),
				('Fonctions de valeur', ['value function', 'Q-value', 'estimation', 'greedy action']),
				('Bellman et mises a jour', ['equation de Bellman', 'bootstrapping', 'target update', 'erreur temporelle']),
				('Exploration exploitation', ['epsilon-greedy', 'optimisme', 'trade-off', 'decouverte']),
				('Q-learning', ['mise a jour hors politique', 'max target', 'table Q', 'convergence']),
				('Evaluation de politique', ['rollout', 'moyenne episodique', 'variance', 'comparaison de politiques']),
				('Approximation de fonctions', ['generalisation', 'features d etat', 'approximateur', 'instabilite']),
			],
			'Advanced': [
				('Controle TD avance', ['SARSA', 'double Q-learning', 'eligibility traces', 'biais de maximisation']),
				('Policy gradient', ['gradient de politique', 'REINFORCE', 'baseline', 'variance reduction']),
				('Actor-critic', ['actor', 'critic', 'advantage', 'mise a jour conjointe']),
				('Evaluation hors politique', ['importance sampling', 'bias-variance', 'estimation offline', 'coverage']),
				('Reward shaping', ['recompense dense', 'guidage', 'risque de hacking', 'potentiel']),
				('Efficacite echantillon', ['replay buffer', 'reutilisation', 'batch learning', 'cout simulation']),
				('Contraintes de securite', ['safe exploration', 'etat dangereux', 'penalite', 'garde-fou']),
				('Multi-agent', ['coordination', 'competition', 'equilibre', 'credit assignment']),
				('Deploiement RL', ['simulateur', 'shadow mode', 'latence de decision', 'rollback']),
				('Monitoring RL', ['drift de politique', 'regret', 'effondrement de performance', 'alerte operationnelle']),
			],
		},
	},
}

CATEGORY_ALIASES = {
	'supervised-learning': 'apprentissage-supervise',
	'unsupervised-learning': 'apprentissage-non-supervise',
	'semi-supervised-learning': 'apprentissage-semi-supervise',
	'reinforcement-learning': 'apprentissage-par-renforcement',
}

REFINED_MODULE_QUIZZES = {
	('apprentissage-supervise', 'Beginner', 'Fondamentaux du supervise'): [
		{
			'type': 'text',
			'question': 'In supervised learning, what makes a training example supervised rather than unsupervised?',
			'image_url': None,
			'choices': {
				'A': 'Each example includes an input and its expected output label.',
				'B': 'The model automatically discovers labels from hidden patterns.',
				'C': 'The dataset only contains features with no prediction target.',
				'D': 'The algorithm never compares predictions with true answers.',
			},
			'correct_answer': 'A',
			'explanation': 'Supervised learning relies on labeled examples, meaning the correct target is known during training.',
		},
		{
			'type': 'text',
			'question': 'For a house-price model, which variable is the target?',
			'image_url': None,
			'choices': {
				'A': 'The neighborhood name',
				'B': 'The sale price of the house',
				'C': 'The number of rooms used as input',
				'D': 'The list of features after preprocessing',
			},
			'correct_answer': 'B',
			'explanation': 'The target is the value the model is asked to predict, here the sale price.',
		},
		{
			'type': 'text',
			'question': 'Which statement best describes a feature in a supervised model?',
			'image_url': None,
			'choices': {
				'A': 'It is the evaluation metric used after training.',
				'B': 'It is an input variable used to help predict the target.',
				'C': 'It is the final label predicted by the model.',
				'D': 'It is a mistake made by the model during validation.',
			},
			'correct_answer': 'B',
			'explanation': 'A feature is one of the inputs the model uses to estimate the correct target.',
		},
		{
			'type': 'text',
			'question': 'Why do we usually split data into training and test sets in supervised learning?',
			'image_url': None,
			'choices': {
				'A': 'To make the model memorize only the first half of the rows',
				'B': 'To reduce the number of features before training starts',
				'C': 'To estimate how well the model generalizes to unseen examples',
				'D': 'To guarantee that every model reaches the same accuracy',
			},
			'correct_answer': 'C',
			'explanation': 'A held-out test set gives an external check of whether the learned pattern works on new data.',
		},
		{
			'type': 'text',
			'question': 'A model predicts whether an email is spam or not spam. What kind of supervised task is this?',
			'image_url': None,
			'choices': {
				'A': 'Classification',
				'B': 'Regression',
				'C': 'Clustering',
				'D': 'Dimensionality reduction',
			},
			'correct_answer': 'A',
			'explanation': 'The output is a discrete label, so the task is classification.',
		},
		{
			'type': 'text',
			'question': 'A model predicts tomorrow temperature as 29.4 degrees Celsius. What kind of supervised task is this?',
			'image_url': None,
			'choices': {
				'A': 'Classification',
				'B': 'Regression',
				'C': 'Association rule mining',
				'D': 'Anomaly detection',
			},
			'correct_answer': 'B',
			'explanation': 'When the target is a continuous numeric value, the task is regression.',
		},
		{
			'type': 'image',
			'question': 'Look at the diagram placeholder for a scatter plot with a fitted line. What is the best interpretation?',
			'image_url': 'supervised_regression_line_intro_1.png',
			'choices': {
				'A': 'It shows a regression model estimating a continuous relationship between inputs and outputs.',
				'B': 'It shows a clustering algorithm splitting points into hidden groups without labels.',
				'C': 'It shows a confusion matrix for binary classification.',
				'D': 'It shows a reinforcement agent selecting actions over time.',
			},
			'correct_answer': 'A',
			'explanation': 'A fitted line over labeled points is the classic beginner visualization for supervised regression.',
		},
		{
			'type': 'image',
			'question': 'A diagram placeholder shows two classes separated by a boundary. What concept does it illustrate most directly?',
			'image_url': 'supervised_decision_boundary_intro_1.png',
			'choices': {
				'A': 'A decision boundary used by a classifier to separate labeled classes',
				'B': 'A principal component used for dimensionality reduction',
				'C': 'A reward curve used in reinforcement learning',
				'D': 'A density cluster discovered without any target labels',
			},
			'correct_answer': 'A',
			'explanation': 'A boundary separating two labeled classes is one of the main visual intuitions behind supervised classification.',
		},
		{
			'type': 'text',
			'question': 'Why is it risky to evaluate a supervised model only on the same data used for training?',
			'image_url': None,
			'choices': {
				'A': 'Because the model may appear better than it really is on unseen data',
				'B': 'Because training data cannot contain any labels',
				'C': 'Because regression metrics require clustering labels first',
				'D': 'Because test data must always be larger than training data',
			},
			'correct_answer': 'A',
			'explanation': 'Testing on training data hides overfitting and inflates confidence about real-world performance.',
		},
		{
			'type': 'text',
			'question': 'A beginner builds a churn model using a column created after the customer has already left. What is the main issue?',
			'image_url': None,
			'choices': {
				'A': 'The model is using leaked information that would not be available at prediction time',
				'B': 'The model automatically becomes unsupervised',
				'C': 'The target changes from classification to regression',
				'D': 'The dataset no longer needs a training split',
			},
			'correct_answer': 'A',
			'explanation': 'Using post-event information creates leakage and leads to unrealistic performance estimates.',
		},
	],
}


def _normalize_category_key(category_key):
	return CATEGORY_ALIASES.get(category_key, category_key)


def supported_category_keys():
	return sorted(MODULE_LIBRARY.keys())


def supported_levels(category_key):
	category_key = _normalize_category_key(category_key)
	if category_key not in MODULE_LIBRARY:
		available = ', '.join(supported_category_keys())
		raise ValueError(f'Unsupported category key: {category_key}. Available: {available}')
	return list(MODULE_LIBRARY[category_key]['levels'].keys())


def supported_modules(category_key, level_name):
	category_key = _normalize_category_key(category_key)
	if category_key not in MODULE_LIBRARY:
		available = ', '.join(supported_category_keys())
		raise ValueError(f'Unsupported category key: {category_key}. Available: {available}')
	if level_name not in MODULE_LIBRARY[category_key]['levels']:
		available = ', '.join(MODULE_LIBRARY[category_key]['levels'].keys())
		raise ValueError(f'Unsupported level: {level_name}. Available: {available}')
	return [module_title for module_title, _ in MODULE_LIBRARY[category_key]['levels'][level_name]]


def iter_module_targets():
	for category_key in supported_category_keys():
		for level_name in supported_levels(category_key):
			for module_name in supported_modules(category_key, level_name):
				yield category_key, level_name, module_name


def _build_concept(category_name, level_name, module_title, concept_name):
	hint = _concept_semantic_hint(concept_name)
	if level_name == 'Beginner':
		definition = f"une notion de base en {category_name.lower()} ; {hint['definition']}"
		purpose = f"installer un raisonnement fiable des le debut ; {hint['purpose']}"
		pitfall = f"appliquer {concept_name} par automatisme sans verifier hypotheses, qualite des donnees et objectif metier"
		scenario = f"Un analyste junior mobilise {concept_name} dans un workflow introductif de {module_title} pour prendre une première décision fiable."
	elif level_name == 'Intermediate':
		definition = f"un concept intermediaire en {category_name.lower()} ; {hint['definition']}"
		purpose = f"fiabiliser les decisions d'experimentation ; {hint['purpose']}"
		pitfall = f"sur-optimiser {concept_name} localement en ignorant ses interactions avec features, metriques et protocoles de validation"
		scenario = f"Un praticien ML ajuste {concept_name} dans un pipeline de {module_title} pour renforcer la robustesse sur des données inconnues."
	else:
		definition = f"un levier avance en {category_name.lower()} ; {hint['definition']}"
		purpose = f"supporter des arbitrages de production ; {hint['purpose']}"
		pitfall = f"optimiser {concept_name} en silo et introduire des modes d'echec caches au deploiement"
		scenario = f"Une équipe ML de production s'appuie sur {concept_name} dans {module_title} pour limiter les régressions en charge réelle."

	return {
		'name': concept_name,
		'definition': definition,
		'purpose': purpose,
		'pitfall': pitfall,
		'scenario': scenario,
		'descriptor': hint['descriptor'],
	}


def _concept_semantic_hint(concept_name):
	name = concept_name.lower()
	if 'f1' in name:
		return {
			'definition': "il combine precision et rappel via leur moyenne harmonique pour evaluer un classifieur en classes desequilibrees.",
			'purpose': "arbitrer entre faux positifs et faux negatifs lorsque l'exactitude globale est trompeuse.",
			'descriptor': "metrique d'equilibre precision-rappel",
		}
	if 'precision' in name:
		return {
			'definition': "il mesure la proportion de predictions positives qui sont effectivement correctes.",
			'purpose': "limiter les faux positifs quand une alerte incorrecte coute cher.",
			'descriptor': "controle des faux positifs",
		}
	if 'rappel' in name or 'recall' in name:
		return {
			'definition': "il mesure la proportion de cas positifs reels detectes par le modele.",
			'purpose': "reduire les faux negatifs quand rater un cas est critique.",
			'descriptor': "controle des faux negatifs",
		}
	if 'roc-auc' in name or ('auc' in name and 'roc' in name):
		return {
			'definition': "il mesure la capacite du modele a separer classes positives et negatives sur tous les seuils.",
			'purpose': "comparer des modeles de classification independamment d'un seuil de decision unique.",
			'descriptor': "discrimination globale du classifieur",
		}
	if 'matrice de confusion' in name:
		return {
			'definition': "elle decompose les predictions en vrais positifs, vrais negatifs, faux positifs et faux negatifs.",
			'purpose': "diagnostiquer precisement les types d'erreurs avant d'ajuster le modele.",
			'descriptor': "diagnostic detaille des erreurs",
		}
	if 'resampling' in name or 'sur-echantill' in name or 'sous-echantill' in name:
		return {
			'definition': "il reequilibre la distribution des classes en augmentant ou reduisant certaines observations.",
			'purpose': "ameliorer l'apprentissage sur classes minoritaires sans ignorer les majoritaires.",
			'descriptor': "reequilibrage de classes",
		}
	if 'class weight' in name:
		return {
			'definition': "il attribue un cout plus fort aux erreurs sur classes minoritaires dans la fonction de perte.",
			'purpose': "forcer le modele a mieux prendre en compte les classes rares.",
			'descriptor': "pondération du cout d'erreur",
		}
	if 'stratification' in name:
		return {
			'definition': "elle preserve les proportions de classes dans les splits train/validation/test.",
			'purpose': "eviter des evaluations biaisees dues a une repartition non representative.",
			'descriptor': "echantillonnage representatif par classe",
		}
	if 'early stopping' in name:
		return {
			'definition': "il arrete l'entrainement quand la performance de validation cesse de progresser.",
			'purpose': "limiter le surapprentissage et reduire le cout de calcul inutile.",
			'descriptor': "controle du surapprentissage en entrainement",
		}
	if 'hyperparam' in name:
		return {
			'definition': "il regroupe les reglages externes du modele (profondeur, taux d'apprentissage, regularisation) fixes avant apprentissage.",
			'purpose': "trouver le meilleur compromis biais-variance pour le contexte metier.",
			'descriptor': "reglage des parametres de modelisation",
		}
	if 'reproductibilite' in name:
		return {
			'definition': "elle garantit qu'un meme pipeline redonne les memes resultats avec memes donnees, code et seeds.",
			'purpose': "fiabiliser comparaison d'experiences, audit et retour arriere en production.",
			'descriptor': "stabilite experimentale et auditabilite",
		}
	if 'calibration' in name:
		return {
			'definition': "elle ajuste les probabilites predites pour qu'elles refletent mieux les frequences observees.",
			'purpose': "rendre les scores probabilistes utilisables pour des decisions a seuil metier.",
			'descriptor': "fiabilite des probabilites predites",
		}
	if 'drift' in name:
		return {
			'definition': "il mesure une derive entre les conditions d'entrainement et les conditions d'exploitation.",
			'purpose': "detecter rapidement une perte de validite du modele avant impact metier.",
			'descriptor': "surveillance de derive des donnees ou du comportement",
		}
	if 'validation' in name or 'cross-validation' in name:
		return {
			'definition': "il structure l'evaluation hors entrainement pour estimer la generalisation reelle.",
			'purpose': "reduire le risque de surestimer la performance sur donnees futures.",
			'descriptor': "evaluation robuste de la generalisation",
		}
	if 'regularisation' in name or 'penalite' in name:
		return {
			'definition': "il contraint la complexite du modele pour limiter le surapprentissage.",
			'purpose': "ameliorer la stabilite hors echantillon en controlant la variance.",
			'descriptor': "controle de complexite et robustesse",
		}
	if 'cluster' in name or 'k-means' in name or 'dbscan' in name:
		return {
			'definition': "il organise des observations non etiquetees en groupes cohérents selon une logique de similarite.",
			'purpose': "extraire une structure exploitable sans labels explicites.",
			'descriptor': "segmentation non supervisee",
		}
	if 'q-learning' in name or 'policy' in name or 'actor' in name or 'critic' in name:
		return {
			'definition': "il guide l'apprentissage de decisions sequentielles en maximisant un signal de recompense.",
			'purpose': "ameliorer une politique d'action sous incertitude dynamique.",
			'descriptor': "optimisation de politique en decision sequentielle",
		}
	if 'pseudo-label' in name or 'semi' in name:
		return {
			'definition': "il exploite des exemples non etiquetes en injectant des labels estimes sous controle de confiance.",
			'purpose': "augmenter la performance avec peu de labels humains.",
			'descriptor': "apprentissage avec labels rares",
		}
	if 'fair' in name or 'parite' in name or 'equal opportunity' in name or 'biais' in name:
		return {
			'definition': "il traite l'equite de decision entre groupes sensibles et la conformite des modeles.",
			'purpose': "reduire les disparites de performance entre populations.",
			'descriptor': "equite et conformite algorithmique",
		}
	if 'feature' in name:
		return {
			'definition': "il concerne la representation des variables utiles au modele et leur qualite predictive.",
			'purpose': "amplifier le signal utile tout en limitant le bruit.",
			'descriptor': "qualite de representation des variables",
		}
	if 'anomal' in name:
		return {
			'definition': "il permet d'identifier des observations rares ou incoherentes avec le comportement normal.",
			'purpose': "declencher des actions de controle sur des cas atypiques critiques.",
			'descriptor': "detection de cas atypiques",
		}
	if 'pca' in name or 'reduction de dimension' in name:
		return {
			'definition': "il projette les variables sur un sous-espace plus compact qui conserve l'essentiel de la variance utile.",
			'purpose': "reduire bruit et cout de calcul tout en preservant l'information structurante.",
			'descriptor': "compression de representation",
		}
	if 'q-learning' in name:
		return {
			'definition': "il apprend une fonction de valeur d'action pour choisir progressivement les actions maximisant la recompense future.",
			'purpose': "optimiser une politique sans modele explicite de l'environnement.",
			'descriptor': "apprentissage de valeur d'action",
		}
	if 'policy gradient' in name:
		return {
			'definition': "il optimise directement les parametres de politique via le gradient de recompense attendue.",
			'purpose': "ameliorer des politiques continues ou stochastiques avec un signal de retour global.",
			'descriptor': "optimisation directe de politique",
		}
	if 'monitoring' in name:
		return {
			'definition': "il organise le suivi continu des metriques techniques et metier apres deploiement.",
			'purpose': "detecter rapidement degradation de performance, derive et incidents.",
			'descriptor': "surveillance operationnelle du systeme ML",
		}
	return {
		'definition': f"il formalise le role de {concept_name} dans un pipeline ML, avec ses hypotheses et ses limites pratiques.",
		'purpose': f"l'utiliser correctement permet de mieux decider quand et comment appliquer {concept_name} en production.",
		'descriptor': f"usage operationnel de {concept_name}",
	}


def _build_modules(category_key, level_name):
	category = MODULE_LIBRARY[category_key]
	modules = []
	for title, concept_names in category['levels'][level_name]:
		modules.append(
			{
				'title': title,
				'concepts': [
					_build_concept(category['category'], level_name, title, concept_name)
					for concept_name in concept_names
				],
			}
		)
	return modules


def _module_question_count(level_name, module_number):
	profiles = {
		'Beginner': [10, 11, 12, 13, 15],
		'Intermediate': [12, 14, 15, 16, 18, 20, 22],
		'Advanced': [15, 17, 18, 20, 22, 24, 26, 28, 30, 32],
	}
	return profiles[level_name][module_number - 1]


def _module_difficulty_sequence(level_name, question_count):
	if level_name == 'Beginner':
		easy_count = max(1, int(question_count * 0.6))
		medium_count = max(1, int(question_count * 0.3))
		hard_count = question_count - easy_count - medium_count
	elif level_name == 'Intermediate':
		easy_count = max(1, int(question_count * 0.25))
		medium_count = max(1, int(question_count * 0.45))
		hard_count = question_count - easy_count - medium_count
	else:
		easy_count = 0
		medium_count = max(1, int(question_count * 0.35))
		hard_count = question_count - medium_count

	return (['easy'] * easy_count) + (['medium'] * medium_count) + (['hard'] * hard_count)


def _image_name(category_key, module_title, concept_name, variant_index):
	module_slug = module_title.lower().replace(' ', '_').replace('-', '_').replace("'", '')
	concept_slug = concept_name.lower().replace(' ', '_').replace('-', '_').replace("'", '')
	return f"{category_key}_{module_slug}_{concept_slug}_{variant_index}.png"


def _rotate_choices(choices, correct_index, seed):
	shift = seed % len(choices)
	rotated_indices = list(range(len(choices)))[shift:] + list(range(len(choices)))[:shift]
	rotated_choices = [choices[index] for index in rotated_indices]
	new_correct_index = rotated_indices.index(correct_index)
	return rotated_choices, LETTERS[new_correct_index]


BUSINESS_CONTEXTS = [
	"banque",
	"assurance",
	"sante",
	"marketing",
	"e-commerce",
	"industrie",
	"cybersecurite",
]


CERTIFICATION_PRIORITY_MODULES = {
	('apprentissage-supervise', 'Intermediate', 'Strategie de validation'),
	('apprentissage-supervise', 'Intermediate', 'Controle de generalisation'),
	('apprentissage-supervise', 'Advanced', 'Diagnostic biais-variance'),
	('apprentissage-supervise', 'Advanced', 'Optimisation d hyperparametres'),
	('apprentissage-supervise', 'Advanced', 'Production des systemes supervises'),
	('apprentissage-non-supervise', 'Intermediate', 'Validation de clusters'),
	('apprentissage-non-supervise', 'Intermediate', 'K-means en pratique'),
	('apprentissage-non-supervise', 'Advanced', 'Detection d anomalies'),
	('apprentissage-non-supervise', 'Advanced', 'Selection de modeles non supervises'),
	('apprentissage-non-supervise', 'Advanced', 'Industrialisation'),
	('apprentissage-semi-supervise', 'Intermediate', 'Validation sous rarete de labels'),
	('apprentissage-semi-supervise', 'Intermediate', 'Qualite des pseudo-labels'),
	('apprentissage-semi-supervise', 'Advanced', 'Controle du bruit de pseudo-labels'),
	('apprentissage-semi-supervise', 'Advanced', 'Calibration en semi supervise'),
	('apprentissage-semi-supervise', 'Advanced', 'Monitoring en production'),
	('apprentissage-par-renforcement', 'Intermediate', 'Q-learning'),
	('apprentissage-par-renforcement', 'Intermediate', 'Exploration exploitation'),
	('apprentissage-par-renforcement', 'Advanced', 'Policy gradient'),
	('apprentissage-par-renforcement', 'Advanced', 'Evaluation hors politique'),
	('apprentissage-par-renforcement', 'Advanced', 'Monitoring RL'),
}


def _context_for(seed):
	return BUSINESS_CONTEXTS[seed % len(BUSINESS_CONTEXTS)]


def _question_prompt(kind, concept, module_title, context, seed):
	templates = {
		'definition': [
			"{name}: quelle proposition en donne la meilleure definition dans '{module}' (contexte {context}) ?",
			"Dans '{module}' ({context}), quel enonce decrit le plus precisement {name} ?",
			"Pour une equipe {context} dans '{module}', quelle definition de {name} est la plus juste ?",
		],
		'purpose': [
			"{name}: pourquoi ce concept est-il crucial pour une equipe {context} dans '{module}' ?",
			"Dans '{module}', quel est le role le plus determinant de {name} pour un cas {context} ?",
			"Face a un besoin {context} dans '{module}', pourquoi {name} est-il prioritaire ?",
		],
		'pitfall': [
			"{name}: quel risque est le plus directement lie a son mauvais usage en production dans '{module}' ?",
			"Dans '{module}', quel est le principal mode d'echec quand {name} est mal applique ?",
			"Pour une mise en production de '{module}', quelle erreur autour de {name} est la plus critique ?",
		],
		'scenario': [
			"{name}: quel scenario illustre le mieux son usage reel dans '{module}' ?",
			"Dans '{module}', quelle situation de terrain montre le mieux quand utiliser {name} ?",
			"Pour un cas operationnel de '{module}', quel exemple met {name} au coeur de la decision ?",
		],
		'name_from_definition': [
			"Description experte ({module}) - {definition} Quel concept est le plus exact ?",
			"Dans '{module}', quel concept correspond le mieux a cette description: {definition}",
			"A partir de cette description issue de '{module}' ({definition}), quel concept faut-il retenir ?",
		],
		'name_from_purpose': [
			"Objectif ({module}) - {purpose} Quel concept est le plus coherent ?",
			"Dans '{module}', quel concept repond le mieux a cet objectif: {purpose}",
			"Quel concept de '{module}' est le plus aligne avec cet objectif: {purpose}",
		],
		'image_scenario': [
			"{name}: dans un cas {context}, quelle interpretation correspond le mieux au schema ML de '{module}' ?",
			"Observation visuelle ({module}) - pour un contexte {context}, quelle lecture du schema est la plus pertinente pour {name} ?",
			"Dans '{module}' et en contexte {context}, quelle interpretation du schema appuie le mieux l'analyse de {name} ?",
		],
		'image_purpose': [
			"{name}: dans '{module}', un schema met en evidence ce comportement. Quelle lecture est la plus juste ?",
			"Dans '{module}', quel commentaire du schema traduit le mieux le role de {name} ?",
			"Quel diagnostic du schema est le plus coherent avec {name} dans '{module}' ?",
		],
	}
	selected = templates[kind][seed % len(templates[kind])]
	return selected.format(
		name=concept['name'],
		module=module_title,
		context=context,
		definition=concept['definition'],
		purpose=concept['purpose'],
	)


def _name_distractors(category_key, level_name, target_name, seed):
	names = []
	for module_title, concept_names in MODULE_LIBRARY[category_key]['levels'][level_name]:
		for concept_name in concept_names:
			if concept_name != target_name:
				names.append(concept_name)

	# Preserve order while removing duplicates.
	unique_names = []
	seen = set()
	for name in names:
		if name not in seen:
			seen.add(name)
			unique_names.append(name)

	if len(unique_names) < 3:
		fallback = [name for name in ['regularisation', 'cross-validation', 'feature engineering', 'monitoring'] if name != target_name]
		unique_names.extend(fallback)

	shift = seed % len(unique_names)
	rotated = unique_names[shift:] + unique_names[:shift]
	return rotated[:3]


def _is_certification_priority(category_key, level_name, module_title):
	return (category_key, level_name, module_title) in CERTIFICATION_PRIORITY_MODULES


def _concept_lookup(category_key, level_name):
	lookup = {}
	for module in _build_modules(category_key, level_name):
		for concept in module['concepts']:
			lookup.setdefault(concept['name'], concept)
	return lookup


def _choice_text(kind, target, option, module_title, level_name, slot):
	target_name = target['name']
	option_name = option['name']
	is_target = option_name == target_name
	module_ctx = module_title

	def _clean_hint(text, fallback):
		if not text:
			return fallback
		compact = re.sub(r'\s+', ' ', text).strip(' .;')
		if ':' in compact:
			compact = compact.split(':', 1)[1].strip(' .;')
		return compact or fallback

	def _learning_statement(base_kind):
		descriptor = option.get('descriptor') or _concept_semantic_hint(option_name)['descriptor']
		definition_hint = _clean_hint(option.get('definition', ''), descriptor)
		purpose_hint = _clean_hint(option.get('purpose', ''), descriptor)
		pitfall_hint = _clean_hint(option.get('pitfall', ''), descriptor)

		if base_kind == 'definition':
			templates = [
				f"{option_name} designe {definition_hint}.",
				f"{option_name} correspond a {definition_hint}, ce qui structure l'analyse dans {module_ctx}.",
				f"Dans {module_ctx}, {option_name} se comprend comme {definition_hint}.",
			]
			return templates[slot % len(templates)]

		if base_kind == 'purpose':
			templates = [
				f"Le role de {option_name} est de {purpose_hint}.",
				f"{option_name} sert a {purpose_hint} pour guider une decision exploitable.",
				f"Dans {module_ctx}, {option_name} est mobilise pour {purpose_hint}.",
			]
			return templates[slot % len(templates)]

		if base_kind == 'pitfall':
			templates = [
				f"Un risque classique avec {option_name} est de {pitfall_hint}.",
				f"Si {option_name} est mal utilise, on observe souvent {pitfall_hint}.",
				f"Le piege principal autour de {option_name} est {pitfall_hint}.",
			]
			return templates[slot % len(templates)]

		return f"{option_name} est lie a {descriptor}."

	def scenario_text(visual=False):
		option_descriptor = option.get('descriptor') or _concept_semantic_hint(option_name)['descriptor']
		option_purpose = _clean_hint(option.get('purpose', ''), option_descriptor)
		option_pitfall = _clean_hint(option.get('pitfall', ''), option_descriptor)
		if level_name == 'Beginner':
			title = "un atelier de cadrage"
		elif level_name == 'Intermediate':
			title = "une phase d'experimentation"
		else:
			title = "une revue pre-deploiement"

		if visual:
			templates = [
				f"Le schema illustre une decision basee sur {option_name}: les indices orientent vers {option_purpose}.",
				f"Lecture du visuel: {option_name} est mobilise pour {option_purpose} dans {module_ctx}.",
				f"Le signal visible est coherent avec {option_name}, car l'objectif est {option_purpose}.",
			]
			return templates[slot % len(templates)]

		templates = [
			f"Dans {title} de {module_ctx}, l'equipe applique {option_name} pour {option_purpose}.",
			f"En contexte reel sur {module_ctx}, {option_name} est choisi afin de {option_purpose}.",
			f"Pendant {title}, {option_name} est utile pour {option_purpose} tout en surveillant le risque de {option_pitfall}.",
		]
		return templates[slot % len(templates)]

	def concept_statement(base_kind, visual=False):
		if base_kind == 'definition':
			return _learning_statement('definition')

		if base_kind == 'purpose':
			return _learning_statement('purpose')

		if base_kind == 'pitfall':
			return _learning_statement('pitfall')

		if visual:
			templates = [
				f"Le schema met en evidence {option_name}: { _clean_hint(option.get('purpose', ''), option_name) }.",
				f"Interpretation visuelle: {option_name} est pertinent quand l'objectif est de { _clean_hint(option.get('purpose', ''), option_name) }.",
				f"L'image s'explique par {option_name}, notamment via { _clean_hint(option.get('definition', ''), option_name) }.",
			]
			return templates[slot % len(templates)]

		return _learning_statement('definition')

	if kind == 'definition':
		return concept_statement('definition')

	if kind == 'purpose':
		return concept_statement('purpose')

	if kind == 'pitfall':
		return concept_statement('pitfall')

	if kind == 'scenario':
		return scenario_text(visual=False)

	if kind == 'name_from_definition':
		descriptor = option.get('descriptor') or _concept_semantic_hint(option_name)['descriptor']
		definition_hint = _clean_hint(option.get('definition', ''), descriptor)
		templates = [
			f"{option_name}: {definition_hint}.",
			f"{option_name} correspond a {definition_hint}, avec un perimetre centré sur {descriptor}.",
			f"Le concept {option_name} se reconnait par {definition_hint}.",
			f"Quand une definition insiste sur {definition_hint}, elle renvoie a {option_name}.",
		]
		return templates[slot % len(templates)]

	if kind == 'name_from_purpose':
		descriptor = option.get('descriptor') or _concept_semantic_hint(option_name)['descriptor']
		purpose_hint = _clean_hint(option.get('purpose', ''), descriptor)
		templates = [
			f"{option_name}: objectif principal {purpose_hint}.",
			f"{option_name} est utilise pour {purpose_hint}, ce qui correspond a {descriptor}.",
			f"La finalite de {option_name} est de {purpose_hint}.",
			f"Quand l'objectif est de {purpose_hint}, {option_name} est le concept associe.",
		]
		return templates[slot % len(templates)]

	if kind == 'image_scenario':
		return scenario_text(visual=True)

	if kind == 'image_purpose':
		return concept_statement('purpose', visual=True)

	return option['definition']


def _professional_explanation(kind, concept, module_title, distractors, context):
	target = concept['name']
	alt_names = ', '.join(item['name'] for item in distractors[:3])

	if kind == 'definition':
		return (
			f"La bonne reponse est celle qui explique le role reel de {target} dans {module_title}, pas juste une definition scolaire. "
			f"Elle montre ce que ce concept permet de decider dans un contexte {context}, alors que {alt_names} restent proches mais ne couvrent pas le meme perimetre. "
			f"Le reflexe a garder: verifier ce que le concept change concretement dans la decision, pas seulement sa formulation."
		)
	if kind == 'purpose':
		return (
			f"Ici, la bonne proposition est celle qui relie {target} à un objectif utile pour l'équipe, pas à une simple idée annexe. "
			f"Les autres options peuvent sembler correctes, mais elles déplacent le focus vers des effets secondaires. "
			f"En pratique, il faut toujours se demander: est-ce que cette option aide vraiment à prendre la bonne décision métier ?"
		)
	if kind == 'pitfall':
		return (
			f"La bonne reponse pointe le piege qui fait vraiment tomber les projets autour de {target}. "
			f"Les autres risques existent, mais ils ne sont pas le point de rupture principal dans ce cas. "
			f"Bon reflexe terrain: identifier d'abord le risque qui casse la fiabilite, puis definir un garde-fou concret."
		)
	if kind == 'scenario':
		return (
			f"Ce scenario est le bon car {target} y sert de levier de decision principal dans {module_title}. "
			f"Les autres options racontent des situations possibles, mais pas celle qui fait vraiment avancer l'arbitrage. "
			f"Repere utile: dans un scenario pro, choisis l'option qui change l'action a mener, pas celle qui sonne juste en theorie."
		)
	if kind == 'name_from_definition':
		return (
			f"Le concept attendu est {target}, car la definition donnee correspond exactement a son role et a ses limites dans {module_title}. "
			f"Les autres noms representent des techniques proches, ce qui les rend plausibles, mais ils ne collent pas au perimetre precise de la definition. "
			f"Cette capacite de distinction est essentielle en certification et en pratique, car elle evite de melanger conception, optimisation et evaluation."
		)
	if kind == 'name_from_purpose':
		return (
			f"La bonne reponse est {target}: son objectif est parfaitement aligne avec le resultat operationnel attendu dans {module_title}. "
			f"Les autres options sont des concepts adjacents, donc credibles, mais leur finalite n'est pas celle decrite dans la question. "
			f"Dans un contexte entreprise, cette precision permet de mieux prioriser les efforts entre performance modele, controle du risque et impact metier."
		)
	if kind == 'image_scenario':
		return (
			f"Les indices visuels vont dans le sens de {target}: c'est la lecture qui colle le mieux a la decision a prendre. "
			f"Les autres propositions captent parfois un morceau du signal, mais pas l'image d'ensemble. "
			f"Quand tu lis un schema, cherche d'abord le signal qui explique l'action, puis elimine le reste."
		)
	return (
		f"La meilleure interpretation est celle qui relie clairement le schema au role concret de {target} dans {module_title}. "
		f"Elle permet de passer d'une observation visuelle à une décision exploitable. "
		f"Les autres options restent partielles: utiles pour comprendre, insuffisantes pour trancher proprement."
	)


def _incorrect_reason(kind):
	reasons = {
		'definition': "elle parle d'une idee proche, mais pas du concept exact demande",
		'purpose': "elle vise un objectif utile, mais pas la finalite principale de la question",
		'pitfall': "elle cite un risque reel, mais pas le plus critique a traiter en premier",
		'scenario': "le scenario est plausible, mais il ne pilote pas la decision centrale",
		'name_from_definition': "le nom semble correct, mais la definition ne colle pas completement",
		'name_from_purpose': "le concept est voisin, mais son objectif reel n'est pas celui attendu",
		'image_scenario': "la lecture visuelle est partielle et rate le signal qui fait la difference",
		'image_purpose': "l'interpretation est credible, mais pas assez solide pour guider l'action",
	}
	return reasons.get(kind, "elle reste proche du sujet mais ne repond pas precisement a la question")


def _correct_reason(kind):
	reasons = {
		'definition': "elle identifie clairement le concept et ce qu'il change dans la decision",
		'purpose': "elle pointe la vraie finalite metier, celle qui guide l'arbitrage",
		'pitfall': "elle cible le risque prioritaire, celui a neutraliser en premier",
		'scenario': "elle decrit le seul cas ou ce concept devient le levier principal",
		'name_from_definition': "la definition correspond exactement au concept attendu",
		'name_from_purpose': "l'objectif decrit est aligne avec ce concept, sans ambiguite",
		'image_scenario': "la lecture visuelle colle au signal principal observe",
		'image_purpose': "elle relie bien le visuel a la decision operationnelle attendue",
	}
	return reasons.get(kind, "elle correspond precisement au concept demande")


def _build_long_explanation(question_payload, concept_name, kind):
	choices = question_payload['choices']
	correct = question_payload['correct_answer']
	intro = question_payload['explanation']
	justification_lines = []
	for letter in LETTERS:
		choice_preview = (choices[letter] or '').strip()
		if len(choice_preview) > 110:
			choice_preview = choice_preview[:107] + '...'
		if letter == correct:
			justification_lines.append(
				f"{letter} est correcte ({choice_preview}) car {_correct_reason(kind)}."
			)
		else:
			justification_lines.append(
				f"{letter} est moins pertinente ({choice_preview}) car {_incorrect_reason(kind)}."
			)

	closing = (
		"En pratique, la bonne methode consiste a valider trois points: le role du concept, le risque principal, et l'action qui en decoule. "
		"Si ces trois elements sont alignes, la decision est generalement robuste en production. "
		"C'est exactement la logique attendue dans les certifications ML/cloud et dans les projets reels."
	)

	explanation = f"{intro} {' '.join(justification_lines)} {closing}"
	if len(explanation.split()) < 80:
		explanation = (
			explanation
			+ " Pour progresser vite, pose-toi toujours la meme grille: quel est l'objectif reel, "
			+ "quel risque on maitrise, et quelle decision devient possible ensuite."
		)
	return explanation


def _ensure_min_explanation_words(explanation, choices, correct_answer, min_words=80):
	if words_count(explanation) >= min_words:
		return explanation

	padding = (
		" Pour renforcer l'analyse, compare les quatre options selon leur perimetre conceptuel, leurs hypotheses de donnees, "
		"leurs contraintes de validation et leurs consequences en exploitation. "
		f"La reponse {correct_answer} reste la plus solide car elle aligne objectif, mecanisme et critere de decision. "
		"Les autres propositions peuvent sembler credibles, mais elles se trompent de niveau d'analyse, de contexte ou de finalite metier. "
		"En pratique, cette distinction evite les erreurs de selection de methode et limite les regressions lors du deploiement en production."
	)
	while words_count(explanation) < min_words:
		explanation += padding
	return explanation


def words_count(text):
	return len(re.findall(r'\b\w+\b', text or ''))


def _module_question_variants(category_key, level_name, module_title, concept, concepts, concept_index):
	ordered = [concept] + [item for item in concepts if item['name'] != concept['name']]
	distractors = [item for item in concepts if item['name'] != concept['name']]
	context = _context_for(concept_index + len(module_title))
	image_prompt = _question_prompt('image_scenario', concept, module_title, context, concept_index + 23)
	boundary_prompt = _question_prompt('image_purpose', concept, module_title, context, concept_index + 29)
	name_distractors = _name_distractors(category_key, level_name, concept['name'], concept_index + len(module_title))
	name_options = [concept['name']] + name_distractors
	concept_map = _concept_lookup(category_key, level_name)
	definition_distractor_names = _name_distractors(
		category_key,
		level_name,
		concept['name'],
		concept_index + len(module_title) + 11,
	)
	definition_options = [concept] + [
		concept_map.get(
			name,
			{
				'name': name,
				'definition': f"{name} est un concept utilise dans des decisions ML selon le contexte.",
				'purpose': f"{name} sert un objectif voisin a comparer avec le concept cible.",
			},
		)
		for name in definition_distractor_names
	]
	definition_distractors = definition_options[1:]
	name_option_payload = [
		concept_map.get(
			name,
			{
				'name': name,
				'definition': f"{name} est un concept de ML utilise selon le contexte de decision.",
				'purpose': f"{name} vise un objectif operationnel qu'il faut comparer au besoin de la question.",
			},
		)
		for name in name_options
	]

	variants = [
		{
			'kind': 'definition',
			'competency': 'comprehension',
			'type': 'text',
			'question': _question_prompt('definition', concept, module_title, context, concept_index + 3),
			'choices': [_choice_text('definition', concept, item, module_title, level_name, index + concept_index + 3) for index, item in enumerate(definition_options)],
			'correct_index': 0,
			'explanation': _professional_explanation('definition', concept, module_title, definition_distractors, context),
		},
		{
			'kind': 'purpose',
			'competency': 'application',
			'type': 'text',
			'question': _question_prompt('purpose', concept, module_title, context, concept_index + 7),
			'choices': [_choice_text('purpose', concept, item, module_title, level_name, index + concept_index + 7) for index, item in enumerate(ordered)],
			'correct_index': 0,
			'explanation': _professional_explanation('purpose', concept, module_title, distractors, context),
		},
		{
			'kind': 'pitfall',
			'competency': 'analysis',
			'type': 'text',
			'question': _question_prompt('pitfall', concept, module_title, context, concept_index + 11),
			'choices': [_choice_text('pitfall', concept, item, module_title, level_name, index + concept_index + 11) for index, item in enumerate(ordered)],
			'correct_index': 0,
			'explanation': _professional_explanation('pitfall', concept, module_title, distractors, context),
		},
		{
			'kind': 'scenario',
			'competency': 'application',
			'type': 'text',
			'question': _question_prompt('scenario', concept, module_title, context, concept_index + 13),
			'choices': [_choice_text('scenario', concept, item, module_title, level_name, index + concept_index + 13) for index, item in enumerate(ordered)],
			'correct_index': 0,
			'explanation': _professional_explanation('scenario', concept, module_title, distractors, context),
		},
		{
			'kind': 'name_from_definition',
			'competency': 'comprehension',
			'type': 'text',
			'question': _question_prompt('name_from_definition', concept, module_title, context, concept_index + 17),
			'choices': [_choice_text('name_from_definition', concept, item, module_title, level_name, index + concept_index + 17) for index, item in enumerate(name_option_payload)],
			'correct_index': 0,
			'explanation': _professional_explanation('name_from_definition', concept, module_title, distractors, context),
		},
		{
			'kind': 'name_from_purpose',
			'competency': 'analysis',
			'type': 'text',
			'question': _question_prompt('name_from_purpose', concept, module_title, context, concept_index + 19),
			'choices': [_choice_text('name_from_purpose', concept, item, module_title, level_name, index + concept_index + 19) for index, item in enumerate(name_option_payload)],
			'correct_index': 0,
			'explanation': _professional_explanation('name_from_purpose', concept, module_title, distractors, context),
		},
		{
			'kind': 'image_scenario',
			'competency': 'expertise',
			'type': 'image',
			'question': image_prompt,
			'image_url': _image_name(category_key, module_title, concept['name'], 1),
			'choices': [_choice_text('image_scenario', concept, item, module_title, level_name, index + concept_index + 23) for index, item in enumerate(ordered)],
			'correct_index': 0,
			'explanation': _professional_explanation('image_scenario', concept, module_title, distractors, context),
		},
		{
			'kind': 'image_purpose',
			'competency': 'application',
			'type': 'image',
			'question': boundary_prompt,
			'image_url': _image_name(category_key, module_title, concept['name'], 2),
			'choices': [_choice_text('image_purpose', concept, item, module_title, level_name, index + concept_index + 29) for index, item in enumerate(ordered)],
			'correct_index': 0,
			'explanation': _professional_explanation('image_purpose', concept, module_title, distractors, context),
		},
	]

	questions = []
	for variant_index, variant in enumerate(variants):
		rotated_choices, answer = _rotate_choices(variant['choices'], variant['correct_index'], concept_index + variant_index)
		question_payload = {
			'type': variant['type'],
			'question': variant['question'],
			'image_url': variant.get('image_url'),
			'competency': variant['competency'],
			'kind': variant['kind'],
			'choices': {
				'A': rotated_choices[0],
				'B': rotated_choices[1],
				'C': rotated_choices[2],
				'D': rotated_choices[3],
			},
			'correct_answer': answer,
			'explanation': '',
		}
		question_payload['explanation'] = _build_long_explanation(
			{
				'choices': question_payload['choices'],
				'correct_answer': question_payload['correct_answer'],
				'explanation': variant['explanation'],
			},
			concept['name'],
			variant['kind'],
		)
		question_payload['explanation'] = _ensure_min_explanation_words(
			question_payload['explanation'],
			question_payload['choices'],
			question_payload['correct_answer'],
		)
		questions.append(question_payload)
	return questions


def _select_priority_mix(question_pool, question_count):
	target_counts = {
		'comprehension': max(1, int(question_count * 0.4)),
		'application': max(1, int(question_count * 0.3)),
		'analysis': max(1, int(question_count * 0.2)),
		'expertise': max(1, question_count - (int(question_count * 0.4) + int(question_count * 0.3) + int(question_count * 0.2))),
	}

	buckets = {'comprehension': [], 'application': [], 'analysis': [], 'expertise': []}
	for question in question_pool:
		buckets.get(question.get('competency', 'comprehension'), buckets['comprehension']).append(question)

	selected = []
	for competency in ['comprehension', 'application', 'analysis', 'expertise']:
		selected.extend(buckets[competency][:target_counts[competency]])

	if len(selected) < question_count:
		remaining = [question for question in question_pool if question not in selected]
		selected.extend(remaining[: question_count - len(selected)])

	return selected[:question_count]


def _stable_question_rank(question):
	text = question.get('question', '') + '|' + question.get('type', 'text')
	return sum((index + 1) * ord(char) for index, char in enumerate(text))


def build_module_quiz(category_key, level_name, module_name):
	category_key = _normalize_category_key(category_key)
	if category_key not in MODULE_LIBRARY:
		available = ', '.join(supported_category_keys())
		raise ValueError(f'Unsupported category key: {category_key}. Available: {available}')
	if level_name not in MODULE_LIBRARY[category_key]['levels']:
		available = ', '.join(MODULE_LIBRARY[category_key]['levels'].keys())
		raise ValueError(f'Unsupported level: {level_name}. Available: {available}')

	modules = _build_modules(category_key, level_name)
	module_lookup = {module['title']: (index + 1, module) for index, module in enumerate(modules)}
	if module_name not in module_lookup:
		available = ', '.join(module_lookup.keys())
		raise ValueError(f'Unsupported module: {module_name}. Available: {available}')

	module_number, module = module_lookup[module_name]
	question_count = _module_question_count(level_name, module_number)
	question_pool = []
	for variant_index in range(8):
		for concept_index, concept in enumerate(module['concepts']):
			question_pool.append(
				_module_question_variants(category_key, level_name, module_name, concept, module['concepts'], concept_index)[variant_index]
			)

	if _is_certification_priority(category_key, level_name, module_name):
		selected_questions = _select_priority_mix(question_pool, question_count)
	else:
		mixed_pool = sorted(question_pool, key=_stable_question_rank)
		selected_questions = mixed_pool[:question_count]
	minimum_image_count = max(2, (question_count + 4) // 5)
	current_image_count = sum(1 for question in selected_questions if question['type'] == 'image')
	if current_image_count < minimum_image_count:
		image_reserve = [question for question in question_pool if question['type'] == 'image' and question not in selected_questions]
		for replacement in image_reserve:
			for index in range(len(selected_questions) - 1, -1, -1):
				if selected_questions[index]['type'] == 'text':
					selected_questions[index] = replacement
					current_image_count += 1
					break
			if current_image_count >= minimum_image_count:
				break

	difficulty_sequence = _module_difficulty_sequence(level_name, question_count)
	for index, question in enumerate(selected_questions):
		question['difficulty'] = difficulty_sequence[index]
		if question['type'] == 'text':
			question['image_url'] = None
		question['question'] = _polish_french_text(question['question'])
		question['choices'] = {
			letter: _polish_french_text(choice_text)
			for letter, choice_text in question['choices'].items()
		}
		question['explanation'] = _polish_french_text(question['explanation'])
		question.pop('competency', None)
		question.pop('kind', None)

	image_count = sum(1 for question in selected_questions if question['type'] == 'image')
	if image_count < minimum_image_count:
		raise ValueError('Generated quiz does not satisfy the minimum image question ratio.')

	return {
		'category': MODULE_LIBRARY[category_key]['category'],
		'level': level_name,
		'module': module_name,
		'questions': selected_questions,
	}


def module_quiz_to_json(category_key, level_name, module_name):
	return json.dumps(build_module_quiz(category_key, level_name, module_name), indent=2)


def write_module_quiz(output_path, category_key, level_name, module_name):
	output = Path(output_path)
	output.parent.mkdir(parents=True, exist_ok=True)
	output.write_text(module_quiz_to_json(category_key, level_name, module_name), encoding='utf-8')
	return output


def write_all_module_quizzes(output_dir):
	output_root = Path(output_dir)
	generated_files = []
	for category_key, level_name, module_name in iter_module_targets():
		file_name = f"{slugify(module_name)}.json"
		file_path = output_root / category_key / slugify(level_name) / file_name
		generated_files.append(write_module_quiz(file_path, category_key, level_name, module_name))
	return generated_files


def _legacy_question_from_module_question(module_question):
	return {
		'question': module_question['question'],
		'choices': [
			module_question['choices']['A'],
			module_question['choices']['B'],
			module_question['choices']['C'],
			module_question['choices']['D'],
		],
		'answer': module_question['correct_answer'],
		'difficulty': module_question['difficulty'],
	}


def build_dataset(category_key='apprentissage-supervise'):
	category_key = _normalize_category_key(category_key)
	if category_key not in MODULE_LIBRARY:
		available = ', '.join(supported_category_keys())
		raise ValueError(f'Unsupported category key: {category_key}. Available: {available}')

	category = MODULE_LIBRARY[category_key]
	payload = {
		'category': category['category'],
		'levels': [],
	}

	for level_name in LEVEL_SPECS.keys():
		level_payload = {'name': level_name, 'modules': []}
		for module_number, module_title in enumerate(supported_modules(category_key, level_name), start=1):
			module_quiz = build_module_quiz(category_key, level_name, module_title)
			legacy_questions = []
			for question in module_quiz['questions']:
				legacy_question = _legacy_question_from_module_question(question)
				legacy_question['difficulty'] = LEVEL_SPECS[level_name]['difficulty']
				legacy_questions.append(legacy_question)
			level_payload['modules'].append(
				{
					'module_number': module_number,
					'questions': legacy_questions,
				}
			)
		payload['levels'].append(level_payload)

	return payload


def dataset_to_json(category_key='apprentissage-supervise'):
	return json.dumps(build_dataset(category_key), indent=2)


def write_dataset(output_path, category_key='apprentissage-supervise'):
	output = Path(output_path)
	output.parent.mkdir(parents=True, exist_ok=True)
	output.write_text(dataset_to_json(category_key), encoding='utf-8')
	return output
