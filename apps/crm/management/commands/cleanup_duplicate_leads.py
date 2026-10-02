from django.core.management.base import BaseCommand
from apps.crm.models import Lead


class Command(BaseCommand):
    help = 'Cleans up duplicate leads by keeping the earliest record and deleting duplicates'

    def handle(self, *args, **options):
        self.stdout.write("Scanning for duplicate leads...")

        all_leads = Lead.objects.all().order_by('id')
        seen = {}
        deleted_count = 0

        for lead in all_leads:
            company = (lead.company_name or '').strip().lower()
            mobile = (lead.mobile or '').strip()
            product = (lead.product_name or '').strip().lower()

            # Unique key for identifying duplicate submissions
            key = f"{company}__{mobile}__{product}"

            if not key or key == "____":
                continue

            if key in seen:
                self.stdout.write(
                    f"Deleting duplicate lead: {lead.id} ({lead.company_name}) -> Original: {seen[key].id}"
                )
                lead.delete()
                deleted_count += 1
            else:
                seen[key] = lead

        self.stdout.write(self.style.SUCCESS(f"Successfully cleaned up {deleted_count} duplicate leads."))
