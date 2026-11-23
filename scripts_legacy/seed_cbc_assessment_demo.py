r"""Create repeatable CBC assessment data for local UI inspection.

Run from the project root:
    venv\Scripts\python.exe seed_cbc_assessment_demo.py
"""

import os
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')

import django

django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

from examinations.models import Examination, ExaminationClass
from grading.models import (
    AssessmentScheme,
    AssessmentType,
    PerformanceLevel,
    Rubric,
    StudentCBAAssessment,
    StudentOverallCBA,
)
from school.models import AcademicYear, Curriculum, GradeLevel, Stream, Subject, Term
from students.models import Student


DEMO_PREFIX = 'DEMO-CBC-2026'
LEVELS = [
    ('PL4', 'Exceeding Expectations', 4),
    ('PL3', 'Meeting Expectations', 3),
    ('PL2', 'Approaching Expectations', 2),
    ('PL1', 'Below Expectations', 1),
]


def first_or_fail(queryset, label):
    value = queryset.first()
    if not value:
        raise RuntimeError(f'No {label} found. Create school structure data first.')
    return value


def make_result(student_index, subject_index, assessment_index):
    """Create deterministic levels with improvement between the two assessments."""
    baseline = [1, 2, 2, 3, 3, 4][(student_index + subject_index) % 6]
    if assessment_index == 2 and student_index % 5 == 0:
        baseline = min(4, baseline + 1)
    if assessment_index == 2 and student_index % 7 == 0:
        baseline = max(1, baseline - 1)
    return baseline


@transaction.atomic
def seed():
    User = get_user_model()
    creator = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first() or User.objects.first()
    if not creator:
        raise RuntimeError('Create an admin user before running this script.')

    cbc = first_or_fail(Curriculum.objects.filter(code='CBC', is_active=True), 'active CBC curriculum')
    grade = first_or_fail(GradeLevel.objects.filter(curriculum=cbc, is_active=True), 'active CBC grade level')
    year = first_or_fail(AcademicYear.objects.all().order_by('-year'), 'academic year')
    term = first_or_fail(Term.objects.filter(academic_year=year), 'term for the selected academic year')
    subjects = list(Subject.objects.filter(curriculum=cbc, is_active=True).order_by('id')[:5])
    if not subjects:
        raise RuntimeError('Create CBC learning areas/subjects before running this script.')

    streams = list(Stream.objects.filter(grade_level=grade, is_active=True))
    if not streams:
        raise RuntimeError(f'No active streams found for {grade.name}. Create streams first.')

    learners = list(Student.objects.filter(
        curriculum=cbc,
        current_grade_level=grade,
        academic_year=year,
        is_active=True,
    ).select_related('current_stream').order_by('id'))
    if not learners:
        for index in range(1, 31):
            student, _ = Student.objects.get_or_create(
                admission_number=f'{DEMO_PREFIX}-STU-{index:03d}',
                defaults={
                    'first_name': f'Demo{index}',
                    'last_name': 'Learner',
                    'date_of_birth': date(2012, 1, 1),
                    'gender': 'M' if index % 2 else 'F',
                    'admission_date': year.start_date,
                    'curriculum': cbc,
                    'current_grade_level': grade,
                    'current_stream': streams[(index - 1) % len(streams)],
                    'academic_year': year,
                    'status': 'ACTIVE',
                    'is_active': True,
                    'created_by': creator,
                },
            )
        learners = list(Student.objects.filter(
            curriculum=cbc,
            current_grade_level=grade,
            academic_year=year,
            is_active=True,
        ).select_related('current_stream').order_by('id'))

    scheme, _ = AssessmentScheme.objects.get_or_create(
        name=f'{DEMO_PREFIX} Configured CBC Scheme',
        curriculum='CBC',
        defaults={
            'description': 'Local demonstration scheme for inspecting CBC analytics. Not an official KNEC calculation.',
            'academic_year': year,
            'created_by': creator,
        },
    )
    scheme.grade_levels.add(grade)

    level_objects = {}
    for code, name, order in LEVELS:
        level_objects[code], _ = PerformanceLevel.objects.get_or_create(
            scheme=scheme,
            level_code=code,
            defaults={
                'level_name': name,
                'descriptor': f'Demo descriptor for {name}.',
                'order': order,
                'numeric_value': order,
            },
        )

    assessment_type, _ = AssessmentType.objects.get_or_create(
        scheme=scheme,
        name=f'{DEMO_PREFIX} Summative Assessment',
        defaults={'category': 'SUMMATIVE', 'weight': 100, 'description': 'Demo assessment for analytics inspection.'},
    )

    rubrics = []
    for subject in subjects:
        rubric, _ = Rubric.objects.get_or_create(
            scheme=scheme,
            name=f'{DEMO_PREFIX} {subject.code} Rubric',
            defaults={'assessment_type': assessment_type, 'subject': subject, 'grade_level': grade},
        )
        rubrics.append(rubric)

    exams = []
    for index, offset in enumerate((0, 45), 1):
        exam, _ = Examination.objects.get_or_create(
            code=f'{DEMO_PREFIX}-A{index}',
            defaults={
                'name': f'{DEMO_PREFIX} Assessment {index}',
                'exam_type': 'CAT',
                'description': 'Generated local CBC assessment data for testing analysis screens.',
                'academic_year': year,
                'term': term,
                'curriculum': cbc,
                'grade_level': grade,
                'start_date': date.today() - timedelta(days=offset),
                'end_date': date.today() - timedelta(days=offset - 1),
                'status': 'PUBLISHED',
                'created_by': creator,
            },
        )
        exam.subjects.set(subjects)
        for stream in streams:
            ExaminationClass.objects.get_or_create(examination=exam, grade_level=grade, stream=stream)
        exams.append(exam)

    assessed_learners = learners[: max(1, int(len(learners) * 0.8))]
    for assessment_index, exam in enumerate(exams, 1):
        for student_index, student in enumerate(assessed_learners):
            levels_for_student = []
            for subject_index, (subject, rubric) in enumerate(zip(subjects, rubrics)):
                level_number = make_result(student_index, subject_index, assessment_index)
                level_code = f'PL{level_number}'
                level = level_objects[level_code]
                score = 55 + level_number * 10 + ((student_index + subject_index) % 6)
                StudentCBAAssessment.objects.update_or_create(
                    student=student,
                    examination=exam,
                    rubric=rubric,
                    defaults={
                        'subject': subject,
                        'criterion_results': {'demo_criterion': level_code},
                        'overall_level': level,
                        'teacher_notes': 'Demo evidence for UI inspection.' if level_number < 3 else '',
                        'score': score,
                    },
                )
                levels_for_student.append(level_number)
            overall_level = level_objects[f'PL{round(sum(levels_for_student) / len(levels_for_student))}']
            total = round(sum(levels_for_student) * 25.0, 1)
            StudentOverallCBA.objects.update_or_create(
                student=student,
                examination=exam,
                defaults={
                    'overall_level': overall_level,
                    'component_scores': {'demo_summative': total},
                    'total_score': total,
                    'total_weighted_score': total,
                    'grade_equivalent': '',
                    'position': student_index + 1,
                },
            )

    print('CBC demo data ready.')
    print(f'Assessment 1: /examinations/{exams[0].id}/analysis/')
    print(f'Assessment 2: /examinations/{exams[1].id}/analysis/')
    print(f'School dashboard: /dashboard/')
    print(f'Learners registered: {len(learners)}')
    print(f'Learners assessed per demo assessment: {len(assessed_learners)}')
    print(f'Learners intentionally not assessed: {len(learners) - len(assessed_learners)}')
    print('This is local demo data and uses a clearly labelled non-official aggregation scheme.')


if __name__ == '__main__':
    seed()
