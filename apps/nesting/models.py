"""
Nesting department.

Design shares cutting files (DXF / PDF / STEP) -> Nesting downloads them, nests them in the
cutting-machine software, cuts the parts and hands them to Production. Production may accept,
reject or ask for rework; Nesting redoes the part and hands it over again. Every MS sheet used and
every sheet left over is recorded so the material estimate of a project can be calculated.

    Design --share--> NestingJob --> NestingTask (parts to cut) --> NestingHandover --> Production
                                 \\-> SheetUsage (sheets used / leftover, weight and cost)
"""
from decimal import Decimal

from django.db import models

STEEL_DENSITY_KG_PER_M3 = Decimal('7850')


def next_code(model, prefix, field):
    """PREFIX-YYYY-0001 style code that never collides with an existing row."""
    from django.utils import timezone
    head = f'{prefix}-{timezone.now().year}-'
    n = model.objects.filter(**{f'{field}__startswith': head}).count() + 1
    while model.objects.filter(**{field: f'{head}{n:04d}'}).exists():
        n += 1
    return f'{head}{n:04d}'


class NestingJob(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received from Design'),
        ('in_nesting', 'Nesting In Progress'),
        ('cutting', 'Cutting In Progress'),
        ('completed', 'Cutting Completed'),
        ('handed_over', 'Handed Over to Production'),
        ('rework', 'Rework / Rejected by Production'),
        ('closed', 'Accepted by Production'),
    ]

    id = models.CharField(max_length=64, primary_key=True)
    nesting_number = models.CharField(max_length=64, unique=True)
    design_job_id = models.CharField(max_length=64, blank=True, default='')
    design_job_number = models.CharField(max_length=64, blank=True, default='')
    project_id = models.CharField(max_length=64, blank=True, default='')
    project_number = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    customer_name = models.CharField(max_length=200, blank=True, default='')
    product_name = models.CharField(max_length=200, blank=True, default='')
    priority = models.CharField(max_length=30, default='medium')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='received')
    shared_by = models.CharField(max_length=150, blank=True, default='')
    shared_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.CharField(max_length=150, blank=True, default='')
    cutting_machine = models.CharField(max_length=150, blank=True, default='')
    program_reference = models.CharField(max_length=150, blank=True, default='')
    required_date = models.CharField(max_length=50, blank=True, default='')
    # [{id, fileName, fileType, fileUrl, revision, source, sharedBy, sharedAt, downloadedBy, downloadedAt}]
    files = models.JSONField(default=list, blank=True)
    remarks = models.TextField(blank=True, default='')
    created_by = models.CharField(max_length=150, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.nesting_number} - {self.product_name}'

    def save(self, *args, **kwargs):
        if not self.nesting_number:
            self.nesting_number = next_code(NestingJob, 'NST', 'nesting_number')
        if not self.id:
            self.id = self.nesting_number
        super().save(*args, **kwargs)

    def refresh_status(self):
        """Derive the job status from its tasks and hand-overs."""
        tasks = list(self.tasks.all())
        if not tasks:
            return
        handovers = list(self.handovers.all())
        open_rework = any(h.status in ('rejected', 'rework_required') and not h.resolved for h in handovers)
        required = sum(t.required_qty for t in tasks)
        cut = sum(min(t.cut_qty, t.required_qty) for t in tasks)
        accepted = sum(h.qty for h in handovers if h.status == 'accepted')
        awaiting = any(h.status == 'handed_over' for h in handovers)
        if open_rework:
            new = 'rework'
        elif required and accepted >= required and not awaiting:
            new = 'closed'
        elif required and cut >= required and (awaiting or accepted):
            new = 'handed_over'
        elif required and cut >= required:
            new = 'completed'
        elif cut > 0:
            new = 'cutting'
        else:
            new = 'received' if self.status == 'received' else 'in_nesting'
        if new != self.status:
            self.status = new
            self.save(update_fields=['status', 'updated_at'])


class NestingTask(models.Model):
    """One part / plate type to cut: how many are required and how many are already cut."""
    STATUS_CHOICES = [('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')]

    id = models.CharField(max_length=64, primary_key=True)
    job = models.ForeignKey(NestingJob, on_delete=models.CASCADE, related_name='tasks')
    part_name = models.CharField(max_length=200)
    part_number = models.CharField(max_length=100, blank=True, default='')
    drawing_number = models.CharField(max_length=100, blank=True, default='')
    material_grade = models.CharField(max_length=60, default='MS')
    thickness_mm = models.FloatField(default=0)
    required_qty = models.IntegerField(default=1)
    cut_qty = models.IntegerField(default=0)
    machine = models.CharField(max_length=150, blank=True, default='')
    program_no = models.CharField(max_length=100, blank=True, default='')
    assigned_to = models.CharField(max_length=150, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True, default='')
    # [{date, qty, by, note}] every cutting entry, for traceability
    cut_log = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.part_name} ({self.cut_qty}/{self.required_qty})'

    def save(self, *args, **kwargs):
        if not self.id:
            import uuid
            self.id = f'NTSK-{uuid.uuid4().hex[:8].upper()}'
        if self.cut_qty >= self.required_qty > 0:
            self.status = 'completed'
        elif self.cut_qty > 0:
            self.status = 'in_progress'
        else:
            self.status = 'pending'
        super().save(*args, **kwargs)


class NestingHandover(models.Model):
    """Cut parts handed to Production. Production accepts, rejects or asks for rework."""
    STATUS_CHOICES = [
        ('handed_over', 'Handed Over - awaiting Production'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('rework_required', 'Rework Required'),
    ]
    KIND_CHOICES = [('fresh', 'Fresh'), ('rework', 'Re-submitted after rework')]

    id = models.CharField(max_length=64, primary_key=True)
    job = models.ForeignKey(NestingJob, on_delete=models.CASCADE, related_name='handovers')
    task = models.ForeignKey(NestingTask, on_delete=models.CASCADE, related_name='handovers')
    qty = models.IntegerField(default=0)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default='fresh')
    rework_of = models.CharField(max_length=64, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='handed_over')
    # a rejected / rework entry becomes resolved once Nesting re-submits it
    resolved = models.BooleanField(default=False)
    handed_by = models.CharField(max_length=150, blank=True, default='')
    handed_at = models.DateTimeField(auto_now_add=True)
    handover_remarks = models.TextField(blank=True, default='')
    reviewed_by = models.CharField(max_length=150, blank=True, default='')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_reason = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-handed_at', '-id']

    def __str__(self):
        return f'{self.id} {self.task_id} x{self.qty} [{self.status}]'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = next_code(NestingHandover, 'NHO', 'id')
        super().save(*args, **kwargs)


class SheetUsage(models.Model):
    """MS sheets consumed / left over for a nesting job (one row per sheet size and thickness)."""
    id = models.CharField(max_length=64, primary_key=True)
    job = models.ForeignKey(NestingJob, on_delete=models.CASCADE, related_name='sheet_usages')
    material_grade = models.CharField(max_length=60, default='MS')
    thickness_mm = models.FloatField(default=0)
    sheet_length_mm = models.FloatField(default=2500)
    sheet_width_mm = models.FloatField(default=1250)
    sheets_issued = models.IntegerField(default=0)
    sheets_used = models.IntegerField(default=0)
    sheets_leftover = models.IntegerField(default=0)     # whole / usable sheets returned to store
    leftover_weight_kg = models.FloatField(default=0)    # weight of reusable offcuts / remnants
    weight_per_sheet_kg = models.FloatField(default=0)   # 0 = calculate from size x thickness
    rate_per_kg = models.FloatField(default=0)
    date = models.CharField(max_length=50, blank=True, default='')
    logged_by = models.CharField(max_length=150, blank=True, default='')
    remarks = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.job_id} {self.material_grade} {self.thickness_mm}mm used {self.sheets_used}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = next_code(SheetUsage, 'SHT', 'id')
        super().save(*args, **kwargs)

    def _exact_unit_weight(self):
        if self.weight_per_sheet_kg:
            return Decimal(str(self.weight_per_sheet_kg))
        vol_m3 = (Decimal(str(self.sheet_length_mm)) / 1000) * (Decimal(str(self.sheet_width_mm)) / 1000) \
            * (Decimal(str(self.thickness_mm)) / 1000)
        return vol_m3 * STEEL_DENSITY_KG_PER_M3

    @property
    def unit_weight_kg(self):
        return float(round(self._exact_unit_weight(), 2))

    @property
    def gross_weight_kg(self):
        # multiply the exact weight, then round once (avoids rounding a rounded number)
        return float(round(self._exact_unit_weight() * self.sheets_used, 2))

    @property
    def net_weight_kg(self):
        """Weight really consumed = weight of sheets used minus reusable offcuts returned to store.
        (sheets_leftover = untouched sheets of the issue that go back to store; they are not part of
        sheets_used, so they are not subtracted again here.)"""
        return round(max(0.0, self.gross_weight_kg - self.leftover_weight_kg), 2)

    @property
    def gross_cost(self):
        return round(self.gross_weight_kg * self.rate_per_kg, 2)

    @property
    def net_cost(self):
        return round(self.net_weight_kg * self.rate_per_kg, 2)
