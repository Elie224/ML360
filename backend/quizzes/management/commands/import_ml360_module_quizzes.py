import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from quizzes.models import Category, Choice, Level, Question, Quiz


LEVEL_ORDER_MAP = {
	'Beginner': (1, 'Apprentissage'),
	'Intermediate': (2, 'Consolidation'),
	'Advanced': (3, 'Maitrise'),
}

OPTION_LETTERS = ('A', 'B', 'C', 'D')
VALIDATION_MODES = ('strict', 'warn')


def _norm_text(value):
	text = str(value or '').lower().strip()
	text = text.encode('ascii', 'ignore').decode('ascii')
	text = re.sub(r'[^a-z0-9]+', ' ', text)
	return text.strip()


def _iter_json_files(input_path):
	path = Path(input_path)
	if not path.exists():
		raise CommandError(f'Input path does not exist: {input_path}')
	if path.is_file():
		return [path]
	return sorted(candidate for candidate in path.rglob('*.json') if candidate.is_file())


def _load_module_payload(file_path):
	payload = json.loads(file_path.read_text(encoding='utf-8'))
	if not {'category', 'level', 'module', 'questions'}.issubset(payload.keys()):
		raise CommandError(f'Unsupported JSON structure in {file_path}')
	return payload


def _collect_payload_schema_errors(file_path, payload):
	errors = []

	if payload.get('level') not in LEVEL_ORDER_MAP:
		available = ', '.join(LEVEL_ORDER_MAP.keys())
		errors.append(f'Unsupported level label in {file_path}: {payload.get("level")}. Available: {available}')

	if not isinstance(payload.get('questions'), list) or not payload['questions']:
		errors.append(f'Questions must be a non-empty list in {file_path}')
		return errors

	seen_module_prompts = {}
	for idx, question_data in enumerate(payload['questions'], start=1):
		prompt = str(question_data.get('question', '')).strip()
		if not prompt:
			errors.append(f'Missing question prompt in {file_path} (question #{idx})')
			continue

		norm_prompt = _norm_text(prompt)
		if norm_prompt in seen_module_prompts:
			errors.append(
				f'Duplicate question prompt in same module file {file_path}: '
				f'question #{idx} duplicates question #{seen_module_prompts[norm_prompt]}'
			)
		seen_module_prompts[norm_prompt] = idx

		choices = question_data.get('choices')
		if not isinstance(choices, dict):
			errors.append(f'Choices must be an object in {file_path} (question #{idx})')
			continue

		missing = [letter for letter in OPTION_LETTERS if letter not in choices]
		if missing:
			errors.append(f'Missing choices {missing} in {file_path} (question #{idx})')

		correct_answer = question_data.get('correct_answer')
		if correct_answer not in OPTION_LETTERS:
			errors.append(f'Invalid correct_answer in {file_path} (question #{idx}): {correct_answer}')

		explanation = str(question_data.get('explanation', '')).lower()
		mentions_first_option = re.search(r'first option|premiere option|premier choix', explanation) is not None
		if mentions_first_option and correct_answer != 'A':
			errors.append(
				f'Explanation/correct_answer conflict in {file_path} (question #{idx}): '
				'Explanation says first option but correct_answer is not A'
			)

	return errors


def _collect_cross_file_duplicate_errors(file_payload_pairs):
	errors = []
	by_category_level = {}
	by_category = {}

	for file_path, payload in file_payload_pairs:
		category = str(payload.get('category', ''))
		level = str(payload.get('level', ''))
		module = str(payload.get('module', ''))

		for idx, question_data in enumerate(payload.get('questions', []), start=1):
			norm_prompt = _norm_text(question_data.get('question', ''))
			if not norm_prompt:
				continue

			cat_level_key = (category, level, norm_prompt)
			if cat_level_key not in by_category_level:
				by_category_level[cat_level_key] = []
			by_category_level[cat_level_key].append((module, file_path, idx))

			category_key = (category, norm_prompt)
			if category_key not in by_category:
				by_category[category_key] = []
			by_category[category_key].append((level, module, file_path, idx))

	for (category, level, _), occurrences in by_category_level.items():
		modules = {module for module, _, _ in occurrences}
		if len(occurrences) > 1 and len(modules) > 1:
			sample = '; '.join([f'{module}#{idx}' for module, _, idx in occurrences[:3]])
			errors.append(
				f'Duplicate question prompt across modules in category/level {category} / {level}: {sample}'
			)

	for (category, _), occurrences in by_category.items():
		scopes = {(level, module) for level, module, _, _ in occurrences}
		if len(occurrences) > 1 and len(scopes) > 1:
			sample = '; '.join([f'{level}/{module}#{idx}' for level, module, _, idx in occurrences[:3]])
			errors.append(
				f'Duplicate question prompt across category {category} (different modules/levels): {sample}'
			)

	return errors


def _enforce_validation_mode(errors, validation_mode, stdout):
	if not errors:
		return

	if validation_mode == 'strict':
		first = errors[0]
		extra = len(errors) - 1
		suffix = f' (+{extra} more)' if extra > 0 else ''
		raise CommandError(f'{first}{suffix}')

	stdout.write('Validation warnings detected (warning mode, import continues):')
	for msg in errors:
		stdout.write(f' - {msg}')


def _resolve_category(payload):
	category_title = payload['category']
	category_slug = slugify(category_title)
	category, _ = Category.objects.update_or_create(
		slug=category_slug,
		defaults={
			'title': category_title,
			'description': f"Categorie importee depuis un quiz JSON ML360 pour {category_title}.",
		},
	)
	return category


def _resolve_level(category, level_name):
	if level_name not in LEVEL_ORDER_MAP:
		available = ', '.join(LEVEL_ORDER_MAP.keys())
		raise CommandError(f'Unsupported level label: {level_name}. Available: {available}')
	order, objective = LEVEL_ORDER_MAP[level_name]
	level = Level.objects.filter(category=category, order=order).first()
	if level is not None:
		return level
	return Level.objects.create(
		category=category,
		title=level_name,
		slug=slugify(level_name),
		objective=objective,
		order=order,
	)


@transaction.atomic
def _import_module_payload(payload, publish=True):
	category = _resolve_category(payload)
	level = _resolve_level(category, payload['level'])
	quiz_slug = slugify(f"{category.slug}-{payload['level']}-{payload['module']}")
	quiz, _ = Quiz.objects.update_or_create(
		slug=quiz_slug,
		defaults={
			'title': payload['module'],
			'category': category,
			'level': level,
			'source_level_name': payload['level'],
			'description': f"Quiz importe pour le module {payload['module']} de la categorie {payload['category']}.",
			'is_published': publish,
		},
	)

	quiz.questions.all().delete()

	for question_order, question_data in enumerate(payload['questions'], start=1):
		question = Question.objects.create(
			quiz=quiz,
			prompt=question_data['question'],
			explanation=question_data.get('explanation', ''),
			order=question_order,
			question_type=Question.QuestionType.SINGLE_CHOICE,
			presentation_type=question_data.get('type', Question.PresentationType.TEXT),
			image_url=question_data.get('image_url') or '',
			difficulty=question_data.get('difficulty', Question.Difficulty.EASY),
		)
		correct_answer = question_data['correct_answer']
		for choice_order, letter in enumerate(OPTION_LETTERS, start=1):
			Choice.objects.create(
				question=question,
				label=question_data['choices'][letter],
				is_correct=letter == correct_answer,
				order=choice_order,
			)

	return quiz


class Command(BaseCommand):
	help = 'Import ML360 module quiz JSON files into the database using the Django ORM.'

	def add_arguments(self, parser):
		parser.add_argument('--input', required=True, help='Path to one module quiz JSON file or a directory containing many JSON files.')
		parser.add_argument('--unpublished', action='store_true', help='Import quizzes as unpublished.')
		parser.add_argument(
			'--validation-mode',
			default='strict',
			choices=VALIDATION_MODES,
			help='Validation behavior: strict blocks import, warn logs warnings and continues.',
		)

	def handle(self, *args, **options):
		json_files = _iter_json_files(options['input'])
		validation_mode = options['validation_mode']
		validation_errors = []
		file_payload_pairs = []
		for file_path in json_files:
			payload = _load_module_payload(file_path)
			validation_errors.extend(_collect_payload_schema_errors(file_path, payload))
			file_payload_pairs.append((file_path, payload))

		validation_errors.extend(_collect_cross_file_duplicate_errors(file_payload_pairs))
		_enforce_validation_mode(validation_errors, validation_mode, self.stdout)

		imported = 0
		for file_path, payload in file_payload_pairs:
			_import_module_payload(payload, publish=not options['unpublished'])
			imported += 1

		self.stdout.write(self.style.SUCCESS(f'Imported {imported} module quiz file(s).'))