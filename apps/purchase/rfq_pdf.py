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
        self.drawString(margin_x, 8.5 * mm, "UMA TECHNO FAB PVT. LTD. • Official Purchase Inquiry Letter • Confidential")

        # Footer Right: Page numbering
        self.setFont('Helvetica', 7.5)
        self.setFillColor(colors.HexColor('#70665F'))
        self.drawRightString(
            page_w - margin_x,
            8.5 * mm,
            f"Page {self._pageNumber} of {page_count}"
        )
        self.restoreState()


def generate_rfq_pdf(rfq, payload=None) -> bytes:
    """
    Generates a professional, print-ready PDF for Purchase Inquiry / Request (REQUIRE)
    matching Uma Technofab format.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=18 * mm,
    )

    printable_w = A4[0] - 24 * mm

    # Extract metadata safely
    p = payload or {}
    rfq_num = str(getattr(rfq, 'rfq_number', None) or getattr(rfq, 'id', None) or p.get('rfqNumber') or 'REQ-2026').strip()
    rfq_date = str(getattr(rfq, 'rfq_date', None) or p.get('rfqDate') or '').strip()
    due_date = str(getattr(rfq, 'due_date', None) or p.get('dueDate') or '').strip()
    proj_id = str(getattr(rfq, 'project_id', None) or getattr(rfq, 'pr_id', None) or p.get('projectId') or 'General').strip()

    # Vendor Details
    vendor_name = str(getattr(rfq, 'supplier_name', None) or p.get('supplierName') or p.get('vendorName') or '').strip()
    vendor_mobile = str(getattr(rfq, 'supplier_mobile', None) or p.get('supplierMobile') or p.get('vendorMobile') or '').strip()
    vendor_email = str(getattr(rfq, 'supplier_email', None) or p.get('supplierEmail') or p.get('vendorEmail') or '').strip()
    vendor_addr = str(getattr(rfq, 'supplier_address', None) or p.get('supplierAddress') or p.get('vendorAddress') or '').strip()
    vendor_gstin = str(getattr(rfq, 'supplier_gstin', None) or p.get('supplierGstin') or p.get('vendorGstin') or '').strip()

    # If vendor is still blank, extract from suppliers JSONField
    supps = getattr(rfq, 'suppliers', None) or []
    if isinstance(supps, list) and len(supps) > 0 and isinstance(supps[0], dict):
        s0 = supps[0]
        if not vendor_name:
            vendor_name = s0.get('supplierName') or s0.get('name') or ''
        if not vendor_mobile:
            vendor_mobile = s0.get('supplierMobile') or s0.get('mobile') or s0.get('phone') or ''
        if not vendor_email:
            vendor_email = s0.get('supplierEmail') or s0.get('email') or ''
        if not vendor_addr:
            vendor_addr = s0.get('supplierAddress') or s0.get('address') or ''
        if not vendor_gstin:
            vendor_gstin = s0.get('supplierGstin') or s0.get('gstin') or ''

    subject_line = str(getattr(rfq, 'subject', None) or p.get('subject') or 'Material Purchase Requirement').strip()
    special_note = str(getattr(rfq, 'special_note', None) or p.get('specialNote') or '').strip()
    deliv_loc = str(getattr(rfq, 'delivery_location', None) or p.get('deliveryLocation') or 'RAJPUR, MEHSANA WORKS').strip()

    # Extract Items
    items = getattr(rfq, 'items', None) or p.get('items') or []
    if not isinstance(items, list):
        items = []

    # Typography & Styles
    styles = getSampleStyleSheet()

    c_primary = colors.HexColor('#75401F')   # Brand Amber/Brown
    c_dark = colors.HexColor('#211B17')      # Text Primary
    c_muted = colors.HexColor('#6B7280')     # Text Muted
    c_border = colors.HexColor('#211B17')    # Box Border

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=c_dark,
        alignment=TA_CENTER,
    )

    company_name_style = ParagraphStyle(
        'CompName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=17,
        textColor=c_primary,
        alignment=TA_LEFT,
    )

    company_sub_style = ParagraphStyle(
        'CompSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#544B45'),
        alignment=TA_LEFT,
    )

    h_bold = ParagraphStyle(
        'HBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10.5,
        textColor=c_dark,
    )

    h_val = ParagraphStyle(
        'HVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=c_dark,
    )

    body_cell = ParagraphStyle(
        'BodyCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=c_dark,
    )

    body_cell_bold = ParagraphStyle(
        'BodyCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=c_dark,
    )

    body_cell_center = ParagraphStyle(
        'BodyCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=c_dark,
        alignment=TA_CENTER,
    )

    story = []

    # 1. Company Letterhead Header
    header_table_data = [
        [
            Paragraph("<b>UMA TECHNO FAB PVT. LTD.</b>", company_name_style),
            Paragraph(f"<b>PURCHASE INQUIRY / REQUIRE</b><br/><font size='7.5' color='#70665F'>RFQ NO: <b>{rfq_num}</b></font>", ParagraphStyle('HRight', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=TA_RIGHT, textColor=c_primary))
        ],
        [
            Paragraph(
                "Manufacturers of Dairy, Chemical, Food & Pharma Process Machinery<br/>"
                "Plot No. 48/B, GIDC Industrial Estate, Makarpura, Vadodara - 390010, Gujarat, India<br/>"
                "Works: Kadi - Mehsana Highway, Rajpur, Dist. Mehsana, Gujarat | Web: www.umatechnofab.com",
                company_sub_style
            ),
            Paragraph(
                f"<b>Date:</b> {rfq_date or '25.10.2026'}<br/>"
                f"<b>Required By:</b> {due_date or 'Immediate'}<br/>"
                f"<b>Project Ref:</b> {proj_id}",
                ParagraphStyle('HMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_RIGHT, textColor=c_dark)
            )
        ]
    ]

    header_table = Table(header_table_data, colWidths=[printable_w * 0.65, printable_w * 0.35])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 2 * mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=1, spaceAfter=3 * mm))

    # 2. Vendor & Inquiry Metadata Grid Box
    vendor_lines = [f"<b>M/S:</b> <b>{(vendor_name or 'VALUED SUPPLIER').upper()}</b>"]
    if vendor_addr:
        vendor_lines.append(f"{vendor_addr}")
    if vendor_mobile:
        vendor_lines.append(f"<b>Contact:</b> {vendor_mobile}")
    if vendor_email:
        vendor_lines.append(f"<b>Email:</b> {vendor_email}")
    if vendor_gstin:
        vendor_lines.append(f"<b>GSTIN:</b> {vendor_gstin}")

    vendor_cell_content = "<br/>".join(vendor_lines)

    doc_meta_lines = [
        f"<b>INQUIRY NO:</b> {rfq_num}",
        f"<b>DATE:</b> {rfq_date or '25.10.2026'}",
        f"<b>DUE / REQUIRED DATE:</b> {due_date or 'Immediate / 7 Days'}",
        f"<b>DELIVERY LOCATION:</b> {deliv_loc}",
        f"<b>PROJECT:</b> {proj_id}",
        f"<b>TAXES:</b> AS APPLICABLE",
        f"<b>GST NO:</b> 24AAEFU9027H1Z3",
    ]
    meta_cell_content = "<br/>".join(doc_meta_lines)

    grid_data = [
        [
            Paragraph(f"<font color='#75401F'><b>SUPPLIER / VENDOR DETAILS:</b></font><br/>{vendor_cell_content}", h_val),
            Paragraph(f"<font color='#75401F'><b>INQUIRY METADATA:</b></font><br/>{meta_cell_content}", h_val)
        ]
    ]

    grid_table = Table(grid_data, colWidths=[printable_w * 0.55, printable_w * 0.45])
    grid_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.2, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.8, c_border),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#FAF7F2')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#FFFFFF')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(grid_table)
    story.append(Spacer(1, 2 * mm))

    # 3. Subject Banner
    subj_banner_data = [[
        Paragraph(f"<b>SUB:</b> <b>{subject_line.upper()}</b>", ParagraphStyle('Subj', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=c_dark))
    ]]
    subj_table = Table(subj_banner_data, colWidths=[printable_w])
    subj_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3EDE4')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(subj_table)
    story.append(Spacer(1, 2 * mm))

    # 4. Material Lines Table
    # Columns: Sr No (24pt), Description & Specs (remaining), Qty (40pt), UOM (35pt), Rate (Blank) (55pt), Amount (Blank) (60pt)
    col_sr = 22 * mm
    col_qty = 18 * mm
    col_uom = 15 * mm
    col_rate = 22 * mm
    col_amt = 24 * mm
    col_desc = printable_w - (col_sr + col_qty + col_uom + col_rate + col_amt)

    table_rows = [
        [
            Paragraph("<b>Sr.<br/>No.</b>", ParagraphStyle('THC', parent=body_cell_center, fontName='Helvetica-Bold', fontSize=8)),
            Paragraph("<b>Description of Material / Item(s) & Specification</b>", ParagraphStyle('THL', parent=body_cell, fontName='Helvetica-Bold', fontSize=8)),
            Paragraph("<b>Qty.</b>", ParagraphStyle('THC2', parent=body_cell_center, fontName='Helvetica-Bold', fontSize=8)),
            Paragraph("<b>UOM</b>", ParagraphStyle('THC3', parent=body_cell_center, fontName='Helvetica-Bold', fontSize=8)),
            Paragraph("<b>Rate / Unit<br/>(₹ Quoted)</b>", ParagraphStyle('THC4', parent=body_cell_center, fontName='Helvetica-Bold', fontSize=8)),
            Paragraph("<b>Total Amount<br/>(₹ Quoted)</b>", ParagraphStyle('THC5', parent=body_cell_center, fontName='Helvetica-Bold', fontSize=8)),
        ]
    ]

    total_qty = 0
    for idx, itm in enumerate(items, 1):
        raw_name = itm.get('itemName') or itm.get('item_name') or itm.get('description') or f"Item {idx}"
        spec = itm.get('dimensions') or itm.get('specification') or ''
        grp = itm.get('groupTitle') or itm.get('group_title') or ''
        qty_num = float(itm.get('quantity') or itm.get('requiredQuantity') or itm.get('required_quantity') or 1)
        total_qty += qty_num
        uom_str = itm.get('unitOfMeasure') or itm.get('unit_of_measure') or itm.get('unit') or 'NOS'

        desc_html = f"<b>[{idx}] {raw_name.strip()}</b>"
        if grp:
            desc_html = f"<font color='#75401F'><b>◆ {grp}</b></font><br/>" + desc_html
        if spec:
            desc_html += f"<br/><font color='#4B5563' size='7'><i>Spec: {spec}</i></font>"

        rate_val = itm.get('rate')
        rate_str = f"₹ {float(rate_val):,.2f}" if rate_val and float(rate_val) > 0 else ""
        amt_val = itm.get('amount')
        amt_str = f"₹ {float(amt_val):,.2f}" if amt_val and float(amt_val) > 0 else ""

        table_rows.append([
            Paragraph(f"<b>{idx}</b>", body_cell_center),
            Paragraph(desc_html, body_cell),
            Paragraph(f"<b>{qty_num:g}</b>", body_cell_center),
            Paragraph(uom_str, body_cell_center),
            Paragraph(rate_str, body_cell_center),
            Paragraph(amt_str, body_cell_center),
        ])

    # Total Qty Row
    table_rows.append([
        Paragraph("", body_cell_center),
        Paragraph("<b>TOTAL REQUIRED QUANTITY:</b>", ParagraphStyle('TotL', parent=body_cell, alignment=TA_RIGHT, fontName='Helvetica-Bold')),
        Paragraph(f"<b>{total_qty:g}</b>", ParagraphStyle('TotQ', parent=body_cell_center, fontName='Helvetica-Bold', textColor=c_primary)),
        Paragraph("<b>ITEMS</b>", ParagraphStyle('TotU', parent=body_cell_center, fontName='Helvetica-Bold')),
        Paragraph("", body_cell_center),
        Paragraph("", body_cell_center),
    ])

    mat_table = Table(table_rows, colWidths=[col_sr, col_desc, col_qty, col_uom, col_rate, col_amt], repeatRows=1)
    mat_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.2, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.6, c_border),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3EDE4')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FAF7F2')),
    ]))
    story.append(mat_table)
    story.append(Spacer(1, 2 * mm))

    # 5. Special Note / Instructions
    if special_note:
        note_data = [[
            Paragraph(f"<b>SPECIAL INSTRUCTIONS:</b><br/>{special_note.replace(chr(10), '<br/>')}", ParagraphStyle('SpecNote', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=c_primary))
        ]]
        note_table = Table(note_data, colWidths=[printable_w])
        note_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, c_border),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFBEB')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(note_table)
        story.append(Spacer(1, 2 * mm))

    # 6. Terms & Conditions and Authorized Signatory
    terms_list = [
        "<b>Delivery:</b> Material strictly along with Delivery Challan, Tax Invoice & Test Certificate (TC).",
        "<b>Documentation:</b> Please submit your challan & invoices in duplicate and in English only.",
        "<b>Rate Validity:</b> No revision in rate shall be accepted without written confirmation.",
        "<b>Freight & Packaging:</b> No packing, forwarding, delivery charges will be allowed unless authorized in writing.",
        "<b>Rejection:</b> Rejected material must be lifted within one week from date of rejection (GRN).",
        "<b>Response:</b> Please quote your best discounted rate with lead delivery schedule at the earliest."
    ]
    terms_html = "<br/>".join([f"{i}. {t}" for i, t in enumerate(terms_list, 1)])

    terms_cell = Paragraph(f"<b>TERMS & CONDITIONS:</b><br/><font size='7' color='#374151'>{terms_html}</font>", h_val)

    signatory_cell = Paragraph(
        "<br/><br/>"
        "<b>Thanking you we remain,</b><br/>"
        "<b>For, UMA TECHNO FAB PVT. LTD.</b><br/><br/><br/>"
        "____________________________<br/>"
        "<b>Authorized Purchase Representative</b>",
        ParagraphStyle('Sign', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, alignment=TA_CENTER, textColor=c_dark)
    )

    footer_grid = Table([[terms_cell, signatory_cell]], colWidths=[printable_w * 0.68, printable_w * 0.32])
    footer_grid.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.6, c_border),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#FAF7F2')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(KeepTogether(footer_grid))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
