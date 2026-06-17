from django.db.models import Count, Prefetch, Q
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Choice, Question, Quiz
from .serializers import (
	AnswerSubmissionSerializer,
	CategorySerializer,
	QuizDetailSerializer,
	QuizListSerializer,
)


class HealthCheckAPIView(APIView):
	def get(self, request):
		return Response({'status': 'ok', 'service': 'ML360 API'})


class CategoryListAPIView(generics.ListAPIView):
	serializer_class = CategorySerializer

	def get_queryset(self):
		return Category.objects.prefetch_related('levels').annotate(
			quizzes_count=Count('quizzes', filter=Q(quizzes__is_published=True), distinct=True)
		)


class QuizListAPIView(generics.ListAPIView):
	serializer_class = QuizListSerializer

	def get_queryset(self):
		queryset = (
			Quiz.objects.filter(is_published=True)
			.select_related('category', 'level')
			.annotate(question_count=Count('questions', distinct=True))
		)

		category_slug = self.request.query_params.get('category')
		if category_slug:
			queryset = queryset.filter(category__slug=category_slug)

		level_slug = self.request.query_params.get('level')
		if level_slug:
			queryset = queryset.filter(level__slug=level_slug)

		return queryset


class QuizDetailAPIView(generics.RetrieveAPIView):
	serializer_class = QuizDetailSerializer
	lookup_field = 'slug'

	def get_queryset(self):
		return (
			Quiz.objects.filter(is_published=True)
			.select_related('category', 'level')
			.prefetch_related(
				Prefetch(
					'questions',
					queryset=Question.objects.order_by('order').prefetch_related(
						Prefetch('choices', queryset=Choice.objects.order_by('order'))
					),
				)
			)
		)


class QuizSubmitAPIView(APIView):
	def post(self, request, slug):
		quiz = (
			Quiz.objects.filter(slug=slug, is_published=True)
			.select_related('category', 'level')
			.prefetch_related(
				Prefetch(
					'questions',
					queryset=Question.objects.order_by('order').prefetch_related(
						Prefetch('choices', queryset=Choice.objects.order_by('order'))
					),
				)
			)
			.first()
		)
		if quiz is None:
			raise serializers.ValidationError({'quiz': 'Quiz introuvable.'})

		serializer = AnswerSubmissionSerializer(data=request.data, context={'quiz': quiz})
		serializer.is_valid(raise_exception=True)

		submitted_answers = {
			item['question'].id: item['choice'].id for item in serializer.validated_data['answers']
		}

		results = []
		correct_answers = 0
		questions = list(quiz.questions.all())

		for question in questions:
			correct_choice = next(choice for choice in question.choices.all() if choice.is_correct)
			selected_choice_id = submitted_answers.get(question.id)
			is_correct = selected_choice_id == correct_choice.id
			if is_correct:
				correct_answers += 1

			results.append(
				{
					'question_id': question.id,
					'selected_choice_id': selected_choice_id,
					'correct_choice_id': correct_choice.id,
					'is_correct': is_correct,
					'explanation': question.explanation,
				}
			)

		total_questions = len(questions)
		percentage = (correct_answers / total_questions * 100) if total_questions else 0

		return Response(
			{
				'quiz': quiz.title,
				'score': correct_answers,
				'total_questions': total_questions,
				'percentage': round(percentage, 2),
				'answers': results,
			},
			status=status.HTTP_200_OK,
		)
