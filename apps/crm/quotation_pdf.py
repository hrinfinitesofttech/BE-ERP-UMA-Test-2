import io
import json
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that computes and renders the total page count
    and a professional footer with company credentials and confidentiality note.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont('Helvetica', 8)
        self.setFillColor(colors.HexColor('#70665F'))
        self.setStrokeColor(colors.HexColor('#EBE3DB'))
        self.setLineWidth(0.6)

        # Footer divider line
        margin_x = 14 * mm
        self.line(margin_x, 14 * mm, A4[0] - margin_x, 14 * mm)

        # Left footnote
        self.drawString(
            margin_x,
            9 * mm,
            'UMA TECHNO FAB PVT. LTD. • Commercial Proposal • Confidential'
        )

        # Right page numbering
        page_text = f'Page {self._pageNumber} of {page_count}'
        self.drawRightString(A4[0] - margin_x, 9 * mm, page_text)
        self.restoreState()


def format_inr(val):
    """Safely format float into INR currency format."""
    try:
        f = float(val or 0)
        return f"INR {f:,.2f}"
    except (ValueError, TypeError):
        return "INR 0.00"


def generate_quotation_pdf(quotation, active_revision=None, payload=None) -> bytes:
    """
    Generate an official, branded Quotation PDF matching the ERP's printable layout.
    Accepts Quotation model instances or dictionary/SimpleNamespace data structures.
    """
    payload = payload or {}

    # Extract base attributes
    quotation_number = str(getattr(quotation, 'quotation_number', None) or payload.get('quotationNumber') or 'QT-DRAFT').strip()
    cur_rev_num = str(getattr(quotation, 'current_revision', None) or payload.get('currentRevision') or 'Rev-00').strip()
    date_str = str(getattr(quotation, 'date', None) or payload.get('date') or '').strip()
    valid_until = str(getattr(quotation, 'valid_until', None) or payload.get('validUntil') or '30 Days from date').strip()
    customer_name = str(getattr(quotation, 'customer_name', None) or payload.get('customerName') or 'Valued Customer').strip()
    contact_person = str(getattr(quotation, 'contact_person', None) or payload.get('contactPerson') or customer_name).strip()
    contact_email = str(getattr(quotation, 'contact_email', None) or payload.get('contactEmail') or payload.get('recipientEmail') or '').strip()
    contact_mobile = str(getattr(quotation, 'contact_mobile', None) or payload.get('contactMobile') or '').strip()
    machine_product = str(getattr(quotation, 'machine_product', None) or payload.get('machineProduct') or 'Industrial Fabrication Equipment').strip()
    enquiry_id = str(getattr(quotation, 'enquiry_id', None) or payload.get('enquiryId') or '').strip()

    # Revisions resolution
    revs = getattr(quotation, 'revisions', None) or payload.get('revisions') or []
    if isinstance(revs, str):
        try:
            revs = json.loads(revs)
        except Exception:
            revs = []

    if not active_revision and revs:
        for r in revs:
            if isinstance(r, dict) and str(r.get('revisionNumber') or '').strip().lower() == cur_rev_num.lower():
                active_revision = r
                break
        if not active_revision and isinstance(revs[-1], dict):
            active_revision = revs[-1]

    active_rev = active_revision or {}

    # Revision-specific metadata
    rev_date = active_rev.get('date') or date_str
    prepared_by = active_rev.get('preparedBy') or getattr(quotation, 'sales_person_name', None) or 'Sales & Engineering Division'
    approved_by = active_rev.get('approvedBy') or getattr(quotation, 'approved_by', None) or ''
    payment_terms = active_rev.get('paymentTerms') or '30% Advance, 60% against Proforma Invoice, 10% on dispatch'
    delivery_time = active_rev.get('deliveryTime') or '6 to 8 Weeks from approval of GA drawing'
    warranty = active_rev.get('warranty') or '12 Months from commissioning or 18 months from supply'
    technical_specs = active_rev.get('technicalSpecs') or 'Strictly compliant with ASME Sec VIII Div 1 / IS 2825 standard fabrication codes.'
    scope_of_supply = active_rev.get('scopeOfSupply') or 'Complete engineering design, raw material procurement, precision fabrication, testing, surface preparation and protective coating.'
    terms_and_conditions = active_rev.get('termsAndConditions') or ''

    # Extract items
    items = getattr(quotation, 'items', None) or active_rev.get('items') or payload.get('items') or []
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            items = []

    # Financials
    subtotal = 0.0
    try:
        val = active_rev.get('subTotal') if active_rev.get('subTotal') is not None else active_rev.get('subtotal')
        if val is None:
            val = getattr(quotation, 'subtotal', None) or payload.get('subtotal') or payload.get('subTotal')
        subtotal = float(val or 0)
    except (ValueError, TypeError):
        subtotal = 0.0

    tax_amount = 0.0
    try:
        val = active_rev.get('taxAmount') if active_rev.get('taxAmount') is not None else active_rev.get('tax_amount')
        if val is None:
            val = getattr(quotation, 'tax_amount', None) or payload.get('taxAmount') or payload.get('tax_amount')
        tax_amount = float(val or 0)
    except (ValueError, TypeError):
        tax_amount = 0.0

    grand_total = 0.0
    try:
        val = active_rev.get('grandTotal') if active_rev.get('grandTotal') is not None else active_rev.get('grand_total')
        if val is None:
            val = getattr(quotation, 'grand_total', None) or getattr(quotation, 'total_amount', None) or payload.get('grandTotal') or payload.get('grand_total')
        grand_total = float(val or 0)
    except (ValueError, TypeError):
        grand_total = 0.0

    if subtotal == 0 and items:
        subtotal = sum(float(it.get('rate', 0)) * float(it.get('quantity', 1)) for it in items)
    if grand_total == 0:
        grand_total = subtotal + tax_amount

    # Document setup (A4 with 14mm margins)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=20 * mm,
        title=f"Quotation_{quotation_number}_{cur_rev_num}",
        author="UMA TECHNO FAB PVT. LTD."
    )

    printable_width = A4[0] - 28 * mm  # ~182mm = 515.9 pt

    # Design styles
    base_styles = getSampleStyleSheet()

    c_primary = colors.HexColor('#75401F')   # CRM Bronze / Uma Brand
    c_dark = colors.HexColor('#1F2937')      # Text primary
    c_muted = colors.HexColor('#70665F')     # Muted text
    c_bg_card = colors.HexColor('#FAF7F2')   # Light warm card bg
    c_border = colors.HexColor('#EBE3DB')    # Crisp border
    c_green = colors.HexColor('#047857')     # Emerald green total

    styles = {
        'CompanyTitle': ParagraphStyle(
            'CompanyTitle',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=19,
            textColor=c_primary,
        ),
        'CompanySub': ParagraphStyle(
            'CompanySub',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#3E2723'),
        ),
        'CompanyDetails': ParagraphStyle(
            'CompanyDetails',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=10.5,
            textColor=c_muted,
        ),
        'DocBadge': ParagraphStyle(
            'DocBadge',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=13,
            textColor=c_primary,
            alignment=TA_RIGHT,
        ),
        'DocMeta': ParagraphStyle(
            'DocMeta',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=c_dark,
            alignment=TA_RIGHT,
        ),
        'CardHeading': ParagraphStyle(
            'CardHeading',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=c_primary,
            textTransform='uppercase',
        ),
        'CustomerName': ParagraphStyle(
            'CustomerName',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=c_dark,
        ),
        'CardBody': ParagraphStyle(
            'CardBody',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=c_dark,
        ),
        'CardBodyMuted': ParagraphStyle(
            'CardBodyMuted',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=10,
            textColor=c_muted,
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        'TableHeaderCenter': ParagraphStyle(
            'TableHeaderCenter',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        'TableHeaderLeft': ParagraphStyle(
            'TableHeaderLeft',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
        'TableHeaderRight': ParagraphStyle(
            'TableHeaderRight',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_RIGHT,
        ),
        'TableCell': ParagraphStyle(
            'TableCell',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10.5,
            textColor=c_dark,
        ),
        'TableCellBold': ParagraphStyle(
            'TableCellBold',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10.5,
            textColor=c_dark,
        ),
        'TableCellDesc': ParagraphStyle(
            'TableCellDesc',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=7,
            leading=9,
            textColor=c_muted,
        ),
        'TableCellCenter': ParagraphStyle(
            'TableCellCenter',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10.5,
            textColor=c_dark,
            alignment=TA_CENTER,
        ),
        'TableCellRight': ParagraphStyle(
            'TableCellRight',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10.5,
            textColor=c_dark,
            alignment=TA_RIGHT,
        ),
        'TotalLabel': ParagraphStyle(
            'TotalLabel',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10.5,
            textColor=c_dark,
            alignment=TA_RIGHT,
        ),
        'TotalValue': ParagraphStyle(
            'TotalValue',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10.5,
            textColor=c_dark,
            alignment=TA_RIGHT,
        ),
        'GrandTotalLabel': ParagraphStyle(
            'GrandTotalLabel',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=12,
            textColor=c_primary,
            alignment=TA_RIGHT,
        ),
        'GrandTotalValue': ParagraphStyle(
            'GrandTotalValue',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            textColor=c_green,
            alignment=TA_RIGHT,
        ),
        'SectionHeading': ParagraphStyle(
            'SectionHeading',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=12,
            textColor=c_primary,
        ),
        'TermLabel': ParagraphStyle(
            'TermLabel',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=10,
            textColor=c_dark,
        ),
        'TermText': ParagraphStyle(
            'TermText',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=10,
            textColor=c_dark,
        ),
    }

    story = []

    # -------------------------------------------------------------
    # 1. LETTERHEAD BANNER
    # -------------------------------------------------------------
    left_letterhead = [
        Paragraph("UMA TECHNO FAB PVT. LTD.", styles['CompanyTitle']),
        Spacer(1, 1 * mm),
        Paragraph("Designers & Manufacturers of Industrial & Process Equipment", styles['CompanySub']),
        Spacer(1, 0.5 * mm),
        Paragraph("Plot No. 48/B, GIDC Industrial Estate, Makarpura, Vadodara - 390010, Gujarat, India", styles['CompanyDetails']),
        Paragraph("GSTIN: 24AABCU9821R1ZX • PAN: AABCU9821R • CIN: U28112GJ2015PTC084221", styles['CompanyDetails']),
        Paragraph("Email: sales@umatechnofab.com • Web: www.umatechnofab.com", styles['CompanyDetails']),
    ]

    right_meta = [
        Paragraph("COMMERCIAL QUOTATION", styles['DocBadge']),
        Spacer(1, 1 * mm),
        Paragraph(f"<b>Quotation No:</b> {quotation_number}", styles['DocMeta']),
        Paragraph(f"<b>Revision:</b> {cur_rev_num}", styles['DocMeta']),
        Paragraph(f"<b>Date:</b> {rev_date or 'Today'}", styles['DocMeta']),
        Paragraph(f"<b>Valid Until:</b> {valid_until}", styles['DocMeta']),
    ]

    header_table = Table(
        [[left_letterhead, right_meta]],
        colWidths=[printable_width * 0.62, printable_width * 0.38]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 3 * mm))

    # Divider bar
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=0, spaceAfter=3 * mm))

    # -------------------------------------------------------------
    # 2. CLIENT & QUOTATION DETAILS CARD
    # -------------------------------------------------------------
    left_card = [
        Paragraph("QUOTATION ADDRESSED TO", styles['CardHeading']),
        Spacer(1, 1 * mm),
        Paragraph(customer_name, styles['CustomerName']),
        Paragraph(f"Attn: <b>{contact_person}</b>", styles['CardBody']),
        Paragraph(f"Email: {contact_email or 'N/A'}", styles['CardBodyMuted']),
        Paragraph(f"Phone / Mobile: {contact_mobile or 'N/A'}", styles['CardBodyMuted']),
    ]

    right_card = [
        Paragraph("PROPOSAL INFORMATION", styles['CardHeading']),
        Spacer(1, 1 * mm),
        Paragraph(f"Equipment Scope: <b>{machine_product}</b>", styles['CardBody']),
        Paragraph(f"Prepared By: <b>{prepared_by}</b>", styles['CardBody']),
        Paragraph(f"Approval Status: <b>{'Approved' if approved_by else 'Official Proposal'}</b>", styles['CardBody']),
        Paragraph(f"Linked Enquiry: {enquiry_id or 'Direct Commercial'}", styles['CardBodyMuted']),
    ]

    card_table = Table(
        [[left_card, right_card]],
        colWidths=[printable_width * 0.50, printable_width * 0.50]
    )
    card_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_card),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(card_table)
    story.append(Spacer(1, 4 * mm))

    # -------------------------------------------------------------
    # 3. BILL OF QUANTITIES & PRICING TABLE
    # -------------------------------------------------------------
    story.append(Paragraph("BILL OF QUANTITIES & PRICING", styles['SectionHeading']))
    story.append(Spacer(1, 2 * mm))

    # Column widths: Total ~516 pt
    col_w = [
        24,   # Sr No
        224,  # Description
        48,   # Qty
        72,   # Rate
        48,   # GST%
        100,  # Total
    ]

    table_data = [
        [
            Paragraph("#", styles['TableHeader']),
            Paragraph("Equipment Description & Specifications", styles['TableHeaderLeft']),
            Paragraph("Qty", styles['TableHeaderCenter']),
            Paragraph("Unit Rate", styles['TableHeaderRight']),
            Paragraph("GST %", styles['TableHeaderCenter']),
            Paragraph("Total Amount", styles['TableHeaderRight']),
        ]
    ]

    if not items:
        # Default single row fallback
        items = [{
            'productName': machine_product,
            'description': 'Commercial fabrication and process equipment scope as per technical discussions.',
            'quantity': 1,
            'unit': 'Set',
            'rate': subtotal or grand_total,
            'taxPercent': 18,
            'amount': subtotal or grand_total,
        }]

    for idx, itm in enumerate(items, 1):
        p_name = itm.get('productName') or itm.get('product_name') or machine_product or 'Fabrication & Process Equipment'
        p_desc = itm.get('description') or ''
        qty = itm.get('quantity', 1)
        unit = itm.get('unit') or 'Nos'
        rate = float(itm.get('rate') or 0)
        tax_pct = float(itm.get('taxPercent') or itm.get('tax_percent') or 18)
        amt = float(itm.get('amount') or 0) or (rate * float(qty))

        desc_flowables = [Paragraph(f"<b>{p_name}</b>", styles['TableCellBold'])]
        if p_desc:
            desc_flowables.append(Paragraph(p_desc, styles['TableCellDesc']))

        table_data.append([
            Paragraph(str(idx), styles['TableCellCenter']),
            desc_flowables,
            Paragraph(f"{qty} {unit}", styles['TableCellCenter']),
            Paragraph(f"INR {rate:,.2f}", styles['TableCellRight']),
            Paragraph(f"{tax_pct:.0f}%", styles['TableCellCenter']),
            Paragraph(f"INR {amt:,.2f}", styles['TableCellRight']),
        ])

    # Subtotal row
    table_data.append([
        '',
        '',
        '',
        '',
        Paragraph("Taxable Subtotal:", styles['TotalLabel']),
        Paragraph(format_inr(subtotal), styles['TotalValue']),
    ])

    # GST row
    table_data.append([
        '',
        '',
        '',
        '',
        Paragraph("Applicable GST:", styles['TotalLabel']),
        Paragraph(format_inr(tax_amount), styles['TotalValue']),
    ])

    # Grand Total row
    table_data.append([
        '',
        '',
        '',
        '',
        Paragraph("Grand Total (INR):", styles['GrandTotalLabel']),
        Paragraph(format_inr(grand_total), styles['GrandTotalValue']),
    ])

    items_table = Table(table_data, colWidths=col_w, repeatRows=1)

    num_item_rows = len(items)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, num_item_rows), 0.5, c_border),
    ]

    # Alternate row background for items
    for r_idx in range(1, num_item_rows + 1):
        if r_idx % 2 == 0:
            t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor('#FCFAF7')))

    # Span bottom total labels
    subtotal_row = num_item_rows + 1
    gst_row = num_item_rows + 2
    grand_row = num_item_rows + 3

    t_style.extend([
        ('SPAN', (0, subtotal_row), (3, subtotal_row)),
        ('LINEABOVE', (4, subtotal_row), (5, subtotal_row), 0.75, c_border),
        ('SPAN', (0, gst_row), (3, gst_row)),
        ('SPAN', (0, grand_row), (3, grand_row)),
        ('BACKGROUND', (4, grand_row), (5, grand_row), colors.HexColor('#FAF0E6')),
        ('BOX', (4, grand_row), (5, grand_row), 1, c_primary),
        ('TOPPADDING', (4, grand_row), (5, grand_row), 6),
        ('BOTTOMPADDING', (4, grand_row), (5, grand_row), 6),
    ])

    items_table.setStyle(TableStyle(t_style))
    story.append(items_table)
    story.append(Spacer(1, 4 * mm))

    # -------------------------------------------------------------
    # 4. COMMERCIAL TERMS & SCOPE
    # -------------------------------------------------------------
    terms_flowables = [
        Paragraph("COMMERCIAL TERMS & TECHNICAL SCOPE", styles['SectionHeading']),
        Spacer(1, 2 * mm),
    ]

    terms_data = [
        [
            [Paragraph("Technical Scope & Standard:", styles['TermLabel']), Paragraph(technical_specs, styles['TermText'])],
            [Paragraph("Payment Terms:", styles['TermLabel']), Paragraph(payment_terms, styles['TermText'])],
        ],
        [
            [Paragraph("Scope of Supply:", styles['TermLabel']), Paragraph(scope_of_supply, styles['TermText'])],
            [Paragraph("Delivery & Warranty:", styles['TermLabel']), Paragraph(f"Delivery: {delivery_time}<br/>Warranty: {warranty}", styles['TermText'])],
        ],
    ]

    if terms_and_conditions:
        lines = [line.strip() for line in terms_and_conditions.split('\n') if line.strip()]
        formatted_tc = "<br/>".join(f"• {ln}" for ln in lines)
        terms_data.append([
            [Paragraph("Standard Terms & Conditions:", styles['TermLabel']), Paragraph(formatted_tc, styles['TermText'])],
            [Paragraph("Inspection & Testing:", styles['TermLabel']), Paragraph("Client/TPI inspection as agreed prior to dispatch. Material Test Certificates (MTC) provided.", styles['TermText'])],
        ])

    terms_table = Table(
        terms_data,
        colWidths=[printable_width * 0.50, printable_width * 0.50]
    )
    terms_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAF7F2')),
        ('BOX', (0, 0), (-1, -1), 0.6, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    terms_flowables.append(terms_table)
    story.append(KeepTogether(terms_flowables))
    story.append(Spacer(1, 4 * mm))

    # -------------------------------------------------------------
    # 5. SIGNATURE & AUTHORIZATION BLOCK
    # -------------------------------------------------------------
    sig_left = [
        Paragraph("<b>Customer Acceptance & Confirmation:</b>", styles['TermLabel']),
        Spacer(1, 1 * mm),
        Paragraph("We hereby accept this commercial proposal and authorize commencement of engineering and fabrication as per the terms specified herein.", styles['CardBodyMuted']),
        Spacer(1, 8 * mm),
        Paragraph("Authorized Signatory & Seal / Date", styles['CardBodyMuted']),
    ]

    sig_right = [
        Paragraph("<b>For UMA TECHNO FAB PVT. LTD.</b>", ParagraphStyle(
            'SigTitle',
            parent=styles['CardBody'],
            fontName='Helvetica-Bold',
            alignment=TA_RIGHT,
            textColor=c_primary,
        )),
        Spacer(1, 10 * mm),
        Paragraph("<b>Authorized Signatory</b>", ParagraphStyle(
            'SigBottom',
            parent=styles['CardBody'],
            fontName='Helvetica-Bold',
            alignment=TA_RIGHT,
        )),
        Paragraph("Commercial & Engineering Division", ParagraphStyle(
            'SigDept',
            parent=styles['CardBodyMuted'],
            alignment=TA_RIGHT,
        )),
    ]

    sig_table = Table(
        [[sig_left, sig_right]],
        colWidths=[printable_width * 0.52, printable_width * 0.48]
    )
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(KeepTogether([
        sig_table,
        Spacer(1, 3 * mm),
        Paragraph(
            "This is an official computer-generated quotation proposal issued by UMA ERP on behalf of UMA TECHNO FAB PVT. LTD.",
            ParagraphStyle(
                'FooterNotice',
                parent=base_styles['Normal'],
                fontName='Helvetica-Oblique',
                fontSize=7,
                leading=9,
                textColor=c_muted,
                alignment=TA_CENTER,
            )
        )
    ]))

    # Build the PDF using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
