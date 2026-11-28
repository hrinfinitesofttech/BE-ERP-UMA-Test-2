from django.contrib import admin

from .models import NestingHandover, NestingJob, NestingTask, SheetUsage


@admin.register(NestingJob)
class NestingJobAdmin(admin.ModelAdmin):
    list_display = ('nesting_number', 'customer_name', 'product_name', 'job_number', 'status', 'assigned_to')
    search_fields = ('nesting_number', 'customer_name', 'product_name', 'job_number')
    list_filter = ('status', 'priority')


@admin.register(NestingTask)
class NestingTaskAdmin(admin.ModelAdmin):
    list_display = ('part_name', 'job', 'thickness_mm', 'required_qty', 'cut_qty', 'status')


@admin.register(NestingHandover)
class NestingHandoverAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'task', 'qty', 'kind', 'status', 'resolved')
    list_filter = ('status', 'kind')


@admin.register(SheetUsage)
class SheetUsageAdmin(admin.ModelAdmin):
    list_display = ('job', 'material_grade', 'thickness_mm', 'sheets_used', 'sheets_leftover')
