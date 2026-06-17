from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Choice, Level, Question, Quiz


class QuizApiTests(APITestCase):
	def setUp(self):
		self.category, _ = Category.objects.update_or_create(
			slug='apprentissage-supervise',
			defaults={
				'title': 'Apprentissage supervise',
				'description': 'Modeles entraines avec donnees etiquetees.',
			},
		)
		self.level, _ = Level.objects.update_or_create(
			category=self.category,
			order=1,
			defaults={
				'title': 'Niveau 1',
				'slug': 'niveau-1',
				'objective': 'Apprentissage',
			},
		)
		self.quiz = Quiz.objects.create(
			title='Bases du supervise',
			slug='bases-du-supervise',
			category=self.category,
			level=self.level,
			description='Quiz d introduction au machine learning supervise.',
		)
		question = Question.objects.create(
			quiz=self.quiz,
			prompt='Quel algorithme est generalement utilise pour une classification binaire ?',
			explanation='La regression logistique est une reference classique pour la classification binaire.',
			order=1,
		)
		self.correct_choice = Choice.objects.create(
			question=question,
			label='Regression logistique',
			is_correct=True,
			order=1,
		)
		Choice.objects.create(
			question=question,
			label='K-means',
			is_correct=False,
			order=2,
		)

	def test_category_list(self):
		response = self.client.get(reverse('category-list'))
		category_slugs = {item['slug'] for item in response.data}
		supervised = next(item for item in response.data if item['slug'] == 'apprentissage-supervise')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('apprentissage-supervise', category_slugs)
		self.assertIn('apprentissage-non-supervise', category_slugs)
		self.assertEqual(supervised['quizzes_count'], 1)
		self.assertEqual(len(supervised['levels']), 4)
		self.assertEqual(supervised['levels'][0]['title'], 'Niveau 1')
		self.assertEqual(supervised['levels'][0]['objective'], 'Apprentissage')

	def test_quiz_detail_hides_answers(self):
		response = self.client.get(reverse('quiz-detail', kwargs={'slug': self.quiz.slug}))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['level']['title'], 'Niveau 1')
		self.assertNotIn('is_correct', response.data['questions'][0]['choices'][0])

	def test_quiz_submission_scores_answers(self):
		question = self.quiz.questions.get()

		response = self.client.post(
			reverse('quiz-submit', kwargs={'slug': self.quiz.slug}),
			{
				'answers': [
					{
						'question_id': question.id,
						'choice_id': self.correct_choice.id,
					}
				]
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['score'], 1)
		self.assertEqual(response.data['percentage'], 100.0)
