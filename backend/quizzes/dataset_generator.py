import json
from pathlib import Path

from django.utils.text import slugify


LETTERS = ['A', 'B', 'C', 'D']

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
	if level_name == 'Beginner':
		definition = f"{concept_name} is a foundational idea in {category_name.lower()} used to understand {module_title.lower()}."
		purpose = f"It helps learners identify the basic role of {concept_name} before using more advanced workflows."
		pitfall = f"A common mistake is to use {concept_name} without first checking the basic assumptions of {module_title.lower()}."
		scenario = f"A beginner studies {module_title.lower()} and uses {concept_name} to explain a simple learning example."
	elif level_name == 'Intermediate':
		definition = f"{concept_name} is applied in {category_name.lower()} to reason about model behavior inside {module_title.lower()}."
		purpose = f"It supports practical decision-making, comparison of methods, and better reasoning during implementation."
		pitfall = f"A common mistake is to apply {concept_name} mechanically without validating whether it improves the workflow."
		scenario = f"A practitioner adjusts {concept_name} while improving a {category_name.lower()} pipeline built around {module_title.lower()}."
	else:
		definition = f"{concept_name} is an advanced lever in {category_name.lower()} for solving real-world problems linked to {module_title.lower()}."
		purpose = f"It supports production-grade decisions, optimization, and problem solving under realistic constraints."
		pitfall = f"A common mistake is to optimize {concept_name} locally while ignoring deployment, drift, cost, or safety impacts."
		scenario = f"A production team uses {concept_name} to solve a high-stakes {category_name.lower()} challenge connected to {module_title.lower()}."

	return {
		'name': concept_name,
		'definition': definition,
		'purpose': purpose,
		'pitfall': pitfall,
		'scenario': scenario,
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
		'Intermediate': [15, 16, 17, 18, 20, 21, 22],
		'Advanced': [20, 21, 22, 23, 24, 26, 27, 28, 29, 30],
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


def _module_question_variants(category_key, level_name, module_title, concept, concepts, concept_index):
	ordered = [concept] + [item for item in concepts if item['name'] != concept['name']]
	image_prompt = f"Which interpretation best matches the ML diagram for {concept['name']} in {module_title}?"
	boundary_prompt = f"A diagram highlights behavior around {concept['name']}. Which statement is the best interpretation?"

	variants = [
		{
			'type': 'text',
			'question': f"In the module '{module_title}', which statement best defines {concept['name']}?",
			'choices': [item['definition'] for item in ordered],
			'correct_index': 0,
			'explanation': f"{concept['name']} is correctly defined by the first option because it captures the core idea used in {module_title.lower()}.",
		},
		{
			'type': 'text',
			'question': f"Why is {concept['name']} important in this module?",
			'choices': [item['purpose'] for item in ordered],
			'correct_index': 0,
			'explanation': f"The correct answer explains the main learning objective behind {concept['name']} in this module.",
		},
		{
			'type': 'text',
			'question': f"Which risk is most directly associated with {concept['name']}?",
			'choices': [item['pitfall'] for item in ordered],
			'correct_index': 0,
			'explanation': f"The first option is correct because it identifies the most common misuse or failure mode tied to {concept['name']}.",
		},
		{
			'type': 'text',
			'question': f"Which scenario best illustrates {concept['name']}?",
			'choices': [item['scenario'] for item in ordered],
			'correct_index': 0,
			'explanation': f"The correct scenario is the one that directly demonstrates how {concept['name']} appears in practice.",
		},
		{
			'type': 'text',
			'question': f"Which concept matches this description: {concept['definition']}",
			'choices': [item['name'] for item in ordered],
			'correct_index': 0,
			'explanation': f"Only {concept['name']} matches that description exactly inside this module.",
		},
		{
			'type': 'text',
			'question': f"Which concept is most closely linked to this goal: {concept['purpose']}",
			'choices': [item['name'] for item in ordered],
			'correct_index': 0,
			'explanation': f"The purpose stated belongs to {concept['name']}, not to the alternative concepts.",
		},
		{
			'type': 'image',
			'question': image_prompt,
			'image_url': _image_name(category_key, module_title, concept['name'], 1),
			'choices': [item['scenario'] for item in ordered],
			'correct_index': 0,
			'explanation': f"The image placeholder represents a realistic ML diagram where the first option best matches {concept['name']}.",
		},
		{
			'type': 'image',
			'question': boundary_prompt,
			'image_url': _image_name(category_key, module_title, concept['name'], 2),
			'choices': [item['purpose'] for item in ordered],
			'correct_index': 0,
			'explanation': f"The correct interpretation links the diagram to the actual role of {concept['name']} in model behavior.",
		},
	]

	questions = []
	for variant_index, variant in enumerate(variants):
		rotated_choices, answer = _rotate_choices(variant['choices'], variant['correct_index'], concept_index + variant_index)
		question_payload = {
			'type': variant['type'],
			'question': variant['question'],
			'image_url': variant.get('image_url'),
			'choices': {
				'A': rotated_choices[0],
				'B': rotated_choices[1],
				'C': rotated_choices[2],
				'D': rotated_choices[3],
			},
			'correct_answer': answer,
			'explanation': variant['explanation'],
		}
		questions.append(question_payload)
	return questions


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

	override_key = (category_key, level_name, module_name)
	if override_key in REFINED_MODULE_QUIZZES:
		questions = []
		for question in REFINED_MODULE_QUIZZES[override_key]:
			questions.append(dict(question))
		difficulty_sequence = _module_difficulty_sequence(level_name, len(questions))
		for index, question in enumerate(questions):
			question['difficulty'] = question.get('difficulty', difficulty_sequence[index])
			if question['type'] == 'text':
				question['image_url'] = None
		return {
			'category': MODULE_LIBRARY[category_key]['category'],
			'level': level_name,
			'module': module_name,
			'questions': questions,
		}

	module_number, module = module_lookup[module_name]
	question_count = _module_question_count(level_name, module_number)
	question_pool = []
	for variant_index in range(8):
		for concept_index, concept in enumerate(module['concepts']):
			question_pool.append(
				_module_question_variants(category_key, level_name, module_name, concept, module['concepts'], concept_index)[variant_index]
			)

	selected_questions = question_pool[:question_count]
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


def _rotate_choices(choices, correct_index, seed):
    shift = seed % len(choices)
    rotated_indices = list(range(len(choices)))[shift:] + list(range(len(choices)))[:shift]
    rotated_choices = [choices[index] for index in rotated_indices]
    new_correct_index = rotated_indices.index(correct_index)
    return rotated_choices, LETTERS[new_correct_index]


def _question_variants(module_title, concept, concepts, difficulty, concept_index):
    ordered = [concept] + [item for item in concepts if item['name'] != concept['name']]

    variants = [
        (
            f"In the module '{module_title}', which statement best defines {concept['name']}?",
            [item['definition'] for item in ordered],
            0,
        ),
        (
            f"Why is {concept['name']} important in this module?",
            [item['purpose'] for item in ordered],
            0,
        ),
        (
            f"Which risk is most directly associated with {concept['name']}?",
            [item['pitfall'] for item in ordered],
            0,
        ),
        (
            f"Which scenario best illustrates {concept['name']}?",
            [item['scenario'] for item in ordered],
            0,
        ),
        (
            f"Which concept matches this description: {concept['definition']}",
            [item['name'] for item in ordered],
            0,
        ),
        (
            f"Which concept is most closely linked to this goal: {concept['purpose']}",
            [item['name'] for item in ordered],
            0,
        ),
        (
            f"A team wants to avoid this mistake: {concept['pitfall']} Which concept should they review first?",
            [item['name'] for item in ordered],
            0,
        ),
        (
            f"Which concept best fits this situation: {concept['scenario']}",
            [item['name'] for item in ordered],
            0,
        ),
    ]

    questions = []
    for variant_index, (question_text, choices, correct_index) in enumerate(variants):
        rotated_choices, answer = _rotate_choices(choices, correct_index, concept_index + variant_index)
        questions.append(
            {
                'question': question_text,
                'choices': rotated_choices,
                'answer': answer,
                'difficulty': difficulty,
            }
        )
    return questions


def _build_module_questions(module_title, concepts, target_count, difficulty):
    question_pool = []
    for variant_index in range(8):
        for concept_index, concept in enumerate(concepts):
            question_pool.append(
                _question_variants(module_title, concept, concepts, difficulty, concept_index)[variant_index]
            )
    return question_pool[:target_count]


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

	for level_name, level_spec in LEVEL_SPECS.items():
		modules = _build_modules(category_key, level_name)
		level_payload = {'name': level_name, 'modules': []}
		for module_number, (module, question_count) in enumerate(zip(modules, level_spec['question_counts']), start=1):
			level_payload['modules'].append(
				{
					'module_number': module_number,
					'questions': _build_module_questions(
						module['title'],
						module['concepts'],
						question_count,
						level_spec['difficulty'],
					),
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
