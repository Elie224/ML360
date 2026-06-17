from django.db import models


class Category(models.Model):
	title = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=140, unique=True)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ['title']
		verbose_name_plural = 'categories'

	def __str__(self):
		return self.title


class Level(models.Model):
	category = models.ForeignKey(Category, related_name='levels', on_delete=models.CASCADE)
	title = models.CharField(max_length=80)
	slug = models.SlugField(max_length=100)
	objective = models.CharField(max_length=120)
	order = models.PositiveSmallIntegerField()

	class Meta:
		ordering = ['category__title', 'order']
		constraints = [
			models.UniqueConstraint(fields=['category', 'slug'], name='unique_level_slug_per_category'),
			models.UniqueConstraint(fields=['category', 'order'], name='unique_level_order_per_category'),
		]

	def __str__(self):
		return f'{self.category.title} - {self.title}'


class Quiz(models.Model):
	title = models.CharField(max_length=180)
	slug = models.SlugField(max_length=200, unique=True)
	category = models.ForeignKey(Category, related_name='quizzes', on_delete=models.CASCADE)
	level = models.ForeignKey(Level, related_name='quizzes', on_delete=models.PROTECT)
	source_level_name = models.CharField(max_length=32, blank=True)
	description = models.TextField(blank=True)
	is_published = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['title']

	def __str__(self):
		return self.title


class Question(models.Model):
	class QuestionType(models.TextChoices):
		SINGLE_CHOICE = 'single_choice', 'Single choice'

	class PresentationType(models.TextChoices):
		TEXT = 'text', 'Text'
		IMAGE = 'image', 'Image'

	class Difficulty(models.TextChoices):
		EASY = 'easy', 'Easy'
		MEDIUM = 'medium', 'Medium'
		HARD = 'hard', 'Hard'

	quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
	prompt = models.TextField()
	explanation = models.TextField(blank=True)
	order = models.PositiveIntegerField(default=1)
	presentation_type = models.CharField(
		max_length=10,
		choices=PresentationType.choices,
		default=PresentationType.TEXT,
	)
	image_url = models.CharField(max_length=255, blank=True)
	difficulty = models.CharField(
		max_length=10,
		choices=Difficulty.choices,
		default=Difficulty.EASY,
	)
	question_type = models.CharField(
		max_length=30,
		choices=QuestionType.choices,
		default=QuestionType.SINGLE_CHOICE,
	)

	class Meta:
		ordering = ['order', 'id']
		constraints = [
			models.UniqueConstraint(fields=['quiz', 'order'], name='unique_question_order_per_quiz'),
		]

	def __str__(self):
		return f'{self.quiz.title} - Q{self.order}'


class Choice(models.Model):
	question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
	label = models.CharField(max_length=255)
	is_correct = models.BooleanField(default=False)
	order = models.PositiveIntegerField(default=1)

	class Meta:
		ordering = ['order', 'id']
		constraints = [
			models.UniqueConstraint(fields=['question', 'order'], name='unique_choice_order_per_question'),
		]

	def __str__(self):
		return self.label
