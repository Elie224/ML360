import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from .models import Choice, Question, Quiz


class ImportModuleQuizTests(TestCase):
	def test_import_module_quiz_file_creates_quiz_questions_and_choices(self):
		with TemporaryDirectory() as temp_dir:
			json_path = Path(temp_dir) / 'fondamentaux-du-supervise.json'
			call_command(
				'generate_ml360_module_quiz',
				'--category',
				'apprentissage-supervise',
				'--level',
				'Beginner',
				'--module',
				'Fondamentaux du supervise',
				'--output',
				str(json_path),
			)

			call_command('import_ml360_module_quizzes', '--input', str(json_path))

			quiz = Quiz.objects.get(title='Fondamentaux du supervise')
			self.assertEqual(quiz.source_level_name, 'Beginner')
			self.assertEqual(quiz.questions.count(), 10)
			self.assertEqual(Choice.objects.count(), 40)
			self.assertGreaterEqual(quiz.questions.filter(presentation_type='image').count(), 2)
			self.assertEqual(quiz.questions.filter(difficulty='hard').count(), 1)

	def test_import_is_idempotent_for_same_file(self):
		with TemporaryDirectory() as temp_dir:
			json_path = Path(temp_dir) / 'fondamentaux-du-supervise.json'
			call_command(
				'generate_ml360_module_quiz',
				'--category',
				'apprentissage-supervise',
				'--level',
				'Beginner',
				'--module',
				'Fondamentaux du supervise',
				'--output',
				str(json_path),
			)

			call_command('import_ml360_module_quizzes', '--input', str(json_path))
			call_command('import_ml360_module_quizzes', '--input', str(json_path))

			self.assertEqual(Quiz.objects.filter(title='Fondamentaux du supervise').count(), 1)
			self.assertEqual(Question.objects.count(), 10)
			self.assertEqual(Choice.objects.count(), 40)