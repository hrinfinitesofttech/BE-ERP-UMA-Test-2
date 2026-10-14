import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()
from erp_backend.urls import api_router

report = []
for prefix, viewset, basename in api_router.registry:
    qs = getattr(viewset, 'queryset', None)
    if qs is not None:
        model = qs.model
    elif hasattr(viewset, 'serializer_class') and hasattr(viewset.serializer_class, 'Meta') and hasattr(viewset.serializer_class.Meta, 'model'):
        model = viewset.serializer_class.Meta.model
    else:
        continue
    
    field_names = [f.name for f in model._meta.fields]
    has_created_at = 'created_at' in field_names
    curr_ordering = qs.query.order_by if qs is not None else ('custom',)
    
    if has_created_at:
        rec = ('-created_at', '-id') if 'id' in field_names else ('-created_at',)
    elif 'timestamp' in field_names:
        rec = ('-timestamp', '-id') if 'id' in field_names else ('-timestamp',)
    elif 'id' in field_names:
        rec = ('-id',)
    else:
        rec = ('-pk',)
    
    # Check if current ordering already puts newest first
    is_desc = any(str(o).startswith('-') for o in curr_ordering) if curr_ordering else False
    needs_fix = not is_desc or curr_ordering in [('code',), ('name',), ('id',), ('item_code',), ('asset_code',)]
    
    report.append({
        'prefix': prefix,
        'model': model.__name__,
        'curr_ordering': curr_ordering,
        'has_created_at': has_created_at,
        'rec': rec,
        'needs_fix': needs_fix
    })

needs_fix_list = [r for r in report if r['needs_fix']]
with open('audit_ordering_results.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total viewsets audited: {len(report)}\n")
    f.write(f"Viewsets needing ordering fix: {len(needs_fix_list)}\n")
    for r in needs_fix_list:
        f.write(f"/{r['prefix']:30} | Model: {r['model']:25} | Current: {str(r['curr_ordering']):25} -> Recommended: {str(r['rec'])}\n")
print("Done writing audit_ordering_results.txt")
