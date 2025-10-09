# alvarez_bakery/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # auth
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),

    # home
    path('', core_views.home, name='home'),

    # Products (Admin only)
    path('products/', core_views.product_list, name='product_list'),
    path('products/new/', core_views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', core_views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', core_views.product_delete, name='product_delete'),

    # POS (Cashier & Admin)
    path('pos/', core_views.pos, name='pos'),
    path('pos/add-to-cart/<int:product_id>/', core_views.add_to_cart, name='add_to_cart'),
    path('pos/update-cart/<int:product_id>/', core_views.update_cart, name='update_cart'),
    path('pos/checkout/', core_views.checkout, name='checkout'),
    path('receipt/<int:sale_id>/', core_views.receipt, name='receipt'),

    # Forecast & Analytics (Admin only)
    path('forecast/', core_views.forecast, name='forecast'),

    # Reports (Admin only)
    path('reports/', core_views.reports, name='reports'),
    path('reports/export/', core_views.reports_export_csv, name='reports_export_csv'),
]

# serve uploaded media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
