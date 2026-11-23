import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')
import django
django.setup()

from grading.models import AssessmentScheme, KCSEGradeRule, KCSEOverallCalculation, PerformanceLevel
from school.models import Curriculum, AcademicYear
from datetime import date

print("=" * 60)
print("  CREATING GRADING DATA")
print("=" * 60)

# Academic Year
year, created = AcademicYear.objects.get_or_create(
    year=2026,
    defaults={
        "name": "Academic Year 2026",
        "start_date": date(2026, 1, 15),
        "end_date": date(2026, 12, 15),
        "is_current": True
    }
)
if created:
    print(f"✅ Academic Year: {year}")
else:
    print(f"ℹ️ Academic Year: {year} (already exists)")

# KCSE Scheme
try:
    curriculum_844 = Curriculum.objects.get(code="844")
    kcse_scheme, created = AssessmentScheme.objects.get_or_create(
        name="KCSE Standard Assessment",
        curriculum="844",
        defaults={"description": "Standard KCSE/8-4-4 assessment", "is_active": True}
    )
    if created:
        print(f"✅ KCSE Scheme: {kcse_scheme.name}")
    else:
        print(f"ℹ️ KCSE Scheme: {kcse_scheme.name} (already exists)")
    
    rules = [
        ("A", 80, 100, 12), ("A-", 75, 79, 11), ("B+", 70, 74, 10),
        ("B", 65, 69, 9), ("B-", 60, 64, 8), ("C+", 55, 59, 7),
        ("C", 45, 54, 6), ("C-", 40, 44, 5), ("D+", 35, 39, 4),
        ("D", 30, 34, 3), ("D-", 25, 29, 2), ("E", 0, 24, 1)
    ]
    
    print("  Creating KCSE grade rules...")
    for i, (grade, min_s, max_s, pts) in enumerate(rules, 1):
        rule, created = KCSEGradeRule.objects.get_or_create(
            scheme=kcse_scheme,
            grade=grade,
            defaults={
                "grade_name": grade,
                "min_score": min_s,
                "max_score": max_s,
                "points": pts,
                "order": i,
                "subject_scope": "ALL",
                "descriptor": f"KCSE {grade}",
                "is_active": True
            }
        )
        if created:
            print(f"  ✅ Grade: {rule.grade} ({rule.min_score}-{rule.max_score})")
    
    calc, created = KCSEOverallCalculation.objects.get_or_create(
        scheme=kcse_scheme,
        name="KCSE Standard Calculation",
        defaults={
            "calculation_type": "STANDARD",
            "best_subject_count": 5,
            "min_subjects": 7,
            "max_subjects": 9,
            "grade_boundaries": {
                "A": 80, "A-": 75, "B+": 70, "B": 65, "B-": 60,
                "C+": 55, "C": 45, "C-": 40, "D+": 35, "D": 30,
                "D-": 25, "E": 0
            },
            "is_active": True
        }
    )
    if created:
        print(f"✅ Overall Calculation: {calc.name}")
        
except Curriculum.DoesNotExist:
    print("❌ 8-4-4 curriculum not found!")

# CBC Scheme
try:
    curriculum_cbc = Curriculum.objects.get(code="CBC")
    cbc_scheme, created = AssessmentScheme.objects.get_or_create(
        name="CBC Standard Assessment",
        curriculum="CBC",
        defaults={"description": "Standard CBC/CBA assessment", "is_active": True}
    )
    if created:
        print(f"✅ CBC Scheme: {cbc_scheme.name}")
    else:
        print(f"ℹ️ CBC Scheme: {cbc_scheme.name} (already exists)")
    
    levels = [
        ("PL4", "Exceeding Expectations", 80),
        ("PL3", "Meeting Expectations", 60),
        ("PL2", "Approaching Expectations", 40),
        ("PL1", "Below Expectations", 20),
    ]
    
    print("  Creating CBC performance levels...")
    for i, (code, name, numeric) in enumerate(levels, 1):
        level, created = PerformanceLevel.objects.get_or_create(
            scheme=cbc_scheme,
            level_code=code,
            defaults={
                "level_name": name,
                "descriptor": f"Level: {name}",
                "numeric_value": numeric,
                "order": i,
                "is_active": True
            }
        )
        if created:
            print(f"  ✅ Level: {level.level_code} - {level.level_name}")
    
except Curriculum.DoesNotExist:
    print("❌ CBC curriculum not found!")

print("\n" + "=" * 60)
print("  ✅ DATA CREATED!")
print("=" * 60)
