from rest_framework import serializers

from .models import NestingJob, NestingTask, NestingHandover, SheetUsage


def _task_numbers(task):
    """Quantities of one task derived from its hand-overs."""
    handovers = list(task.handovers.all())
    # parts that left Nesting for the first time = fresh hand-overs (rework entries re-use the same parts)
    handed_out = sum(h.qty for h in handovers if h.kind == 'fresh')
    accepted = sum(h.qty for h in handovers if h.status == 'accepted')
    awaiting = sum(h.qty for h in handovers if h.status == 'handed_over')
    rework = sum(h.qty for h in handovers if h.status in ('rejected', 'rework_required') and not h.resolved)
    return {
        'handed_qty': handed_out,
        'accepted_qty': accepted,
        'awaiting_review_qty': awaiting,
        'rework_qty': rework,
        'remaining_to_cut_qty': max(0, task.required_qty - task.cut_qty),
        'available_to_hand_over_qty': max(0, task.cut_qty - handed_out),
    }


class NestingTaskSerializer(serializers.ModelSerializer):
    job_id = serializers.PrimaryKeyRelatedField(source='job', queryset=NestingJob.objects.all())
    nesting_number = serializers.CharField(source='job.nesting_number', read_only=True)
    project_number = serializers.CharField(source='job.project_number', read_only=True)
    job_number = serializers.CharField(source='job.job_number', read_only=True)
    customer_name = serializers.CharField(source='job.customer_name', read_only=True)
    quantities = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = NestingTask
        exclude = ['job']
        read_only_fields = ['id', 'cut_qty', 'status', 'cut_log']

    def get_quantities(self, obj):
        return _task_numbers(obj)

    def get_progress_percent(self, obj):
        return round(min(obj.cut_qty, obj.required_qty) / obj.required_qty * 100) if obj.required_qty else 0

    def validate_required_qty(self, value):
        if value < 1:
            raise serializers.ValidationError('Required quantity must be at least 1.')
        return value

    def validate(self, attrs):
        if self.instance and 'required_qty' in attrs and attrs['required_qty'] < self.instance.cut_qty:
            raise serializers.ValidationError(
                {'required_qty': f'{self.instance.cut_qty} already cut; required quantity cannot be lower.'})
        return attrs


class NestingHandoverSerializer(serializers.ModelSerializer):
    job_id = serializers.CharField(read_only=True)
    task_id = serializers.CharField(read_only=True)
    part_name = serializers.CharField(source='task.part_name', read_only=True)
    part_number = serializers.CharField(source='task.part_number', read_only=True)
    thickness_mm = serializers.FloatField(source='task.thickness_mm', read_only=True)
    nesting_number = serializers.CharField(source='job.nesting_number', read_only=True)
    project_number = serializers.CharField(source='job.project_number', read_only=True)
    job_number = serializers.CharField(source='job.job_number', read_only=True)
    customer_name = serializers.CharField(source='job.customer_name', read_only=True)
    needs_attention = serializers.SerializerMethodField()

    class Meta:
        model = NestingHandover
        fields = '__all__'
        read_only_fields = ['status', 'kind', 'rework_of', 'resolved', 'handed_by', 'reviewed_by',
                            'reviewed_at', 'review_reason', 'qty']

    def get_needs_attention(self, obj):
        """True for rejected / rework entries Nesting still has to redo - shown highlighted in the UI."""
        return obj.status in ('rejected', 'rework_required') and not obj.resolved


class SheetUsageSerializer(serializers.ModelSerializer):
    job_id = serializers.PrimaryKeyRelatedField(source='job', queryset=NestingJob.objects.all())
    unit_weight_kg = serializers.FloatField(read_only=True)
    gross_weight_kg = serializers.FloatField(read_only=True)
    net_weight_kg = serializers.FloatField(read_only=True)
    gross_cost = serializers.FloatField(read_only=True)
    net_cost = serializers.FloatField(read_only=True)

    class Meta:
        model = SheetUsage
        exclude = ['job']
        read_only_fields = ['id', 'logged_by']

    def validate(self, attrs):
        g = lambda k: attrs.get(k, getattr(self.instance, k, 0) if self.instance else 0) or 0
        for key in ('sheets_issued', 'sheets_used', 'sheets_leftover', 'leftover_weight_kg',
                    'rate_per_kg', 'thickness_mm'):
            if g(key) < 0:
                raise serializers.ValidationError({key: 'Cannot be negative.'})
        issued, used = g('sheets_issued'), g('sheets_used')
        if issued and used > issued:
            raise serializers.ValidationError({'sheets_used': 'Sheets used cannot be more than sheets issued.'})
        # untouched sheets go back to store: derive when not given
        if issued and 'sheets_leftover' not in attrs and not (self.instance and self.instance.sheets_leftover):
            attrs['sheets_leftover'] = issued - used
        return attrs


class NestingJobSerializer(serializers.ModelSerializer):
    """List view: the job plus roll-up numbers (parts, progress, sheets, material estimate)."""
    summary = serializers.SerializerMethodField()

    class Meta:
        model = NestingJob
        fields = '__all__'
        read_only_fields = ['id', 'nesting_number', 'status', 'created_by']

    def get_summary(self, obj):
        return job_summary(obj)


class NestingJobDetailSerializer(NestingJobSerializer):
    tasks = NestingTaskSerializer(many=True, read_only=True)
    handovers = NestingHandoverSerializer(many=True, read_only=True)
    sheet_usages = SheetUsageSerializer(many=True, read_only=True)


def job_summary(job):
    tasks = list(job.tasks.all())
    handovers = list(job.handovers.all())
    sheets = list(job.sheet_usages.all())
    required = sum(t.required_qty for t in tasks)
    cut = sum(min(t.cut_qty, t.required_qty) for t in tasks)
    accepted = sum(h.qty for h in handovers if h.status == 'accepted')
    return {
        'task_count': len(tasks),
        'required_qty': required,
        'cut_qty': cut,
        'accepted_qty': accepted,
        'awaiting_review_qty': sum(h.qty for h in handovers if h.status == 'handed_over'),
        'rework_qty': sum(h.qty for h in handovers if h.status in ('rejected', 'rework_required') and not h.resolved),
        'progress_percent': round(cut / required * 100) if required else 0,
        'sheets_issued': sum(s.sheets_issued for s in sheets),
        'sheets_used': sum(s.sheets_used for s in sheets),
        'sheets_leftover': sum(s.sheets_leftover for s in sheets),
        'leftover_weight_kg': round(sum(s.leftover_weight_kg for s in sheets), 2),
        'gross_weight_kg': round(sum(s.gross_weight_kg for s in sheets), 2),
        'net_weight_kg': round(sum(s.net_weight_kg for s in sheets), 2),
        'gross_cost': round(sum(s.gross_cost for s in sheets), 2),
        'net_cost': round(sum(s.net_cost for s in sheets), 2),
    }
