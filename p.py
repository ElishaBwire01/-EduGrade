"""
EduGrade System Health Check
Run this script to verify all components are working correctly
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')
django.setup()

from django.apps import apps
from django.db import connection
from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.management import call_command

# Import all models to check
from school.models import AcademicYear, Term, Curriculum, GradeLevel, Stream, Subject
from students.models import Student, StudentHistory
from teachers.models import TeacherProfile, TeacherAssignment, TeacherRequest, ClassTeacher
from examinations.models import Examination, ExaminationClass, SubjectScoreConfig
from marks.models import MarkEntry, MarkSubmission, MarkCorrection
from grading.models import (
    AssessmentScheme, KCSEGradeRule, KCSEOverallCalculation,
    PerformanceLevel, Rubric, AssessmentType, AssessmentComponent,
    StudentKCSEGrade, StudentOverallKCSE, StudentCBAAssessment, StudentOverallCBA
)

from django.db import connection

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_success(msg):
    print(f"  ✅ {msg}")

def print_error(msg):
    print(f"  ❌ {msg}")

def print_warning(msg):
    print(f"  ⚠️  {msg}")

def print_info(msg):
    print(f"  ℹ️  {msg}")

def check_database():
    """Check if database is accessible"""
    print_header("DATABASE CHECK")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print_success("Database connection successful")
            return True
    except Exception as e:
        print_error(f"Database connection failed: {str(e)}")
        return False

def check_installed_apps():
    """Check if all required apps are installed"""
    print_header("INSTALLED APPS CHECK")
    required_apps = [
        'core', 'authentication', 'users', 'school', 'students',
        'teachers', 'examinations', 'marks', 'grading'
    ]
    
    installed = apps.get_app_configs()
    installed_names = [app.name for app in installed]
    
    all_found = True
    for app in required_apps:
        if app in installed_names:
            print_success(f"{app} app installed")
        else:
            print_error(f"{app} app NOT installed")
            all_found = False
    return all_found

def check_tables():
    """Check if all required database tables exist"""
    print_header("DATABASE TABLES CHECK")
    
    required_models = [
        ('school', 'AcademicYear'),
        ('school', 'Term'),
        ('school', 'Curriculum'),
        ('school', 'GradeLevel'),
        ('school', 'Stream'),
        ('school', 'Subject'),
        ('students', 'Student'),
        ('students', 'StudentHistory'),
        ('teachers', 'TeacherProfile'),
        ('teachers', 'TeacherAssignment'),
        ('teachers', 'TeacherRequest'),
        ('teachers', 'ClassTeacher'),
        ('examinations', 'Examination'),
        ('marks', 'MarkEntry'),
        ('marks', 'MarkSubmission'),
        ('grading', 'AssessmentScheme'),
        ('grading', 'KCSEGradeRule'),
        ('grading', 'PerformanceLevel'),
    ]
    
    tables = connection.introspection.table_names()
    all_found = True
    
    for app, model_name in required_models:
        model = apps.get_model(app, model_name)
        table_name = model._meta.db_table
        if table_name in tables:
            print_success(f"{app}.{model_name} table exists")
        else:
            print_error(f"{app}.{model_name} table missing")
            all_found = False
    return all_found

def check_data_counts():
    """Check data counts in key tables"""
    print_header("DATA COUNTS CHECK")
    
    try:
        # School data
        year_count = AcademicYear.objects.count()
        term_count = Term.objects.count()
        curriculum_count = Curriculum.objects.count()
        grade_count = GradeLevel.objects.count()
        stream_count = Stream.objects.count()
        subject_count = Subject.objects.count()
        
        print_info(f"Academic Years: {year_count}")
        print_info(f"Terms: {term_count}")
        print_info(f"Curriculums: {curriculum_count}")
        print_info(f"Grade Levels: {grade_count}")
        print_info(f"Streams: {stream_count}")
        print_info(f"Subjects: {subject_count}")
        
        if year_count == 0:
            print_warning("No academic years found! Run Phase 2 setup.")
        if curriculum_count == 0:
            print_warning("No curriculums found! Run Phase 2 setup.")
        
        # Student data
        student_count = Student.objects.count()
        print_info(f"Students: {student_count}")
        
        # Teacher data
        teacher_count = TeacherProfile.objects.count()
        assignment_count = TeacherAssignment.objects.count()
        print_info(f"Teachers: {teacher_count}")
        print_info(f"Teacher Assignments: {assignment_count}")
        
        # Examination data
        exam_count = Examination.objects.count()
        print_info(f"Examinations: {exam_count}")
        
        # Mark data
        mark_count = MarkEntry.objects.count()
        print_info(f"Marks Entered: {mark_count}")
        
        # Grading data
        scheme_count = AssessmentScheme.objects.count()
        kcse_rules_count = KCSEGradeRule.objects.count()
        cbc_levels_count = PerformanceLevel.objects.count()
        
        print_info(f"Assessment Schemes: {scheme_count}")
        print_info(f"KCSE Grade Rules: {kcse_rules_count}")
        print_info(f"CBC Performance Levels: {cbc_levels_count}")
        
        if scheme_count == 0:
            print_warning("No assessment schemes found! Run grading setup.")
        
        return True
    except Exception as e:
        print_error(f"Error checking data: {str(e)}")
        return False

def check_relationships():
    """Check model relationships"""
    print_header("RELATIONSHIPS CHECK")
    
    try:
        # Check if curriculums have subjects
        for curriculum in Curriculum.objects.filter(is_active=True):
            subject_count = curriculum.subjects.count()
            print_info(f"{curriculum.name} has {subject_count} subjects")
            
            if subject_count == 0:
                print_warning(f"No subjects for {curriculum.name}")
        
        # Check if streams have students
        for stream in Stream.objects.filter(is_active=True):
            student_count = stream.students.count()
            if student_count > 0:
                print_info(f"{stream.name} has {student_count} students")
        
        # Check if teachers have assignments
        for teacher in TeacherProfile.objects.filter(is_active=True)[:3]:
            assignment_count = teacher.assignments.count()
            print_info(f"{teacher.full_name} has {assignment_count} assignments")
        
        return True
    except Exception as e:
        print_error(f"Error checking relationships: {str(e)}")
        return False

def check_users():
    """Check user accounts"""
    print_header("USER ACCOUNTS CHECK")
    
    try:
        total_users = User.objects.count()
        superusers = User.objects.filter(is_superuser=True)
        staff_users = User.objects.filter(is_staff=True)
        active_users = User.objects.filter(is_active=True)
        
        print_info(f"Total Users: {total_users}")
        print_info(f"Superusers: {superusers.count()}")
        print_info(f"Staff Users: {staff_users.count()}")
        print_info(f"Active Users: {active_users.count()}")
        
        if superusers.exists():
            for admin in superusers:
                print_success(f"Admin: {admin.username} ({admin.email or 'No email'})")
        else:
            print_warning("No superuser found! Run: python manage.py createsuperuser")
        
        return True
    except Exception as e:
        print_error(f"Error checking users: {str(e)}")
        return False

def check_grading_system():
    """Check grading system configuration"""
    print_header("GRADING SYSTEM CHECK")
    
    try:
        # KCSE Scheme
        kcse_schemes = AssessmentScheme.objects.filter(curriculum='844', is_active=True)
        if kcse_schemes.exists():
            print_success("KCSE assessment scheme found")
            for scheme in kcse_schemes:
                rule_count = scheme.kcse_rules.count()
                print_info(f"  {scheme.name}: {rule_count} grade rules")
                
                # Check grade rules
                if rule_count > 0:
                    print_success("  KCSE grade rules configured")
                else:
                    print_warning("  No KCSE grade rules found")
        else:
            print_error("No KCSE assessment scheme found")
        
        # CBC Scheme
        cbc_schemes = AssessmentScheme.objects.filter(curriculum='CBC', is_active=True)
        if cbc_schemes.exists():
            print_success("CBC assessment scheme found")
            for scheme in cbc_schemes:
                level_count = scheme.cbc_levels.count()
                print_info(f"  {scheme.name}: {level_count} performance levels")
                
                if level_count > 0:
                    print_success("  CBC performance levels configured")
                else:
                    print_warning("  No CBC performance levels found")
        else:
            print_error("No CBC assessment scheme found")
        
        return True
    except Exception as e:
        print_error(f"Error checking grading system: {str(e)}")
        return False

def check_kcse_engine():
    """Check KCSE engine"""
    print_header("KCSE ENGINE CHECK")
    
    try:
        from grading.kcse_engine import KCSEEngine
        print_success("KCSE Engine module found")
        
        # Check if there are examinations to process
        kcse_exams = Examination.objects.filter(curriculum__code='844')
        if kcse_exams.exists():
            print_info(f"Found {kcse_exams.count()} KCSE examinations")
            for exam in kcse_exams[:3]:
                print_info(f"  - {exam.name} ({exam.code})")
        else:
            print_warning("No KCSE examinations found")
        
        return True
    except ImportError as e:
        print_error(f"KCSE Engine import failed: {str(e)}")
        return False

def check_cbc_engine():
    """Check CBC engine"""
    print_header("CBC ENGINE CHECK")
    
    try:
        from grading.cbc_engine import CBCEngine
        print_success("CBC Engine module found")
        
        # Check if there are examinations to process
        cbc_exams = Examination.objects.filter(curriculum__code='CBC')
        if cbc_exams.exists():
            print_info(f"Found {cbc_exams.count()} CBC examinations")
            for exam in cbc_exams[:3]:
                print_info(f"  - {exam.name} ({exam.code})")
        else:
            print_warning("No CBC examinations found")
        
        return True
    except ImportError as e:
        print_error(f"CBC Engine import failed: {str(e)}")
        return False

def check_permissions():
    """Check if the system has proper permissions"""
    print_header("PERMISSIONS CHECK")
    
    # Check if required modules exist
    required_files = [
        ('school', 'models.py'),
        ('students', 'models.py'),
        ('teachers', 'models.py'),
        ('examinations', 'models.py'),
        ('marks', 'models.py'),
        ('grading', 'models.py'),
        ('grading', 'kcse_engine.py'),
        ('grading', 'cbc_engine.py'),
    ]
    
    all_found = True
    for app, file_name in required_files:
        file_path = os.path.join(app, file_name)
        if os.path.exists(file_path):
            print_success(f"{file_path} exists")
        else:
            print_error(f"{file_path} missing")
            all_found = False
    
    # Check templates
    template_dirs = [
        'templates/school',
        'templates/students',
        'templates/teachers',
        'templates/examinations',
        'templates/marks',
        'templates/grading',
    ]
    
    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            print_success(f"{template_dir} directory exists")
        else:
            print_warning(f"{template_dir} directory missing")
    
    return all_found

def check_urls():
    """Check if URLs are configured"""
    print_header("URL CONFIGURATION CHECK")
    
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        url_patterns = [
            ('admin/', 'Admin'),
            ('', 'Home'),
            ('auth/', 'Authentication'),
            ('students/', 'Students'),
            ('teachers/', 'Teachers'),
            ('examinations/', 'Examinations'),
            ('marks/', 'Marks'),
            ('grading/', 'Grading'),
        ]
        
        url_list = [str(p) for p in resolver.url_patterns]
        
        for pattern, name in url_patterns:
            found = False
            for url in url_list:
                if pattern in url:
                    found = True
                    break
            if found:
                print_success(f"URL: /{pattern} ({name}) configured")
            else:
                print_warning(f"URL: /{pattern} ({name}) NOT configured")
        
        return True
    except Exception as e:
        print_error(f"Error checking URLs: {str(e)}")
        return False

def run_health_check():
    """Run complete health check"""
    print_header("EDUGRADE SYSTEM HEALTH CHECK")
    print(f"  Time: {django.utils.timezone.now()}")
    
    results = {
        'database': check_database(),
        'apps': check_installed_apps(),
        'tables': check_tables(),
        'data': check_data_counts(),
        'relationships': check_relationships(),
        'users': check_users(),
        'grading': check_grading_system(),
        'kcse_engine': check_kcse_engine(),
        'cbc_engine': check_cbc_engine(),
        'permissions': check_permissions(),
        'urls': check_urls(),
    }
    
    # Summary
    print_header("SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"  Total Checks: {total}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    
    if passed == total:
        print_success("🎉 ALL CHECKS PASSED! System is ready!")
        print_info("Visit: http://127.0.0.1:8000/")
    else:
        print_warning("⚠️  Some checks failed. Review the details above.")
        print_info("Run these commands to fix common issues:")
        print_info("  python manage.py makemigrations")
        print_info("  python manage.py migrate")
        print_info("  python manage.py createsuperuser")
        print_info("  python create_grading_systems.py")
        print_info("  python create_school_data.py")
    
    print("\n" + "=" * 60)
    print("  HEALTH CHECK COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_health_check()
