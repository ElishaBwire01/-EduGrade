import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')
import django
django.setup()

from django.db import connection
from datetime import datetime

print("=" * 60)
print("  FIXING GRADING TABLES")
print("=" * 60)

# Drop tables
print("\n🗑️ Dropping broken tables...")
tables = [
    "assessment_schemes", "kcse_grade_rules", "kcse_overall_calculations",
    "performance_levels", "assessment_types", "rubrics", "rubric_criteria",
    "rubric_descriptors", "assessment_components", "component_aggregations",
    "student_cbc_assessments", "student_kcse_grades", "student_overall_cba",
    "student_overall_kcse"
]

with connection.cursor() as cursor:
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  ✅ Dropped {table}")
        except:
            pass

# Clear migrations
print("\n🗑️ Clearing migrations...")
with connection.cursor() as cursor:
    try:
        cursor.execute("DELETE FROM django_migrations WHERE app='grading'")
        print("  ✅ Cleared grading migrations")
    except:
        pass

# Create tables - fixed column names
print("\n📋 Creating tables...")
with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            curriculum VARCHAR(10) NOT NULL,
            description TEXT,
            is_active BOOL NOT NULL,
            academic_year_id INTEGER,
            effective_from DATE,
            effective_to DATE,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            created_by_id INTEGER
        )
    """)
    print("  ✅ Created assessment_schemes")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kcse_grade_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id INTEGER NOT NULL,
            subject_id INTEGER,
            subject_scope VARCHAR(20) NOT NULL,
            grade VARCHAR(3) NOT NULL,
            grade_name VARCHAR(50) NOT NULL,
            points DECIMAL NOT NULL,
            min_score INTEGER NOT NULL,
            max_score INTEGER NOT NULL,
            descriptor VARCHAR(100),
            sort_order INTEGER NOT NULL,
            is_active BOOL NOT NULL
        )
    """)
    print("  ✅ Created kcse_grade_rules")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kcse_overall_calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            calculation_type VARCHAR(20) NOT NULL,
            best_subject_count INTEGER NOT NULL,
            min_subjects INTEGER NOT NULL,
            max_subjects INTEGER NOT NULL,
            grade_boundaries TEXT,
            is_active BOOL NOT NULL
        )
    """)
    print("  ✅ Created kcse_overall_calculations")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id INTEGER NOT NULL,
            level_code VARCHAR(3) NOT NULL,
            level_name VARCHAR(50) NOT NULL,
            descriptor TEXT NOT NULL,
            sort_order INTEGER NOT NULL,
            numeric_value INTEGER,
            is_active BOOL NOT NULL
        )
    """)
    print("  ✅ Created performance_levels")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(20) NOT NULL,
            description TEXT,
            weight DECIMAL NOT NULL,
            is_active BOOL NOT NULL
        )
    """)
    print("  ✅ Created assessment_types")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rubrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            assessment_type_id INTEGER,
            subject_id INTEGER,
            grade_level_id INTEGER,
            is_active BOOL NOT NULL
        )
    """)
    print("  ✅ Created rubrics")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rubric_criteria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rubric_id INTEGER NOT NULL,
            criterion VARCHAR(200) NOT NULL,
            description TEXT,
            max_level_id INTEGER,
            sort_order INTEGER NOT NULL,
            is_active BOOL NOT NULL
        )
    """)
    print("  ✅ Created rubric_criteria")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rubric_descriptors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            criterion_id INTEGER NOT NULL,
            level_id INTEGER NOT NULL,
            descriptor TEXT NOT NULL
        )
    """)
    print("  ✅ Created rubric_descriptors")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            component_type VARCHAR(20) NOT NULL,
            weight DECIMAL NOT NULL,
            description TEXT,
            is_active BOOL NOT NULL
        )
    """)
    print("  ✅ Created assessment_components")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS component_aggregations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            aggregation_type VARCHAR(20) NOT NULL,
            formula TEXT,
            is_active BOOL NOT NULL
        )
    """)
    print("  ✅ Created component_aggregations")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_kcse_grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            examination_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            raw_mark DECIMAL NOT NULL,
            grade VARCHAR(3) NOT NULL,
            points DECIMAL NOT NULL,
            is_core BOOL NOT NULL,
            is_best_subject BOOL NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """)
    print("  ✅ Created student_kcse_grades")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_overall_kcse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            examination_id INTEGER NOT NULL,
            total_points DECIMAL NOT NULL,
            mean_grade VARCHAR(3) NOT NULL,
            mean_score DECIMAL NOT NULL,
            core_subjects_count INTEGER NOT NULL,
            best_subjects_count INTEGER NOT NULL,
            total_subjects_used INTEGER NOT NULL,
            position INTEGER,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """)
    print("  ✅ Created student_overall_kcse")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_cbc_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            examination_id INTEGER NOT NULL,
            rubric_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            criterion_results TEXT NOT NULL,
            overall_level_id INTEGER,
            teacher_notes TEXT,
            component_id INTEGER,
            score DECIMAL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """)
    print("  ✅ Created student_cbc_assessments")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_overall_cba (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            examination_id INTEGER NOT NULL,
            overall_level_id INTEGER,
            component_scores TEXT NOT NULL,
            total_score DECIMAL NOT NULL,
            total_weighted_score DECIMAL NOT NULL,
            grade_equivalent VARCHAR(3),
            position INTEGER,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """)
    print("  ✅ Created student_overall_cba")

# Mark migration
print("\n📝 Marking migration...")
with connection.cursor() as cursor:
    try:
        cursor.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('grading', '0001_initial', datetime('now'))")
        print("  ✅ Migration marked complete")
    except:
        print("  ⚠️ Migration already marked")

print("\n" + "=" * 60)
print("  ✅ TABLES CREATED!")
print("=" * 60)
