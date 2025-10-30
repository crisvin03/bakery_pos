from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta, datetime

from .models import Product, SalesTransaction, SalesItem
from .forms import ProductForm
from .utils import daily_sales, top_sellers, moving_average_forecast
from .reports import sales_csv

def is_admin(user):
    return user.is_staff  # treat staff=True as Admin role

@login_required
def home(request):
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Today's sales data
    today_sales = SalesTransaction.objects.filter(created_at__date=today)
    today_revenue = sum(sale.total_amount for sale in today_sales)
    today_orders = today_sales.count()
    today_avg_ticket = today_revenue / today_orders if today_orders > 0 else 0
    
    # Yesterday's sales for comparison
    yesterday_sales = SalesTransaction.objects.filter(created_at__date=yesterday)
    yesterday_revenue = sum(sale.total_amount for sale in yesterday_sales)
    today_growth = ((today_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0
    
    # Low stock products (assuming we have a stock field or can calculate from sales)
    low_stock_count = Product.objects.filter(is_active=True).count()  # Placeholder - would need stock tracking
    
    # Top sellers (last 7 days)
    week_start = today - timedelta(days=7)
    top_products = top_sellers(start=week_start, end=today, limit=5)
    
    # Recent transactions (last 7)
    recent_sales = SalesTransaction.objects.select_related().prefetch_related('items').order_by('-created_at')[:7]
    recent_sales_data = []
    for sale in recent_sales:
        recent_sales_data.append({
            'id': sale.id,
            'created_at': sale.created_at.strftime('%H:%M'),
            'item_count': sale.items.count(),
            'total_amount': f"{sale.total_amount:.2f}"
        })
    
    # Last 7 days sales for chart
    last7_labels = []
    last7_values = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        day_sales = SalesTransaction.objects.filter(created_at__date=day)
        day_revenue = sum(sale.total_amount for sale in day_sales)
        last7_labels.append(day.strftime('%a'))
        last7_values.append(day_revenue)
    
    return render(request, 'core/home.html', {
        'kpi_today_sales': f"{today_revenue:.2f}",
        'kpi_today_growth': f"{today_growth:+.1f}%",
        'kpi_today_orders': today_orders,
        'kpi_avg_ticket': f"{today_avg_ticket:.2f}",
        'kpi_low_stock': low_stock_count,
        'top_products': top_products,
        'recent_sales': recent_sales_data,
        'last7_labels': last7_labels,
        'last7_values': last7_values,
    })

# ---------------- Admin: Product CRUD -----------------
@login_required
@user_passes_test(is_admin)
def product_list(request):
    q = (request.GET.get('q') or '').strip()
    qs = Product.objects.filter(stock__gt=0).order_by('name')
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(name__icontains=q) | Q(ingredients__icontains=q))
    return render(request, 'core/product_list.html', {'products': qs, 'q': q})

@login_required
@user_passes_test(is_admin)
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  # <-- IMPORTANT
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created.')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'core/product_form.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)  # <-- IMPORTANT
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated.')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'core/product_form.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('product_list')
    return render(request, 'core/product_delete.html', {'product': product})

# ---------------- POS: Cashier & Admin -----------------
@login_required
def pos(request):
    products = Product.objects.filter(is_active=True).order_by('name')
    cart = request.session.get('cart', {})
    print(f"POS view - Cart data: {cart}")
    return render(request, 'core/pos.html', {'products': products, 'cart': cart})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = request.session.get('cart', {})
    qty = int(request.POST.get('qty', 1))
    if qty <= 0: qty = 1
    item = cart.get(str(product_id), {'name': product.name, 'unit_price': float(product.price), 'qty': 0})
    item['qty'] += qty
    cart[str(product_id)] = item
    request.session['cart'] = cart
    request.session.modified = True  # Ensure session is saved
    return redirect('pos')

@login_required
def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    print(f"Before update - Product {product_id}, Cart: {cart}")
    
    if str(product_id) in cart:
        qty = int(request.POST.get('qty', 1))
        print(f"Updating product {product_id} to quantity {qty}")
        
        if qty <= 0:
            cart.pop(str(product_id))
            print(f"Removed product {product_id} from cart")
        else:
            cart[str(product_id)]['qty'] = qty
            print(f"Updated product {product_id} quantity to {qty}")
        
        request.session['cart'] = cart
        request.session.modified = True  # Ensure session is saved
        print(f"After update - Cart: {cart}")
    else:
        print(f"Product {product_id} not found in cart")
    
    return redirect('pos')

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if request.method == 'POST' and cart:
        # Debug: Print cart data before processing
        print(f"Checkout cart data: {cart}")
        discount = float(request.POST.get('discount', 0) or 0)
        payment_method = request.POST.get('payment_method', 'CASH')
        total = 0.0
        for pid, item in cart.items():
            total += item['unit_price'] * item['qty']
        total_after_discount = max(0.0, total - discount)

        sale = SalesTransaction.objects.create(
            cashier=request.user,
            total_amount=total_after_discount,
            discount=discount,
            payment_method=payment_method
        )
        for pid, item in cart.items():
            # Debug: Print each item being saved
            print(f"Creating SalesItem: Product {pid}, Qty: {item['qty']}, Unit Price: {item['unit_price']}, Line Total: {item['unit_price'] * item['qty']}")
            SalesItem.objects.create(
                sale=sale,
                product=Product.objects.get(pk=int(pid)),
                qty=item['qty'],
                unit_price=item['unit_price'],
                line_total=item['unit_price'] * item['qty']
            )
        request.session['cart'] = {}
        messages.success(request, f'Sale #{sale.id} completed.')
        return redirect('receipt', sale_id=sale.id)
    return redirect('pos')

@login_required
def receipt(request, sale_id):
    sale = get_object_or_404(SalesTransaction, pk=sale_id)
    return render(request, 'core/receipt.html', {'sale': sale})

# ---------------- Admin: Forecast & Analytics -----------
@login_required
@user_passes_test(is_admin)
def forecast(request):
    today = date.today()
    start = today - timedelta(days=60)
    history = daily_sales(start=start, end=today)
    forecast_points = moving_average_forecast(history, horizon=7, window=7)
    top = top_sellers(start=start, end=today, limit=5)
    return render(request, 'core/forecast.html', {
        'history': history,
        'forecast_points': forecast_points,
        'top': top,
    })

# ---------------- Admin: Reports ------------------------
@login_required
@user_passes_test(is_admin)
def reports(request):
    # Defaults: last 30 days
    today = date.today()
    start_str = request.GET.get('start', (today - timedelta(days=30)).isoformat())
    end_str = request.GET.get('end', today.isoformat())
    start = datetime.fromisoformat(start_str).date()
    end = datetime.fromisoformat(end_str).date()
    history = daily_sales(start=start, end=end)
    return render(request, 'core/reports.html', {'history': history, 'start': start_str, 'end': end_str})

@login_required
@user_passes_test(is_admin)
def reports_export_csv(request):
    today = date.today()
    start_str = request.GET.get('start', (today - timedelta(days=30)).isoformat())
    end_str = request.GET.get('end', today.isoformat())
    start = datetime.fromisoformat(start_str).date()
    end = datetime.fromisoformat(end_str).date()
    csv_data = sales_csv(start, end, 'daily')
    resp = HttpResponse(csv_data, content_type='text/csv')
    resp['Content-Disposition'] = f'attachment; filename="sales_{start}_{end}.csv"'
    return resp
