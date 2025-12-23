import os
import requests
import base64
from django.db.models import Sum, F
from .models import SalesItem
from datetime import date, timedelta
from django.conf import settings

def daily_sales(start=None, end=None):
    # returns list of dicts: [{'date': date, 'revenue': float}]
    qs = SalesItem.objects.all()
    if start:
        qs = qs.filter(sale__created_at__date__gte=start)
    if end:
        qs = qs.filter(sale__created_at__date__lte=end)
    agg = (qs.values('sale__created_at__date')
             .annotate(revenue=Sum(F('line_total')))
             .order_by('-sale__created_at__date'))
    return [{'date': r['sale__created_at__date'], 'revenue': float(r['revenue'] or 0)} for r in agg]

def daily_quantity(start=None, end=None):
    # returns list of dicts: [{'date': date, 'quantity': int}]
    qs = SalesItem.objects.all()
    if start:
        qs = qs.filter(sale__created_at__date__gte=start)
    if end:
        qs = qs.filter(sale__created_at__date__lte=end)
    agg = (qs.values('sale__created_at__date')
             .annotate(quantity=Sum('qty'))
             .order_by('-sale__created_at__date'))
    return [{'date': r['sale__created_at__date'], 'quantity': int(r['quantity'] or 0)} for r in agg]

def top_sellers(start=None, end=None, limit=5):
    qs = SalesItem.objects.all()
    if start:
        qs = qs.filter(sale__created_at__date__gte=start)
    if end:
        qs = qs.filter(sale__created_at__date__lte=end)
    agg = (qs.values('product__name')
             .annotate(qty=Sum('qty'), revenue=Sum('line_total'))
             .order_by('-qty')[:limit])
    result = []
    for r in agg:
        qty = int(r['qty'] or 0)
        revenue = float(r['revenue'] or 0)
        avg_price = revenue / qty if qty > 0 else 0.0
        result.append({
            'product': r['product__name'],
            'qty': qty,
            'revenue': revenue,
            'avg_price': round(avg_price, 2)
        })
    return result

def moving_average_forecast(history, horizon=7, window=7):
    # history: list of {'date': date, 'revenue': float}
    if not history:
        return [{'day': i+1, 'forecast': 0.0} for i in range(horizon)]
    # simple avg of last window days
    last_vals = [h['revenue'] for h in history[-window:]]
    avg = sum(last_vals) / max(1, len(last_vals))
    return [{'day': i+1, 'forecast': round(avg, 2)} for i in range(horizon)]


def upload_image_to_imgbb(image_file):
    """
    Upload an image file to ImgBB and return the URL
    """
    api_key = os.getenv('IMGBB_API_KEY')
    
    if not api_key or api_key == 'your_imgbb_api_key_here':
        return None, "ImgBB API key not configured"
    
    try:
        # Read image file and encode to base64
        image_data = image_file.read()
        encoded_image = base64.b64encode(image_data)
        
        # Prepare API request
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": api_key,
            "image": encoded_image,
            "expiration": 0,  # No expiration
        }
        
        # Upload to ImgBB
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('success'):
            return data['data']['url'], None
        else:
            return None, data.get('error', {}).get('message', 'Upload failed')
            
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Upload error: {str(e)}"
