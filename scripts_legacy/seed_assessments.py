"""
EduGrade Assessment & Student Data Seed Script
==============================================
Creates assessment schemes (KCSE + CBC) and generates student assessment
records for a target examination.

Usage:
    python seed_assessments.py [--exam-code CODE] [--clear] [--dry-run]

Without --exam-code, the script will:
  1. Ensure assessment schemes exist (create if missing)
  2. Pick the first LOCKED/PUBLISHED exam per curriculum
  3. Seed student assessment data for that exam

With --clear, existing StudentKCSEGrade / StudentOverallKCSE /
StudentCBAAssessment / StudentOverallCBA records are deleted first.
"""

import os
import sys
import argparse
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "edugrade.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

from school.models import AcademicYear, Curriculum, GradeLevel, Subject
from students.models import Student
from examinations.models import Examination
from grading.models import (
    AssessmentScheme, KCSEGradeRule, KCSEOverallCalculation,
    PerformanceLevel, AssessmentType, Rubric, RubricCriterion,
    RubricDescriptor, AssessmentComponent, ComponentAggregation,
    StudentKCSEGrade, StudentOverallKCSE,
    StudentCBAAssessment, StudentOverallCBA,
)
from marks.models import MarkEntry
from grading.services import (
    create_kcse_assessment_scheme,
    create_cbc_assessment_scheme,
    seed_student_assessments,
    seed_cbc_assessments,
)

User = get_user_model()


def header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def info(msg):
    print(f"  [i] {msg}")


def success(msg):
    print(f"  [+] {msg}")


def warn(msg):
    print(f"  [!] {msg}")


def error(msg):
    print(f"  [X] {msg}")


def ensure_schemes(clear=False):
    """Create KCSE and CBC assessment schemes if they don't exist."""
    header("ASSESSMENT SCHEME SETUP")

    # Get current academic year
    academic_year = AcademicYear.objects.filter(is_current=True).first()
    if not academic_year:
        academic_year = AcademicYear.objects.first()
    if not academic_year:
        error("No academic year found. Run school setup first.")
        sys.exit(1)
    info(f"Using academic year: {academic_year.year}")

    # Get or create admin user for created_by
    admin_user = User.objects.filter(is_staff=True).first() or User.objects.first()

    # --- KCSE / 8-4-4 ---
    kcse_scheme = AssessmentScheme.objects.filter(curriculum="844", is_active=True).first()
    if kcse_scheme and not clear:
        success(f"KCSE scheme already exists: {kcse_scheme.name}")
    else:
        if clear and kcse_scheme:
            info("Clearing existing KCSE scheme and related rules...")
            KCSEGradeRule.objects.filter(scheme=kcse_scheme).delete()
            KCSEOverallCalculation.objects.filter(scheme=kcse_scheme).delete()
            kcse_scheme.delete()

        try:
            kcse_scheme = create_kcse_assessment_scheme(
                academic_year=academic_year,
                created_by=admin_user,
            )
            success(f"KCSE scheme created: {kcse_scheme.name}")
            rule_count = KCSEGradeRule.objects.filter(scheme=kcse_scheme).count()
            info(f"  → {rule_count} grade rules")
            calc = KCSEOverallCalculation.objects.filter(scheme=kcse_scheme).first()
            if calc:
                info(f"  → Overall calculation: {calc.name} (best {calc.best_subject_count} + core)")
        except Exception as e:
            error(f"Failed to create KCSE scheme: {e}")
            return False

    # --- CBC ---
    cbc_scheme = AssessmentScheme.objects.filter(curriculum="CBC", is_active=True).first()
    if cbc_scheme and not clear:
        success(f"CBC scheme already exists: {cbc_scheme.name}")
    else:
        if clear and cbc_scheme:
            info("Clearing existing CBC scheme and related data...")
            RubricDescriptor.objects.filter(criterion__rubric__scheme=cbc_scheme).delete()
            RubricCriterion.objects.filter(rubric__scheme=cbc_scheme).delete()
            Rubric.objects.filter(scheme=cbc_scheme).delete()
            AssessmentType.objects.filter(scheme=cbc_scheme).delete()
            ComponentAggregation.objects.filter(scheme=cbc_scheme).delete()
            AssessmentComponent.objects.filter(scheme=cbc_scheme).delete()
            PerformanceLevel.objects.filter(scheme=cbc_scheme).delete()
            cbc_scheme.delete()

        try:
            cbc_scheme = create_cbc_assessment_scheme(
                academic_year=academic_year,
                created_by=admin_user,
            )
            success(f"CBC scheme created: {cbc_scheme.name}")
            level_count = PerformanceLevel.objects.filter(scheme=cbc_scheme).count()
            info(f"  → {level_count} performance levels")
            type_count = AssessmentType.objects.filter(scheme=cbc_scheme).count()
            info(f"  → {type_count} assessment types")
            rubric_count = Rubric.objects.filter(scheme=cbc_scheme).count()
            info(f"  → {rubric_count} rubrics")
            comp_count = AssessmentComponent.objects.filter(scheme=cbc_scheme).count()
            info(f"  → {comp_count} assessment components")
        except Exception as e:
            error(f"Failed to create CBC scheme: {e}")
            return False

    return True


def find_target_exams():
    """Find exams for each curriculum to seed student data."""
    header("EXAMINATION DISCOVERY")

    exams = {}
    for code in ("844", "CBC"):
        curriculum = Curriculum.objects.filter(code=code).first()
        if not curriculum:
            warn(f"Curriculum '{code}' not found in database.")
            continue

        exam = Examination.objects.filter(
            curriculum=curriculum,
            status__in=["LOCKED", "PUBLISHED", "ACTIVE"],
        ).order_by("-start_date").first()

        if exam:
            exams[code] = exam
            success(f"Found exam for {code}: {exam.code} — {exam.name} ({exam.status})")
        else:
            warn(f"No exam found for curriculum {code}.")

    return exams


def clear_existing_assessments():
    """Delete existing student assessment results."""
    header("CLEARING EXISTING ASSESSMENT DATA")

    deleted = {}
    for model, label in [
        (StudentKCSEGrade, "StudentKCSEGrade"),
        (StudentOverallKCSE, "StudentOverallKCSE"),
        (StudentCBAAssessment, "StudentCBAAssessment"),
        (StudentOverallCBA, "StudentOverallCBA"),
    ]:
        count = model.objects.count()
        model.objects.all().delete()
        deleted[label] = count
        info(f"Deleted {count} {label} records")

    return deleted


def seed_exam_data(exam_code, exam, clear=False, dry_run=False):
    """Seed student assessment data for a single examination."""
    label = "KCSE" if exam_code == "844" else "CBC"
    header(f"SEEDING STUDENT DATA — {label} ({exam.code})")

    if clear:
        if exam_code == "844":
            StudentKCSEGrade.objects.filter(examination=exam).delete()
            StudentOverallKCSE.objects.filter(examination=exam).delete()
        else:
            StudentCBAAssessment.objects.filter(examination=exam).delete()
            StudentOverallCBA.objects.filter(examination=exam).delete()
        info(f"Cleared existing {label} results for this exam.")

    # Determine target students
    grade_level = exam.grade_level
    subject = exam.subjects.first() if exam.subjects.exists() else None

    # Get students enrolled at this grade level (could filter by stream too)
    students = Student.objects.filter(
        current_grade_level=grade_level,
        is_active=True,
    ).order_by("admission_number")

    student_count = students.count()
    info(f"Target students: {student_count}")

    if student_count == 0:
        warn(f"No active students found for grade level {grade_level.name}.")
        return

    # Also ensure MarkEntry exists for 844 (so the grading engine has data)
    if exam_code == "844":
        from decimal import Decimal
        import random
        random.seed(42)

        mark_count = 0
        for student in students:
            for subj in exam.subjects.all():
                existing = MarkEntry.objects.filter(
                    student=student, examination=exam, subject=subj
                ).first()
                if not existing:
                    score = round(random.uniform(35, 98), 1)
                    MarkEntry.objects.create(
                        student=student,
                        examination=exam,
                        subject=subj,
                        grade_level=grade_level,
                        stream=student.current_stream,
                        score=score,
                        status="APPROVED",
                        entered_by=User.objects.filter(is_staff=True).first(),
                    )
                    mark_count += 1
                else:
                    # Ensure status is approved
                    if existing.status != "APPROVED":
                        existing.status = "APPROVED"
                        existing.save(update_fields=["status"])

        info(f"MarkEntry records ready ({mark_count} new created).")

    if dry_run:
        info("[DRY RUN] Would generate student assessment records now.")
        return

    # Seed assessment data
    try:
        with transaction.atomic():
            if exam_code == "844":
                result = seed_student_assessments(exam, students=students)
                success(f"KCSE grades created: {result['kcse_grades']}")
                success(f"Overall KCSE results: {result['overalls']}")
            else:
                result = seed_cbc_assessments(exam, students=students)
                success(f"CBC assessments created: {result['cbc_assessments']}")
                success(f"Overall CBA results: {result['overalls']}")
    except Exception as e:
        error(f"Failed to seed {label} data: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Seed EduGrade with assessment schemes and student data"
    )
    parser.add_argument(
        "--exam-code",
        choices=["844", "CBC"],
        help="Curriculum code to seed. If omitted, both are processed.",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing student assessment records before seeding.",
    )
    parser.add_argument(
        "--clear-schemes",
        action="store_true",
        help="Delete and recreate assessment schemes.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without writing data.",
    )
    args = parser.parse_args()

    header("EDUGRADE ASSESSMENT & DATA SEED")

    # Check prerequisites
    if AcademicYear.objects.count() == 0:
        error("No academic years found. Create one via /school/setup/ first.")
        sys.exit(1)

    if Curriculum.objects.count() < 2:
        warn("Not all curriculums found. Consider running school setup.")

    # Step 1: Ensure assessment schemes exist
    if not ensure_schemes(clear=args.clear_schemes):
        error("Failed to set up assessment schemes. Aborting.")
        sys.exit(1)

    # Step 2: Find target examinations
    exams = find_target_exams()
    if not exams:
        error("No examinations found. Create one via /examinations/create/ first.")
        sys.exit(1)

    # Step 3: Optionally clear all existing student assessment data
    if args.clear:
        clear_existing_assessments()

    # Step 4: Seed student data
    target_codes = [args.exam_code] if args.exam_code else list(exams.keys())

    for code in target_codes:
        exam = exams.get(code)
        if not exam:
            if code not in exams:
                warn(f"No exam available for curriculum '{code}'. Skipping.")
            continue

        try:
            seed_exam_data(code, exam, clear=args.clear, dry_run=args.dry_run)
        except Exception as e:
            error(f"Error seeding {code} data: {e}")

    header("SEED COMPLETE")
    info("Run 'python p.py' to verify system health.")
    info("Open http://127.0.0.1:8000/ to view the application.")


if __name__ == "__main__":
    main()
