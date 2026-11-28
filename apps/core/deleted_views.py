"""Track and restore soft-deleted records across the whole ERP (admin / manager only)."""
from django.apps import apps
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .rbac_permissions import is_department_manager
from .softdelete import soft_delete_models


def _label(obj):
    try:
        return str(obj)[:160]
    except Exception:
        return str(obj.pk)


class DeletedRecordsView(APIView):
    """
    GET  /api/core/deleted-records/?model=crm.Lead&search=abc&limit=100
         -> deleted rows (newest first) with who deleted them and when; without ``model`` all models are listed
    POST /api/core/deleted-records/  {"model": "crm.Lead", "id": "LEAD-2026-0005"}  -> restore
    """
    permission_classes = [permissions.IsAuthenticated]

    def _guard(self, request):
        if not is_department_manager(request.user):
            return Response({'error': 'Only a manager or admin can view or restore deleted records.'},
                            status=status.HTTP_403_FORBIDDEN)
        return None

    def get(self, request):
        denied = self._guard(request)
        if denied:
            return denied
        wanted = (request.query_params.get('model') or '').strip().lower()
        search = (request.query_params.get('search') or '').strip().lower()
        try:
            limit = max(1, min(int(request.query_params.get('limit') or 200), 1000))
        except ValueError:
            limit = 200

        rows = []
        models_ = soft_delete_models()
        if wanted:
            models_ = [m for m in models_ if m._meta.label.lower() == wanted or m.__name__.lower() == wanted]
        for model in models_:
            for obj in model.all_objects.filter(is_active=False).order_by('-deleted_at')[:limit]:
                label = _label(obj)
                if search and search not in label.lower() and search not in str(obj.pk).lower():
                    continue
                rows.append({
                    'model': model._meta.label,
                    'modelName': str(model._meta.verbose_name).title(),
                    'id': str(obj.pk),
                    'label': label,
                    'deletedAt': obj.deleted_at.isoformat() if obj.deleted_at else '',
                    'deletedBy': obj.deleted_by,
                })
        rows.sort(key=lambda r: r['deletedAt'], reverse=True)
        return Response(rows[:limit])

    def post(self, request):
        denied = self._guard(request)
        if denied:
            return denied
        label = str(request.data.get('model') or '').strip()
        pk = request.data.get('id')
        try:
            model = apps.get_model(label)
        except (LookupError, ValueError):
            return Response({'error': f'Unknown model "{label}".'}, status=status.HTTP_400_BAD_REQUEST)
        if model not in soft_delete_models():
            return Response({'error': f'{label} does not support restore.'}, status=status.HTTP_400_BAD_REQUEST)
        obj = model.all_objects.filter(pk=pk).first()
        if obj is None:
            return Response({'error': 'Record not found.'}, status=status.HTTP_404_NOT_FOUND)
        if obj.is_active:
            return Response({'error': 'This record is not deleted.'}, status=status.HTTP_400_BAD_REQUEST)
        obj.restore()
        return Response({'success': True, 'model': label, 'id': str(obj.pk), 'message': 'Record restored.'})
