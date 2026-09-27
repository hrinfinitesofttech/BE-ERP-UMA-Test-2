from django.db import models


class ApprovalItem(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    category = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    record_number = models.CharField(max_length=64)
    requester_name = models.CharField(max_length=128)
    requester_role = models.CharField(max_length=128, blank=True)
    request_date = models.DateField()
    amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    related_job_number = models.CharField(max_length=64, blank=True)
    remarks = models.TextField(blank=True)
    urgency = models.CharField(max_length=32, default='Normal')
    status = models.CharField(max_length=32, default='Pending')

    class Meta:
        ordering = ['-request_date']

    def __str__(self):
        return f"{self.title} ({self.record_number}) - {self.status}"


class ERPAlertItem(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    module = models.CharField(max_length=64)
    severity = models.CharField(max_length=32, default='Info')
    title = models.CharField(max_length=255)
    description = models.TextField()
    target_url = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    action_required = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.severity}] {self.title}"
