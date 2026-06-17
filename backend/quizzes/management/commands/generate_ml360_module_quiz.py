from django.core.management.base import BaseCommand, CommandError

from quizzes.dataset_generator import write_module_quiz


class Command(BaseCommand):
	help = 'Generate a strict JSON quiz for one ML360 category, level, and module.'

	def add_arguments(self, parser):
		parser.add_argument('--category', required=True, help='ML360 category key, for example apprentissage-supervise.')
		parser.add_argument('--level', required=True, help='Module level: Beginner, Intermediate, or Advanced.')
		parser.add_argument('--module', required=True, help='Exact module title to export.')
		parser.add_argument('--output', required=True, help='Destination JSON file path.')

	def handle(self, *args, **options):
		try:
			path = write_module_quiz(
				options['output'],
				options['category'],
				options['level'],
				options['module'],
			)
		except ValueError as exc:
			raise CommandError(str(exc)) from exc

		self.stdout.write(self.style.SUCCESS(f'Module quiz generated: {path}'))