from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Seeds all phases (Phase 1 to Phase 6) in sequence'

    def handle(self, *args, **options):
        self.stdout.write('==================================================')
        self.stdout.write('STARTING COMPLETE SEEDING FOR UMA TECHNO FAB ERP')
        self.stdout.write('==================================================')

        for phase in range(1, 7):
            self.stdout.write(f'\n--- RUNNING PHASE {phase} SEED ---')
            call_command(f'seed_phase{phase}')

        self.stdout.write('\n==================================================')
        self.stdout.write(self.style.SUCCESS('[ALL PHASES 1 TO 6 SEEDED SUCCESSFULLY]'))
        self.stdout.write('==================================================')
