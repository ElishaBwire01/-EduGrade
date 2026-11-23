import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')
import django
django.setup()

from django.db import connection
from django.contrib.auth.models import User

print("=" * 60)
print("  HEALTH CHECK")
print("=" * 60)

# Check database
print("\n📊 Database:")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("  ✅ Database connected")
except:
    print("  ❌ Database connection failed")

# Check grading tables
print("\n📊 Grading Tables:")
tables_to_check = [
    "assessment_schemes",
    "kcse_grade_rules", 
    "performance_levels"
]

with connection.cursor() as cursor:
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"  ✅ {table} exists")
            else:
                print(f"  ❌ {table} missing")
        except:
            print(f"  ⚠️ Could not check {table}")

# Check grading data
print("\n📊 Grading Data:")
from grading.models import AssessmentScheme, KCSEGradeRule, PerformanceLevel
print(f"  📋 Assessment Schemes: {AssessmentScheme.objects.count()}")
print(f"  📋 KCSE Grade Rules: {KCSEGradeRule.objects.count()}")
print(f"  📋 CBC Performance Levels: {PerformanceLevel.objects.count()}")

# Check user
print("\n👤 User:")
users = User.objects.filter(is_superuser=True)
if users.exists():
    for user in users:
        print(f"  ✅ Admin: {user.username}")
else:
    print("  ⚠️ No admin user found")

print("\n" + "=" * 60)
print("  ✅ HEALTH CHECK COMPLETE")
print("=" * 60)
