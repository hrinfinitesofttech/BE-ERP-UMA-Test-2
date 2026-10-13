from django.core.management.base import BaseCommand
from apps.hr.models import LeaveType, LeaveBalance, ShiftMaster
from apps.authentication.models import User


DEFAULT_LEAVE_TYPES = [
    {
        'id': 'LT-01',
        'leave_code': 'CL',
        'leave_name': 'Casual Leave (CL)',
        'annual_quota': 12.0,
        'monthly_accrual': 1.0,
        'carry_forward_allowed': False,
        'max_consecutive_days': 3,
        'half_day_allowed': True,
        'attachment_required': False,
        'status': 'Active',
    },
    {
        'id': 'LT-02',
        'leave_code': 'SL',
        'leave_name': 'Sick Leave (SL)',
        'annual_quota': 12.0,
        'monthly_accrual': 1.0,
        'carry_forward_allowed': True,
        'max_consecutive_days': 7,
        'half_day_allowed': True,
        'attachment_required': True,
        'status': 'Active',
    },
    {
        'id': 'LT-03',
        'leave_code': 'EL',
        'leave_name': 'Earned / Privilege Leave (EL)',
        'annual_quota': 18.0,
        'monthly_accrual': 1.5,
        'carry_forward_allowed': True,
        'max_consecutive_days': 15,
        'half_day_allowed': True,
        'attachment_required': False,
        'status': 'Active',
    },
    {
        'id': 'LT-04',
        'leave_code': 'CO',
        'leave_name': 'Compensatory Off (Comp-Off)',
        'annual_quota': 6.0,
        'monthly_accrual': 0.5,
        'carry_forward_allowed': False,
        'max_consecutive_days': 2,
        'half_day_allowed': True,
        'attachment_required': False,
        'status': 'Active',
    },
    {
        'id': 'LT-05',
        'leave_code': 'ML',
        'leave_name': 'Maternity / Paternity Leave',
        'annual_quota': 90.0,
        'monthly_accrual': 0.0,
        'carry_forward_allowed': False,
        'max_consecutive_days': 90,
        'half_day_allowed': False,
        'attachment_required': True,
        'status': 'Active',
    },
]


class Command(BaseCommand):
    help = 'Seeds Phase 3 standard Leave Types, Shift Master, and initial Leave Balances for active employees'

    def handle(self, *args, **options):
        # 1. Seed Shift Master
        shift, created = ShiftMaster.objects.get_or_create(
            id='SHIFT-GEN',
            defaults={
                'shift_name': 'General Day Shift (09:00 - 18:00)',
                'start_time': '09:00',
                'end_time': '18:00',
                'grace_period_minutes': 15,
                'break_duration_minutes': 60,
                'late_rule': 'Late after 09:15 AM (15 mins grace).',
                'early_checkout_rule': 'Early before 18:00 PM.',
                'overtime_rule': 'Overtime calculated after 18:30 PM.',
                'weekly_off': 'Sunday',
                'status': 'Active'
            }
        )
        self.stdout.write(self.style.SUCCESS(f"ShiftMaster verified: {shift.shift_name}"))

        # 2. Seed Leave Types
        seeded_types = []
        for lt_data in DEFAULT_LEAVE_TYPES:
            lt_obj, _ = LeaveType.objects.update_or_create(
                id=lt_data['id'],
                defaults=lt_data
            )
            seeded_types.append(lt_obj)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(seeded_types)} standard Leave Types."))

        # 3. Seed Leave Balances for all active employees
        active_users = User.objects.filter(is_active=True)
        balance_count = 0
        for u in active_users:
            emp_name = u.name or f"{u.first_name} {u.last_name}".strip() or u.username
            dept_name = u.department_name or (u.department.name if u.department else 'General')
            for lt in seeded_types:
                b_id = f"BAL-{u.id}-{lt.leave_code}-26"
                LeaveBalance.objects.get_or_create(
                    employee_id=u.id,
                    leave_type_id=lt.id,
                    financial_year='2026-2027',
                    defaults={
                        'id': b_id,
                        'employee_name': emp_name,
                        'department': dept_name,
                        'leave_code': lt.leave_code,
                        'leave_name': lt.leave_name,
                        'total_credited': lt.annual_quota,
                        'used': 0.0,
                        'pending_approval': 0.0,
                        'available_balance': lt.annual_quota,
                    }
                )
                balance_count += 1

        self.stdout.write(self.style.SUCCESS(f"Verified {balance_count} Leave Balances across {active_users.count()} active employees."))
