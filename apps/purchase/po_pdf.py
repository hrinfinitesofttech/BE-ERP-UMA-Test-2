import io
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
    Two-pass canvas that renders total page numbers and official footer on every page.
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        margin_x = 12 * mm
        page_w, page_h = A4

        # Top border accent bar
        self.setFillColor(colors.HexColor('#75401F'))
        self.rect(0, page_h - 4 * mm, page_w, 4 * mm, stroke=0, fill=1)

        # Footer divider line
        self.setStrokeColor(colors.HexColor('#D5C7B8'))
        self.setLineWidth(0.6)
        self.line(margin_x, 13 * mm, page_w - margin_x, 13 * mm)

        # Footer Left: Organization note
        self.setFont('Helvetica-Bold', 7.5)
        self.setFillColor(colors.HexColor('#544B45'))
        self.drawString(margin_x, 8.5 * mm, "UMA TECHNO FAB PVT. LTD. • Official Purchase Order • Confidential")

        # Footer Right: Page numbering
        self.setFont('Helvetica', 7.5)
        self.setFillColor(colors.HexColor('#70665F'))
        self.drawRightString(
            page_w - margin_x,
            8.5 * mm,
            f"Page {self._pageNumber} of {page_count}"
        )
        self.restoreState()


def number_to_words_indian(num: float) -> str:
    """
    Converts numbers into Indian format words (Rupees ... Only).
    """
    try:
        n = int(round(num))
        if n == 0:
            return "Rupees Zero Only"

        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                 "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                 "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

        def convert_chunk(val):
            out = []
            if val >= 100:
                out.append(units[val // 100] + " Hundred")
                val %= 100
            if val >= 20:
                out.append(tens[val // 10] + (" " + units[val % 10] if val % 10 != 0 else ""))
            elif val > 0:
                out.append(units[val])
            return " ".join(out)

        crores = n // 10000000
        n %= 10000000
        lakhs = n // 100000
        n %= 100000
        thousands = n // 1000
        n %= 1000
        hundreds = n

        parts = []
        if crores > 0:
            parts.append(convert_chunk(crores) + " Crore")
        if lakhs > 0:
            parts.append(convert_chunk(lakhs) + " Lakh")
        if thousands > 0:
            parts.append(convert_chunk(thousands) + " Thousand")
        if hundreds > 0:
            parts.append(convert_chunk(hundreds))

        return "Rupees " + " ".join(parts).strip() + " Only"
    except Exception:
        return f"INR {num:,.2f}"


def generate_po_pdf(po, payload=None) -> bytes:
    """
    Generates a professional, print-ready PDF for Purchase Order (PO)
    matching Uma Technofab official letterhead and engineering standards.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=18 * mm,
    )

    printable_w = A4[0] - 20 * mm

    # Extract metadata safely
    p = payload or {}

    raw_po_num = getattr(po, 'po_number', None) or getattr(po, 'poNumber', None) or getattr(po, 'id', None) or p.get('poNumber') or p.get('po_number') or 'PO-2026-0001'
    po_num = str(raw_po_num).strip()
    if po_num == '-' or not po_num:
        po_num = 'PO-2026-0001'

    po_date = str(getattr(po, 'date', None) or getattr(po, 'poDate', None) or p.get('poDate') or p.get('date') or '').strip()
    rev_num = str(getattr(po, 'revision_number', None) or getattr(po, 'revisionNumber', None) or p.get('revisionNumber') or 'Rev-00').strip()
    deliv_date = str(getattr(po, 'delivery_date', None) or getattr(po, 'expectedDeliveryDate', None) or p.get('deliveryDate') or p.get('expectedDeliveryDate') or '').strip()
    proj_id = str(getattr(po, 'project_id', None) or getattr(po, 'projectId', None) or p.get('projectId') or getattr(po, 'job_code', None) or p.get('jobCode') or 'General').strip()
    quote_ref = str(p.get('quotationRef') or p.get('supplierQuotationNumber') or getattr(po, 'pr_number', None) or '').strip()
    pay_terms = str(getattr(po, 'payment_terms', None) or getattr(po, 'paymentTerms', None) or p.get('paymentTerms') or '30 Days Credit after GRN').strip()
    deliv_terms = str(getattr(po, 'delivery_terms', None) or getattr(po, 'deliveryTerms', None) or p.get('deliveryTerms') or 'FOR Destination (Rajpur Works)').strip()
    dispatch_mode = str(getattr(po, 'dispatch_mode', None) or getattr(po, 'dispatchMode', None) or p.get('dispatchMode') or 'By Road Transport').strip()
    spec_instr = str(getattr(po, 'special_instructions', None) or getattr(po, 'specialInstructions', None) or getattr(po, 'remarks', None) or p.get('specialInstructions') or '').strip()

    # Vendor Details
    vendor_name = str(getattr(po, 'supplier_name', None) or getattr(po, 'supplierName', None) or p.get('supplierName') or 'Supplier').strip()
    vendor_mobile = str(getattr(po, 'supplier_mobile', None) or getattr(po, 'supplierMobile', None) or p.get('supplierMobile') or '').strip()
    vendor_email = str(getattr(po, 'supplier_email', None) or getattr(po, 'supplierEmail', None) or p.get('supplierEmail') or '').strip()
    vendor_addr = str(getattr(po, 'supplier_address', None) or getattr(po, 'supplierAddress', None) or p.get('supplierAddress') or '').strip()
    vendor_gstin = str(getattr(po, 'supplier_gstin', None) or getattr(po, 'supplierGstin', None) or p.get('supplierGstin') or '').strip()
    contact_person = str(getattr(po, 'contact_person', None) or getattr(po, 'contactPerson', None) or p.get('contactPerson') or '').strip()

    # If vendor contact or email is empty, lookup from Supplier model if available
    if getattr(po, 'supplier_id', None) or p.get('supplierId'):
        try:
            from .models import Supplier
            s_id = getattr(po, 'supplier_id', None) or p.get('supplierId')
            s_obj = Supplier.objects.filter(id=s_id).first() or Supplier.objects.filter(vendor_code=s_id).first()
            if s_obj:
                if not vendor_name or vendor_name.lower() in ['supplier', 'vendor']:
                    vendor_name = s_obj.name
                if not vendor_mobile:
                    vendor_mobile = s_obj.mobile or s_obj.phone or ''
                if not vendor_email:
                    vendor_email = s_obj.email or ''
                if not vendor_addr:
                    vendor_addr = s_obj.address or ''
                if not vendor_gstin:
                    vendor_gstin = s_obj.gstin or ''
                if not contact_person:
                    contact_person = s_obj.contact_person or ''
        except Exception:
            pass

    # Items & Financials
    items = getattr(po, 'items', None) or p.get('items') or []
    sub_total = float(getattr(po, 'sub_total', 0) or getattr(po, 'subTotal', 0) or p.get('subTotal') or 0)
    tax_amount = float(getattr(po, 'tax_amount', 0) or getattr(po, 'taxTotal', 0) or p.get('taxAmount') or p.get('taxTotal') or 0)
    discount_amount = float(getattr(po, 'discount_amount', 0) or getattr(po, 'discountAmount', 0) or p.get('discountAmount') or 0)
    freight_charges = float(getattr(po, 'freight_charges', 0) or getattr(po, 'freightCharges', 0) or p.get('freightCharges') or 0)
    grand_total = float(getattr(po, 'grand_total', 0) or getattr(po, 'grandTotal', 0) or getattr(po, 'totalAmount', 0) or p.get('grandTotal') or 0)

    # Styles
    styles = getSampleStyleSheet()

    c_primary = colors.HexColor('#75401F')   # Warm brand amber/brown
    c_primary_light = colors.HexColor('#FAF7F2')
    c_border = colors.HexColor('#D5C7B8')
    c_dark = colors.HexColor('#211B17')
    c_sub = colors.HexColor('#70665F')
    c_green = colors.HexColor('#047857')

    company_name_style = ParagraphStyle(
        'CompName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=c_primary,
        alignment=TA_LEFT,
    )

    company_sub_style = ParagraphStyle(
        'CompSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#544B45'),
        alignment=TA_LEFT,
    )

    doc_title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=15,
        alignment=TA_RIGHT,
        textColor=c_primary,
    )

    doc_meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        alignment=TA_RIGHT,
        textColor=c_dark,
    )

    h_bold = ParagraphStyle(
        'HBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=c_dark,
    )

    body_cell = ParagraphStyle(
        'BodyCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        textColor=c_dark,
    )

    body_cell_bold = ParagraphStyle(
        'BodyCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=c_dark,
    )

    body_cell_center = ParagraphStyle(
        'BodyCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        textColor=c_dark,
        alignment=TA_CENTER,
    )

    body_cell_right = ParagraphStyle(
        'BodyCellRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        textColor=c_dark,
        alignment=TA_RIGHT,
    )

    story = []

    # 1. Company Letterhead Header
    header_table_data = [
        [
            Paragraph("<b>UMA TECHNO FAB PVT. LTD.</b>", company_name_style),
            Paragraph(f"<b>PURCHASE ORDER</b><br/><font size='8' color='#70665F'>PO NO: <b>{po_num}</b></font>", doc_title_style)
        ],
        [
            Paragraph(
                "Designers & Manufacturers of Process Equipment, Storage Tanks, Piping & Heavy Fabrication<br/>"
                "<b>Regd. Office:</b> Plot No. 48/B, GIDC Industrial Estate, Makarpura, Vadodara - 390010, Gujarat, India<br/>"
                "<b>Works:</b> Survey No. 1040/3, Ahmedabad-Mehsana Highway, Rajpur, Dist. Mehsana - 382715, Gujarat<br/>"
                "<b>GSTIN:</b> 24AAACU5567R1Z1 | <b>CIN:</b> U29299GJ2020PTC118942 | <b>Email:</b> info@umatechnofab.com",
                company_sub_style
            ),
            Paragraph(
                f"<b>PO Date:</b> {po_date or 'Current'}<br/>"
                f"<b>Revision:</b> {rev_num}<br/>"
                f"<b>Delivery Due:</b> {deliv_date or '10 Days'}<br/>"
                f"<b>Project Ref:</b> {proj_id}",
                doc_meta_style
            )
        ]
    ]

    header_table = Table(header_table_data, colWidths=[printable_w * 0.64, printable_w * 0.36])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 1.5 * mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=1, spaceAfter=2.5 * mm))

    # 2. Vendor & Commercial Order Details Grid
    vendor_lines = [f"<b>M/S:</b> <b>{(vendor_name or 'SUPPLIER').upper()}</b>"]
    if vendor_addr:
        vendor_lines.append(f"{vendor_addr}")
    if contact_person:
        vendor_lines.append(f"<b>Attn:</b> {contact_person}")
    if vendor_mobile:
        vendor_lines.append(f"<b>Mobile:</b> {vendor_mobile}")
    if vendor_email:
        vendor_lines.append(f"<b>Email:</b> {vendor_email}")
    if vendor_gstin:
        vendor_lines.append(f"<b>GSTIN / UIN:</b> {vendor_gstin}")

    vendor_cell_content = "<br/>".join(vendor_lines)

    order_meta_lines = [
        f"<b>PO NUMBER:</b> {po_num}",
        f"<b>PO DATE:</b> {po_date or '25.10.2026'}",
        f"<b>PROJECT / JOB:</b> {proj_id}",
    ]
    if quote_ref:
        order_meta_lines.append(f"<b>QUOTATION REF:</b> {quote_ref}")
    order_meta_lines.extend([
        f"<b>PAYMENT TERMS:</b> {pay_terms}",
        f"<b>DELIVERY TERMS:</b> {deliv_terms}",
        f"<b>DISPATCH MODE:</b> {dispatch_mode}",
    ])

    order_meta_content = "<br/>".join(order_meta_lines)

    grid_data = [
        [
            Paragraph("<b>VENDOR / SUPPLIER DETAILS</b>", h_bold),
            Paragraph("<b>ORDER & DISPATCH TERMS</b>", h_bold),
        ],
        [
            Paragraph(vendor_cell_content, body_cell),
            Paragraph(order_meta_content, body_cell),
        ]
    ]

    grid_table = Table(grid_data, colWidths=[printable_w * 0.52, printable_w * 0.48])
    grid_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#F2ECE4')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#EFEAE2')),
        ('BACKGROUND', (0, 1), (-1, 1), c_primary_light),
        ('BOX', (0, 0), (-1, -1), 0.8, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(grid_table)
    story.append(Spacer(1, 2 * mm))

    # 3. Bill To & Ship To Banner
    addr_banner_data = [
        [
            Paragraph("<b>BILL TO:</b> UMA TECHNO FAB PVT. LTD., Plot 48/B, GIDC Makarpura, Vadodara - 390010 (GSTIN: 24AAACU5567R1Z1)", body_cell),
            Paragraph("<b>SHIP TO / CONSIGNEE:</b> UMA TECHNO FAB PVT. LTD., Survey No. 1040/3, Rajpur Works, Mehsana - 382715", body_cell),
        ]
    ]
    addr_table = Table(addr_banner_data, colWidths=[printable_w * 0.50, printable_w * 0.50])
    addr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9F6F0')),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(addr_table)
    story.append(Spacer(1, 2.5 * mm))

    # 4. Material Line Items Table
    col_w = [
        printable_w * 0.05,  # # (Sr)
        printable_w * 0.35,  # Item Description & Specs
        printable_w * 0.10,  # HSN/SAC
        printable_w * 0.08,  # Qty
        printable_w * 0.07,  # UOM
        printable_w * 0.11,  # Unit Rate
        printable_w * 0.11,  # Taxable Amt
        printable_w * 0.13,  # Total (INR)
    ]

    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=8.5,
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    items_header = [
        Paragraph("<b>Sr</b>", th_style),
        Paragraph("<b>Item Description & Specifications</b>", ParagraphStyle('THL', parent=th_style, alignment=TA_LEFT)),
        Paragraph("<b>HSN/SAC</b>", th_style),
        Paragraph("<b>Qty</b>", th_style),
        Paragraph("<b>UOM</b>", th_style),
        Paragraph("<b>Rate (₹)</b>", ParagraphStyle('THR', parent=th_style, alignment=TA_RIGHT)),
        Paragraph("<b>Taxable (₹)</b>", ParagraphStyle('THR2', parent=th_style, alignment=TA_RIGHT)),
        Paragraph("<b>Total (₹)</b>", ParagraphStyle('THR3', parent=th_style, alignment=TA_RIGHT)),
    ]

    items_table_rows = [items_header]

    calc_subtotal = 0.0
    for idx, itm in enumerate(items, 1):
        name = str(itm.get('itemName') or itm.get('item_name') or itm.get('description') or f"Item #{idx}").strip()
        code = str(itm.get('itemCode') or itm.get('item_code') or '').strip()
        spec = str(itm.get('specification') or itm.get('dimensions') or '').strip()
        hsn = str(itm.get('hsnCode') or itm.get('hsn_code') or '7219').strip()
        qty = float(itm.get('orderedQuantity') or itm.get('quantity') or itm.get('ordered_quantity') or 1)
        uom = str(itm.get('unitOfMeasure') or itm.get('unit') or 'NOS').strip()
        rate = float(itm.get('unitPrice') or itm.get('unit_price') or itm.get('rate') or 0)
        line_total = float(itm.get('totalPrice') or itm.get('total_price') or (qty * rate))
        if line_total == 0 and rate > 0:
            line_total = qty * rate

        calc_subtotal += line_total

        desc_content = f"<b>{name}</b>"
        if code:
            desc_content += f" <font color='#70665F'>[{code}]</font>"
        if spec:
            desc_content += f"<br/><font size='6.5' color='#544B45'>Spec: {spec}</font>"

        items_table_rows.append([
            Paragraph(f"<b>{idx}</b>", body_cell_center),
            Paragraph(desc_content, body_cell),
            Paragraph(hsn, body_cell_center),
            Paragraph(f"<b>{qty:g}</b>", body_cell_center),
            Paragraph(uom, body_cell_center),
            Paragraph(f"₹{rate:,.2f}" if rate > 0 else "-", body_cell_right),
            Paragraph(f"₹{line_total:,.2f}" if line_total > 0 else "-", body_cell_right),
            Paragraph(f"<b>₹{line_total:,.2f}</b>" if line_total > 0 else "-", body_cell_right),
        ])

    if len(items_table_rows) == 1:
        items_table_rows.append([
            Paragraph("1", body_cell_center),
            Paragraph("<b>Custom Engineering Material Item</b>", body_cell),
            Paragraph("7219", body_cell_center),
            Paragraph("1", body_cell_center),
            Paragraph("NOS", body_cell_center),
            Paragraph(f"₹{grand_total:,.2f}", body_cell_right),
            Paragraph(f"₹{grand_total:,.2f}", body_cell_right),
            Paragraph(f"<b>₹{grand_total:,.2f}</b>", body_cell_right),
        ])
        calc_subtotal = grand_total

    items_table = Table(items_table_rows, colWidths=col_w, repeatRows=1)
    table_style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
    ]

    # Alternating row background
    for r_idx in range(1, len(items_table_rows)):
        if r_idx % 2 == 0:
            table_style_commands.append(('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor('#FAF8F5')))

    items_table.setStyle(TableStyle(table_style_commands))
    story.append(items_table)
    story.append(Spacer(1, 2 * mm))

    # 5. Financial Summary & Amount in Words
    final_subtotal = sub_total if sub_total > 0 else calc_subtotal
    final_tax = tax_amount if tax_amount > 0 else (final_subtotal * 0.18 if (grand_total > final_subtotal) else 0)
    final_grand_total = grand_total if grand_total > 0 else (final_subtotal + final_tax + freight_charges - discount_amount)

    amt_in_words = number_to_words_indian(final_grand_total)

    summary_rows = [
        [Paragraph("Taxable Subtotal:", body_cell), Paragraph(f"₹{final_subtotal:,.2f}", body_cell_right)],
    ]
    if discount_amount > 0:
        summary_rows.append([Paragraph("Discount Amount:", body_cell), Paragraph(f"-₹{discount_amount:,.2f}", body_cell_right)])
    if final_tax > 0:
        summary_rows.append([Paragraph("Applicable GST (CGST+SGST/IGST):", body_cell), Paragraph(f"₹{final_tax:,.2f}", body_cell_right)])
    if freight_charges > 0:
        summary_rows.append([Paragraph("Freight & Packing:", body_cell), Paragraph(f"₹{freight_charges:,.2f}", body_cell_right)])
    summary_rows.append([
        Paragraph("<b>NET GRAND TOTAL (INR):</b>", ParagraphStyle('GTL', parent=h_bold, textColor=c_green, fontSize=8.5)),
        Paragraph(f"<b>₹{final_grand_total:,.2f}</b>", ParagraphStyle('GTR', parent=h_bold, alignment=TA_RIGHT, textColor=c_green, fontSize=9.5))
    ])

    summary_table = Table(summary_rows, colWidths=[printable_w * 0.28, printable_w * 0.18])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_primary_light),
        ('BOX', (0, 0), (-1, -1), 0.7, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))

    words_cell = [
        Paragraph("<b>AMOUNT IN WORDS:</b>", ParagraphStyle('AWHead', parent=h_bold, fontSize=7.5, textColor=c_primary)),
        Spacer(1, 1 * mm),
        Paragraph(f"<b>{amt_in_words}</b>", ParagraphStyle('AWBody', parent=body_cell_bold, fontSize=8, textColor=c_dark)),
    ]
    if spec_instr:
        words_cell.extend([
            Spacer(1, 2 * mm),
            Paragraph(f"<b>SPECIAL INSTRUCTIONS:</b> <font color='#544B45'>{spec_instr}</font>", body_cell)
        ])

    words_table = Table([[words_cell, summary_table]], colWidths=[printable_w * 0.54, printable_w * 0.46])
    words_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(words_table)
    story.append(Spacer(1, 2.5 * mm))

    # 6. Terms & Conditions Box
    terms_paragraphs = [
        Paragraph("<b>COMMERCIAL & FABRICATION TERMS & CONDITIONS:</b>", ParagraphStyle('THead', parent=h_bold, fontSize=7.5, textColor=c_primary)),
        Spacer(1, 1 * mm),
        Paragraph("1. <b>Quality & Specs:</b> Material must strictly conform to engineering dimensions, tolerances, chemical/mechanical standards and Grade.", body_cell),
        Paragraph("2. <b>Documentation:</b> Supply must strictly be accompanied by Tax Invoice, Delivery Challan & Manufacturer's Test Certificate (MTC / TC).", body_cell),
        Paragraph("3. <b>Delivery:</b> Strictly adhering to agreed delivery schedule. Any delay without prior written notice may attract LD / penalty.", body_cell),
        Paragraph("4. <b>Inspection:</b> Inspection will be conducted at our Rajpur Works upon arrival. Discrepant or defective items will be rejected.", body_cell),
        Paragraph(f"5. <b>Payment:</b> {pay_terms}. Releases after receipt of original invoice, inspection and GRN clearance.", body_cell),
    ]

    terms_table = Table([[terms_paragraphs]], colWidths=[printable_w])
    terms_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAF7F2')),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(terms_table)
    story.append(Spacer(1, 3 * mm))

    # 7. Official Signatures Section
    sig_data = [
        [
            Paragraph("<b>PREPARED BY</b><br/><br/><br/><br/>_______________________<br/>Purchase Department", body_cell_center),
            Paragraph("<b>CHECKED & VERIFIED</b><br/><br/><br/><br/>_______________________<br/>Planning & Quality Stores", body_cell_center),
            Paragraph("<b>AUTHORIZED SIGNATORY</b><br/><br/><br/><br/>_______________________<br/><b>For UMA TECHNO FAB PVT. LTD.</b>", body_cell_center),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[printable_w * 0.33, printable_w * 0.33, printable_w * 0.34])
    sig_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FCFBF9')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(KeepTogether(sig_table))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
