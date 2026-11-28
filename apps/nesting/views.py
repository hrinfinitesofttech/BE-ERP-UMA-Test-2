from apps.core.softdelete import SoftDeleteViewSetMixin
import logging
from collections import defaultdict

from django.db import models, transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.models import Notification
from apps.core.rbac_permissions import is_admin

from .models import NestingHandover, NestingJob, NestingTask, SheetUsage
from .serializers import (
    NestingHandoverSerializer, NestingJobDetailSerializer, NestingJobSerializer,
    NestingTaskSerializer, SheetUsageSerializer, job_summary,
)

log = logging.getLogger(__name__)


# ----------------------------------------------------------------------------- helpers
def actor(request):
    u = request.user
    return (getattr(u, 'name', '') or getattr(u, 'username', '') or 'User').strip()


def qp(request, *names):
    """Read a query param given in camelCase or snake_case."""
    for n in names:
        v = request.query_params.get(n)
        if v:
            return v
    return ''


def body(request, *names, default=None):
    for n in names:
        v = request.data.get(n)
        if v not in (None, ''):
            return v
    return default


def to_int(value, field='quantity'):
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        raise ValueError(f'{field} must be a number.')
    return n


def notify(department, title, message, link='/nesting', kind='info', priority='normal'):
    try:
        Notification.objects.create(title=title, message=message, type=kind, department=department,
                                    link_url=link, priority=priority)
    except Exception:
        log.exception('Nesting notification failed')


def err(message, code=status.HTTP_400_BAD_REQUEST, **extra):
    return Response({'error': message, **extra}, status=code)


def file_type_of(name, fmt=''):
    fmt = (fmt or '').strip().upper().lstrip('.')
    if fmt:
        return fmt
    if '.' in (name or ''):
        return name.rsplit('.', 1)[-1].upper()
    return 'FILE'


def split_off(h, qty, **overrides):
    """Split `qty` parts off a hand-over entry. Returns the entry that now holds exactly `qty` parts."""
    if qty >= h.qty:
        for k, v in overrides.items():
            setattr(h, k, v)
        h.save()
        return h
    part = NestingHandover.objects.create(
        job=h.job, task=h.task, qty=qty, kind=h.kind, rework_of=h.rework_of, status=h.status,
        resolved=h.resolved, handed_by=h.handed_by, handover_remarks=h.handover_remarks,
        reviewed_by=h.reviewed_by, reviewed_at=h.reviewed_at, review_reason=h.review_reason)
    NestingHandover.objects.filter(pk=part.pk).update(handed_at=h.handed_at)
    h.qty -= qty
    h.save(update_fields=['qty'])
    part.refresh_from_db()
    for k, v in overrides.items():
        setattr(part, k, v)
    part.save()
    return part


# ----------------------------------------------------------------------------- jobs
class NestingJobViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = NestingJob.objects.all().prefetch_related('tasks', 'handovers', 'sheet_usages')
    serializer_class = NestingJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        return NestingJobDetailSerializer if self.action == 'retrieve' else NestingJobSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get('status'):
            qs = qs.filter(status=p['status'])
        pid = qp(self.request, 'projectId', 'project_id')
        if pid:
            qs = qs.filter(models.Q(project_id=pid) | models.Q(project_number=pid))
        jn = qp(self.request, 'jobNumber', 'job_number')
        if jn:
            qs = qs.filter(job_number=jn)
        dj = qp(self.request, 'designJobId', 'design_job_id')
        if dj:
            qs = qs.filter(models.Q(design_job_id=dj) | models.Q(design_job_number=dj))
        s = p.get('search')
        if s:
            qs = qs.filter(models.Q(nesting_number__icontains=s) | models.Q(customer_name__icontains=s)
                           | models.Q(product_name__icontains=s) | models.Q(job_number__icontains=s)
                           | models.Q(project_number__icontains=s))
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=actor(self.request))

    # -- files Design can share ------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='design-files')
    def design_files(self, request):
        """List every file attached to a design job (for the 'Share to Nesting' picker)."""
        dj = self._design_job(qp(request, 'designJobId', 'design_job_id'))
        if not dj:
            return err('Design job not found.', status.HTTP_404_NOT_FOUND)
        return Response({'designJobId': dj.id, 'designJobNumber': dj.design_job_number,
                         'files': self._collect_design_files(dj)})

    @staticmethod
    def _design_job(ref):
        from apps.designer.models import DesignJob
        if not ref:
            return None
        return DesignJob.objects.filter(models.Q(id=ref) | models.Q(design_job_number=ref)).first()

    @staticmethod
    def _collect_design_files(dj):
        from apps.designer.models import AssemblyDrawing, Design3DModel, Drawing2D
        refs = {dj.id, dj.design_job_number}
        out = []

        def add(fid, name, fmt, url, revision, source):
            if not url and not name:
                return
            out.append({'id': fid, 'fileName': name or fid, 'fileType': file_type_of(name, fmt),
                        'fileUrl': url or '', 'revision': revision or '', 'source': source})

        if dj.file_url or dj.drawing_file_name:
            add(f'job:{dj.id}', dj.drawing_file_name or dj.drawing_title or dj.design_job_number,
                dj.drawing_format, dj.file_url, dj.active_revision, 'Design Job')
        for i, a in enumerate(dj.attachments or []):
            if isinstance(a, dict):
                add(f'att:{dj.id}:{i}', a.get('fileName') or a.get('name') or a.get('file_name'),
                    a.get('fileType') or a.get('type') or a.get('format'),
                    a.get('fileUrl') or a.get('url') or a.get('file_url') or a.get('data'),
                    a.get('revision'), 'Attachment')
        for d in Drawing2D.objects.filter(design_job_id__in=refs):
            add(f'2d:{d.id}', f'{d.drawing_number} - {d.title}', d.file_format, d.file_url, d.revision, '2D Drawing')
        for d in AssemblyDrawing.objects.filter(design_job_id__in=refs):
            add(f'asm:{d.id}', f'{d.assembly_number} - {d.assembly_title}', d.file_format, d.file_url,
                d.revision_number, 'Assembly Drawing')
        for d in Design3DModel.objects.filter(design_job_id__in=refs):
            add(f'3d:{d.id}', f'{d.model_number} - {d.model_name}', 'STEP', d.file_url, d.version, '3D Model')
        return out

    @action(detail=False, methods=['post'], url_path='share-from-design')
    def share_from_design(self, request):
        """Design shares files with Nesting. Re-sharing an open design job adds files to the same job."""
        ref = body(request, 'designJobId', 'design_job_id')
        dj = self._design_job(ref)
        if not dj:
            return err('Design job not found.', status.HTTP_404_NOT_FOUND)
        wanted = body(request, 'fileIds', 'file_ids')
        extra = body(request, 'files', default=[]) or []
        files = self._collect_design_files(dj)
        if wanted:
            files = [f for f in files if f['id'] in set(wanted)]
        for f in extra:  # files picked from the user's computer by the Design user
            if isinstance(f, dict) and (f.get('fileName') or f.get('name')):
                name = f.get('fileName') or f.get('name')
                files.append({'id': f.get('id') or f'up:{timezone.now().timestamp():.0f}:{len(files)}',
                              'fileName': name, 'fileType': file_type_of(name, f.get('fileType')),
                              'fileUrl': f.get('fileUrl') or f.get('url') or '', 'revision': f.get('revision', ''),
                              'source': 'Uploaded by Design'})
        if not files:
            return err('Select at least one design file (DXF / PDF / STEP) to share.')
        by, now = actor(request), timezone.now()
        for f in files:
            f.update({'sharedBy': by, 'sharedAt': now.isoformat(), 'downloadedBy': '', 'downloadedAt': ''})

        with transaction.atomic():
            job = NestingJob.objects.filter(design_job_id=dj.id).exclude(status='closed').first()
            created = job is None
            if created:
                job = NestingJob.objects.create(
                    design_job_id=dj.id, design_job_number=dj.design_job_number, project_id=dj.project_id,
                    project_number=dj.project_number, job_number=dj.job_number, customer_name=dj.customer_name,
                    product_name=dj.product_name, priority=body(request, 'priority', default=dj.priority or 'medium'),
                    shared_by=by, shared_at=now, assigned_to=body(request, 'assignedTo', 'assigned_to', default=''),
                    required_date=body(request, 'requiredDate', 'required_date', default=dj.required_date or ''),
                    remarks=body(request, 'remarks', default=''), created_by=by, files=[])
            known = {(x.get('fileName'), x.get('revision')) for x in job.files}
            added = [f for f in files if (f['fileName'], f['revision']) not in known]
            job.files = list(job.files) + added
            if not created:
                job.shared_by, job.shared_at = by, now
                if body(request, 'remarks'):
                    job.remarks = f"{job.remarks}\n{body(request, 'remarks')}".strip()
            job.save()
        notify('nesting', 'New files shared for nesting',
               f'{by} shared {len(added)} file(s) for {job.product_name or job.nesting_number} '
               f'({job.customer_name}). Job {job.nesting_number}.', f'/nesting/{job.id}', 'info', 'high')
        return Response(NestingJobDetailSerializer(job).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark-downloaded')
    def mark_downloaded(self, request, pk=None):
        job = self.get_object()
        fid = body(request, 'fileId', 'file_id')
        by, now = actor(request), timezone.now().isoformat()
        hit = False
        for f in job.files:
            if fid is None or f.get('id') == fid:
                f['downloadedBy'], f['downloadedAt'] = by, now
                hit = True
        if not hit:
            return err('File not found on this nesting job.', status.HTTP_404_NOT_FOUND)
        job.save(update_fields=['files', 'updated_at'])
        return Response(NestingJobDetailSerializer(job).data)

    @action(detail=True, methods=['post'], url_path='start')
    def start(self, request, pk=None):
        """Nesting engineer takes the job: records who, which cutting machine and the program reference."""
        job = self.get_object()
        job.assigned_to = body(request, 'assignedTo', 'assigned_to', default=job.assigned_to or actor(request))
        job.cutting_machine = body(request, 'cuttingMachine', 'cutting_machine', default=job.cutting_machine)
        job.program_reference = body(request, 'programReference', 'program_reference', default=job.program_reference)
        if job.status == 'received':
            job.status = 'in_nesting'
        job.save()
        return Response(NestingJobDetailSerializer(job).data)

    # -- reports ---------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        jobs = list(NestingJob.objects.all().prefetch_related('tasks', 'handovers', 'sheet_usages'))
        by_status = defaultdict(int)
        for j in jobs:
            by_status[j.status] += 1
        rework = NestingHandover.objects.filter(status__in=['rejected', 'rework_required'], resolved=False)
        return Response({
            'totalJobs': len(jobs),
            'byStatus': dict(by_status),
            'awaitingProductionReview': NestingHandover.objects.filter(status='handed_over').count(),
            'openRework': rework.count(),
            'openReworkQty': sum(h.qty for h in rework),
            'sheetsUsed': sum(job_summary(j)['sheets_used'] for j in jobs),
        })

    @action(detail=False, methods=['get'], url_path='project-summary')
    def project_summary(self, request):
        """Material estimate per project: sheets used / left over, weight and cost, parts cut / accepted."""
        pid = qp(request, 'projectId', 'project_id')
        jn = qp(request, 'jobNumber', 'job_number')
        qs = NestingJob.objects.all().prefetch_related('tasks', 'handovers', 'sheet_usages')
        if pid:
            qs = qs.filter(models.Q(project_id=pid) | models.Q(project_number=pid))
        if jn:
            qs = qs.filter(job_number=jn)
        groups = {}
        for j in qs:
            key = j.project_id or j.project_number or j.job_number or '-'
            g = groups.setdefault(key, {
                'projectId': j.project_id, 'projectNumber': j.project_number, 'jobNumber': j.job_number,
                'customerName': j.customer_name, 'productName': j.product_name, 'jobs': [],
                'totals': defaultdict(float), 'byThickness': {}})
            s = job_summary(j)
            g['jobs'].append({'id': j.id, 'nestingNumber': j.nesting_number, 'status': j.status, **{
                'requiredQty': s['required_qty'], 'cutQty': s['cut_qty'], 'acceptedQty': s['accepted_qty']}})
            for k, v in s.items():
                if k != 'progress_percent' and isinstance(v, (int, float)):
                    g['totals'][k] += v
            for u in j.sheet_usages.all():
                t = g['byThickness'].setdefault(str(u.thickness_mm), {
                    'thicknessMm': u.thickness_mm, 'sheetsUsed': 0, 'sheetsLeftover': 0, 'netWeightKg': 0.0, 'netCost': 0.0})
                t['sheetsUsed'] += u.sheets_used
                t['sheetsLeftover'] += u.sheets_leftover
                t['netWeightKg'] = round(t['netWeightKg'] + u.net_weight_kg, 2)
                t['netCost'] = round(t['netCost'] + u.net_cost, 2)
        out = []
        for g in groups.values():
            tot = {k: round(v, 2) for k, v in g['totals'].items()}
            g['totals'] = tot
            g['byThickness'] = sorted(g['byThickness'].values(), key=lambda x: x['thicknessMm'])
            out.append(g)
        return Response(out)


# ----------------------------------------------------------------------------- tasks
class NestingTaskViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = NestingTask.objects.all().select_related('job').prefetch_related('handovers')
    serializer_class = NestingTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        jid = qp(self.request, 'jobId', 'job_id', 'nestingJobId')
        if jid:
            qs = qs.filter(job_id=jid)
        if self.request.query_params.get('status'):
            qs = qs.filter(status=self.request.query_params['status'])
        return qs

    def _after(self, task):
        task.job.refresh_status()

    def perform_create(self, serializer):
        task = serializer.save()
        job = task.job
        if job.status == 'received':
            job.status = 'in_nesting'
            job.save(update_fields=['status', 'updated_at'])

    def perform_update(self, serializer):
        self._after(serializer.save())

    @action(detail=True, methods=['post'], url_path='log-cutting')
    def log_cutting(self, request, pk=None):
        """Record how many parts were cut (adds to the quantity already cut)."""
        task = self.get_object()
        try:
            qty = to_int(body(request, 'qty', 'quantity'))
        except ValueError as e:
            return err(str(e))
        if qty <= 0:
            return err('Cut quantity must be greater than zero.')
        remaining = task.required_qty - task.cut_qty
        if qty > remaining:
            return err(f'Only {remaining} more can be cut for this task (required {task.required_qty}, '
                       f'already cut {task.cut_qty}).', remaining=remaining)
        with transaction.atomic():
            task.cut_qty += qty
            task.cut_log = list(task.cut_log) + [{
                'date': timezone.now().isoformat(), 'qty': qty, 'by': actor(request),
                'note': body(request, 'note', 'remarks', default='')}]
            task.save()
            task.job.refresh_status()
        return Response(NestingTaskSerializer(task).data)

    @action(detail=True, methods=['post'], url_path='hand-over')
    def hand_over(self, request, pk=None):
        """Give cut parts to Production."""
        task = self.get_object()
        avail = NestingTaskSerializer(task).data['quantities']['available_to_hand_over_qty']
        try:
            qty = to_int(body(request, 'qty', 'quantity', default=avail))
        except ValueError as e:
            return err(str(e))
        if qty <= 0:
            return err('Nothing to hand over: cut some parts first.' if avail == 0 else 'Quantity must be greater than zero.')
        if qty > avail:
            return err(f'Only {avail} cut part(s) are available to hand over.', available=avail)
        with transaction.atomic():
            h = NestingHandover.objects.create(
                job=task.job, task=task, qty=qty, kind='fresh', handed_by=actor(request),
                handover_remarks=body(request, 'remarks', default=''))
            task.job.refresh_status()
        notify('production', 'Cut parts handed over by Nesting',
               f'{qty} x {task.part_name} ({task.job.job_number or task.job.nesting_number}) is ready for '
               f'Production. Please accept or send back.', '/nesting/production-review', 'approval_request', 'high')
        return Response(NestingHandoverSerializer(h).data, status=status.HTTP_201_CREATED)


# ----------------------------------------------------------------------------- hand-overs
class NestingHandoverViewSet(viewsets.ReadOnlyModelViewSet):
    """Production's inbox. Created by `tasks/{id}/hand-over`, resolved by the actions below."""
    queryset = NestingHandover.objects.all().select_related('job', 'task')
    serializer_class = NestingHandoverSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get('status'):
            qs = qs.filter(status__in=p['status'].split(','))
        jid = qp(self.request, 'jobId', 'job_id')
        if jid:
            qs = qs.filter(job_id=jid)
        if p.get('attention') in ('1', 'true'):
            qs = qs.filter(status__in=['rejected', 'rework_required'], resolved=False)
        return qs

    def _review(self, request, pk, new_status, reason_required):
        with transaction.atomic():
            h = NestingHandover.objects.select_for_update().select_related('job', 'task').get(pk=pk)
            if h.status != 'handed_over':
                return err(f'This hand-over is already {h.get_status_display()}.')
            if h.handed_by == actor(request) and not is_admin(request.user):
                return err('You cannot review your own hand-over. Production must accept or reject it.',
                           status.HTTP_403_FORBIDDEN)
            reason = body(request, 'reason', 'remarks', 'comment', default='')
            if reason_required and not str(reason).strip():
                return err('Please give the reason (what is wrong with the part).')
            try:
                qty = to_int(body(request, 'qty', 'quantity', default=h.qty))
            except ValueError as e:
                return err(str(e))
            if qty <= 0 or qty > h.qty:
                return err(f'Quantity must be between 1 and {h.qty}.')
            entry = split_off(h, qty, status=new_status, reviewed_by=actor(request),
                              reviewed_at=timezone.now(), review_reason=str(reason).strip())
            entry.job.refresh_status()
        if new_status != 'accepted':
            label = 'rejected' if new_status == 'rejected' else 'sent back for rework'
            notify('nesting', f'Parts {label} by Production',
                   f'{entry.qty} x {entry.task.part_name} ({entry.job.job_number or entry.job.nesting_number}) '
                   f'{label}: {entry.review_reason}', f'/nesting/{entry.job_id}', 'alert', 'high')
        return Response(NestingHandoverSerializer(entry).data)

    @action(detail=True, methods=['post'], url_path='accept')
    def accept(self, request, pk=None):
        return self._review(request, pk, 'accepted', False)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        return self._review(request, pk, 'rejected', True)

    @action(detail=True, methods=['post'], url_path='rework')
    def rework(self, request, pk=None):
        return self._review(request, pk, 'rework_required', True)

    @action(detail=True, methods=['post'], url_path='resubmit')
    def resubmit(self, request, pk=None):
        """Nesting has redone the rejected / rework parts and hands them to Production again."""
        with transaction.atomic():
            h = NestingHandover.objects.select_for_update().select_related('job', 'task').get(pk=pk)
            if h.status not in ('rejected', 'rework_required') or h.resolved:
                return err('Only a rejected / rework entry that is still open can be re-submitted.')
            try:
                qty = to_int(body(request, 'qty', 'quantity', default=h.qty))
            except ValueError as e:
                return err(str(e))
            if qty <= 0 or qty > h.qty:
                return err(f'Quantity must be between 1 and {h.qty}.')
            old = split_off(h, qty, resolved=True)
            new = NestingHandover.objects.create(
                job=old.job, task=old.task, qty=qty, kind='rework', rework_of=old.id, handed_by=actor(request),
                handover_remarks=body(request, 'remarks', default='Re-submitted after rework'))
            old.job.refresh_status()
        notify('production', 'Reworked parts handed over again',
               f'{qty} x {new.task.part_name} ({new.job.job_number or new.job.nesting_number}) re-submitted '
               f'after rework.', '/nesting/production-review', 'approval_request', 'high')
        return Response(NestingHandoverSerializer(new).data, status=status.HTTP_201_CREATED)


# ----------------------------------------------------------------------------- sheets
class SheetUsageViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = SheetUsage.objects.all().select_related('job')
    serializer_class = SheetUsageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        jid = qp(self.request, 'jobId', 'job_id')
        if jid:
            qs = qs.filter(job_id=jid)
        return qs

    def perform_create(self, serializer):
        serializer.save(logged_by=actor(self.request), date=serializer.validated_data.get('date')
                        or timezone.now().strftime('%Y-%m-%d'))
