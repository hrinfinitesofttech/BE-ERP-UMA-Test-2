"""Financial statements computed live from the ledger: Trial Balance, Trading & P&L, Balance Sheet, Ratios."""
from collections import OrderedDict
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from .ledger_models import (AccountGroup, Ledger, LedgerEntry, StockItem, BALANCE_SHEET_NATURES, CREDIT_NATURES)

ZERO = Decimal('0')
OPENING_STOCK = 'Opening Stock'


def fy_range(fy=None):
    """fy like '2025-26' -> (start, end). Default: FY containing today."""
    if not fy:
        t = date.today()
        y = t.year if t.month >= 4 else t.year - 1
    else:
        y = int(str(fy)[:4])
    return date(y, 4, 1), date(y + 1, 3, 31), f"{y}-{str(y + 1)[2:]}"


def f(v):
    return float(round(Decimal(v or 0), 2))


def _group_path(group, cache):
    if group.pk in cache:
        return cache[group.pk]
    chain, g = [], group
    while g is not None:
        chain.append(g)
        g = g.parent
    cache[group.pk] = list(reversed(chain))
    return cache[group.pk]


def ledger_balances(d_from, d_to):
    """Return list of dicts per ledger with opening/debit/credit/closing (signed: Dr positive)."""
    prior = {r['ledger_id']: (r['d'] or ZERO) - (r['c'] or ZERO) for r in
             LedgerEntry.objects.filter(voucher_date__lt=d_from).values('ledger_id').annotate(d=Sum('debit'), c=Sum('credit'))}
    during = {r['ledger_id']: (r['d'] or ZERO, r['c'] or ZERO) for r in
              LedgerEntry.objects.filter(voucher_date__gte=d_from, voucher_date__lte=d_to)
              .values('ledger_id').annotate(d=Sum('debit'), c=Sum('credit'))}
    cache, out = {}, []
    for led in Ledger.objects.select_related('group', 'group__parent', 'group__parent__parent').all():
        path = _group_path(led.group, cache)
        top = path[0]
        nature = top.nature
        is_bs = nature in BALANCE_SHEET_NATURES
        if is_bs:
            opening = led.signed_opening + prior.get(led.pk, ZERO)
        else:
            # Opening stock ledger is a P&L item for the period: keep its opening
            opening = ZERO
        d, c = during.get(led.pk, (ZERO, ZERO))
        out.append({'ledger': led, 'name': led.name, 'id': led.pk, 'group': led.group.name, 'top': top.name,
                    'path': [g.name for g in path], 'nature': nature, 'is_bs': is_bs,
                    'opening': opening, 'debit': d, 'credit': c, 'closing': opening + d - c})
    return out


def _split(signed):
    return (signed, ZERO) if signed >= 0 else (ZERO, -signed)


def closing_stock_value():
    return StockItem.objects.aggregate(v=Sum('closing_value'))['v'] or ZERO


def trial_balance(fy=None):
    d_from, d_to, code = fy_range(fy)
    rows = ledger_balances(d_from, d_to)
    # P&L natured ledgers: closing within period; Opening Stock ledger carries its opening balance in TB
    lines, tdr, tcr = [], ZERO, ZERO
    for r in rows:
        signed = r['closing']
        dr, cr = _split(signed)
        tdr += dr; tcr += cr
        lines.append({'ledger_id': r['id'], 'ledger': r['name'], 'group': r['group'], 'top_group': r['top'],
                      'path': r['path'], 'nature': r['nature'], 'opening': f(r['opening']), 'debit': f(r['debit']),
                      'credit': f(r['credit']), 'closing_dr': f(dr), 'closing_cr': f(cr)})
    return {'financial_year': code, 'from': d_from.isoformat(), 'to': d_to.isoformat(), 'lines': lines,
            'total_dr': f(tdr), 'total_cr': f(tcr), 'difference': f(tdr - tcr), 'is_balanced': abs(tdr - tcr) < Decimal('0.01')}


def _sum_group(rows, top=None, group=None, nature=None, credit_normal=False):
    t = ZERO
    for r in rows:
        if top and r['top'] != top:
            continue
        if group and group not in r['path']:
            continue
        if nature and r['nature'] != nature:
            continue
        t += (-r['closing'] if credit_normal else r['closing'])
    return t


def _items(rows, group=None, nature=None, credit_normal=False, exclude=()):
    items = []
    for r in rows:
        if group and group not in r['path']:
            continue
        if nature and r['nature'] != nature:
            continue
        if r['name'] in exclude:
            continue
        amt = -r['closing'] if credit_normal else r['closing']
        items.append({'name': r['name'], 'amount': f(amt), 'group': r['group']})
    return items


def profit_loss(fy=None):
    d_from, d_to, code = fy_range(fy)
    rows = ledger_balances(d_from, d_to)
    opening_stock_row = next((r for r in rows if r['name'] == OPENING_STOCK), None)
    opening_stock = opening_stock_row['opening'] if opening_stock_row else ZERO
    closing_stock = closing_stock_value()
    sales = _sum_group(rows, nature='Sales', credit_normal=True)
    purchase = _sum_group(rows, nature='Purchase')
    direct_exp = _sum_group(rows, nature='DirectExpense')
    direct_inc = _sum_group(rows, nature='DirectIncome', credit_normal=True)
    indirect_exp = _sum_group(rows, nature='IndirectExpense')
    indirect_inc = _sum_group(rows, nature='IndirectIncome', credit_normal=True)

    trading_dr = opening_stock + purchase + direct_exp
    trading_cr = sales + direct_inc + closing_stock
    gross = trading_cr - trading_dr  # +ve profit
    net = gross + indirect_inc - indirect_exp

    return {
        'financial_year': code, 'from': d_from.isoformat(), 'to': d_to.isoformat(),
        'trading': {
            'dr': {'opening_stock': f(opening_stock), 'purchase': f(purchase), 'purchase_items': _items(rows, nature='Purchase'),
                   'direct_expenses': f(direct_exp), 'direct_expense_items': _items(rows, nature='DirectExpense'),
                   'gross_profit': f(gross) if gross > 0 else 0.0,
                   'total': f(max(trading_dr, trading_cr))},
            'cr': {'sales': f(sales), 'sales_items': _items(rows, nature='Sales', credit_normal=True),
                   'direct_incomes': f(direct_inc), 'direct_income_items': _items(rows, nature='DirectIncome', credit_normal=True),
                   'closing_stock': f(closing_stock),
                   'gross_loss': f(-gross) if gross < 0 else 0.0,
                   'total': f(max(trading_dr, trading_cr))},
        },
        'pl': {
            'dr': {'indirect_expenses': f(indirect_exp), 'indirect_expense_items': _items(rows, nature='IndirectExpense'),
                   'gross_loss_bf': f(-gross) if gross < 0 else 0.0,
                   'nett_profit': f(net) if net > 0 else 0.0},
            'cr': {'gross_profit_bf': f(gross) if gross > 0 else 0.0,
                   'indirect_incomes': f(indirect_inc), 'indirect_income_items': _items(rows, nature='IndirectIncome', credit_normal=True),
                   'nett_loss': f(-net) if net < 0 else 0.0},
        },
        'summary': {'sales': f(sales), 'gross_profit': f(gross), 'nett_profit': f(net),
                    'total_expenses': f(direct_exp + indirect_exp)},
        '_raw': {'rows': rows, 'sales': sales, 'gross': gross, 'net': net, 'direct_exp': direct_exp,
                 'indirect_exp': indirect_exp, 'closing_stock': closing_stock},
    }


def balance_sheet(fy=None, _pl=None):
    pl = _pl or profit_loss(fy)
    raw = pl['_raw']
    rows, net, closing_stock = raw['rows'], raw['net'], raw['closing_stock']
    d_from, d_to, code = fy_range(fy)

    capital_items = _items(rows, group='Capital Account', credit_normal=True)
    capital_total = sum(Decimal(str(i['amount'])) for i in capital_items)
    loan_items = _items(rows, group='Loans (Liability)', credit_normal=True)
    cl_items = [i for i in _items(rows, group='Current Liabilities', credit_normal=True)]
    pl_open = _sum_group(rows, group='Profit & Loss A/c', credit_normal=True)

    fixed_items = _items(rows, nature='FixedAssets')
    invest_items = _items(rows, nature='Investments')
    ca_groups = OrderedDict()
    for gname in ('Loans & Advances (Asset)', 'Sundry Debtors', 'Cash-in-hand', 'Bank Accounts', 'Tax Receivables'):
        ca_groups[gname] = _items(rows, group=gname)
    ca_total = closing_stock + sum(Decimal(str(i['amount'])) for v in ca_groups.values() for i in v)
    loans_total = sum(Decimal(str(i['amount'])) for i in loan_items)
    cl_total = sum(Decimal(str(i['amount'])) for i in cl_items)
    fixed_total = sum(Decimal(str(i['amount'])) for i in fixed_items)
    invest_total = sum(Decimal(str(i['amount'])) for i in invest_items)

    liab_total = capital_total + loans_total + cl_total + pl_open + net
    asset_total = fixed_total + invest_total + ca_total
    diff = asset_total - liab_total  # positive => liabilities short (difference in opening balances)
    return {
        'financial_year': code, 'as_on': d_to.isoformat(),
        'liabilities': {
            'capital_account': {'total': f(capital_total), 'items': capital_items},
            'loans': {'total': f(loans_total), 'items': loan_items},
            'current_liabilities': {'total': f(cl_total), 'items': cl_items},
            'profit_loss': {'opening_balance': f(pl_open), 'current_period': f(net), 'total': f(pl_open + net)},
            'difference_in_books': f(diff) if diff > 0 else 0.0,
            'total': f(liab_total + (diff if diff > 0 else ZERO)),
        },
        'assets': {
            'fixed_assets': {'total': f(fixed_total), 'items': fixed_items},
            'investments': {'total': f(invest_total), 'items': invest_items},
            'current_assets': {'total': f(ca_total), 'closing_stock': f(closing_stock),
                               'groups': [{'name': k, 'total': f(sum(Decimal(str(i['amount'])) for i in v)), 'items': v}
                                          for k, v in ca_groups.items()]},
            'difference_in_books': f(-diff) if diff < 0 else 0.0,
            'total': f(asset_total + (-diff if diff < 0 else ZERO)),
        },
        'is_balanced': abs(diff) < Decimal('0.01'),
        '_raw': {'ca_total': ca_total, 'cl_total': cl_total, 'capital': capital_total, 'loans': loans_total,
                 'groups': ca_groups},
    }


def ratio_analysis(fy=None):
    pl = profit_loss(fy)
    bs = balance_sheet(fy, _pl=pl)
    raw, bsr = pl['_raw'], bs['_raw']
    d_from, d_to, code = fy_range(fy)
    days = (d_to - d_from).days + 1
    sales, net, gross = raw['sales'], raw['net'], raw['gross']
    ca, cl = bsr['ca_total'], bsr['cl_total']
    stock = raw['closing_stock']
    capital, loans = bsr['capital'], bsr['loans']
    wc = ca - cl
    rows = raw['rows']
    cash = _sum_group(rows, group='Cash-in-hand')
    bank = _sum_group(rows, group='Bank Accounts')
    bank_od = sum((-r['closing'] for r in rows if r['name'] == 'Bank OD A/c.'), ZERO)
    debtors = _sum_group(rows, group='Sundry Debtors')
    creditors = _sum_group(rows, group='Sundry Creditors', credit_normal=True)
    purchase = _sum_group(rows, nature='Purchase')
    op_cost = raw['direct_exp'] + raw['indirect_exp']

    def div(a, b, mult=1):
        return f(Decimal(a) / Decimal(b) * mult) if b else None

    return {
        'financial_year': code,
        'principal_groups': {
            'working_capital': f(wc), 'cash_in_hand': f(cash), 'bank_accounts': f(bank), 'bank_od': f(bank_od),
            'sundry_debtors': f(debtors), 'sundry_creditors': f(creditors), 'sales_accounts': f(sales),
            'purchase_accounts': f(purchase), 'stock_in_hand': f(stock), 'nett_profit': f(net),
        },
        'ratios': [
            {'key': 'current_ratio', 'label': 'Current Ratio', 'value': div(ca, cl), 'unit': ':1', 'formula': 'Current Assets : Current Liabilities'},
            {'key': 'quick_ratio', 'label': 'Quick Ratio', 'value': div(ca - stock, cl), 'unit': ':1', 'formula': '(Current Assets - Stock-in-hand) : Current Liabilities'},
            {'key': 'debt_equity', 'label': 'Debt / Equity Ratio', 'value': div(loans, capital + net), 'unit': ':1', 'formula': 'Loans (Liability) : (Capital Account + Nett Profit)'},
            {'key': 'gross_profit_pct', 'label': 'Gross Profit %', 'value': div(gross, sales, 100), 'unit': '%', 'formula': 'Gross Profit / Sales Accounts'},
            {'key': 'nett_profit_pct', 'label': 'Nett Profit %', 'value': div(net, sales, 100), 'unit': '%', 'formula': 'Nett Profit / Sales Accounts'},
            {'key': 'operating_cost_pct', 'label': 'Operating Cost %', 'value': div(op_cost, sales, 100), 'unit': '%', 'formula': '(Direct + Indirect Expenses) / Sales Accounts'},
            {'key': 'recv_turnover_days', 'label': 'Recv. Turnover in days', 'value': div(debtors * days, sales), 'unit': 'days', 'formula': 'Sundry Debtors x days in period / Sales Accounts'},
            {'key': 'roi_pct', 'label': 'Return on Investment %', 'value': div(net, capital + net, 100), 'unit': '%', 'formula': 'Nett Profit / (Capital Account + Nett Profit)'},
            {'key': 'wc_turnover', 'label': 'Working Capital Turnover', 'value': div(sales, wc), 'unit': 'x', 'formula': 'Sales Accounts / Working Capital'},
            {'key': 'row_pct', 'label': 'Return on Working Capital %', 'value': div(net, wc, 100), 'unit': '%', 'formula': 'Nett Profit / Working Capital'},
            {'key': 'inventory_turnover', 'label': 'Inventory Turnover', 'value': div(sales, stock), 'unit': 'x', 'formula': 'Sales Accounts / Closing Stock'},
        ],
    }


def strip_raw(d):
    d = dict(d)
    d.pop('_raw', None)
    return d
