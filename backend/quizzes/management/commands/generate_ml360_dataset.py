from django.core.management.base import BaseCommand, CommandError

from quizzes.dataset_generator import write_dataset


class Command(BaseCommand):
	help = 'Generate a strict JSON dataset for an ML360 category.'

	def add_arguments(self, parser):
		parser.add_argument(
			'--category',
			required=True,
			help='Category key to generate, for example apprentissage-supervise or apprentissage-par-renforcement.',
		)
		parser.add_argument('--output', required=True, help='Destination JSON file path.')

	def handle(self, *args, **options):
		category = options['category']
		output = options['output']

		try:
			path = write_dataset(output, category)
		except ValueError as exc:
			raise CommandError(str(exc)) from exc

		self.stdout.write(self.style.SUCCESS(f'Dataset generated: {path}'))