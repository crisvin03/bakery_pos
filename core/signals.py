from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import LoginHistory
from django.utils import timezone

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Record login history when a user logs in"""
    ip_address = None
    user_agent = ''
    
    if request:
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
    
    LoginHistory.objects.create(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Record logout time when a user logs out"""
    if user:
        # Update the most recent login record for this user that doesn't have a logout time
        latest_login = LoginHistory.objects.filter(
            user=user,
            logout_time__isnull=True
        ).order_by('-login_time').first()
        
        if latest_login:
            latest_login.logout_time = timezone.now()
            latest_login.save()

