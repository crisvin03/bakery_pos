import csv
from io import StringIO
from django.db.models import Sum, F
from .models import SalesItem

def sales_csv(start, end, granularity='daily'):
    # Build CSV string of date,revenue,qty
    qs = SalesItem.objects.filter(sale__created_at__date__gte=start,
                                  sale__created_at__date__lte=end)
    agg = (qs.values('sale__created_at__date')
             .annotate(revenue=Sum(F('line_total')), qty=Sum('qty'))
             .order_by('sale__created_at__date'))
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Date','Revenue','Quantity'])
    for r in agg:
        writer.writerow([r['sale__created_at__date'], float(r['revenue'] or 0), int(r['qty'] or 0)])
    return buf.getvalue()
