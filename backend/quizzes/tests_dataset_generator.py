import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import SimpleTestCase

from .dataset_generator import build_dataset, build_module_quiz, supported_category_keys


class DatasetGeneratorTests(SimpleTestCase):
	def test_build_dataset_matches_required_structure(self):
		dataset = build_dataset('apprentissage-supervise')

		self.assertEqual(dataset['category'], 'Apprentissage supervise')
		self.assertEqual([level['name'] for level in dataset['levels']], ['Beginner', 'Intermediate', 'Advanced'])

		expected_counts = {
			'Beginner': [10, 11, 12, 13, 15],
			'Intermediate': [12, 14, 15, 16, 18, 20, 22],
			'Advanced': [15, 17, 18, 20, 22, 24, 26, 28, 30, 32],
		}
		expected_difficulty = {
			'Beginner': 'easy',
			'Intermediate': 'medium',
			'Advanced': 'hard',
		}

		for level in dataset['levels']:
			self.assertEqual(len(level['modules']), len(expected_counts[level['name']]))
			for module, expected_count in zip(level['modules'], expected_counts[level['name']]):
				self.assertGreaterEqual(len(module['questions']), 10)
				self.assertEqual(len(module['questions']), expected_count)
				for question in module['questions']:
					self.assertEqual(len(question['choices']), 4)
					self.assertIn(question['answer'], ['A', 'B', 'C', 'D'])
					self.assertEqual(question['difficulty'], expected_difficulty[level['name']])

	def test_supported_categories_match_ml360_scope(self):
		self.assertEqual(
			supported_category_keys(),
			[
				'apprentissage-non-supervise',
				'apprentissage-par-renforcement',
				'apprentissage-semi-supervise',
				'apprentissage-supervise',
			],
		)
		self.assertEqual(build_dataset('reinforcement-learning')['category'], 'Apprentissage par renforcement')

	def test_management_command_writes_strict_json(self):
		with TemporaryDirectory() as temp_dir:
			output_path = Path(temp_dir) / 'apprentissage-supervise.json'
			call_command('generate_ml360_dataset', '--category', 'apprentissage-supervise', '--output', str(output_path))

			self.assertTrue(output_path.exists())
			payload = json.loads(output_path.read_text(encoding='utf-8'))
			self.assertEqual(payload['category'], 'Apprentissage supervise')
			self.assertEqual(len(payload['levels']), 3)

	def test_build_module_quiz_matches_strict_json_contract(self):
		payload = build_module_quiz('apprentissage-supervise', 'Beginner', 'Fondamentaux du supervise')

		self.assertEqual(payload['category'], 'Apprentissage supervise')
		self.assertEqual(payload['level'], 'Beginner')
		self.assertEqual(payload['module'], 'Fondamentaux du supervise')
		self.assertEqual(len(payload['questions']), 10)

		image_questions = [question for question in payload['questions'] if question['type'] == 'image']
		self.assertGreaterEqual(len(image_questions), 2)

		for question in payload['questions']:
			self.assertIn(question['type'], ['text', 'image'])
			self.assertEqual(sorted(question['choices'].keys()), ['A', 'B', 'C', 'D'])
			self.assertIn(question['correct_answer'], ['A', 'B', 'C', 'D'])
			self.assertIn(question['difficulty'], ['easy', 'medium', 'hard'])
			self.assertTrue(question['explanation'])
			if question['type'] == 'image':
				self.assertIsNotNone(question['image_url'])
			else:
				self.assertIsNone(question['image_url'])

	def test_module_quiz_command_writes_json(self):
		with TemporaryDirectory() as temp_dir:
			output_path = Path(temp_dir) / 'fondamentaux-du-supervise.json'
			call_command(
				'generate_ml360_module_quiz',
				'--category',
				'apprentissage-supervise',
				'--level',
				'Beginner',
				'--module',
				'Fondamentaux du supervise',
				'--output',
				str(output_path),
			)

			self.assertTrue(output_path.exists())
			payload = json.loads(output_path.read_text(encoding='utf-8'))
			self.assertEqual(payload['module'], 'Fondamentaux du supervise')
			self.assertEqual(payload['level'], 'Beginner')

	def test_all_module_quiz_command_writes_full_tree(self):
		with TemporaryDirectory() as temp_dir:
			call_command('generate_ml360_all_module_quizzes', '--output-dir', temp_dir)

			generated_files = list(Path(temp_dir).rglob('*.json'))
			self.assertEqual(len(generated_files), 88)
			self.assertTrue(
				(Path(temp_dir) / 'apprentissage-supervise' / 'beginner' / 'fondamentaux-du-supervise.json').exists()
			)