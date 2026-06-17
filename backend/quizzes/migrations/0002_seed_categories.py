from django.db import migrations


def seed_categories(apps, schema_editor):
	Category = apps.get_model('quizzes', 'Category')
	defaults = [
		{
			'title': 'Apprentissage supervise',
			'slug': 'apprentissage-supervise',
			'description': 'Modeles entraines avec des donnees etiquetees pour predire une cible.',
		},
		{
			'title': 'Apprentissage non supervise',
			'slug': 'apprentissage-non-supervise',
			'description': 'Methodes qui detectent des structures ou regroupements sans etiquettes.',
		},
		{
			'title': 'Apprentissage semi supervise',
			'slug': 'apprentissage-semi-supervise',
			'description': 'Approches melangeant un petit volume de donnees etiquetees et beaucoup de donnees brutes.',
		},
		{
			'title': 'Apprentissage par renforcement',
			'slug': 'apprentissage-par-renforcement',
			'description': 'Agents qui apprennent par essais, erreurs et recompenses dans un environnement.',
		},
	]

	for item in defaults:
		Category.objects.update_or_create(slug=item['slug'], defaults=item)


def unseed_categories(apps, schema_editor):
	Category = apps.get_model('quizzes', 'Category')
	Category.objects.filter(
		slug__in=[
			'apprentissage-supervise',
			'apprentissage-non-supervise',
			'apprentissage-semi-supervise',
			'apprentissage-par-renforcement',
		]
	).delete()


class Migration(migrations.Migration):

	dependencies = [
		('quizzes', '0001_initial'),
	]

	operations = [
		migrations.RunPython(seed_categories, unseed_categories),
	]