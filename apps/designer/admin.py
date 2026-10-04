from django.contrib import admin
from .models import (
    DesignJob,
    CustomerRequirement,
    Drawing2D,
    Design3DModel,
    BOMHeader,
    DesignRevisionLog,
    TechnicalDocumentItem,
    DesignTask,
    AssemblyDrawing,
)

@admin.register(DesignTask)
class DesignTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_name', 'designer', 'priority', 'status', 'due_date', 'progress_percent')
    search_fields = ('id', 'task_name', 'designer', 'job_number', 'customer_name')
    list_filter = ('status', 'priority', 'designer', 'created_at')

@admin.register(DesignJob)
class DesignJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'design_job_number', 'project_id', 'project_number', 'job_number', 'customer_id')
    search_fields = ('id', 'design_job_number', 'project_id', 'project_number')
    list_filter = ('machine_type', 'status', 'created_at', 'updated_at')

@admin.register(CustomerRequirement)
class CustomerRequirementAdmin(admin.ModelAdmin):
    list_display = ('id', 'design_job_id', 'project_id', 'job_number', 'customer_name', 'contact_person')
    search_fields = ('id', 'design_job_id', 'project_id', 'job_number')
    list_filter = ('machine_type', 'created_at')

@admin.register(Drawing2D)
class Drawing2DAdmin(admin.ModelAdmin):
    list_display = ('id', 'design_job_id', 'drawing_number', 'title', 'revision', 'status')
    search_fields = ('id', 'design_job_id', 'drawing_number', 'title')
    list_filter = ('status', 'created_at')

@admin.register(Design3DModel)
class Design3DModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'design_job_id', 'model_number', 'model_name', 'software', 'version')
    search_fields = ('id', 'design_job_id', 'model_number', 'model_name')
    list_filter = ('status', 'created_at')

@admin.register(BOMHeader)
class BOMHeaderAdmin(admin.ModelAdmin):
    list_display = ('id', 'bom_number', 'design_job_id', 'project_id', 'job_number', 'active_revision')
    search_fields = ('id', 'bom_number', 'design_job_id', 'project_id')
    list_filter = ('status', 'created_at', 'updated_at')

@admin.register(DesignRevisionLog)
class DesignRevisionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'design_job_id', 'revision_number', 'reason', 'requested_by', 'approved_by')
    search_fields = ('id', 'design_job_id', 'revision_number')

@admin.register(TechnicalDocumentItem)
class TechnicalDocumentItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'design_job_id', 'doc_number', 'title', 'category', 'file_url')
    search_fields = ('id', 'design_job_id', 'doc_number', 'title')
    list_filter = ('category',)

@admin.register(AssemblyDrawing)
class AssemblyDrawingAdmin(admin.ModelAdmin):
    list_display = ('id', 'assembly_number', 'assembly_title', 'revision_number', 'file_format', 'file_size', 'drawn_by', 'approved_by')
    search_fields = ('id', 'assembly_number', 'assembly_title', 'sub_assembly_code', 'job_number')
    list_filter = ('file_format', 'revision_number', 'created_at')

