from django.core.management.base import BaseCommand

from quizzes.dataset_generator import write_all_module_quizzes


class Command(BaseCommand):
	help = 'Generate strict JSON quiz files for all ML360 categories, levels, and modules.'

	def add_arguments(self, parser):
		parser.add_argument('--output-dir', required=True, help='Directory where all module quiz JSON files will be written.')

	def handle(self, *args, **options):
		generated_files = write_all_module_quizzes(options['output_dir'])
		self.stdout.write(self.style.SUCCESS(f'Generated {len(generated_files)} module quiz files.'))