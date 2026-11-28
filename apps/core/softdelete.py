"""
Soft delete for the ERP.

Nothing is physically removed any more: "delete" sets ``is_active = False`` and records who deleted the row and
when. Normal queries (``Model.objects``) only ever see active rows, so every screen, report and total ignores
deleted records automatically. ``Model.all_objects`` sees everything (used for restore and for number
generation, so a new document never re-uses the number of a deleted one).

Usage
-----
    class Lead(SoftDeleteModel):            # adds is_active, deleted_at, deleted_by
        ...

    class LeadViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
        ...                                  # DELETE -> soft delete, POST <id>/restore/ -> restore
"""
from django.db import models
from django.dispatch import Signal
from django.utils import timezone

# Sent after a row has been soft deleted / restored. Accounting listens to these to reverse / re-post ledger entries.
post_soft_delete = Signal()
post_restore = Signal()


def _who(user):
    if user is None or isinstance(user, str):
        return (user or '').strip()
    return (getattr(user, 'name', '') or getattr(user, 'username', '') or str(getattr(user, 'pk', '') or '')).strip()


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self, user=None):  # type: ignore[override]
        """Soft delete every row of the queryset."""
        rows = list(self)
        if not rows:
            return 0, {}
        now, who = timezone.now(), _who(user)
        self.model.all_objects.filter(pk__in=[r.pk for r in rows]).update(
            is_active=False, deleted_at=now, deleted_by=who)
        for row in rows:
            row.is_active, row.deleted_at, row.deleted_by = False, now, who
            post_soft_delete.send(sender=self.model, instance=row)
        return len(rows), {self.model._meta.label: len(rows)}

    def hard_delete(self):
        """Really remove the rows. Only for tests / data clean-up scripts, never from a screen."""
        return super().delete()

    def restore(self):
        rows = list(self.model.all_objects.filter(pk__in=list(self.values_list('pk', flat=True))))
        self.model.all_objects.filter(pk__in=[r.pk for r in rows]).update(is_active=True, deleted_at=None, deleted_by='')
        for row in rows:
            row.is_active, row.deleted_at, row.deleted_by = True, None, ''
            post_restore.send(sender=self.model, instance=row)
        return len(rows)


class ActiveManager(models.Manager.from_queryset(SoftDeleteQuerySet)):  # type: ignore[misc]
    """Default manager: active rows only."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class AllManager(models.Manager.from_queryset(SoftDeleteQuerySet)):  # type: ignore[misc]
    """Every row, active or deleted."""


class SoftDeleteModel(models.Model):
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=150, blank=True, default='')

    objects = ActiveManager()
    all_objects = AllManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, user=None):  # noqa: D401
        """Soft delete this row."""
        now, who = timezone.now(), _who(user)
        type(self).all_objects.filter(pk=self.pk).update(is_active=False, deleted_at=now, deleted_by=who)
        self.is_active, self.deleted_at, self.deleted_by = False, now, who
        post_soft_delete.send(sender=type(self), instance=self)
        return 1, {self._meta.label: 1}

    def hard_delete(self):
        """Really remove the row (tests / maintenance only)."""
        return super().delete()

    def restore(self):
        type(self).all_objects.filter(pk=self.pk).update(is_active=True, deleted_at=None, deleted_by='')
        self.is_active, self.deleted_at, self.deleted_by = True, None, ''
        post_restore.send(sender=type(self), instance=self)


def purge(model):
    """Physically empty a table (factory reset / test-data clean-up only). Soft delete models are removed for real."""
    if issubclass(model, SoftDeleteModel):
        return model.all_objects.all().hard_delete()
    return model.objects.all().delete()


def soft_delete_models():
    """Every concrete model that uses soft delete."""
    from django.apps import apps
    return [m for m in apps.get_models() if issubclass(m, SoftDeleteModel)]


# ------------------------------------------------------------------ DRF
try:  # keep the models module importable without DRF (migrations, scripts)
    from rest_framework import status as _status
    from rest_framework.decorators import action as _action
    from rest_framework.response import Response as _Response
except Exception:  # pragma: no cover
    _status = _action = _Response = None


if _action is not None:
    class SoftDeleteViewSetMixin:
        """DELETE soft deletes (who + when are recorded); ``POST <id>/restore/`` brings the record back."""

        def perform_destroy(self, instance):
            instance.delete(user=self.request.user)

        def _find_any(self, pk):
            model = self.get_queryset().model
            pk_name = model._meta.pk.name
            return model.all_objects.filter(**{pk_name: pk}).first()

        @_action(detail=True, methods=['post'], url_path='restore')
        def restore(self, request, pk=None):
            from .rbac_permissions import is_department_manager
            if not is_department_manager(request.user):
                return _Response({'error': 'Only a manager or admin can restore deleted records.'},
                                 status=_status.HTTP_403_FORBIDDEN)
            obj = self._find_any(pk)
            if obj is None:
                return _Response({'error': 'Record not found.'}, status=_status.HTTP_404_NOT_FOUND)
            if obj.is_active:
                return _Response({'error': 'This record is not deleted.'}, status=_status.HTTP_400_BAD_REQUEST)
            obj.restore()
            return _Response({'success': True, 'id': str(obj.pk), 'message': 'Record restored.'})
