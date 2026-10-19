"""
Python Django Version Diff Engine for UMA ERP
RFC 6902 / Deep Object & Tabular Diff Engine
Computes differences between ERP document snapshots across Macro, Meso (Line Items), and Micro (Fields) levels.
"""

from typing import Dict, Any, List, Optional


COMMON_FIELD_MAPPINGS = {
    'grandTotal': {'label': 'Grand Total', 'type': 'CURRENCY', 'category': 'financial'},
    'grand_total': {'label': 'Grand Total', 'type': 'CURRENCY', 'category': 'financial'},
    'subTotal': {'label': 'Sub Total', 'type': 'CURRENCY', 'category': 'financial'},
    'sub_total': {'label': 'Sub Total', 'type': 'CURRENCY', 'category': 'financial'},
    'taxAmount': {'label': 'Tax Amount', 'type': 'CURRENCY', 'category': 'financial'},
    'tax_amount': {'label': 'Tax Amount', 'type': 'CURRENCY', 'category': 'financial'},
    'discountAmount': {'label': 'Discount Amount', 'type': 'CURRENCY', 'category': 'financial'},
    'discount_amount': {'label': 'Discount Amount', 'type': 'CURRENCY', 'category': 'financial'},
    'poAmount': {'label': 'PO Amount', 'type': 'CURRENCY', 'category': 'financial'},
    'po_amount': {'label': 'PO Amount', 'type': 'CURRENCY', 'category': 'financial'},
    'deliveryTime': {'label': 'Delivery Schedule', 'type': 'STRING', 'category': 'schedule'},
    'delivery_time': {'label': 'Delivery Schedule', 'type': 'STRING', 'category': 'schedule'},
    'deliveryDate': {'label': 'Delivery Date', 'type': 'DATE', 'category': 'schedule'},
    'delivery_date': {'label': 'Delivery Date', 'type': 'DATE', 'category': 'schedule'},
    'paymentTerms': {'label': 'Payment Terms', 'type': 'STRING', 'category': 'terms'},
    'payment_terms': {'label': 'Payment Terms', 'type': 'STRING', 'category': 'terms'},
    'warranty': {'label': 'Warranty Period', 'type': 'STRING', 'category': 'terms'},
    'status': {'label': 'Document Status', 'type': 'STATUS', 'category': 'general'},
    'technicalSpecs': {'label': 'Technical Specs', 'type': 'STRING', 'category': 'specifications'},
    'technical_specs': {'label': 'Technical Specs', 'type': 'STRING', 'category': 'specifications'},
    'scopeOfSupply': {'label': 'Scope of Supply', 'type': 'STRING', 'category': 'specifications'},
    'scope_of_supply': {'label': 'Scope of Supply', 'type': 'STRING', 'category': 'specifications'},
    'termsAndConditions': {'label': 'Terms & Conditions', 'type': 'STRING', 'category': 'terms'},
    'terms_and_conditions': {'label': 'Terms & Conditions', 'type': 'STRING', 'category': 'terms'},
    'remarks': {'label': 'Remarks / Notes', 'type': 'STRING', 'category': 'general'},
}

LINE_ITEM_FIELD_MAPPINGS = {
    'productName': 'Item / Product Name',
    'product_name': 'Item / Product Name',
    'description': 'Description',
    'quantity': 'Quantity',
    'unit': 'Unit (UOM)',
    'rate': 'Unit Rate',
    'amount': 'Total Amount',
    'taxPercent': 'GST / Tax %',
    'tax_percent': 'GST / Tax %',
    'discountPercent': 'Discount %',
    'discount_percent': 'Discount %',
}


def is_values_different(a: Any, b: Any) -> bool:
    if a is None and b is None:
        return False
    if a == '' and (b is None or b == ''):
        return False
    if b == '' and (a is None or a == ''):
        return False

    # Numeric equivalence (e.g. 10 vs 10.0 or "10")
    try:
        if isinstance(a, (int, float)) or isinstance(b, (int, float)):
            return float(a or 0) != float(b or 0)
    except (ValueError, TypeError):
        pass

    if isinstance(a, str) and isinstance(b, str):
        return a.strip() != b.strip()

    return a != b


def compute_version_diff(
    version_a_meta: Dict[str, Any],
    version_a_data: Dict[str, Any],
    version_b_meta: Dict[str, Any],
    version_b_data: Dict[str, Any],
    items_key: str = 'items',
    identity_key: str = 'id'
) -> Dict[str, Any]:
    """
    Computes differences between two document snapshots across Macro, Line Items, and Fields.
    """
    data_a = version_a_data or {}
    data_b = version_b_data or {}

    # 1. Micro-Level Field Differences
    field_diffs = []
    seen_keys = set()

    for key, mapping in COMMON_FIELD_MAPPINGS.items():
        if key == items_key or key in seen_keys:
            continue

        val_a = data_a.get(key)
        val_b = data_b.get(key)

        if is_values_different(val_a, val_b):
            field_diffs.append({
                'path': key,
                'fieldLabel': mapping['label'],
                'category': mapping['category'],
                'oldValue': val_a,
                'newValue': val_b,
                'type': mapping['type'],
            })
            seen_keys.add(key)

    # 2. Meso-Level Line Item Differences
    list_a = data_a.get(items_key) or []
    list_b = data_b.get(items_key) or []
    if not isinstance(list_a, list):
        list_a = []
    if not isinstance(list_b, list):
        list_b = []

    line_item_diffs, item_summary = compare_line_items(list_a, list_b, identity_key)

    # 3. Macro-Level Financial & Status Summary
    amount_a = float(data_a.get('grandTotal') or data_a.get('grand_total') or data_a.get('poAmount') or data_a.get('po_amount') or 0)
    amount_b = float(data_b.get('grandTotal') or data_b.get('grand_total') or data_b.get('poAmount') or data_b.get('po_amount') or 0)
    diff_amount = amount_b - amount_a
    pct_change = (diff_amount / amount_a * 100.0) if amount_a > 0 else 0.0

    status_a = str(data_a.get('status', 'unknown'))
    status_b = str(data_b.get('status', 'unknown'))

    return {
        'sourceVersion': version_a_meta,
        'targetVersion': version_b_meta,
        'macroDiff': {
            'statusChanged': status_a != status_b,
            'oldStatus': status_a,
            'newStatus': status_b,
            'financialDifference': {
                'oldAmount': amount_a,
                'newAmount': amount_b,
                'diffAmount': diff_amount,
                'percentageChange': round(pct_change, 2),
            }
        },
        'fieldDiffs': field_diffs,
        'lineItemDiffs': [
            {
                'tableName': items_key,
                'tableLabel': 'Line Items & Bill of Materials',
                'items': line_item_diffs,
                'summary': item_summary,
            }
        ]
    }


def compare_line_items(list_a: List[Dict[str, Any]], list_b: List[Dict[str, Any]], identity_key: str):
    items = []
    map_a = {}
    map_b = {}

    def get_key(item: Dict[str, Any], idx: int) -> str:
        return str(item.get(identity_key) or item.get('productName') or item.get('product_name') or f"item-{idx}")

    for idx, item in enumerate(list_a):
        map_a[get_key(item, idx)] = item

    for idx, item in enumerate(list_b):
        map_b[get_key(item, idx)] = item

    added = 0
    removed = 0
    modified = 0
    unchanged = 0

    # Process items in B
    for idx, item_b in enumerate(list_b):
        key = get_key(item_b, idx)
        item_a = map_a.get(key)
        name = item_b.get('productName') or item_b.get('product_name') or item_b.get('itemName') or key

        if not item_a:
            added += 1
            items.append({
                'id': key,
                'keyIdentifier': name,
                'diffType': 'ADDED',
                'newItem': item_b,
            })
        else:
            field_changes = []
            for f_key, f_label in LINE_ITEM_FIELD_MAPPINGS.items():
                if is_values_different(item_a.get(f_key), item_b.get(f_key)):
                    field_changes.append({
                        'path': f"items[{key}].{f_key}",
                        'fieldLabel': f_label,
                        'oldValue': item_a.get(f_key),
                        'newValue': item_b.get(f_key),
                    })

            if field_changes:
                modified += 1
                items.append({
                    'id': key,
                    'keyIdentifier': name,
                    'diffType': 'MODIFIED',
                    'oldItem': item_a,
                    'newItem': item_b,
                    'fieldChanges': field_changes,
                })
            else:
                unchanged += 1
                items.append({
                    'id': key,
                    'keyIdentifier': name,
                    'diffType': 'UNCHANGED',
                    'oldItem': item_a,
                    'newItem': item_b,
                })

    # Process removed items
    for idx, item_a in enumerate(list_a):
        key = get_key(item_a, idx)
        if key not in map_b:
            removed += 1
            name = item_a.get('productName') or item_a.get('product_name') or item_a.get('itemName') or key
            items.append({
                'id': key,
                'keyIdentifier': name,
                'diffType': 'REMOVED',
                'oldItem': item_a,
            })

    return items, {'added': added, 'removed': removed, 'modified': modified, 'unchanged': unchanged}
