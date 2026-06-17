from django.db import migrations, models
import django.db.models.deletion


LEVEL_DEFAULTS = [
	('niveau-1', 'Niveau 1', 'Apprentissage', 1),
	('niveau-2', 'Niveau 2', 'Consolidation', 2),
	('niveau-3', 'Niveau 3', 'Maitrise', 3),
	('niveau-4', 'Niveau 4', 'Expert', 4),
]


def seed_levels(apps, schema_editor):
	Category = apps.get_model('quizzes', 'Category')
	Level = apps.get_model('quizzes', 'Level')

	for category in Category.objects.all():
		for slug, title, objective, order in LEVEL_DEFAULTS:
			Level.objects.update_or_create(
				category=category,
				order=order,
				defaults={
					'slug': slug,
					'title': title,
					'objective': objective,
				},
			)


def backfill_quiz_levels(apps, schema_editor):
	Quiz = apps.get_model('quizzes', 'Quiz')
	Level = apps.get_model('quizzes', 'Level')

	mapping = {
		'beginner': 1,
		'intermediate': 2,
		'advanced': 3,
	}

	for quiz in Quiz.objects.all():
		level_order = mapping.get(getattr(quiz, 'difficulty', None), 1)
		level = Level.objects.filter(category_id=quiz.category_id, order=level_order).first()
		if level is not None:
			quiz.level_id = level.id
			quiz.save(update_fields=['level'])


def unseed_levels(apps, schema_editor):
	Level = apps.get_model('quizzes', 'Level')
	Level.objects.filter(slug__in=[slug for slug, _, _, _ in LEVEL_DEFAULTS]).delete()


class Migration(migrations.Migration):

	dependencies = [
		('quizzes', '0002_seed_categories'),
	]

	operations = [
		migrations.CreateModel(
			name='Level',
			fields=[
				('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('title', models.CharField(max_length=80)),
				('slug', models.SlugField(max_length=100)),
				('objective', models.CharField(max_length=120)),
				('order', models.PositiveSmallIntegerField()),
				('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='levels', to='quizzes.category')),
			],
			options={
				'ordering': ['category__title', 'order'],
			},
		),
		migrations.AddConstraint(
			model_name='level',
			constraint=models.UniqueConstraint(fields=('category', 'slug'), name='unique_level_slug_per_category'),
		),
		migrations.AddConstraint(
			model_name='level',
			constraint=models.UniqueConstraint(fields=('category', 'order'), name='unique_level_order_per_category'),
		),
		migrations.AddField(
			model_name='quiz',
			name='level',
			field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='quizzes', to='quizzes.level'),
		),
		migrations.RunPython(seed_levels, unseed_levels),
		migrations.RunPython(backfill_quiz_levels, migrations.RunPython.noop),
		migrations.RemoveField(
			model_name='quiz',
			name='difficulty',
		),
		migrations.AlterField(
			model_name='quiz',
			name='level',
			field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='quizzes', to='quizzes.level'),
		),
	]
