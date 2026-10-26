from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.core.approval_security import (
    validate_approval_permission,
    validate_approval_transition,
    validate_edit_safety,
    log_approval_audit,
)


from .models import (
    Supplier,
    SupplierContact,
    PurchaseRequisition,
    RequestForQuotation,
    SupplierQuotation,
    QuotationComparison,
    PurchaseOrder,
    PurchaseReturn,
    MaterialRequirement,
)
from .serializers import (
    SupplierSerializer,
    SupplierContactSerializer,
    PurchaseRequisitionSerializer,
    RequestForQuotationSerializer,
    SupplierQuotationSerializer,
    QuotationComparisonSerializer,
    PurchaseOrderSerializer,
    PurchaseReturnSerializer,
    MaterialRequirementSerializer,
)


class MaterialRequirementViewSet(viewsets.ModelViewSet):
    queryset = MaterialRequirement.objects.all().order_by('-created_at')
    serializer_class = MaterialRequirementSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = f"MRP-REQ-{MaterialRequirement.objects.count() + 1:05d}"
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by('-created_at', '-id')
    serializer_class = SupplierSerializer
    permission_classes = [permissions.AllowAny]


class SupplierContactViewSet(viewsets.ModelViewSet):
    queryset = SupplierContact.objects.all().order_by('-id')
    serializer_class = SupplierContactSerializer
    permission_classes = [permissions.AllowAny]


from django.db.models import Q
from django.http import Http404


class PurchaseRequisitionViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.all().order_by('-created_at', '-id')
    serializer_class = PurchaseRequisitionSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        pk = self.kwargs.get('pk')
        obj = PurchaseRequisition.objects.filter(Q(id=pk) | Q(pr_number=pk)).first()
        if not obj:
            raise Http404(f"Purchase Requisition '{pk}' not found")
        return obj

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        pr_num = data.get('prNumber') or data.get('pr_number') or data.get('id') or f"PR-2026-{PurchaseRequisition.objects.count() + 1:04d}"
        pr_id = data.get('id') or pr_num

        pr_obj, _ = PurchaseRequisition.objects.update_or_create(
            id=pr_id,
            defaults={
                'pr_number': pr_num,
                'project_id': data.get('projectId') or data.get('project_id', '') or 'PRJ-2026-0001',
                'job_code': data.get('jobId') or data.get('jobNumber') or data.get('job_code', '') or 'JOB-2026-001',
                'requested_by': data.get('requestedBy') or data.get('requested_by') or 'Purchase Admin',
                'department': data.get('department') or 'Purchase / Planning',
                'request_date': data.get('requisitionDate') or data.get('prDate') or data.get('request_date') or datetime.now().strftime('%Y-%m-%d'),
                'required_by_date': data.get('requiredByDate') or data.get('required_by_date') or data.get('requiredDate') or '2026-12-31',
                'priority': data.get('priority') or 'High',
                'status': data.get('status') or 'Submitted',
                'items': data.get('items') if isinstance(data.get('items'), list) else [],
                'total_estimated_cost': float(data.get('estimatedCost') or data.get('total_estimated_cost') or 0),
                'remarks': data.get('remarks', ''),
                'approved_by': data.get('approvedBy') or data.get('approved_by'),
            }
        )
        return Response(PurchaseRequisitionSerializer(pr_obj).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        pr = self.get_object()
        safe, err_resp = validate_edit_safety(pr, request.data)
        if not safe:
            return err_resp
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'status' in data:
            pr.status = data['status']
        if 'approvedBy' in data or 'approved_by' in data:
            pr.approved_by = data.get('approvedBy') or data.get('approved_by')
        if 'remarks' in data:
            pr.remarks = data['remarks']
        if 'priority' in data:
            pr.priority = data['priority']
        if 'items' in data and isinstance(data['items'], list):
            pr.items = data['items']
        if 'estimatedCost' in data or 'total_estimated_cost' in data:
            pr.total_estimated_cost = float(data.get('estimatedCost') or data.get('total_estimated_cost') or pr.total_estimated_cost)
        pr.save()
        return Response(PurchaseRequisitionSerializer(pr).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'patch'], url_path='approve')
    def approve(self, request, pk=None):
        pr = self.get_object()
        
        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Purchase', 'Procurement', 'Stores', 'Production', 'Planning', 'Management'],
            allowed_roles=['Purchase Manager', 'Store Manager', 'Production Manager', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        valid_trans, trans_resp = validate_approval_transition(pr.status, 'approve')
        if not valid_trans:
            return trans_resp

        approver = user_info['name'] or request.data.get('approvedBy') or request.data.get('approved_by') or 'Purchase Admin'
        notes = request.data.get('comment') or request.data.get('approvalNotes') or 'Requisition approved'

        pr.status = 'Approved'
        pr.approved_by = approver
        if notes:
            pr.remarks = f"{pr.remarks} | Approved: {notes}".strip(' |')
        pr.save()

        log_approval_audit(user_info, 'APPROVE', 'Purchase', 'PurchaseRequisition', pr.id, notes)
        return Response(PurchaseRequisitionSerializer(pr).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'patch'], url_path='reject')
    def reject(self, request, pk=None):
        pr = self.get_object()
        
        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Purchase', 'Procurement', 'Stores', 'Production', 'Planning', 'Management'],
            allowed_roles=['Purchase Manager', 'Store Manager', 'Production Manager', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        valid_trans, trans_resp = validate_approval_transition(pr.status, 'reject')
        if not valid_trans:
            return trans_resp

        reason = request.data.get('reason') or request.data.get('rejectionReason') or request.data.get('remarks') or 'Requisition rejected'
        pr.status = 'Rejected'
        pr.remarks = f"{pr.remarks} | Rejected: {reason}".strip(' |')
        pr.save()

        log_approval_audit(user_info, 'REJECT', 'Purchase', 'PurchaseRequisition', pr.id, reason)
        return Response(PurchaseRequisitionSerializer(pr).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'patch'], url_path='disapprove')
    def disapprove(self, request, pk=None):
        return self.reject(request, pk=pk)


    @action(detail=True, methods=['post'], url_path='convert-to-rfq')
    def convert_to_rfq(self, request, pk=None):
        pr = self.get_object()
        rfq_code = f"RFQ-2026-{RequestForQuotation.objects.count() + 1:04d}"
        rfq = RequestForQuotation.objects.create(
            id=rfq_code,
            rfq_number=rfq_code,
            pr_id=pr.id,
            rfq_date=datetime.now().strftime('%Y-%m-%d'),
            due_date=request.data.get('dueDate') or request.data.get('due_date', ''),
            suppliers=request.data.get('suppliers', []),
            items=pr.items,
            status='sent',
            terms_and_conditions='Payment terms: 30 days. Delivery: Vadodara Makarpura unit.',
        )
        pr.status = 'converted_to_rfq'
        pr.save(update_fields=['status'])
        return Response(RequestForQuotationSerializer(rfq).data, status=status.HTTP_201_CREATED)


class RequestForQuotationViewSet(viewsets.ModelViewSet):
    queryset = RequestForQuotation.objects.all().order_by('-created_at', '-id')
    serializer_class = RequestForQuotationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            rfq_num = data.get('rfqNumber') or data.get('rfq_number') or f"RFQ-2026-{RequestForQuotation.objects.count() + 1:04d}"
            data['id'] = rfq_num
            data['rfq_number'] = rfq_num
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='send-email')
    def send_email_direct(self, request):
        rfq_payload = request.data.get('rfq') or {}
        rfq_id = request.data.get('id') or request.data.get('rfqId') or request.data.get('rfqNumber') or rfq_payload.get('rfqNumber') or rfq_payload.get('id')
        return self.send_email(request, pk=rfq_id)

    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        import logging
        import re
        from django.db import models
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        from apps.purchase.rfq_pdf import generate_rfq_pdf
        logger = logging.getLogger(__name__)

        rfq_payload = request.data.get('rfq') or request.data
        rfq = None
        if pk:
            rfq = RequestForQuotation.objects.filter(models.Q(id=pk) | models.Q(rfq_number=pk)).first()
        if not rfq and rfq_payload:
            payload_num = rfq_payload.get('rfqNumber') or rfq_payload.get('rfq_number') or rfq_payload.get('id')
            if payload_num:
                rfq = RequestForQuotation.objects.filter(models.Q(id=payload_num) | models.Q(rfq_number=payload_num)).first()

        if not rfq:
            # Auto-create or instantiate from payload for seamless client resilience
            rfq_num = rfq_payload.get('rfqNumber') or rfq_payload.get('rfq_number') or str(pk or 'REQ-2026')
            s_name = rfq_payload.get('supplierName') or rfq_payload.get('supplier_name') or rfq_payload.get('vendorName') or 'Supplier'
            s_email = rfq_payload.get('supplierEmail') or rfq_payload.get('supplier_email') or request.data.get('recipientEmail') or ''
            s_mobile = rfq_payload.get('supplierMobile') or rfq_payload.get('supplier_mobile') or ''
            s_id = rfq_payload.get('supplierId') or rfq_payload.get('supplier_id') or ''
            s_addr = rfq_payload.get('supplierAddress') or rfq_payload.get('supplier_address') or ''
            s_gstin = rfq_payload.get('supplierGstin') or rfq_payload.get('supplier_gstin') or ''
            p_id = rfq_payload.get('projectId') or rfq_payload.get('project_id') or 'General'
            r_date = rfq_payload.get('rfqDate') or rfq_payload.get('rfq_date') or ''
            d_date = rfq_payload.get('dueDate') or rfq_payload.get('due_date') or ''
            itms = rfq_payload.get('items') or []
            subj = rfq_payload.get('subject') or 'Material Purchase Requirement'
            s_note = rfq_payload.get('specialNote') or rfq_payload.get('special_note') or ''
            deliv = rfq_payload.get('deliveryLocation') or rfq_payload.get('delivery_location') or 'RAJPUR'

            try:
                rfq = RequestForQuotation.objects.create(
                    id=str(pk),
                    rfq_number=rfq_num,
                    supplier_id=s_id,
                    supplier_name=s_name,
                    supplier_mobile=s_mobile,
                    supplier_email=s_email,
                    supplier_address=s_addr,
                    supplier_gstin=s_gstin,
                    project_id=p_id,
                    rfq_date=r_date,
                    due_date=d_date,
                    items=itms,
                    subject=subj,
                    special_note=s_note,
                    delivery_location=deliv,
                    status='Sent to Suppliers'
                )
            except Exception as ex:
                logger.warning(f"Auto-creating RFQ {pk} encountered ({ex}), using memory object.")
                from types import SimpleNamespace
                rfq = SimpleNamespace(
                    id=str(pk),
                    rfq_number=rfq_num,
                    supplier_id=s_id,
                    supplier_name=s_name,
                    supplier_mobile=s_mobile,
                    supplier_email=s_email,
                    supplier_address=s_addr,
                    supplier_gstin=s_gstin,
                    project_id=p_id,
                    rfq_date=r_date,
                    due_date=d_date,
                    items=itms,
                    subject=subj,
                    special_note=s_note,
                    delivery_location=deliv,
                    status='Sent to Suppliers',
                    save=lambda *args, **kwargs: None
                )

        # Collect and deduplicate recipients (Primary + Additional selected vendors)
        raw_recipients = []

        # 1. Direct explicit recipient
        single_recip = request.data.get('recipientEmail') or request.data.get('recipient_email') or request.data.get('email')
        if single_recip:
            if isinstance(single_recip, list):
                raw_recipients.extend(single_recip)
            else:
                raw_recipients.extend(str(single_recip).split(','))

        # 2. Multi-recipients list
        multi_recips = request.data.get('recipients') or request.data.get('additionalEmails') or []
        if isinstance(multi_recips, list):
            raw_recipients.extend(multi_recips)
        elif isinstance(multi_recips, str):
            raw_recipients.extend(multi_recips.split(','))

        # 3. Fallback to RFQ vendor email
        rfq_email = getattr(rfq, 'supplier_email', '')
        if not rfq_email and getattr(rfq, 'suppliers', None):
            supps = rfq.suppliers
            if isinstance(supps, list) and len(supps) > 0 and isinstance(supps[0], dict):
                rfq_email = supps[0].get('supplierEmail') or supps[0].get('email') or ''
        if rfq_email:
            raw_recipients.append(rfq_email)

        # Clean and filter valid email strings
        recipients = []
        for r in raw_recipients:
            cleaned = str(r or '').strip()
            if cleaned and '@' in cleaned and cleaned.lower() not in [e.lower() for e in recipients]:
                recipients.append(cleaned)

        if not recipients:
            return Response(
                {'error': 'No valid recipient email address provided. Please specify a supplier email.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update and persist primary email to RFQ
        if recipients and hasattr(rfq, 'save'):
            try:
                rfq.supplier_email = recipients[0]
                rfq.status = 'Sent to Suppliers'
                rfq.save(update_fields=['supplier_email', 'status'])
            except Exception:
                pass

        # Generate official RFQ inquiry PDF
        clean_rfq_num = re.sub(r'[^A-Za-z0-9_-]', '_', str(getattr(rfq, 'rfq_number', None) or pk or 'REQ'))
        pdf_filename = f"Official_Purchase_Inquiry_{clean_rfq_num}.pdf"
        pdf_bytes = None
        try:
            pdf_bytes = generate_rfq_pdf(rfq, payload=rfq_payload)
            logger.info(f"Generated RFQ PDF '{pdf_filename}' ({len(pdf_bytes)} bytes)")
        except Exception as pdf_ex:
            logger.warning(f"Error generating RFQ PDF: {pdf_ex}")

        # Items text & HTML rows
        items = getattr(rfq, 'items', []) or rfq_payload.get('items') or []
        items_rows_html = ""
        items_text = ""
        for idx, itm in enumerate(items, 1):
            p_name = itm.get('itemName') or itm.get('item_name') or itm.get('description') or f"Item {idx}"
            spec = itm.get('dimensions') or itm.get('specification') or ''
            qty = float(itm.get('quantity') or itm.get('requiredQuantity') or itm.get('required_quantity') or 1)
            unit = itm.get('unitOfMeasure') or itm.get('unit_of_measure') or 'NOS'

            items_text += f"  {idx}. {p_name} {f'({spec})' if spec else ''} | Required Qty: {qty:g} {unit}\n"
            desc_html = f'<div style="font-size: 11px; color: #6b7280; margin: 2px 0 0 0;">Specification: {spec}</div>' if spec else ''
            items_rows_html += f"""
            <tr style="border-bottom: 1px solid #f0e6dd;">
              <td style="padding: 9px 8px; vertical-align: top; font-weight: bold; font-size: 12px; color: #75401f; width: 32px;">#{idx}</td>
              <td style="padding: 9px 8px; vertical-align: top;">
                <div style="font-weight: 700; font-size: 13px; color: #1f2937;">{p_name}</div>
                {desc_html}
              </td>
              <td align="center" style="padding: 9px 8px; vertical-align: top; white-space: nowrap;">
                <span style="font-size: 13px; font-weight: 800; color: #047857; background: #ecfdf5; padding: 2px 8px; border-radius: 4px; border: 1px solid #a7f3d0;">
                  {qty:g} {unit}
                </span>
              </td>
            </tr>
            """

        subject = f"Official Purchase Inquiry (REQUIRE) - {rfq.rfq_number} - UMA TECHNO FAB PVT. LTD."

        email_text = f"""Dear Valued Vendor / Supplier,

Please find our official Material Purchase Requirement / Inquiry (REQUIRE) from UMA TECHNO FAB PVT. LTD.

============================================================
INQUIRY DETAILS:
Requisition No : {rfq.rfq_number}
Date           : {rfq.rfq_date}
Required By    : {rfq.due_date or 'Earliest / Immediate'}
Project Ref    : {rfq.project_id or 'General'}
Subject        : {rfq.subject or 'Material Purchase Requirement'}
Delivery Site  : {rfq.delivery_location or 'Rajpur Works'}
Official PDF   : {pdf_filename} (Attached)
============================================================

REQUIRED MATERIAL SPECIFICATIONS:
{items_text}

Special Instructions:
{rfq.special_note or 'Please send your best discounted commercial quotation, delivery timeline, and confirm Test Certificate (TC) availability.'}

Commercial Terms:
- Material strictly along with Delivery Challan, Tax Invoice & Test Certificate (TC).
- Please mention rate per unit/kg and applicable GST.
- Inspection compliant with standard industrial fabrication norms.

The complete official inquiry letter is attached as PDF: {pdf_filename}

Warm Regards,
Purchase & Procurement Department
UMA TECHNO FAB PVT. LTD.
Plot No. 48/B, GIDC Industrial Estate, Makarpura, Vadodara - 390010, Gujarat, India
Works: Kadi - Mehsana Highway, Rajpur, Dist. Mehsana, Gujarat
Web: www.umatechnofab.com | Email: info@umatechnofab.com
"""

        from_email_setting = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'UMA TECHNO FAB <hrinfinitesofttech@gmail.com>'
        email_match = re.search(r'<([^>]+)>', str(from_email_setting))
        reply_to_addr = email_match.group(1).strip() if email_match else str(from_email_setting).strip()

        email_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 16px; background-color: #f6f3ee; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #ebd8c8; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
    <!-- Top Accent Bar -->
    <tr>
      <td height="6" style="background: #75401f;"></td>
    </tr>
    <!-- Header -->
    <tr>
      <td style="padding: 20px 24px 14px 24px; border-bottom: 1px solid #f0e6dd; background: #faf7f2;">
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
          <tr>
            <td>
              <h2 style="margin: 0; font-size: 18px; color: #75401f; font-weight: 800; letter-spacing: -0.5px;">UMA TECHNO FAB PVT. LTD.</h2>
              <div style="font-size: 11px; color: #70665f; margin-top: 2px;">Purchase & Procurement Department • Official Material Inquiry</div>
            </td>
            <td align="right">
              <span style="font-size: 11px; font-weight: 700; color: #75401f; background: #ebd8c8; padding: 4px 10px; border-radius: 6px; font-family: monospace;">
                {rfq.rfq_number}
              </span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    <!-- Body -->
    <tr>
      <td style="padding: 20px 24px;">
        <p style="font-size: 13px; color: #374151; margin: 0 0 14px 0; line-height: 1.5;">
          Dear <strong>{rfq.supplier_name or 'Valued Vendor'}</strong>,
        </p>
        <p style="font-size: 13px; color: #374151; margin: 0 0 16px 0; line-height: 1.5;">
          We are pleased to invite your best quotation for the material purchase requirements outlined below.
          The official stamped Inquiry Letter has been attached in PDF format: <strong>{pdf_filename}</strong>.
        </p>

        <!-- Metadata Box -->
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background: #faf7f2; border-radius: 8px; border: 1px solid #ebd8c8; margin-bottom: 18px; font-size: 12px;">
          <tr>
            <td style="padding: 10px 14px; border-bottom: 1px solid #ebd8c8;" width="50%">
              <span style="color: #70665f;">Inquiry Reference:</span> <strong style="color: #1f2937; font-family: monospace;">{rfq.rfq_number}</strong>
            </td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #ebd8c8;" width="50%">
              <span style="color: #70665f;">Date:</span> <strong style="color: #1f2937;">{rfq.rfq_date}</strong>
            </td>
          </tr>
          <tr>
            <td style="padding: 10px 14px;" width="50%">
              <span style="color: #70665f;">Linked Project:</span> <strong style="color: #75401f; font-family: monospace;">{rfq.project_id or 'General'}</strong>
            </td>
            <td style="padding: 10px 14px;" width="50%">
              <span style="color: #70665f;">Delivery Site:</span> <strong style="color: #1f2937;">{rfq.delivery_location or 'Rajpur Works'}</strong>
            </td>
          </tr>
        </table>

        <!-- Material Items Table -->
        <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #1f2937; font-weight: 700; text-transform: uppercase;">
          Required Material Items ({len(items)} items)
        </h4>
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="border-collapse: collapse; margin-bottom: 18px;">
          <thead>
            <tr style="border-bottom: 2px solid #ebd8c8; background: #fdfaf6;">
              <th align="left" style="padding: 8px; font-size: 11px; color: #70665f; font-weight: 700; width: 32px;">#</th>
              <th align="left" style="padding: 8px; font-size: 11px; color: #70665f; font-weight: 700;">Description</th>
              <th align="center" style="padding: 8px; font-size: 11px; color: #70665f; font-weight: 700; width: 90px;">Quantity</th>
            </tr>
          </thead>
          <tbody>
            {items_rows_html}
          </tbody>
        </table>

        <!-- Special Instructions Box -->
        {f'''
        <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px 14px; border-radius: 6px; font-size: 12px; color: #92400e; margin-bottom: 18px;">
          <strong>Special Instructions:</strong><br/>
          {rfq.special_note}
        </div>
        ''' if rfq.special_note else ''}

        <!-- Terms Box -->
        <div style="background: #faf7f2; border: 1px solid #ebd8c8; padding: 12px 14px; border-radius: 6px; font-size: 11px; color: #544b45; line-height: 1.5; margin-bottom: 20px;">
          <strong style="color: #75401f;">Inquiry Terms:</strong><br/>
          • Please reply with your best discounted rate per unit/kg and delivery schedule.<br/>
          • Material must strictly be accompanied by Tax Invoice, Delivery Challan & Test Certificate (TC).<br/>
          • Complete technical specifications and official letterhead are attached in the PDF.
        </div>

        <!-- Footer Contact -->
        <div style="padding-top: 14px; border-top: 1px solid #f0e6dd; font-size: 11px; color: #70665f; line-height: 1.4;">
          <strong style="color: #1f2937;">UMA TECHNO FAB PVT. LTD.</strong><br/>
          Plot No. 48/B, GIDC Industrial Estate, Makarpura, Vadodara - 390010<br/>
          Email: <a href="mailto:{reply_to_addr}" style="color: #75401f; text-decoration: none;">{reply_to_addr}</a> • Web: www.umatechnofab.com
        </div>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        try:
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=email_text,
                from_email=from_email_setting,
                to=recipients,
                reply_to=[reply_to_addr],
                headers={
                    'X-Mailer': 'UMA ERP Purchase System',
                    'X-Priority': '3',
                }
            )
            email_msg.attach_alternative(email_html, "text/html")
            if pdf_bytes:
                email_msg.attach(pdf_filename, pdf_bytes, 'application/pdf')

            email_msg.send(fail_silently=False)

            return Response({
                'success': True,
                'message': f"Official Purchase Inquiry {rfq.rfq_number} successfully dispatched via SMTP to {len(recipients)} recipient(s) with attached PDF ({pdf_filename}).",
                'rfqId': rfq.id,
                'rfqNumber': rfq.rfq_number,
                'recipients': recipients,
                'pdfFilename': pdf_filename,
            }, status=status.HTTP_200_OK)

        except Exception as mail_ex:
            logger.error(f"Failed to dispatch RFQ email via SMTP: {mail_ex}", exc_info=True)
            return Response({
                'success': False,
                'error': f"SMTP dispatch failed: {str(mail_ex)}",
                'recipients': recipients,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupplierQuotationViewSet(viewsets.ModelViewSet):
    queryset = SupplierQuotation.objects.all().order_by('-created_at', '-id')
    serializer_class = SupplierQuotationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            sq_num = data.get('quotationNumber') or data.get('quotation_number') or f"SQ-2026-{SupplierQuotation.objects.count() + 1:04d}"
            data['id'] = sq_num
            data['quotation_number'] = sq_num
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuotationComparisonViewSet(viewsets.ModelViewSet):
    queryset = QuotationComparison.objects.all().order_by('-created_at', '-id')
    serializer_class = QuotationComparisonSerializer
    permission_classes = [permissions.AllowAny]


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().order_by('-created_at', '-id')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        pk = self.kwargs.get('pk')
        obj = PurchaseOrder.objects.filter(Q(id=pk) | Q(po_number=pk)).first()
        if not obj:
            raise Http404(f"Purchase Order '{pk}' not found")
        return obj

    def create(self, request, *args, **kwargs):
        import threading
        if not hasattr(self.__class__, '_create_lock'):
            self.__class__._create_lock = threading.Lock()

        with self.__class__._create_lock:
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            po_num = data.get('poNumber') or data.get('po_number') or data.get('id')
            if not po_num:
                count = PurchaseOrder.objects.count() + 1
                po_num = f"PO-2026-{count:04d}"
                while PurchaseOrder.objects.filter(Q(id=po_num) | Q(po_number=po_num)).exists():
                    count += 1
                    po_num = f"PO-2026-{count:04d}"
            po_id = data.get('id') or po_num
            data['id'] = po_id
            data['po_number'] = po_num

            existing = PurchaseOrder.objects.filter(Q(id=po_id) | Q(po_number=po_num)).first()
            if existing:
                serializer = self.get_serializer(existing, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data, status=status.HTTP_200_OK)

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        safe, err_resp = validate_edit_safety(instance, request.data)
        if not safe:
            return err_resp
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'patch'], url_path='approve')
    def approve_po(self, request, pk=None):
        po = self.get_object()
        
        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Purchase', 'Procurement', 'Management'],
            allowed_roles=['Purchase Manager', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        valid_trans, trans_resp = validate_approval_transition(po.status, 'approve')
        if not valid_trans:
            return trans_resp

        approver = user_info['name'] or request.data.get('approvedBy') or request.data.get('approved_by') or 'Purchase Manager'
        comment = request.data.get('comment') or request.data.get('approvalNotes') or 'PO Approved'

        po.status = 'Approved'
        po.approved_by = approver
        if comment:
            po.remarks = f"{po.remarks} | Approved: {comment}".strip(' |')
        po.save(update_fields=['status', 'approved_by', 'remarks'])

        log_approval_audit(user_info, 'APPROVE', 'Purchase', 'PurchaseOrder', po.id, comment)
        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'patch'], url_path='reject')
    def reject_po(self, request, pk=None):
        po = self.get_object()
        
        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Purchase', 'Procurement', 'Management'],
            allowed_roles=['Purchase Manager', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        valid_trans, trans_resp = validate_approval_transition(po.status, 'reject')
        if not valid_trans:
            return trans_resp

        reason = request.data.get('reason') or request.data.get('rejectionReason') or request.data.get('remarks') or 'PO Rejected'
        po.status = 'Rejected'
        if reason:
            po.remarks = f"{po.remarks} | Rejected: {reason}".strip(' |')
        po.save(update_fields=['status', 'remarks'])

        log_approval_audit(user_info, 'REJECT', 'Purchase', 'PurchaseOrder', po.id, reason)
        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='send-email')
    def send_email_direct(self, request):
        po_payload = request.data.get('po') or {}
        po_id = request.data.get('id') or request.data.get('poId') or request.data.get('poNumber') or po_payload.get('poNumber') or po_payload.get('id')
        return self.send_email(request, pk=po_id)

    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        import logging
        import re
        from django.db import models
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        from apps.purchase.po_pdf import generate_po_pdf
        logger = logging.getLogger(__name__)

        po_payload = request.data.get('po') or request.data
        po = None
        if pk:
            po = PurchaseOrder.objects.filter(models.Q(id=pk) | models.Q(po_number=pk)).first()
        if not po and po_payload:
            payload_num = po_payload.get('poNumber') or po_payload.get('po_number') or po_payload.get('id')
            if payload_num:
                po = PurchaseOrder.objects.filter(models.Q(id=payload_num) | models.Q(po_number=payload_num)).first()

        if not po:
            # Auto-create or instantiate from payload for seamless client resilience
            raw_po_num = po_payload.get('poNumber') or po_payload.get('po_number') or str(pk or 'PO-2026')
            po_num = str(raw_po_num).strip()
            if po_num == '-' or not po_num:
                po_num = f"PO-{datetime.now().year}-{PurchaseOrder.objects.count() + 1:04d}"

            s_name = po_payload.get('supplierName') or po_payload.get('supplier_name') or 'Supplier'
            s_email = po_payload.get('supplierEmail') or po_payload.get('supplier_email') or request.data.get('recipientEmail') or ''
            s_mobile = po_payload.get('supplierMobile') or po_payload.get('supplier_mobile') or ''
            s_id = po_payload.get('supplierId') or po_payload.get('supplier_id') or 'SUP-001'
            s_addr = po_payload.get('supplierAddress') or po_payload.get('supplier_address') or ''
            s_gstin = po_payload.get('supplierGstin') or po_payload.get('supplier_gstin') or ''
            p_id = po_payload.get('projectId') or po_payload.get('project_id') or 'General'
            p_date = po_payload.get('poDate') or po_payload.get('date') or datetime.now().strftime('%Y-%m-%d')
            d_date = po_payload.get('deliveryDate') or po_payload.get('expectedDeliveryDate') or ''
            itms = po_payload.get('items') or []
            p_terms = po_payload.get('paymentTerms') or '30 Days Credit'
            sub_t = float(po_payload.get('subTotal') or 0)
            tax_t = float(po_payload.get('taxAmount') or po_payload.get('taxTotal') or 0)
            g_total = float(po_payload.get('grandTotal') or po_payload.get('totalAmount') or 0)

            try:
                po = PurchaseOrder.objects.create(
                    id=str(pk),
                    po_number=po_num,
                    supplier_id=s_id,
                    supplier_name=s_name,
                    contact_person=po_payload.get('contactPerson') or '',
                    supplier_gstin=s_gstin,
                    supplier_address=s_addr,
                    project_id=p_id,
                    job_code=po_payload.get('jobCode') or po_payload.get('jobId') or '',
                    date=p_date,
                    delivery_date=d_date,
                    payment_terms=p_terms,
                    items=itms,
                    sub_total=sub_t,
                    tax_amount=tax_t,
                    grand_total=g_total,
                    status='Sent to Supplier'
                )
            except Exception as ex:
                logger.warning(f"Auto-creating PO {pk} encountered ({ex}), using memory object.")
                from types import SimpleNamespace
                po = SimpleNamespace(
                    id=str(pk),
                    po_number=po_num,
                    supplier_id=s_id,
                    supplier_name=s_name,
                    contact_person=po_payload.get('contactPerson') or '',
                    supplier_gstin=s_gstin,
                    supplier_address=s_addr,
                    supplier_email=s_email,
                    supplier_mobile=s_mobile,
                    project_id=p_id,
                    job_code=po_payload.get('jobCode') or po_payload.get('jobId') or '',
                    date=p_date,
                    delivery_date=d_date,
                    payment_terms=p_terms,
                    delivery_terms=po_payload.get('deliveryTerms') or 'FOR Destination (Rajpur Works)',
                    dispatch_mode=po_payload.get('dispatchMode') or 'By Road Transport',
                    special_instructions=po_payload.get('specialInstructions') or '',
                    items=itms,
                    sub_total=sub_t,
                    tax_amount=tax_t,
                    grand_total=g_total,
                    status='Sent to Supplier',
                    save=lambda *args, **kwargs: None
                )

        # Collect and deduplicate recipients
        raw_recipients = []
        single_recip = request.data.get('recipientEmail') or request.data.get('recipient_email') or request.data.get('email')
        if single_recip:
            if isinstance(single_recip, list):
                raw_recipients.extend(single_recip)
            else:
                raw_recipients.extend(str(single_recip).split(','))

        multi_recips = request.data.get('recipients') or request.data.get('additionalEmails') or []
        if isinstance(multi_recips, list):
            raw_recipients.extend(multi_recips)
        elif isinstance(multi_recips, str):
            raw_recipients.extend(multi_recips.split(','))

        # Fallback to vendor master email if available
        po_supp_email = getattr(po, 'supplier_email', '')
        if not po_supp_email and getattr(po, 'supplier_id', None):
            try:
                from .models import Supplier
                s = Supplier.objects.filter(id=po.supplier_id).first() or Supplier.objects.filter(vendor_code=po.supplier_id).first()
                if s and s.email:
                    po_supp_email = s.email
            except Exception:
                pass
        if po_supp_email:
            raw_recipients.append(po_supp_email)

        recipients = []
        for r in raw_recipients:
            cleaned = str(r or '').strip()
            if cleaned and '@' in cleaned and cleaned.lower() not in [e.lower() for e in recipients]:
                recipients.append(cleaned)

        if not recipients:
            return Response(
                {'error': 'No valid recipient email address provided. Please specify a supplier email.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status
        if hasattr(po, 'save'):
            try:
                po.status = 'Sent to Supplier'
                po.save(update_fields=['status'])
            except Exception:
                pass

        # Generate official PO PDF
        po_num_clean = re.sub(r'[^A-Za-z0-9_-]', '_', str(getattr(po, 'po_number', None) or pk or 'PO-2026'))
        pdf_filename = f"Official_Purchase_Order_{po_num_clean}.pdf"
        pdf_bytes = None
        try:
            pdf_bytes = generate_po_pdf(po, payload=po_payload)
            logger.info(f"Generated PO PDF '{pdf_filename}' ({len(pdf_bytes)} bytes)")
        except Exception as pdf_ex:
            logger.warning(f"Error generating PO PDF: {pdf_ex}")

        # Ordered item rows
        items = getattr(po, 'items', []) or po_payload.get('items') or []
        items_rows_html = ""
        items_text = ""
        for idx, itm in enumerate(items, 1):
            p_name = itm.get('itemName') or itm.get('item_name') or itm.get('description') or f"Item {idx}"
            spec = itm.get('dimensions') or itm.get('specification') or ''
            qty = float(itm.get('orderedQuantity') or itm.get('quantity') or 1)
            uom = itm.get('unitOfMeasure') or itm.get('unit') or 'NOS'
            rate = float(itm.get('unitPrice') or itm.get('rate') or 0)
            tot = float(itm.get('totalPrice') or (qty * rate))

            items_text += f"  {idx}. {p_name} {f'({spec})' if spec else ''} | Qty: {qty:g} {uom} @ ₹{rate:,.2f} = ₹{tot:,.2f}\n"
            desc_html = f'<div style="font-size: 11px; color: #6b7280; margin: 2px 0 0 0;">Spec: {spec}</div>' if spec else ''
            items_rows_html += f"""
            <tr style="border-bottom: 1px solid #f0e6dd;">
              <td style="padding: 9px 8px; vertical-align: top; font-weight: bold; font-size: 12px; color: #75401f; width: 32px;">#{idx}</td>
              <td style="padding: 9px 8px; vertical-align: top;">
                <div style="font-weight: 700; font-size: 13px; color: #1f2937;">{p_name}</div>
                {desc_html}
              </td>
              <td align="center" style="padding: 9px 8px; vertical-align: top; white-space: nowrap;">
                <span style="font-size: 13px; font-weight: 800; color: #047857; background: #ecfdf5; padding: 2px 8px; border-radius: 4px; border: 1px solid #a7f3d0;">
                  {qty:g} {uom}
                </span>
              </td>
              <td align="right" style="padding: 9px 8px; vertical-align: top; font-size: 13px; color: #374151;">
                ₹{rate:,.2f}
              </td>
              <td align="right" style="padding: 9px 8px; vertical-align: top; font-size: 13px; font-weight: 700; color: #1f2937;">
                ₹{tot:,.2f}
              </td>
            </tr>
            """

        g_total_val = float(getattr(po, 'grand_total', 0) or getattr(po, 'totalAmount', 0) or po_payload.get('grandTotal') or 0)
        formatted_grand_total = f"₹{g_total_val:,.2f}"
        po_display_num = getattr(po, 'po_number', None) or pk

        subject = f"OFFICIAL PURCHASE ORDER: {po_display_num} - {getattr(po, 'supplier_name', 'Supplier')} - UMA TECHNO FAB PVT. LTD."

        email_text = f"""Dear {getattr(po, 'supplier_name', 'Valued Supplier')},

Please find our official Purchase Order (PO) details below from UMA TECHNO FAB PVT. LTD.

============================================================
PURCHASE ORDER DETAILS:
PO Number      : {po_display_num}
PO Date        : {getattr(po, 'date', '') or getattr(po, 'poDate', '')}
Delivery Due   : {getattr(po, 'delivery_date', '') or 'As agreed'}
Project Ref    : {getattr(po, 'project_id', '') or getattr(po, 'job_code', '') or 'General'}
Payment Terms  : {getattr(po, 'payment_terms', '30 Days Credit after GRN')}
Delivery Site  : {getattr(po, 'delivery_terms', 'FOR Destination (Rajpur Works)')}
Order Total    : INR {g_total_val:,.2f}
Official PDF   : {pdf_filename} (Attached)
============================================================

ORDERED LINE ITEMS:
{items_text}

Special Instructions:
{getattr(po, 'special_instructions', '') or 'Material must be accompanied by original Mill Test Certificate (MTC) and Delivery Challan.'}

Order Terms & Compliance:
1. Supply must strictly conform to engineering dimensions, tolerances and material grade.
2. Material must strictly be accompanied by Tax Invoice, Delivery Challan & Test Certificate (TC).
3. Delivery schedule must be adhered to strictly.
4. Inspection will be conducted at our Rajpur Works upon arrival.

The complete official engineering purchase order is attached as PDF: {pdf_filename}

Warm Regards,
Purchase & Procurement Department
UMA TECHNO FAB PVT. LTD.
Plot No. 48/B, GIDC Industrial Estate, Makarpura, Vadodara - 390010, Gujarat, India
Works: Survey No. 1040/3, Ahmedabad-Mehsana Highway, Rajpur, Dist. Mehsana - 382715, Gujarat
Web: www.umatechnofab.com | Email: info@umatechnofab.com
"""

        from_email_setting = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'UMA TECHNO FAB <hrinfinitesofttech@gmail.com>'
        email_match = re.search(r'<([^>]+)>', str(from_email_setting))
        reply_to_addr = email_match.group(1).strip() if email_match else str(from_email_setting).strip()

        email_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 16px; background-color: #f6f3ee; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #ebd8c8; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
    <!-- Top Accent Bar -->
    <tr>
      <td height="6" style="background: #75401f;"></td>
    </tr>
    <!-- Header -->
    <tr>
      <td style="padding: 20px 24px 14px 24px; border-bottom: 1px solid #f0e6dd; background: #faf7f2;">
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
          <tr>
            <td>
              <h2 style="margin: 0; font-size: 18px; color: #75401f; font-weight: 800; letter-spacing: -0.5px;">UMA TECHNO FAB PVT. LTD.</h2>
              <div style="font-size: 11px; color: #70665f; margin-top: 2px;">Purchase & Procurement Department • Official Purchase Order</div>
            </td>
            <td align="right">
              <span style="font-size: 11px; font-weight: 700; color: #75401f; background: #ebd8c8; padding: 4px 10px; border-radius: 6px; font-family: monospace;">
                {po_display_num}
              </span>
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- Body -->
    <tr>
      <td style="padding: 24px;">
        <p style="font-size: 14px; color: #1f2937; margin: 0 0 16px 0; line-height: 1.5;">
          Dear <strong>{getattr(po, 'supplier_name', 'Valued Supplier')}</strong>,
        </p>
        <p style="font-size: 13px; color: #4b5563; margin: 0 0 20px 0; line-height: 1.5;">
          We are pleased to place our official <strong>Purchase Order ({po_display_num})</strong> for the procurement of material items detailed below. Please confirm receipt and delivery schedule.
        </p>

        <!-- Summary Grid -->
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background: #faf7f2; border: 1px solid #ebd8c8; border-radius: 8px; margin-bottom: 20px; font-size: 12px;">
          <tr>
            <td style="padding: 10px 14px; border-bottom: 1px solid #f0e6dd; color: #70665f; width: 35%;">PO Reference:</td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #f0e6dd; color: #1f2937; font-weight: 700; font-family: monospace;">{po_display_num}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; border-bottom: 1px solid #f0e6dd; color: #70665f;">PO Date:</td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #f0e6dd; color: #1f2937; font-weight: 600;">{getattr(po, 'date', '') or getattr(po, 'poDate', '')}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; border-bottom: 1px solid #f0e6dd; color: #70665f;">Committed Delivery Date:</td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #f0e6dd; color: #047857; font-weight: 700;">{getattr(po, 'delivery_date', '') or 'As agreed'}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; border-bottom: 1px solid #f0e6dd; color: #70665f;">Payment Terms:</td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #f0e6dd; color: #1f2937; font-weight: 600;">{getattr(po, 'payment_terms', '30 Days Credit')}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; border-bottom: 1px solid #f0e6dd; color: #70665f;">Total Order Value:</td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #f0e6dd; color: #047857; font-weight: 800; font-size: 14px;">{formatted_grand_total}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; color: #70665f;">Delivery Site:</td>
            <td style="padding: 10px 14px; color: #1f2937; font-weight: 600;">UMA TECHNO FAB PVT. LTD., Rajpur Works, Mehsana</td>
          </tr>
        </table>

        <!-- Line Items Table -->
        <h4 style="margin: 0 0 10px 0; font-size: 13px; color: #75401f; text-transform: uppercase; letter-spacing: 0.5px;">Ordered Line Items</h4>
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="border: 1px solid #ebd8c8; border-radius: 8px; overflow: hidden; margin-bottom: 20px; font-size: 12px;">
          <thead style="background: #75401f; color: #ffffff;">
            <tr>
              <th align="left" style="padding: 8px; font-size: 11px; text-transform: uppercase;">#</th>
              <th align="left" style="padding: 8px; font-size: 11px; text-transform: uppercase;">Material Description</th>
              <th align="center" style="padding: 8px; font-size: 11px; text-transform: uppercase;">Quantity</th>
              <th align="right" style="padding: 8px; font-size: 11px; text-transform: uppercase;">Rate</th>
              <th align="right" style="padding: 8px; font-size: 11px; text-transform: uppercase;">Total (INR)</th>
            </tr>
          </thead>
          <tbody>
            {items_rows_html}
          </tbody>
        </table>

        <!-- Attachment Badge -->
        <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 12px 14px; border-radius: 8px; margin-bottom: 18px;">
          <table width="100%" border="0" cellpadding="0" cellspacing="0">
            <tr>
              <td width="30" valign="middle">
                <span style="font-size: 20px;">📎</span>
              </td>
              <td valign="middle">
                <div style="font-weight: 700; font-size: 12px; color: #065f46;">
                  Official PO Attached: {pdf_filename}
                </div>
                <div style="font-size: 11px; color: #047857; margin-top: 2px;">
                  Complete letterhead, terms & conditions, and authorized signature.
                </div>
              </td>
            </tr>
          </table>
        </div>

        <!-- Terms Box -->
        <div style="background: #faf7f2; border: 1px solid #ebd8c8; padding: 12px 14px; border-radius: 6px; font-size: 11px; color: #544b45; line-height: 1.5; margin-bottom: 20px;">
          <strong style="color: #75401f;">Supply Compliance Terms:</strong><br/>
          • Material must strictly be accompanied by Delivery Challan, Tax Invoice & Mill Test Certificate (MTC).<br/>
          • Inspection will be conducted at our Rajpur Works upon arrival.<br/>
          • Please reply to this email acknowledging receipt and confirming delivery date.
        </div>

        <!-- Footer Contact -->
        <div style="padding-top: 14px; border-top: 1px solid #f0e6dd; font-size: 11px; color: #70665f; line-height: 1.4;">
          <strong style="color: #1f2937;">UMA TECHNO FAB PVT. LTD.</strong><br/>
          Plot No. 48/B, GIDC Industrial Estate, Makarpura, Vadodara - 390010<br/>
          Email: <a href="mailto:{reply_to_addr}" style="color: #75401f; text-decoration: none;">{reply_to_addr}</a> • Web: www.umatechnofab.com
        </div>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        try:
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=email_text,
                from_email=from_email_setting,
                to=recipients,
                reply_to=[reply_to_addr],
                headers={
                    'X-Mailer': 'UMA ERP Purchase PO Dispatcher',
                    'X-Priority': '3',
                }
            )
            email_msg.attach_alternative(email_html, "text/html")
            if pdf_bytes:
                email_msg.attach(pdf_filename, pdf_bytes, 'application/pdf')

            email_msg.send(fail_silently=False)
            logger.info(f"Successfully sent official PO email {po_display_num} to {recipients} via SMTP")

            return Response({
                'success': True,
                'message': f"Official Purchase Order {po_display_num} with attached PDF successfully dispatched to {', '.join(recipients)} via SMTP.",
                'poNumber': po_display_num,
                'recipients': recipients,
                'pdfFilename': pdf_filename,
            }, status=status.HTTP_200_OK)

        except Exception as mail_ex:
            logger.error(f"Failed to dispatch PO email via SMTP: {mail_ex}")
            return Response({
                'success': False,
                'error': f"Failed to dispatch PO email via SMTP: {str(mail_ex)}",
                'details': str(mail_ex),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PurchaseReturnViewSet(viewsets.ModelViewSet):
    queryset = PurchaseReturn.objects.all().order_by('-created_at', '-id')
    serializer_class = PurchaseReturnSerializer
    permission_classes = [permissions.AllowAny]
