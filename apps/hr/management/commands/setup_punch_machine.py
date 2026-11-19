from django.core.management.base import BaseCommand
from apps.hr.models import PunchMachineConfig


class Command(BaseCommand):
    help = 'Create default punch machine configuration'

    def handle(self, *args, **options):
        config, created = PunchMachineConfig.objects.get_or_create(
            corporate_id='support',
            defaults={
                'machine_name': 'eTimeOffice Machine',
                'base_url': 'https://api.etimeoffice.com/api',
                'corporate_id': 'support',
                'username': 'support',
                'password': 'support',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created punch machine config: {config.id}'))
        else:
            self.stdout.write(f'Config already exists: {config.id}')
