from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth import get_user_model
User = get_user_model()
from core.access import send_notification, send_approval_reminder


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Send notifications on first login."""
    is_first_login = user.last_login is None or user.date_joined == user.last_login
    
    if is_first_login:
        send_notification(
            user,
            title="Welcome to EduGrade!",
            message=(
                f"Welcome, {user.get_full_name() or user.username}! Your account has been created.\n\n"
                f"Please complete your profile and request admin approval to activate your account.\n\n"
                f"Click below to request approval."
            ),
            notification_type="SYSTEM",
            url="/teachers/request-approval/",
        )
        send_approval_reminder(user)

