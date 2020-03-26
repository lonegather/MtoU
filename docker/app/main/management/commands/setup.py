from django.core.management.base import BaseCommand
import main


class Command(BaseCommand):
    help = 'Setup core data'

    def handle(self, *args, **options):
        try:
            main.reset()
        except Exception as e:
            self.stderr.write(e)
            return
        self.stdout.write('Data Setup Successful')
