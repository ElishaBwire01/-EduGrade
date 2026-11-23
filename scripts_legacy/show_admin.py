import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')
import django
django.setup()
from django.contrib.auth.models import User

print("=" * 50)
print("EDUGRADE - ADMIN USER INFORMATION")
print("=" * 50)

# Get all superusers
admins = User.objects.filter(is_superuser=True)

if admins.exists():
    print(f"\n✅ Found {admins.count()} admin user(s):\n")
    for admin in admins:
        print(f"   Username: {admin.username}")
        print(f"   Full Name: {admin.get_full_name() or 'Not set'}")
        print(f"   Email: {admin.email or 'Not set'}")
        print(f"   Staff: {admin.is_staff}")
        print(f"   Superuser: {admin.is_superuser}")
        print(f"   Active: {admin.is_active}")
        print(f"   Last Login: {admin.last_login or 'Never'}")
        print(f"   Date Joined: {admin.date_joined}")
        print("-" * 30)
else:
    print("\n❌ No admin users found!")
    print("   Run: python manage.py createsuperuser")
    print("   to create one.")

print("\n" + "=" * 50)
print("Tip: You can login with any of these usernames")
print("at: http://127.0.0.1:8000/auth/login/")
print("=" * 50)
