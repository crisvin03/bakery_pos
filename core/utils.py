from django.db.models import Sum, F
from .models import SalesItem
from datetime import date, timedelta

def daily_sales(start=None, end=None):
    # returns list of dicts: [{'date': date, 'revenue': float}]
    qs = SalesItem.objects.all()
    if start:
        qs = qs.filter(sale__created_at__date__gte=start)
    if end:
        qs = qs.filter(sale__created_at__date__lte=end)
    agg = (qs.values('sale__created_at__date')
             .annotate(revenue=Sum(F('line_total')))
             .order_by('sale__created_at__date'))
    return [{'date': r['sale__created_at__date'], 'revenue': float(r['revenue'] or 0)} for r in agg]

def top_sellers(start=None, end=None, limit=5):
    qs = SalesItem.objects.all()
    if start:
        qs = qs.filter(sale__created_at__date__gte=start)
    if end:
        qs = qs.filter(sale__created_at__date__lte=end)
    agg = (qs.values('product__name')
             .annotate(qty=Sum('qty'), revenue=Sum('line_total'))
             .order_by('-qty')[:limit])
    return [{'product': r['product__name'], 'qty': int(r['qty'] or 0), 'revenue': float(r['revenue'] or 0)} for r in agg]

def moving_average_forecast(history, horizon=7, window=7):
    # history: list of {'date': date, 'revenue': float}
    if not history:
        return [{'day': i+1, 'forecast': 0.0} for i in range(horizon)]
    # simple avg of last window days
    last_vals = [h['revenue'] for h in history[-window:]]
    avg = sum(last_vals) / max(1, len(last_vals))
    return [{'day': i+1, 'forecast': round(avg, 2)} for i in range(horizon)]
