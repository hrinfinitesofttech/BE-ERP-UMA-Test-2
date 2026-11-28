from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import viewsets, serializers, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from . import posting, reports
from .ledger_models import (AccountGroup, Ledger, LedgerEntry, Voucher, DepreciationAsset, StockItem, PaymentRequest)
from .models import PurchaseInvoice, SupplierPayment, SalesInvoice


# ------------------------------------------------------------------ serializers
class AccountGroupSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, default='')

    class Meta:
        model = AccountGroup
        fields = ['id', 'name', 'parent', 'parent_name', 'nature', 'sort_order', 'is_system']


class LedgerSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    nature = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Ledger
        fields = ['id', 'name', 'group', 'group_name', 'nature', 'opening_balance', 'opening_type', 'party_type',
                  'party_id', 'status', 'is_system', 'sort_order', 'balance']

    def get_nature(self, obj):
        g = obj.group
        while g.parent_id:
            g = g.parent
        return g.nature

    def get_balance(self, obj):
        agg = obj.entries.aggregate(d=Sum('debit'), c=Sum('credit'))
        signed = obj.signed_opening + (agg['d'] or 0) - (agg['c'] or 0)
        return {'amount': float(abs(signed)), 'type': 'Dr' if signed >= 0 else 'Cr'}


class LedgerEntrySerializer(serializers.ModelSerializer):
    ledger_name = serializers.CharField(source='ledger.name', read_only=True)

    class Meta:
        model = LedgerEntry
        fields = ['id', 'voucher_type', 'voucher_no', 'voucher_date', 'ledger', 'ledger_name', 'debit', 'credit',
                  'narration', 'source_type', 'source_id']


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = '__all__'
        read_only_fields = ['voucher_no', 'total_amount', 'created_at']

    def validate_lines(self, lines):
        if not lines or len(lines) < 2:
            raise serializers.ValidationError('At least two ledger lines are required.')
        d = sum(Decimal(str(l.get('debit') or 0)) for l in lines)
        c = sum(Decimal(str(l.get('credit') or 0)) for l in lines)
        if d != c:
            raise serializers.ValidationError(f'Voucher not balanced: Debit {d} != Credit {c}.')
        if d <= 0:
            raise serializers.ValidationError('Voucher amount must be greater than zero.')
        for l in lines:
            if not Ledger.objects.filter(pk=l.get('ledger_id')).exists():
                raise serializers.ValidationError(f"Unknown ledger id {l.get('ledger_id')}.")
        return lines


class DepreciationAssetSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    depreciation = serializers.SerializerMethodField()
    wdv = serializers.SerializerMethodField()

    class Meta:
        model = DepreciationAsset
        fields = ['id', 'financial_year', 'group_name', 'particulars', 'rate', 'opening', 'addition1', 'addition2',
                  'sales', 'sort_order', 'total', 'depreciation', 'wdv']

    def _c(self, o):
        return o.compute()

    def get_total(self, o): return float(self._c(o)['total'])
    def get_depreciation(self, o): return float(self._c(o)['depreciation'])
    def get_wdv(self, o): return float(self._c(o)['wdv'])


class StockItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockItem
        fields = '__all__'
        read_only_fields = ['closing_value']


class PaymentRequestSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = PaymentRequest
        fields = '__all__'
        read_only_fields = ['request_no', 'paid_amount', 'payment_number', 'approved_by']

    def get_balance(self, o):
        return float((o.amount or 0) - (o.paid_amount or 0))


# ------------------------------------------------------------------ viewsets
class AccountGroupViewSet(viewsets.ModelViewSet):
    queryset = AccountGroup.objects.select_related('parent').all()
    serializer_class = AccountGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def destroy(self, request, *a, **kw):
        g = self.get_object()
        if g.is_system or g.ledgers.exists() or g.children.exists():
            return Response({'error': 'System groups or groups with ledgers cannot be deleted.'}, status=400)
        return super().destroy(request, *a, **kw)


class LedgerViewSet(viewsets.ModelViewSet):
    queryset = Ledger.objects.select_related('group', 'group__parent').all()
    serializer_class = LedgerSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    search_fields = ['name']
    filterset_fields = ['group', 'status']

    def destroy(self, request, *a, **kw):
        led = self.get_object()
        if led.entries.exists() or led.is_system:
            return Response({'error': 'Ledger has postings or is a system ledger; mark it Inactive instead.'}, status=400)
        return super().destroy(request, *a, **kw)

    @action(detail=True, methods=['get'])
    def statement(self, request, pk=None):
        led = self.get_object()
        return Response(ledger_statement(led, request.query_params.get('from'), request.query_params.get('to')))


def _parse(d, default):
    try:
        return date.fromisoformat(d) if d else default
    except ValueError:
        return default


def ledger_statement(led, d_from, d_to):
    fy_from, fy_to, _ = reports.fy_range()
    d_from, d_to = _parse(d_from, fy_from), _parse(d_to, fy_to)
    prior = led.entries.filter(voucher_date__lt=d_from).aggregate(d=Sum('debit'), c=Sum('credit'))
    opening = led.signed_opening + (prior['d'] or 0) - (prior['c'] or 0)
    run, rows, tdr, tcr = opening, [], Decimal('0'), Decimal('0')
    for e in led.entries.filter(voucher_date__gte=d_from, voucher_date__lte=d_to).order_by('voucher_date', 'id'):
        run += e.debit - e.credit
        tdr += e.debit; tcr += e.credit
        # counter-party ledgers of the same voucher
        others = list(LedgerEntry.objects.filter(source_type=e.source_type, source_id=e.source_id, voucher_no=e.voucher_no)
                      .exclude(pk=e.pk).values_list('ledger__name', flat=True)[:3])
        rows.append({'date': e.voucher_date.isoformat(), 'voucher_type': e.voucher_type, 'voucher_no': e.voucher_no,
                     'particulars': ', '.join(others), 'narration': e.narration, 'debit': float(e.debit),
                     'credit': float(e.credit), 'balance': float(abs(run)), 'balance_type': 'Dr' if run >= 0 else 'Cr'})
    return {'ledger': {'id': led.pk, 'name': led.name, 'group': led.group.name}, 'from': d_from.isoformat(), 'to': d_to.isoformat(),
            'opening': float(abs(opening)), 'opening_type': 'Dr' if opening >= 0 else 'Cr', 'rows': rows,
            'total_debit': float(tdr), 'total_credit': float(tcr), 'closing': float(abs(run)),
            'closing_type': 'Dr' if run >= 0 else 'Cr'}


class DayBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        fy_from, fy_to, _ = reports.fy_range()
        d_from, d_to = _parse(request.query_params.get('from'), date.today() - timedelta(days=30)), _parse(request.query_params.get('to'), date.today())
        qs = LedgerEntry.objects.filter(voucher_date__gte=d_from, voucher_date__lte=d_to).select_related('ledger')
        vt = request.query_params.get('voucher_type')
        if vt:
            qs = qs.filter(voucher_type=vt)
        q = request.query_params.get('q')
        if q:
            qs = qs.filter(Q(voucher_no__icontains=q) | Q(ledger__name__icontains=q) | Q(narration__icontains=q))
        qs = qs.order_by('-voucher_date', '-id')[:1000]
        return Response([{**LedgerEntrySerializer(e).data} for e in qs])


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['voucher_no', 'narration', 'reference']
    filterset_fields = ['voucher_type', 'status']

    PREFIX = {'Payment': 'PMT', 'Receipt': 'RCT', 'Journal': 'JV', 'Contra': 'CNT'}

    def perform_create(self, serializer):
        vt = serializer.validated_data.get('voucher_type', 'Journal')
        prefix = self.PREFIX.get(vt, 'VCH')
        n = Voucher.objects.filter(voucher_type=vt).count() + 1
        no = f"{prefix}-{reports.fy_range()[2]}-{n:04d}"
        while Voucher.objects.filter(voucher_no=no).exists():
            n += 1
            no = f"{prefix}-{reports.fy_range()[2]}-{n:04d}"
        total = sum(Decimal(str(l.get('debit') or 0)) for l in serializer.validated_data['lines'])
        serializer.save(voucher_no=no, total_amount=total, created_by=getattr(self.request.user, 'username', ''))


class DepreciationAssetViewSet(viewsets.ModelViewSet):
    queryset = DepreciationAsset.objects.all()
    serializer_class = DepreciationAssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filterset_fields = ['financial_year', 'group_name']

    @action(detail=False, methods=['get'])
    def chart(self, request):
        fy = request.query_params.get('fy') or reports.fy_range()[2]
        rows = list(DepreciationAsset.objects.filter(financial_year=fy))
        data = DepreciationAssetSerializer(rows, many=True).data
        blocks = {}
        for r in data:
            b = blocks.setdefault(r['group_name'], {'group': r['group_name'], 'opening': 0, 'addition1': 0, 'addition2': 0,
                                                      'sales': 0, 'total': 0, 'depreciation': 0, 'wdv': 0})
            for k in ('addition1', 'addition2', 'sales'):
                b[k] += float(r[k])
            b['opening'] += float(r['opening'])
            for k in ('total', 'depreciation', 'wdv'):
                b[k] += r[k]
        # reconcile with books (ledger closing before depreciation is posted)
        posted = LedgerEntry.objects.filter(source_type='Voucher', voucher_no=f'DEP-{fy}').exists()
        totals = {k: round(sum(b[k] for b in blocks.values()), 2) for k in ('opening', 'addition1', 'addition2', 'sales', 'total', 'depreciation', 'wdv')}
        return Response({'financial_year': fy, 'rows': data, 'blocks': list(blocks.values()), 'totals': totals,
                         'depreciation_posted': posted})

    @action(detail=False, methods=['post'], url_path='post-depreciation')
    def post_depreciation(self, request):
        fy = request.data.get('financial_year') or reports.fy_range()[2]
        amt = posting.post_depreciation(fy)
        return Response({'financial_year': fy, 'amount': float(amt)})

    @action(detail=False, methods=['post'], url_path='carry-forward')
    def carry_forward(self, request):
        """Create next year's chart with Opening = this year's WDV."""
        fy = request.data.get('financial_year') or reports.fy_range()[2]
        y = int(fy[:4]) + 1
        nxt = f"{y}-{str(y + 1)[2:]}"
        n = 0
        for a in DepreciationAsset.objects.filter(financial_year=fy):
            _, new = DepreciationAsset.objects.get_or_create(
                financial_year=nxt, particulars=a.particulars,
                defaults={'group_name': a.group_name, 'rate': a.rate, 'opening': a.compute()['wdv'], 'sort_order': a.sort_order})
            n += int(new)
        return Response({'next_year': nxt, 'created': n})


class StockItemViewSet(viewsets.ModelViewSet):
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    search_fields = ['name']
    filterset_fields = ['category']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        data = StockItemSerializer(StockItem.objects.all(), many=True).data
        cats = {}
        for r in data:
            c = cats.setdefault(r['category'], {'category': r['category'], 'count': 0, 'value': 0.0, 'qty_items': 0})
            c['count'] += 1
            c['value'] += float(r['closing_value'])
            c['qty_items'] += 1 if float(r['closing_qty']) else 0
        return Response({'items': data, 'categories': list(cats.values()),
                         'total_value': round(sum(c['value'] for c in cats.values()), 2), 'count': len(data)})

    @action(detail=False, methods=['post'], url_path='sync-from-store')
    def sync_from_store(self, request):
        """Pull live quantities & valuation from the Store module (StockBalance) into the accounts stock list."""
        from apps.store.models import StockBalance, ItemMaster
        agg, created, updated = {}, 0, 0
        for b in StockBalance.objects.all():
            a = agg.setdefault(b.item_code, {'name': b.item_name, 'uom': b.uom, 'cat': b.category, 'qty': 0.0, 'val': 0.0})
            a['qty'] += float(b.quantity or 0)
            a['val'] += float(b.total_value or (b.quantity or 0) * (b.unit_rate or 0))
        types = {i.item_code: i.item_type for i in ItemMaster.objects.all()}
        for code, a in agg.items():
            qty = Decimal(str(round(a['qty'], 3)))
            rate = Decimal(str(round(a['val'] / a['qty'], 2))) if a['qty'] else Decimal('0')
            cat = 'Finished Goods' if 'finish' in (types.get(code) or a['cat'] or '').lower() else 'Raw Material'
            obj = StockItem.objects.filter(Q(store_item_code=code) | Q(name__iexact=a['name'])).first()
            if obj:
                obj.closing_qty, obj.rate, obj.store_item_code, obj.uom = qty, rate, code, a['uom'] or obj.uom
                obj.save(); updated += 1
            else:
                StockItem.objects.create(name=a['name'], category=cat, uom=a['uom'], closing_qty=qty, rate=rate,
                                         store_item_code=code, sub_group='From Store'); created += 1
        return Response({'created': created, 'updated': updated, 'store_items': len(agg)})


class PaymentRequestViewSet(viewsets.ModelViewSet):
    queryset = PaymentRequest.objects.all()
    serializer_class = PaymentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['request_no', 'supplier_name', 'source_ref', 'po_number', 'description']
    filterset_fields = ['status', 'department', 'supplier_id', 'source_type', 'po_number']

    def perform_create(self, serializer):
        n = PaymentRequest.objects.count() + 1
        no = f"PR-{timezone.now().strftime('%y%m')}-{n:04d}"
        while PaymentRequest.objects.filter(request_no=no).exists():
            n += 1
            no = f"PR-{timezone.now().strftime('%y%m')}-{n:04d}"
        serializer.save(request_no=no, requested_by=serializer.validated_data.get('requested_by') or getattr(self.request.user, 'username', ''))

    @action(detail=False, methods=['get'])
    def summary(self, request):
        qs = PaymentRequest.objects.all()
        out = {}
        for s in ('Pending', 'Approved', 'Paid', 'Rejected'):
            sub = qs.filter(status=s)
            out[s] = {'count': sub.count(), 'amount': float(sub.aggregate(a=Sum('amount'))['a'] or 0)}
        return Response(out)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        r = self.get_object()
        if r.status not in ('Pending',):
            return Response({'error': f'Cannot approve a {r.status} request.'}, status=400)
        r.status = 'Approved'
        r.approved_by = getattr(request.user, 'username', '') or 'Accounts'
        r.save()
        return Response(PaymentRequestSerializer(r).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        r = self.get_object()
        if r.status == 'Paid':
            return Response({'error': 'Already paid.'}, status=400)
        r.status = 'Rejected'
        r.remarks = request.data.get('remarks') or r.remarks
        r.save()
        return Response(PaymentRequestSerializer(r).data)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """Accounts pays the request: creates a SupplierPayment (-> ledger posting) and updates the source invoice."""
        r = self.get_object()
        if r.status not in ('Approved', 'Pending'):
            return Response({'error': f'Cannot pay a {r.status} request.'}, status=400)
        try:
            amt = Decimal(str(request.data.get('amount') or (r.amount - r.paid_amount)))
        except Exception:
            return Response({'error': 'Invalid amount.'}, status=400)
        if amt <= 0 or amt > (r.amount - r.paid_amount):
            return Response({'error': 'Amount must be > 0 and not exceed the outstanding balance.'}, status=400)
        n = SupplierPayment.all_objects.count() + 1
        no = f"PAY-SUP-{timezone.now().strftime('%Y%m%d')}-{n:03d}"
        while SupplierPayment.objects.filter(Q(id=no) | Q(payment_number=no)).exists():
            n += 1
            no = f"PAY-SUP-{timezone.now().strftime('%Y%m%d')}-{n:03d}"
        inv_no = r.source_ref if r.source_type == 'Purchase Invoice' else ''
        SupplierPayment.objects.create(
            id=no, payment_number=no, payment_date=_parse(request.data.get('payment_date'), date.today()),
            supplier_id=r.supplier_id or r.supplier_name, supplier_name=r.supplier_name,
            purchase_invoice_number=inv_no, payment_mode=request.data.get('payment_mode') or 'Bank Transfer',
            bank_name=request.data.get('bank_name') or '', amount=amt,
            reference_number=request.data.get('reference_number') or r.request_no, status='Paid',
            remarks=f'Against {r.request_no}', created_by=getattr(request.user, 'username', 'Accounts'))
        # update bill outstanding (SupplierPaymentViewSet logic does this only via its own perform_create)
        if inv_no:
            inv = PurchaseInvoice.objects.filter(invoice_number=inv_no).first()
            if inv:
                inv.paid_amount = Decimal(str(inv.paid_amount or 0)) + amt
                inv.outstanding_amount = max(Decimal('0'), Decimal(str(inv.grand_total)) - inv.paid_amount)
                inv.payment_status = 'Paid' if inv.outstanding_amount == 0 else 'Partially Paid'
                inv.status = 'Paid' if inv.outstanding_amount == 0 else inv.status
                inv.save()
        r.refresh_from_db()
        if not inv_no:  # invoice-backed requests were already synced from the bill itself
            r.paid_amount = (r.paid_amount or 0) + amt
        r.payment_number = no
        r.status = 'Paid' if r.paid_amount >= r.amount else 'Approved'
        r.save()
        return Response(PaymentRequestSerializer(r).data)


# ------------------------------------------------------------------ report + setup endpoints
class ReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, kind):
        fy = request.query_params.get('fy')
        if kind == 'trial-balance':
            return Response(reports.trial_balance(fy))
        if kind == 'profit-loss':
            return Response(reports.strip_raw(reports.profit_loss(fy)))
        if kind == 'balance-sheet':
            return Response(reports.strip_raw(reports.balance_sheet(fy)))
        if kind == 'ratio-analysis':
            return Response(reports.ratio_analysis(fy))
        return Response({'error': 'Unknown report'}, status=404)


class SetupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, action_name):
        if action_name == 'seed':
            return Response(posting.seed_master())
        if action_name == 'rebuild':
            return Response(posting.rebuild_all())
        return Response({'error': 'Unknown action'}, status=404)

    def get(self, request, action_name):
        if action_name == 'status':
            return Response({'groups': AccountGroup.objects.count(), 'ledgers': Ledger.objects.count(),
                             'entries': LedgerEntry.objects.count(), 'dep_assets': DepreciationAsset.objects.count(),
                             'stock_items': StockItem.objects.count(), 'financial_year': reports.fy_range()[2]})
        return Response({'error': 'Unknown action'}, status=404)
