import json
from collections import defaultdict
from calendar import month_abbr
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta, datetime

from .models import Product, SalesTransaction, SalesItem, LoginHistory
from .forms import ProductForm, CashierForm, ProfileEditForm
from .utils import daily_sales, daily_quantity, top_sellers, moving_average_forecast, upload_image_to_imgbb
from .reports import sales_csv
from django.contrib.auth import get_user_model

User = get_user_model()

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
    
    # Active products count (matching POS view logic: non-archived, with stock, not expired)
    active_products_count = Product.objects.filter(
        is_archived=False,
        stock__gt=0
    ).exclude(
        expiration_date__lt=today
    ).count()
    
    # Top sellers (last 7 days)
    week_start = today - timedelta(days=7)
    top_products = top_sellers(start=week_start, end=today, limit=5)
    
    # Recent transactions (last 6)
    recent_sales = SalesTransaction.objects.select_related().prefetch_related('items').order_by('-created_at')[:6]
    recent_sales_data = []
    for sale in recent_sales:
        recent_sales_data.append({
            'id': sale.id,
            'created_at': sale.created_at.strftime('%H:%M'),
            'item_count': sale.items.count(),
            'total_amount': f"{sale.total_amount:.2f}"
        })
    
    # Last 7 months sales for chart (grouped by month)
    # Get sales data for the last 7 months
    start_date = today.replace(day=1) - timedelta(days=180)  # Approximately 7 months back
    monthly_data = defaultdict(lambda: {'revenue': 0.0, 'quantity': 0})
    
    # Get all sales items in the date range
    sales_items = SalesItem.objects.filter(
        sale__created_at__date__gte=start_date,
        sale__created_at__date__lte=today
    ).select_related('sale')
    
    # Group by month
    for item in sales_items:
        sale_date = item.sale.created_at.date()
        month_key = f"{sale_date.year}-{sale_date.month:02d}"
        monthly_data[month_key]['revenue'] += float(item.line_total)
        monthly_data[month_key]['quantity'] += int(item.qty)
    
    # Sort by date and get last 7 months
    sorted_months = sorted(monthly_data.keys())[-7:]
    
    last7_labels = []
    last7_values = []
    last7_quantities = []
    
    for month_key in sorted_months:
        year, month = month_key.split('-')
        month_name = month_abbr[int(month)]
        last7_labels.append(f"{month_name} {year}")
        last7_values.append(float(monthly_data[month_key]['revenue']))
        last7_quantities.append(int(monthly_data[month_key]['quantity']))
    
    return render(request, 'core/home.html', {
        'kpi_today_sales': f"{today_revenue:.2f}",
        'kpi_today_growth': f"{today_growth:+.1f}%",
        'kpi_today_orders': today_orders,
        'kpi_avg_ticket': f"{today_avg_ticket:.2f}",
        'kpi_low_stock': active_products_count,
        'top_products': top_products,
        'recent_sales': recent_sales_data,
        'last7_labels': json.dumps(last7_labels),
        'last7_values': json.dumps(last7_values),
        'last7_quantities': json.dumps(last7_quantities),
    })

# ---------------- Admin: Product CRUD -----------------
@login_required
@user_passes_test(is_admin)
def product_list(request):
    q = (request.GET.get('q') or '').strip()
    show_archived = request.GET.get('archived', '').lower() == 'true'
    
    # Show all products (including out of stock) for admin management
    # By default, exclude archived products unless explicitly requested
    if show_archived:
        qs = Product.objects.filter(is_archived=True).order_by('name')
    else:
        qs = Product.objects.filter(is_archived=False).order_by('name')
    
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(name__icontains=q) | Q(ingredients__icontains=q))
    return render(request, 'core/product_list.html', {'products': qs, 'q': q, 'show_archived': show_archived})

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
        # Check if product has sales history
        sales_items_count = SalesItem.objects.filter(product=product).count()
        
        if sales_items_count > 0:
            # Archive the product instead of deleting
            product.is_archived = True
            product.is_active = False  # Also deactivate it
            product.save()
            messages.success(
                request, 
                f'Product "{product.name}" has been archived. It is referenced in {sales_items_count} sales record(s). '
                'You can restore it from the archived products view.'
            )
        else:
            # No sales history, safe to delete
            product.delete()
            messages.success(request, 'Product deleted successfully.')
        
        return redirect('product_list')
    return render(request, 'core/product_delete.html', {'product': product})

@login_required
@user_passes_test(is_admin)
def product_restore(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.is_archived = False
        product.is_active = True  # Also restore active status when restoring
        product.save()
        messages.success(request, f'Product "{product.name}" has been restored successfully.')
        return redirect('product_list')
    return render(request, 'core/product_restore.html', {'product': product})

# ---------------- POS: Cashier & Admin -----------------
@login_required
def pos(request):
    from datetime import date
    today = date.today()
    
    # Show all non-archived products with stock that are not expired
    # Include products with no expiration date set
    # Note: We check is_active in add_to_cart, but show all non-archived products here for flexibility
    products = Product.objects.filter(
        is_archived=False,
        stock__gt=0
    ).exclude(
        expiration_date__lt=today
    ).order_by('name')
    
    cart = request.session.get('cart', {})
    return render(request, 'core/pos.html', {'products': products, 'cart': cart})

@login_required
def add_to_cart(request, product_id):
    from datetime import date
    # Match POS view logic: non-archived products (is_active check removed to match POS display)
    product = get_object_or_404(Product, pk=product_id, is_archived=False)
    
    # Check if product is expired
    if product.is_expired():
        messages.error(request, f'❌ Cannot add "{product.name}" - Product has expired!')
        return redirect('pos')
    
    # Check if product is in stock
    if product.stock <= 0:
        messages.error(request, f'❌ Cannot add "{product.name}" - Out of stock!')
        return redirect('pos')
    
    cart = request.session.get('cart', {})
    qty = int(request.POST.get('qty', 1))
    if qty <= 0: qty = 1
    
    # Check if adding this quantity exceeds available stock
    current_cart_qty = cart.get(str(product_id), {}).get('qty', 0)
    if current_cart_qty + qty > product.stock:
        messages.warning(request, f'⚠️ Only {product.stock} units available for "{product.name}"')
        qty = max(1, product.stock - current_cart_qty)
    
    item = cart.get(str(product_id), {'name': product.name, 'unit_price': float(product.price), 'qty': 0})
    item['qty'] += qty
    cart[str(product_id)] = item
    request.session['cart'] = cart
    request.session.modified = True  # Ensure session is saved
    messages.success(request, f'✅ Added {qty}x {product.name} to cart')
    return redirect('pos')

@login_required
def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    print(f"Before update - Product {product_id}, Cart: {cart}")
    
    if str(product_id) in cart:
        # Check if product still exists and is valid
        try:
            # Match POS view logic: non-archived products (is_active check removed to match POS display)
            product = Product.objects.get(pk=product_id, is_archived=False)
            if product.is_expired():
                cart.pop(str(product_id))
                messages.error(request, f'❌ Removed "{product.name}" from cart - Product has expired!')
                request.session['cart'] = cart
                request.session.modified = True
                return redirect('pos')
            elif product.stock <= 0:
                cart.pop(str(product_id))
                messages.error(request, f'❌ Removed "{product.name}" from cart - Out of stock!')
                request.session['cart'] = cart
                request.session.modified = True
                return redirect('pos')
        except Product.DoesNotExist:
            cart.pop(str(product_id))
            messages.warning(request, '⚠️ Product no longer available')
            request.session['cart'] = cart
            request.session.modified = True
            return redirect('pos')
        
        qty = int(request.POST.get('qty', 1))
        print(f"Updating product {product_id} to quantity {qty}")
        
        if qty <= 0:
            cart.pop(str(product_id))
            print(f"Removed product {product_id} from cart")
        else:
            # Ensure quantity doesn't exceed stock
            if qty > product.stock:
                qty = product.stock
                messages.warning(request, f'⚠️ Limited to {product.stock} units for "{product.name}"')
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
    from datetime import date
    cart = request.session.get('cart', {})
    if request.method == 'POST' and cart:
        # Validate all products in cart before checkout
        invalid_products = []
        for pid, item in cart.items():
            try:
                product = Product.objects.get(pk=int(pid))
                if product.is_expired():
                    invalid_products.append(product.name)
                elif not product.is_active:
                    invalid_products.append(product.name)
                elif product.stock < item['qty']:
                    invalid_products.append(f"{product.name} (insufficient stock)")
            except Product.DoesNotExist:
                invalid_products.append(f"Product ID {pid}")
        
        if invalid_products:
            messages.error(request, f'❌ Cannot checkout - Some products are expired, inactive, or out of stock: {", ".join(invalid_products)}')
            return redirect('pos')
        
        # Debug: Print cart data before processing
        print(f"Checkout cart data: {cart}")
        discount = float(request.POST.get('discount', 0) or 0)
        payment_method = request.POST.get('payment_method', 'CASH')
        cash_received = float(request.POST.get('cash_received', 0) or 0)
        total = 0.0
        for pid, item in cart.items():
            total += item['unit_price'] * item['qty']
        total_after_discount = max(0.0, total - discount)
        change = max(0.0, cash_received - total_after_discount)

        sale = SalesTransaction.objects.create(
            cashier=request.user,
            total_amount=total_after_discount,
            discount=discount,
            payment_method=payment_method
        )
        
        # Store cash_received and change in session for receipt
        request.session[f'sale_{sale.id}_cash_received'] = cash_received
        request.session[f'sale_{sale.id}_change'] = change
        for pid, item in cart.items():
            # Debug: Print each item being saved
            print(f"Creating SalesItem: Product {pid}, Qty: {item['qty']}, Unit Price: {item['unit_price']}, Line Total: {item['unit_price'] * item['qty']}")
            product = Product.objects.get(pk=int(pid))
            SalesItem.objects.create(
                sale=sale,
                product=product,
                qty=item['qty'],
                unit_price=item['unit_price'],
                line_total=item['unit_price'] * item['qty']
            )
            # Update stock
            product.stock -= item['qty']
            product.save()
        request.session['cart'] = {}
        messages.success(request, f'Sale #{sale.id} completed.')
        return redirect('receipt', sale_id=sale.id)
    return redirect('pos')

@login_required
def receipt(request, sale_id):
    sale = get_object_or_404(SalesTransaction, pk=sale_id)
    # Get cash_received and change from session
    cash_received = request.session.get(f'sale_{sale_id}_cash_received', 0)
    change = request.session.get(f'sale_{sale_id}_change', 0)
    return render(request, 'core/receipt.html', {
        'sale': sale,
        'cash_received': cash_received,
        'change': change
    })

# ---------------- Admin: Forecast & Analytics -----------
@login_required
@user_passes_test(is_admin)
def forecast(request):
    today = date.today()
    start = today - timedelta(days=60)
    history = daily_sales(start=start, end=today)
    quantity_history = daily_quantity(start=start, end=today)
    forecast_points = moving_average_forecast(history, horizon=7, window=7)
    top = top_sellers(start=start, end=today, limit=5)
    # Sales performance for last 7 days
    start_7days = today - timedelta(days=7)
    top_7days = top_sellers(start=start_7days, end=today, limit=10)
    return render(request, 'core/forecast.html', {
        'history': history,
        'quantity_history': quantity_history,
        'forecast_points': forecast_points,
        'top': top,
        'top_7days': top_7days,
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

# ---------------- Admin: Cashier Management -----------------
@login_required
@user_passes_test(is_admin)
def cashier_list(request):
    """List all cashiers (non-staff users)"""
    cashiers = User.objects.filter(is_staff=False).order_by('-date_joined')
    
    # Get login history count for each cashier
    cashiers_with_stats = []
    for cashier in cashiers:
        login_count = LoginHistory.objects.filter(user=cashier).count()
        last_login = LoginHistory.objects.filter(user=cashier).first()
        cashiers_with_stats.append({
            'user': cashier,
            'login_count': login_count,
            'last_login': last_login.login_time if last_login else None,
        })
    
    return render(request, 'core/cashier_list.html', {
        'cashiers': cashiers_with_stats
    })

@login_required
@user_passes_test(is_admin)
def cashier_create(request):
    """Create a new cashier account"""
    if request.method == 'POST':
        form = CashierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cashier "{form.cleaned_data["username"]}" created successfully.')
            return redirect('cashier_list')
    else:
        form = CashierForm()
    return render(request, 'core/cashier_form.html', {'form': form})

@login_required
def profile(request):
    """Display and edit the current user's profile information"""
    from .models import UserProfile
    
    user = request.user
    
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                user_profile.profile_picture = request.FILES['profile_picture']
                user_profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=user)
    
    return render(request, 'core/profile.html', {
        'user': user,
        'form': form,
        'user_profile': user_profile,
    })

@login_required
@user_passes_test(is_admin)
def cashier_login_history(request, user_id):
    """View login history for a specific cashier"""
    cashier = get_object_or_404(User, pk=user_id, is_staff=False)
    login_history = LoginHistory.objects.filter(user=cashier).order_by('-login_time')[:100]  # Last 100 logins
    
    return render(request, 'core/cashier_login_history.html', {
        'cashier': cashier,
        'login_history': login_history,
    })


@login_required
@user_passes_test(is_admin)
def upload_image(request):
    """Handle image upload via ImgBB API"""
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        
        # Upload to ImgBB
        image_url, error = upload_image_to_imgbb(image_file)
        
        if error:
            return JsonResponse({'success': False, 'error': error}, status=400)
        
        return JsonResponse({'success': True, 'image_url': image_url})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
