import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')
import django
django.setup()

from grading.models import AssessmentScheme, KCSEGradeRule, KCSEOverallCalculation, PerformanceLevel
from school.models import Curriculum, GradeLevel, Subject

print("=" * 50)
print("CREATING GRADING SYSTEMS")
print("=" * 50)

# ============ KCSE SCHEME ============
print("\n📚 Creating KCSE/8-4-4 Scheme...")

try:
    curriculum_844 = Curriculum.objects.get(code='844')
    
    kcse_scheme, created = AssessmentScheme.objects.get_or_create(
        name='KCSE Standard Assessment',
        curriculum='844',
        defaults={
            'description': 'Standard KCSE/8-4-4 assessment scheme with A-E grading',
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created KCSE scheme: {kcse_scheme.name}")
    else:
        print(f"ℹ️ KCSE scheme already exists")
    
    # Create KCSE grade rules
    kcse_rules = [
        {'grade': 'A', 'grade_name': 'Very Good', 'min_score': 80, 'max_score': 100, 'points': 12, 'order': 1},
        {'grade': 'A-', 'grade_name': 'Very Good', 'min_score': 75, 'max_score': 79, 'points': 11, 'order': 2},
        {'grade': 'B+', 'grade_name': 'Good', 'min_score': 70, 'max_score': 74, 'points': 10, 'order': 3},
        {'grade': 'B', 'grade_name': 'Good', 'min_score': 65, 'max_score': 69, 'points': 9, 'order': 4},
        {'grade': 'B-', 'grade_name': 'Good', 'min_score': 60, 'max_score': 64, 'points': 8, 'order': 5},
        {'grade': 'C+', 'grade_name': 'Average', 'min_score': 55, 'max_score': 59, 'points': 7, 'order': 6},
        {'grade': 'C', 'grade_name': 'Average', 'min_score': 45, 'max_score': 54, 'points': 6, 'order': 7},
        {'grade': 'C-', 'grade_name': 'Average', 'min_score': 40, 'max_score': 44, 'points': 5, 'order': 8},
        {'grade': 'D+', 'grade_name': 'Weak', 'min_score': 35, 'max_score': 39, 'points': 4, 'order': 9},
        {'grade': 'D', 'grade_name': 'Weak', 'min_score': 30, 'max_score': 34, 'points': 3, 'order': 10},
        {'grade': 'D-', 'grade_name': 'Weak', 'min_score': 25, 'max_score': 29, 'points': 2, 'order': 11},
        {'grade': 'E', 'grade_name': 'Poor', 'min_score': 0, 'max_score': 24, 'points': 1, 'order': 12},
    ]
    
    for rule_data in kcse_rules:
        rule, created = KCSEGradeRule.objects.get_or_create(
            scheme=kcse_scheme,
            grade=rule_data['grade'],
            defaults={
                'grade_name': rule_data['grade_name'],
                'min_score': rule_data['min_score'],
                'max_score': rule_data['max_score'],
                'points': rule_data['points'],
                'order': rule_data['order'],
                'subject_scope': 'ALL',
                'descriptor': rule_data['grade_name']
            }
        )
        if created:
            print(f"   ✅ Created grade rule: {rule.grade} ({rule.min_score}-{rule.max_score})")
    
    # Create KCSE overall calculation
    calc, created = KCSEOverallCalculation.objects.get_or_create(
        scheme=kcse_scheme,
        name='KCSE Standard Calculation',
        defaults={
            'calculation_type': 'STANDARD',
            'best_subject_count': 5,
            'min_subjects': 7,
            'max_subjects': 9,
            'grade_boundaries': {
                'A': 80, 'A-': 75, 'B+': 70, 'B': 65, 'B-': 60,
                'C+': 55, 'C': 45, 'C-': 40, 'D+': 35, 'D': 30,
                'D-': 25, 'E': 0
            }
        }
    )
    
    if created:
        print(f"✅ Created overall calculation: {calc.name}")
    
except Curriculum.DoesNotExist:
    print("❌ 8-4-4 curriculum not found. Please run Phase 2 setup first.")

# ============ CBC SCHEME ============
print("\n📚 Creating CBC/CBA Scheme...")

try:
    curriculum_cbc = Curriculum.objects.get(code='CBC')
    
    cbc_scheme, created = AssessmentScheme.objects.get_or_create(
        name='CBC/CBA Standard Assessment',
        curriculum='CBC',
        defaults={
            'description': 'Standard CBC/CBA assessment scheme with PL1-PL4 performance levels',
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created CBC scheme: {cbc_scheme.name}")
    else:
        print(f"ℹ️ CBC scheme already exists")
    
    # Create performance levels
    cbc_levels = [
        {'code': 'PL4', 'name': 'Exceeding Expectations', 'order': 1, 'numeric': 80,
         'descriptor': 'The learner demonstrates performance beyond the expected competency level'},
        {'code': 'PL3', 'name': 'Meeting Expectations', 'order': 2, 'numeric': 60,
         'descriptor': 'The learner meets the expected competency requirements'},
        {'code': 'PL2', 'name': 'Approaching Expectations', 'order': 3, 'numeric': 40,
         'descriptor': 'The learner is progressing toward the required competency but still has gaps'},
        {'code': 'PL1', 'name': 'Below Expectations', 'order': 4, 'numeric': 20,
         'descriptor': 'The learner has not yet demonstrated the required competency'},
    ]
    
    for level_data in cbc_levels:
        level, created = PerformanceLevel.objects.get_or_create(
            scheme=cbc_scheme,
            level_code=level_data['code'],
            defaults={
                'level_name': level_data['name'],
                'descriptor': level_data['descriptor'],
                'order': level_data['order'],
                'numeric_value': level_data['numeric'],
                'is_active': True
            }
        )
        if created:
            print(f"   ✅ Created performance level: {level.level_code} - {level.level_name}")
    
    print("✅ CBC scheme created successfully!")

except Curriculum.DoesNotExist:
    print("❌ CBC curriculum not found. Please run Phase 2 setup first.")

print("\n" + "=" * 50)
print("✅ GRADING SYSTEMS SETUP COMPLETE!")
print("=" * 50)
