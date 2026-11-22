"""Payslip PDF (reportlab). Uses 'Rs.' because the built-in PDF fonts have no rupee glyph."""
import io
import zipfile
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen',
         'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
_TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']


def _two(n):
    return _ONES[n] if n < 20 else (_TENS[n // 10] + (' ' + _ONES[n % 10] if n % 10 else ''))


def _three(n):
    out = ''
    if n >= 100:
        out += _ONES[n // 100] + ' Hundred'
        n %= 100
        if n:
            out += ' '
    return out + (_two(n) if n else '')


def amount_in_words(amount):
    """Indian numbering: 1,23,456.50 -> 'One Lakh Twenty Three Thousand Four Hundred Fifty Six Rupees and Fifty Paise Only'."""
    amt = Decimal(str(amount or 0)).quantize(Decimal('0.01'))
    neg = amt < 0
    amt = abs(amt)
    rupees, paise = int(amt), int((amt - int(amt)) * 100)
    if rupees == 0 and paise == 0:
        return 'Zero Rupees Only'
    parts = []
    for div, name in ((10000000, 'Crore'), (100000, 'Lakh'), (1000, 'Thousand')):
        if rupees >= div:
            parts.append(_three(rupees // div) + ' ' + name)
            rupees %= div
    if rupees:
        parts.append(_three(rupees))
    words = ' '.join(parts) or 'Zero'
    out = f'{words} Rupees' + (f' and {_two(paise)} Paise' if paise else '') + ' Only'
    return ('Minus ' if neg else '') + out


def _n(v):
    v = Decimal(str(v or 0))
    return f'{v:,.2f}'


def _day(v):
    v = Decimal(str(v or 0))
    return f'{v:g}'


def build_payslip(rec, company):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
                            title=f'Payslip {rec.employee_name} {rec.month_year}', author=company.get('name', ''))
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle('h1', parent=ss['Title'], fontSize=17, leading=20, textColor=colors.HexColor('#1F3FB0'), alignment=0, spaceAfter=0)
    small = ParagraphStyle('small', parent=ss['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#475569'))
    norm = ParagraphStyle('norm', parent=ss['Normal'], fontSize=9, leading=11)
    bold = ParagraphStyle('bold', parent=norm, fontName='Helvetica-Bold')
    right = ParagraphStyle('right', parent=norm, alignment=2)

    story = []
    head = Table([[
        [Paragraph(company.get('name', ''), h1), Paragraph(company.get('address', ''), small),
         Paragraph(company.get('contact', ''), small)],
        [Paragraph('<b>SALARY SLIP</b>', ParagraphStyle('t', parent=norm, alignment=2, fontSize=12)),
         Paragraph(f'For the month of <b>{rec.month_year}</b>', right), Paragraph(f'Ref: {rec.payroll_number}', ParagraphStyle('r', parent=small, alignment=2))],
    ]], colWidths=[118 * mm, 64 * mm])
    head.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, 0), 1.2, colors.HexColor('#1F3FB0')),
                              ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    story += [head, Spacer(1, 6)]

    def kv(label, val):
        return [Paragraph(f'<font color="#64748b">{label}</font>', norm), Paragraph(f'<b>{val or "-"}</b>', norm)]

    info = Table([
        kv('Employee ID', rec.employee_id) + kv('Employee Name', rec.employee_name),
        kv('Department', rec.department) + kv('Designation', rec.designation),
        kv('Date of Joining', rec.joining_date) + kv('PAN', rec.pan_number),
        kv('UAN (PF)', rec.uan_number) + kv('ESI No.', rec.esi_number),
        kv('Bank', rec.bank_name) + kv('Bank A/C No.', rec.bank_account_no),
        kv('IFSC', rec.bank_ifsc) + kv('Calendar Days', _day(rec.calendar_days)),
        kv('Paid Days', _day(rec.paid_days)) + kv('Loss of Pay Days', _day(rec.loss_of_pay_days)),
    ], colWidths=[30 * mm, 61 * mm, 30 * mm, 61 * mm])
    info.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#cbd5e1')), ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                              ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5)]))
    story += [info, Spacer(1, 8)]

    earn = [('Basic Salary', rec.basic_salary), ('House Rent Allowance (HRA)', rec.hra), ('Conveyance Allowance', rec.conveyance_allowance),
            ('Medical Allowance', rec.medical_allowance), ('Special Allowance', rec.special_allowance), ('Overtime', rec.overtime_amount),
            ('Other Earnings', rec.other_earnings), ('Reimbursements', rec.reimbursement_amount)]
    # records created before the engine only carry a combined "allowances" figure
    if not any(Decimal(str(v or 0)) for _, v in earn[2:5]) and Decimal(str(rec.allowances or 0)):
        earn[2:5] = [('Special & Other Allowances', rec.allowances)]
    ded = [('Provident Fund (Employee)', rec.pf_deduction), ('ESI (Employee)', rec.esi_deduction), ('Professional Tax', rec.pt_deduction),
           ('Income Tax (TDS)', rec.tds_deduction), ('Loan / Advance Recovery', rec.loan_advance_recovery), ('Other Deductions', rec.other_deductions)]
    earn = [(a, b) for a, b in earn if Decimal(str(b or 0)) != 0 or a in ('Basic Salary',)]
    ded = [(a, b) for a, b in ded if Decimal(str(b or 0)) != 0] or [('No deductions', 0)]
    rows = max(len(earn), len(ded))
    earn += [('', None)] * (rows - len(earn))
    ded += [('', None)] * (rows - len(ded))
    total_earn = Decimal(str(rec.gross_earnings or 0)) + Decimal(str(rec.reimbursement_amount or 0))
    data = [[Paragraph('<b>EARNINGS</b>', norm), Paragraph('<b>Amount (Rs.)</b>', right), Paragraph('<b>DEDUCTIONS</b>', norm), Paragraph('<b>Amount (Rs.)</b>', right)]]
    for (a, av), (d, dv) in zip(earn, ded):
        data.append([Paragraph(a, norm), Paragraph(_n(av) if av is not None else '', right), Paragraph(d, norm), Paragraph(_n(dv) if dv is not None and d != 'No deductions' else '', right)])
    data.append([Paragraph('<b>Total Earnings</b>', norm), Paragraph(f'<b>{_n(total_earn)}</b>', right),
                 Paragraph('<b>Total Deductions</b>', norm), Paragraph(f'<b>{_n(rec.total_deductions)}</b>', right)])
    t = Table(data, colWidths=[56 * mm, 35 * mm, 56 * mm, 35 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')), ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#94a3b8')), ('LINEAFTER', (1, 0), (1, -1), 0.6, colors.HexColor('#94a3b8')),
        ('LINEABOVE', (0, -1), (-1, -1), 0.8, colors.HexColor('#475569')), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    story += [t, Spacer(1, 8)]

    net = Table([[Paragraph('<b>NET PAY</b>', ParagraphStyle('np', parent=norm, fontSize=11)),
                  Paragraph(f'<b>Rs. {_n(rec.net_salary)}</b>', ParagraphStyle('npv', parent=norm, fontSize=11, alignment=2))],
                 [Paragraph(f'<i>{amount_in_words(rec.net_salary)}</i>', ParagraphStyle('w', parent=small, fontSize=8.5)), '']],
                colWidths=[120 * mm, 62 * mm])
    net.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1F3FB0')), ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef2ff')),
                             ('SPAN', (0, 1), (1, 1)), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    story += [net, Spacer(1, 6)]

    if rec.status == 'Paid' and rec.paid_date:
        story.append(Paragraph(f'Paid on {rec.paid_date:%d %b %Y} via {rec.payment_mode or "Bank Transfer"}'
                               + (f' (Ref: {rec.payment_ref})' if rec.payment_ref else ''), small))
    story += [Spacer(1, 4), Paragraph(f'Employer contribution (not deducted from pay): PF Rs. {_n(rec.employer_pf)}, ESI Rs. {_n(rec.employer_esi)}.', small),
              Spacer(1, 18), Paragraph('This is a computer-generated payslip and does not require a signature.', small)]
    doc.build(story)
    return buf.getvalue()


def safe_name(rec):
    return ''.join(c if c.isalnum() else '_' for c in f'{rec.employee_name}_{rec.employee_id}_{rec.month_year}').strip('_') + '.pdf'


def build_zip(records, company):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for r in records:
            z.writestr(safe_name(r), build_payslip(r, company))
    return out.getvalue()
