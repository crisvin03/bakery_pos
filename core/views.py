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
    return render(request, 'core/home.html')

# ---------------- Admin: Product CRUD -----------------
@login_required
@user_passes_test(is_admin)
def product_list(request):
    q = (request.GET.get('q') or '').strip()
    qs = Product.objects.all().order_by('name')
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
