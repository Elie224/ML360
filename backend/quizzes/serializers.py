from rest_framework import serializers

from .models import Category, Choice, Level, Question, Quiz


class LevelSerializer(serializers.ModelSerializer):
	class Meta:
		model = Level
		fields = ('id', 'title', 'slug', 'objective', 'order')


class CategorySerializer(serializers.ModelSerializer):
	quizzes_count = serializers.IntegerField(read_only=True)
	levels = LevelSerializer(many=True, read_only=True)

	class Meta:
		model = Category
		fields = ('id', 'title', 'slug', 'description', 'quizzes_count', 'levels')


class ChoicePublicSerializer(serializers.ModelSerializer):
	class Meta:
		model = Choice
		fields = ('id', 'label', 'order')


class QuestionPublicSerializer(serializers.ModelSerializer):
	choices = ChoicePublicSerializer(many=True, read_only=True)

	class Meta:
		model = Question
		fields = (
			'id',
			'prompt',
			'explanation',
			'order',
			'question_type',
			'presentation_type',
			'image_url',
			'difficulty',
			'choices',
		)


class QuizListSerializer(serializers.ModelSerializer):
	category = CategorySerializer(read_only=True)
	level = LevelSerializer(read_only=True)
	question_count = serializers.IntegerField(read_only=True)

	class Meta:
		model = Quiz
		fields = (
			'id',
			'title',
			'slug',
			'description',
			'source_level_name',
			'level',
			'is_published',
			'question_count',
			'category',
		)


class QuizDetailSerializer(serializers.ModelSerializer):
	category = CategorySerializer(read_only=True)
	level = LevelSerializer(read_only=True)
	questions = QuestionPublicSerializer(many=True, read_only=True)

	class Meta:
		model = Quiz
		fields = (
			'id',
			'title',
			'slug',
			'description',
			'source_level_name',
			'level',
			'category',
			'questions',
		)


class AnswerItemSerializer(serializers.Serializer):
	question_id = serializers.IntegerField()
	choice_id = serializers.IntegerField()


class AnswerSubmissionSerializer(serializers.Serializer):
	answers = AnswerItemSerializer(many=True)

	def validate_answers(self, value):
		quiz = self.context['quiz']
		question_map = {question.id: question for question in quiz.questions.all()}
		seen_question_ids = set()
		normalized_answers = []

		for item in value:
			question = question_map.get(item['question_id'])
			if question is None:
				raise serializers.ValidationError('Une question ne correspond pas a ce quiz.')

			if question.id in seen_question_ids:
				raise serializers.ValidationError('Chaque question ne peut etre soumise qu une fois.')

			choice = next((choice for choice in question.choices.all() if choice.id == item['choice_id']), None)
			if choice is None:
				raise serializers.ValidationError('Une reponse ne correspond pas a la question selectionnee.')

			seen_question_ids.add(question.id)
			normalized_answers.append({'question': question, 'choice': choice})

		return normalized_answers