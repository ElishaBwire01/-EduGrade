from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction

from django.core.paginator import Paginator
from .models import Student, StudentHistory
from school.models import AcademicYear, Curriculum, GradeLevel, Stream
from django.contrib.auth import get_user_model
User = get_user_model()
from datetime import datetime
from core.access import can_manage_student, can_use_class, permitted_student_queryset, can_edit_student, is_admin
from core.models import AuditLog
from teachers.models import ClassTeacher, TeacherProfile

try:
    from grading.models import (
        StudentKCSEGrade,
        StudentOverallKCSE,
        StudentCBAAssessment,
        StudentOverallCBA,
    )
except ImportError:
    StudentKCSEGrade = None
    StudentOverallKCSE = None
    StudentCBAAssessment = None
    StudentOverallCBA = None


def _positive_id(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _validate_placement(grade_level_id, stream_id, academic_year_id, curriculum_id=None):
    grade_level_id = _positive_id(grade_level_id)
    stream_id = _positive_id(stream_id)
    academic_year_id = _positive_id(academic_year_id)
    curriculum_id = _positive_id(curriculum_id) if curriculum_id is not None else None

    grade_level = GradeLevel.objects.filter(id=grade_level_id, is_active=True).first() if grade_level_id else None
    stream = Stream.objects.filter(id=stream_id, is_active=True).first() if stream_id else None
    academic_year = AcademicYear.objects.filter(id=academic_year_id).first() if academic_year_id else None
    curriculum = Curriculum.objects.filter(id=curriculum_id, is_active=True).first() if curriculum_id else None

    if not grade_level or not stream or not academic_year:
        return None, None, None, None, 'Select a valid grade, stream, and academic year.'
    if stream.grade_level_id != grade_level.id:
        return None, None, None, None, 'The selected stream does not belong to the selected grade.'
    if curriculum_id is not None:
        if not curriculum:
            return None, None, None, None, 'Select a valid curriculum.'
        if grade_level.curriculum_id != curriculum.id:
            return None, None, None, None, 'The selected grade does not belong to the selected curriculum.'

    return grade_level, stream, academic_year, curriculum, None


def _record_current_placement(student, grade_level, stream, academic_year):
    placement_changed = (
        student.current_grade_level_id != grade_level.id
        or student.current_stream_id != stream.id
        or student.academic_year_id != academic_year.id
    )
    has_current_history = StudentHistory.objects.filter(student_id=student.id, is_current=True).exists()

    if not placement_changed:
        if not has_current_history:
            StudentHistory.objects.create(
                student_id=student.id,
                grade_level_id=grade_level.id,
                stream_id=stream.id,
                academic_year_id=academic_year.id,
                is_current=True,
            )
        return False

    StudentHistory.objects.filter(student_id=student.id, is_current=True).update(is_current=False)
    StudentHistory.objects.create(
        student_id=student.id,
        grade_level_id=grade_level.id,
        stream_id=stream.id,
        academic_year_id=academic_year.id,
        is_current=True,
    )
    return True


def _student_exam_history(student):
    """Build a normalized performance history for both supported curricula."""
    exam_ids = set()
    if StudentOverallKCSE:
        exam_ids.update(StudentOverallKCSE.objects.filter(student=student).values_list('examination_id', flat=True))
    if StudentKCSEGrade:
        exam_ids.update(StudentKCSEGrade.objects.filter(student=student).values_list('examination_id', flat=True))
    if StudentOverallCBA:
        exam_ids.update(StudentOverallCBA.objects.filter(student=student).values_list('examination_id', flat=True))
    if StudentCBAAssessment:
        exam_ids.update(StudentCBAAssessment.objects.filter(student=student).values_list('examination_id', flat=True))

    from examinations.models import Examination
    exams = Examination.objects.filter(id__in=exam_ids).select_related(
        'academic_year', 'term', 'curriculum'
    ).order_by('start_date', 'id')
    history = []

    for exam in exams:
        score = None
        grade = '-'
        position = None
        subject_count = 0

        if exam.curriculum.code == '844' and StudentOverallKCSE:
            overall = StudentOverallKCSE.objects.filter(student=student, examination=exam).first()
            if overall:
                score = float(overall.mean_score)
                grade = overall.mean_grade
                position = overall.position
            if StudentKCSEGrade:
                subject_count = StudentKCSEGrade.objects.filter(student=student, examination=exam).count()
        elif exam.curriculum.code == 'CBC' and StudentOverallCBA:
            overall = StudentOverallCBA.objects.filter(student=student, examination=exam).select_related('overall_level').first()
            if overall:
                score = float(overall.total_weighted_score)
                grade = overall.overall_level.level_code if overall.overall_level else (overall.grade_equivalent or '-')
                position = overall.position
            if StudentCBAAssessment:
                subject_count = StudentCBAAssessment.objects.filter(student=student, examination=exam).values('subject').distinct().count()

        if score is None and exam.curriculum.code == '844' and StudentKCSEGrade:
            marks = StudentKCSEGrade.objects.filter(student=student, examination=exam)
            if marks.exists():
                score = sum(float(mark.raw_mark) for mark in marks) / marks.count()
                subject_count = marks.count()
                grade = 'Pending overall grade'
        elif score is None and exam.curriculum.code == 'CBC' and StudentCBAAssessment:
            assessments = StudentCBAAssessment.objects.filter(student=student, examination=exam).exclude(score__isnull=True)
            if assessments.exists():
                score = sum(float(item.score) for item in assessments) / assessments.count()
                subject_count = assessments.values('subject').distinct().count()
                grade = 'Pending overall level'

        if score is not None:
            history.append({
                'id': exam.id,
                'name': exam.name,
                'code': exam.code,
                'date_label': exam.start_date.strftime('%b %Y'),
                'year': exam.academic_year.year,
                'term': exam.term.name,
                'curriculum': exam.curriculum.code,
                'score': round(score, 1),
                'grade': grade,
                'position': position,
                'subject_count': subject_count,
            })

    return history


def _student_selected_exam(student, exam_id):
    """Return subject-level details for one exam selected from the profile."""
    from examinations.models import Examination
    exam = Examination.objects.filter(id=exam_id).select_related('academic_year', 'term', 'curriculum').first()
    if not exam:
        return None

    subjects = []
    overall = None
    if exam.curriculum.code == '844' and StudentKCSEGrade:
        subjects = [
            {'name': item.subject.name, 'score': float(item.raw_mark), 'grade': item.grade, 'points': float(item.points)}
            for item in StudentKCSEGrade.objects.filter(student=student, examination=exam).select_related('subject').order_by('subject__name')
        ]
        if StudentOverallKCSE:
            result = StudentOverallKCSE.objects.filter(student=student, examination=exam).first()
            if result:
                overall = {'score': float(result.mean_score), 'grade': result.mean_grade, 'position': result.position, 'total': float(result.total_points)}
    elif exam.curriculum.code == 'CBC' and StudentCBAAssessment:
        subjects = [
            {
                'name': item.subject.name,
                'score': float(item.score) if item.score is not None else None,
                'grade': item.overall_level.level_code if item.overall_level else '-',
                'points': item.overall_level.numeric_value if item.overall_level and item.overall_level.numeric_value is not None else '-',
            }
            for item in StudentCBAAssessment.objects.filter(student=student, examination=exam).select_related('subject', 'overall_level').order_by('subject__name')
        ]
        if StudentOverallCBA:
            result = StudentOverallCBA.objects.filter(student=student, examination=exam).select_related('overall_level').first()
            if result:
                overall = {
                    'score': float(result.total_weighted_score),
                    'grade': result.overall_level.level_code if result.overall_level else (result.grade_equivalent or '-'),
                    'position': result.position,
                    'total': float(result.total_score),
                }

    return {'exam': exam, 'subjects': subjects, 'overall': overall}

@login_required
def student_list(request):
    """List all students"""
    students = permitted_student_queryset(request.user).select_related('current_grade_level', 'current_stream', 'academic_year')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(admission_number__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filter by grade level
    grade_level_id = request.GET.get('grade_level')
    if grade_level_id:
        students = students.filter(current_grade_level_id=grade_level_id)
    
    # Filter by stream
    stream_id = request.GET.get('stream')
    if stream_id:
        students = students.filter(current_stream_id=stream_id)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        students = students.filter(status=status)
    
    # Pagination
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    query_params = request.GET.copy()
    query_params.pop('page', None)
    
    context = {
        'students': page_obj,
        'search_query': search_query,
        'grade_levels': GradeLevel.objects.filter(is_active=True),
        'streams': Stream.objects.filter(is_active=True),
        'status_choices': Student.STATUS_CHOICES,
        'selected_grade_level': grade_level_id or '',
        'selected_stream': stream_id or '',
        'selected_status': status or '',
        'students_844': Student.objects.filter(curriculum__code='844').count(),
        'students_cbc': Student.objects.filter(curriculum__code='CBC').count(),
        'pagination_query': query_params.urlencode(),
    }
    return render(request, 'students/list.html', context)


@login_required
def student_detail(request, student_id):
    """View student details"""
    student = get_object_or_404(permitted_student_queryset(request.user), id=student_id)
    exam_history = _student_exam_history(student)
    selected_exam_id = request.GET.get('exam_id')
    if selected_exam_id and not selected_exam_id.isdigit():
        selected_exam_id = None
    selected_exam = _student_selected_exam(student, selected_exam_id) if selected_exam_id else None
    if selected_exam is None and exam_history:
        selected_exam_id = str(exam_history[-1]['id'])
        selected_exam = _student_selected_exam(student, selected_exam_id)

    scores = [item['score'] for item in exam_history]
    average_score = round(sum(scores) / len(scores), 1) if scores else None
    change = round(scores[-1] - scores[0], 1) if len(scores) > 1 else None
    slope = (scores[-1] - scores[0]) / (len(scores) - 1) if len(scores) > 1 else 0
    predicted_score = round(max(0, min(100, scores[-1] + slope)), 1) if scores else None
    trend = 'Improving' if slope > 0.5 else 'Declining' if slope < -0.5 else 'Stable'
    cbc_learning_areas = []
    strengths = []
    improvement_areas = []
    interventions = []
    if selected_exam and StudentCBAAssessment:
        current_exam = selected_exam['exam']
        previous_exam_id = None
        exam_ids = [item['id'] for item in exam_history]
        if current_exam.id in exam_ids:
            index = exam_ids.index(current_exam.id)
            if index > 0:
                previous_exam_id = exam_ids[index - 1]
        current = StudentCBAAssessment.objects.filter(
            student=student, examination=current_exam
        ).select_related('subject', 'overall_level')
        previous = {}
        if previous_exam_id:
            previous = {
                item.subject_id: item.overall_level.level_code
                for item in StudentCBAAssessment.objects.filter(
                    student=student, examination_id=previous_exam_id
                ).select_related('overall_level')
                if item.overall_level
            }
        level_order = {'PL1': 1, 'PL2': 2, 'PL3': 3, 'PL4': 4}
        for item in current:
            current_level = item.overall_level.level_code if item.overall_level else '-'
            previous_level = previous.get(item.subject_id, '-')
            if current_level in {'PL3', 'PL4'}:
                strengths.append(item.subject.name)
            if current_level in {'PL1', 'PL2'}:
                improvement_areas.append(item.subject.name)
                interventions.append(f'Provide targeted support and practical activities in {item.subject.name}.')
            if current_level != '-' and previous_level != '-':
                direction = 'Improving' if level_order[current_level] > level_order[previous_level] else 'Declining' if level_order[current_level] < level_order[previous_level] else 'Stable'
            else:
                direction = 'New'
            cbc_learning_areas.append({
                'name': item.subject.name,
                'current': current_level,
                'previous': previous_level,
                'trend': direction,
                'note': item.teacher_notes,
            })

    context = {
        'student': student,
        'history': student.history.all().order_by('-academic_year'),
        'exam_history': exam_history,
        'selected_exam': selected_exam,
        'selected_exam_id': int(selected_exam_id) if selected_exam_id else None,
        'exam_scores': scores,
        'average_exam_score': average_score,
        'score_change': change,
        'predicted_score': predicted_score,
        'performance_trend': trend,
        'cbc_learning_areas': cbc_learning_areas,
        'strengths': list(dict.fromkeys(strengths)),
        'improvement_areas': list(dict.fromkeys(improvement_areas)),
        'interventions': list(dict.fromkeys(interventions)),
    }
    return render(request, 'students/detail.html', context)


@login_required
def student_create(request):
    """Create a new student — admin and class teachers only."""
    if not is_admin(request.user):
        try:
            teacher = TeacherProfile.objects.get(user=request.user)
            if not ClassTeacher.objects.filter(teacher=teacher, is_active=True).exists():
                messages.error(request, 'Only administrators and class teachers can register learners.')
                return redirect('core:dashboard')
        except TeacherProfile.DoesNotExist:
            messages.error(request, 'You do not have a teacher profile.')
            return redirect('core:dashboard')
    if request.method == 'POST':
        try:
            # Get form data
            admission_number = request.POST.get('admission_number')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            middle_name = request.POST.get('middle_name', '')
            date_of_birth = request.POST.get('date_of_birth')
            gender = request.POST.get('gender')
            nationality = request.POST.get('nationality', 'Kenyan')
            religion = request.POST.get('religion', '')
            
            email = request.POST.get('email', '')
            phone_number = request.POST.get('phone_number', '')
            address = request.POST.get('address', '')
            
            admission_date = request.POST.get('admission_date')
            curriculum_id = request.POST.get('curriculum')
            grade_level_id = request.POST.get('grade_level')
            stream_id = request.POST.get('stream')
            academic_year_id = request.POST.get('academic_year')

            if not can_use_class(request.user, grade_level_id, stream_id, academic_year_id):
                messages.error(request, 'You can only add learners to your assigned class and stream.')
                return redirect('students:create')
            
            guardian_name = request.POST.get('guardian_name', '')
            guardian_phone = request.POST.get('guardian_phone', '')
            guardian_email = request.POST.get('guardian_email', '')
            guardian_relationship = request.POST.get('guardian_relationship', '')
            
            status = request.POST.get('status', 'ACTIVE')
            
            # Validate admission number uniqueness
            if Student.objects.filter(admission_number=admission_number).exists():
                messages.error(request, f'Student with admission number {admission_number} already exists!')
                return redirect('students:create')
            
            # Create student
            student = Student.objects.create(
                admission_number=admission_number,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                date_of_birth=date_of_birth,
                gender=gender,
                nationality=nationality,
                religion=religion,
                email=email,
                phone_number=phone_number,
                address=address,
                admission_date=admission_date,
                curriculum_id=curriculum_id,
                current_grade_level_id=grade_level_id,
                current_stream_id=stream_id,
                academic_year_id=academic_year_id,
                guardian_name=guardian_name,
                guardian_phone=guardian_phone,
                guardian_email=guardian_email,
                guardian_relationship=guardian_relationship,
                status=status,
                created_by=request.user
            )
            
            # Create history entry
            StudentHistory.objects.create(
                student=student,
                academic_year_id=academic_year_id,
                grade_level_id=grade_level_id,
                stream_id=stream_id,
                is_current=True
            )
            
            messages.success(request, f'Student {student.full_name} registered successfully!')
            return redirect('students:detail', student_id=student.id)
            
        except Exception as e:
            messages.error(request, f'Error creating student: {str(e)}')
            return redirect('students:create')
    
    context = {
        'curriculums': Curriculum.objects.filter(is_active=True),
        'grade_levels': GradeLevel.objects.filter(is_active=True),
        'streams': Stream.objects.filter(is_active=True),
        'academic_years': AcademicYear.objects.all().order_by('-year'),
        'gender_choices': Student.GENDER_CHOICES,
        'status_choices': Student.STATUS_CHOICES,
        'today': datetime.now().date(),
    }
    return render(request, 'students/create.html', context)


@login_required
def student_edit(request, student_id):
    """Edit student details — admin and class teachers only."""
    student = get_object_or_404(permitted_student_queryset(request.user), id=student_id)
    
    if not is_admin(request.user) and not can_edit_student(request.user, student):
        messages.error(request, 'Only administrators and class teachers can edit learner details.')
        return redirect('students:detail', student_id=student.id)
    
    if request.method == 'POST':
        admission_number = request.POST.get('admission_number', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()
        gender = request.POST.get('gender', '').strip()
        nationality = request.POST.get('nationality', 'Kenyan').strip()
        religion = request.POST.get('religion', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        admission_date = request.POST.get('admission_date', '').strip()
        curriculum_id = request.POST.get('curriculum', '').strip()
        grade_level_id = request.POST.get('grade_level', '').strip()
        stream_id = request.POST.get('stream', '').strip()
        academic_year_id = request.POST.get('academic_year', '').strip()
        guardian_name = request.POST.get('guardian_name', '').strip()
        guardian_phone = request.POST.get('guardian_phone', '').strip()
        guardian_email = request.POST.get('guardian_email', '').strip()
        guardian_relationship = request.POST.get('guardian_relationship', '').strip()
        status = request.POST.get('status', 'ACTIVE').strip()

        required_fields = {
            'admission number': admission_number,
            'first name': first_name,
            'last name': last_name,
            'date of birth': date_of_birth,
            'gender': gender,
            'admission date': admission_date,
            'curriculum': curriculum_id,
            'grade': grade_level_id,
            'stream': stream_id,
            'academic year': academic_year_id,
        }
        missing = [label for label, value in required_fields.items() if not value]
        if missing:
            messages.error(request, 'Required field(s): ' + ', '.join(missing) + '.')
            return redirect('students:edit', student_id=student.id)
        if status not in dict(Student.STATUS_CHOICES):
            messages.error(request, 'Select a valid student status.')
            return redirect('students:edit', student_id=student.id)

        grade_level, stream, academic_year, curriculum, placement_error = _validate_placement(
            grade_level_id, stream_id, academic_year_id, curriculum_id
        )
        if placement_error:
            messages.error(request, placement_error)
            return redirect('students:edit', student_id=student.id)
        if not can_use_class(request.user, grade_level.id, stream.id, academic_year.id):
            messages.error(request, 'You can only manage learners in your assigned class and stream.')
            return redirect('students:edit', student_id=student.id)
        if Student.objects.filter(admission_number=admission_number).exclude(id=student.id).exists():
            messages.error(request, f'Admission number {admission_number} is already in use.')
            return redirect('students:edit', student_id=student.id)

        try:
            with transaction.atomic():
                _record_current_placement(student, grade_level, stream, academic_year)
                student.admission_number = admission_number
                student.first_name = first_name
                student.last_name = last_name
                student.middle_name = middle_name or None
                student.date_of_birth = date_of_birth
                student.gender = gender
                student.nationality = nationality or 'Kenyan'
                student.religion = religion or None
                student.email = email or None
                student.phone_number = phone_number or None
                student.address = address or None
                student.admission_date = admission_date
                student.curriculum_id = curriculum.id
                student.current_grade_level_id = grade_level.id
                student.current_stream_id = stream.id
                student.academic_year_id = academic_year.id
                student.guardian_name = guardian_name or None
                student.guardian_phone = guardian_phone or None
                student.guardian_email = guardian_email or None
                student.guardian_relationship = guardian_relationship or None
                student.status = status
                student.updated_by = request.user
                student.save()
                _record_current_placement(student, grade_level, stream, academic_year)

            messages.success(request, f'Student {student.full_name} updated successfully!')
            return redirect('students:detail', student_id=student.id)
        except Exception as e:
            messages.error(request, f'Error updating student: {str(e)}')
            return redirect('students:edit', student_id=student.id)
    
    context = {
        'student': student,
        'curriculums': Curriculum.objects.filter(is_active=True),
        'grade_levels': GradeLevel.objects.filter(is_active=True),
        'streams': Stream.objects.filter(is_active=True),
        'academic_years': AcademicYear.objects.all().order_by('-year'),
        'gender_choices': Student.GENDER_CHOICES,
        'status_choices': Student.STATUS_CHOICES,
    }
    return render(request, 'students/edit.html', context)


@login_required
def student_delete(request, student_id):
    """Delete/Deactivate a student — admin and class teachers only."""
    student = get_object_or_404(permitted_student_queryset(request.user), id=student_id)
    
    if not is_admin(request.user) and not can_edit_student(request.user, student):
        messages.error(request, 'Only administrators and class teachers can delete or deactivate learners.')
        return redirect('students:detail', student_id=student.id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            student.delete()
            messages.success(request, f'Student {student.full_name} deleted successfully!')
        elif action == 'deactivate':
            student.is_active = False
            student.status = 'INACTIVE'
            student.save()
            messages.success(request, f'Student {student.full_name} deactivated successfully!')
        
        return redirect('students:list')
    
    context = {'student': student}
    return render(request, 'students/delete.html', context)


@login_required
def student_transfer(request, student_id):
    """Transfer student to another class — admin and class teachers only."""
    student = get_object_or_404(permitted_student_queryset(request.user), id=student_id)
    
    if not is_admin(request.user) and not can_edit_student(request.user, student):
        messages.error(request, 'Only administrators and class teachers can transfer learners.')
        return redirect('students:detail', student_id=student.id)
    
    if request.method == 'POST':
        grade_level, stream, academic_year, _, placement_error = _validate_placement(
            request.POST.get('grade_level'),
            request.POST.get('stream'),
            request.POST.get('academic_year'),
        )
        if placement_error:
            messages.error(request, placement_error)
            return redirect('students:transfer', student_id=student.id)
        if is_admin(request.user) is False and not can_edit_student(request.user, student):
            messages.error(request, 'You can only transfer learners assigned to your class.')
            return redirect('students:transfer', student_id=student.id)
        if is_admin(request.user) and not can_use_class(request.user, grade_level.id, stream.id, academic_year.id):
            messages.error(request, 'You can only transfer learners within your assigned class scope.')
            return redirect('students:transfer', student_id=student.id)

        try:
            with transaction.atomic():
                old_placement = {
                    'grade_level': student.current_grade_level_id,
                    'stream': student.current_stream_id,
                    'academic_year': student.academic_year_id,
                }
                student.current_grade_level_id = grade_level.id
                student.current_stream_id = stream.id
                student.academic_year_id = academic_year.id
                student.updated_by = request.user
                student.save()
                _record_current_placement(student, grade_level, stream, academic_year)
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='Student',
                    object_id=str(student.id),
                    object_repr=str(student),
                    changes={'placement_from': old_placement, 'placement_to': {
                        'grade_level': grade_level.id,
                        'stream': stream.id,
                        'academic_year': academic_year.id,
                    }},
                )

            messages.success(request, f'Student {student.full_name} transferred successfully!')
            return redirect('students:detail', student_id=student.id)
        except Exception as e:
            messages.error(request, f'Error transferring student: {str(e)}')
            return redirect('students:transfer', student_id=student.id)
    
    context = {
        'student': student,
        'grade_levels': GradeLevel.objects.filter(is_active=True),
        'streams': Stream.objects.filter(is_active=True),
        'academic_years': AcademicYear.objects.all().order_by('-year'),
    }
    return render(request, 'students/transfer.html', context)


@login_required
def student_bulk_transfer(request):
    """Transfer multiple students to another class."""
    source_students = Student.objects.none()  # BUG FIX: initialize before conditional assignment
    if not is_admin(request.user):
        messages.error(request, 'Only administrators can perform bulk student transfers.')
        return redirect('students:list')

    if request.method == 'POST':
        source_grade, source_stream, source_year, _, source_error = _validate_placement(
            request.POST.get('source_grade_level'),
            request.POST.get('source_stream'),
            request.POST.get('source_academic_year'),
        )
        destination_grade, destination_stream, destination_year, _, destination_error = _validate_placement(
            request.POST.get('destination_grade_level'),
            request.POST.get('destination_stream'),
            request.POST.get('destination_academic_year'),
        )
        if source_error or destination_error:
            messages.error(request, source_error or destination_error)
            return redirect('students:bulk_transfer')
        if (
            source_grade.id == destination_grade.id
            and source_stream.id == destination_stream.id
            and source_year.id == destination_year.id
        ):
            messages.error(request, 'Select a different destination class.')
            return redirect('students:bulk_transfer')
        if not can_use_class(request.user, source_grade.id, source_stream.id, source_year.id):
            messages.error(request, 'You can only transfer learners from your assigned class scope.')
            return redirect('students:bulk_transfer')
        if not can_use_class(request.user, destination_grade.id, destination_stream.id, destination_year.id):
            messages.error(request, 'You can only transfer learners to your assigned class scope.')
            return redirect('students:bulk_transfer')

        requested_ids = request.POST.getlist('student_ids')
        student_ids = []
        for value in requested_ids:
            student_id = _positive_id(value)
            if student_id and student_id not in student_ids:
                student_ids.append(student_id)
        if not student_ids:
            messages.error(request, 'Select at least one student to transfer.')
            return redirect('students:bulk_transfer')

        source_students = permitted_student_queryset(request.user).filter(
            current_grade_level_id=source_grade.id,
            current_stream_id=source_stream.id,
            academic_year_id=source_year.id,
            id__in=student_ids,
        )
        students = list(source_students.select_related('current_grade_level', 'current_stream', 'academic_year'))
        if len(students) != len(student_ids):
            messages.error(request, 'One or more selected students are not in the selected source class.')
            return redirect('students:bulk_transfer')

        try:
            with transaction.atomic():
                for student in students:
                    student.current_grade_level_id = destination_grade.id
                    student.current_stream_id = destination_stream.id
                    student.academic_year_id = destination_year.id
                    student.updated_by = request.user
                    student.save()
                    _record_current_placement(student, destination_grade, destination_stream, destination_year)

            messages.success(request, f'{len(students)} students transferred successfully!')
            return redirect('students:list')
        except Exception as e:
            messages.error(request, f'Error transferring students: {str(e)}')
            return redirect('students:bulk_transfer')

    source_grade_id = request.GET.get('source_grade_level', '')
    source_stream_id = request.GET.get('source_stream', '')
    source_year_id = request.GET.get('source_academic_year', '')
    source_grade = None
    source_stream = None
    source_year = None
    if source_grade_id and source_stream_id and source_year_id:
        source_grade, source_stream, source_year, _, source_error = _validate_placement(
            source_grade_id, source_stream_id, source_year_id
        )
        if not source_error and can_use_class(request.user, source_grade.id, source_stream.id, source_year.id):
            source_students = permitted_student_queryset(request.user).filter(
                current_grade_level_id=source_grade.id,
                current_stream_id=source_stream.id,
                academic_year_id=source_year.id,
            ).select_related('current_grade_level', 'current_stream', 'academic_year')

    context = {
        'grade_levels': GradeLevel.objects.filter(is_active=True),
        'streams': Stream.objects.filter(is_active=True),
        'academic_years': AcademicYear.objects.all().order_by('-year'),
        'source_grade_level': source_grade_id,
        'source_stream': source_stream_id,
        'source_academic_year': source_year_id,
        'source_grade': source_grade,
        'source_stream_object': source_stream,
        'source_year_object': source_year,
        'source_students': source_students,
    }
    return render(request, 'students/bulk_transfer.html', context)


@login_required
def api_students_search(request):
    """API endpoint for student search (autocomplete)"""
    query = request.GET.get('q', '')
    if len(query) >= 2:
        students = permitted_student_queryset(request.user).filter(
            Q(admission_number__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).values('id', 'admission_number', 'first_name', 'last_name')[:10]
        return JsonResponse({'students': list(students)})
    return JsonResponse({'students': []})



# ============================================================
# PHASE 4: LEARNER PORTFOLIO
# ============================================================
@login_required
def student_portfolio(request, student_id):
    """Display a CBC learner portfolio: assessments grouped by
    LearningArea -> Strand -> SubStrand -> LearningOutcome,
    with evidence, observations, feedback and latest performance level.
    Default: current academic year only. ?all=1 -> full history.
    """
    from grading.models import (
        StudentCBAAssessment, TeacherObservation, LearnerFeedback,
        AssessmentEvidence,
    )
    from school.models import LearningArea, Strand, SubStrand, LearningOutcome

    student = get_object_or_404(
        Student.objects.select_related(
            'curriculum', 'current_grade_level', 'current_stream', 'academic_year'
        ),
        id=student_id,
    )

    show_all = request.GET.get('all') == '1'
    current_year = student.academic_year

    # ---- base queryset ----
    cba_qs = StudentCBAAssessment.objects.filter(student=student).select_related(
        'learning_outcome', 'rubric', 'subject', 'overall_level',
        'learning_outcome__sub_strand__strand__learning_area',
    )
    if not show_all and current_year:
        cba_qs = cba_qs.filter(examination__academic_year=current_year)

    obs_qs = TeacherObservation.objects.filter(student=student).select_related(
        'learning_outcome', 'recorded_by',
    )
    if not show_all and current_year:
        # observations have no direct academic_year FK — use date filter
        from django.utils import timezone
        obs_qs = obs_qs.filter(observed_on__year=current_year.year)

    fb_qs = LearnerFeedback.objects.filter(student=student).select_related(
        'student_assessment', 'given_by',
    )
    if not show_all and current_year:
        fb_qs = fb_qs.filter(given_on__year=current_year.year)

    # ---- build hierarchy ----
    # group by LearningArea -> Strand -> SubStrand -> LearningOutcome
    tree = {}  # {la_id: {strand_id: {substrand_id: {lo_id: {...}}}}}

    for cba in cba_qs:
        lo = cba.learning_outcome
        if not lo:
            continue
        ss = lo.sub_strand
        st = ss.strand
        la = st.learning_area

        tree.setdefault(la.id, {'la': la, 'strands': {}})
        tree[la.id]['strands'].setdefault(st.id, {'st': st, 'substrands': {}})
        tree[la.id]['strands'][st.id]['substrands'].setdefault(ss.id, {'ss': ss, 'outcomes': {}})
        tree[la.id]['strands'][st.id]['substrands'][ss.id]['outcomes'].setdefault(
            lo.id, {'lo': lo, 'assessments': [], 'evidence': [], 'observations': [], 'feedback': []}
        )
        tree[la.id]['strands'][st.id]['substrands'][ss.id]['outcomes'][lo.id]['assessments'].append(cba)

    # ---- attach evidence / observations / feedback ----
    # Evidence: linked via StudentCBAAssessment
    evidence_by_cba = {}
    for ev in AssessmentEvidence.objects.filter(
        student_assessment__in=cba_qs, is_active=True
    ).select_related('learning_outcome'):
        evidence_by_cba.setdefault(ev.student_assessment_id, []).append(ev)

    for la in tree.values():
        for st in la['strands'].values():
            for ss in st['substrands'].values():
                for entry in ss['outcomes'].values():
                    for cba in entry['assessments']:
                        entry['evidence'].extend(evidence_by_cba.get(cba.id, []))

    # Observations: link to LO
    for obs in obs_qs:
        lo = obs.learning_outcome
        if not lo:
            continue
        ss = lo.sub_strand; st = ss.strand; la = st.learning_area
        # find in tree
        try:
            entry = tree[la.id]['strands'][st.id]['substrands'][ss.id]['outcomes'][lo.id]
            entry['observations'].append(obs)
        except KeyError:
            # LO has observations but no CBA — still show it
            tree.setdefault(la.id, {'la': la, 'strands': {}})
            tree[la.id]['strands'].setdefault(st.id, {'st': st, 'substrands': {}})
            tree[la.id]['strands'][st.id]['substrands'].setdefault(ss.id, {'ss': ss, 'outcomes': {}})
            tree[la.id]['strands'][st.id]['substrands'][ss.id]['outcomes'].setdefault(
                lo.id, {'lo': lo, 'assessments': [], 'evidence': [], 'observations': [], 'feedback': []}
            )
            tree[la.id]['strands'][st.id]['substrands'][ss.id]['outcomes'][lo.id]['observations'].append(obs)

    # Feedback: linked to student and optionally to a CBA (via student_assessment.learning_outcome)
    for fb in fb_qs:
        cba = fb.student_assessment
        if cba and cba.learning_outcome:
            lo = cba.learning_outcome
            ss = lo.sub_strand; st = ss.strand; la = st.learning_area
            try:
                tree[la.id]['strands'][st.id]['substrands'][ss.id]['outcomes'][lo.id]['feedback'].append(fb)
            except KeyError:
                pass

    # ---- compute summary stats ----
    all_assessments = list(cba_qs)
    total_assessments = len(all_assessments)
    total_evidence = AssessmentEvidence.objects.filter(
        student_assessment__in=cba_qs, is_active=True
    ).count()
    total_observations = obs_qs.count()
    total_feedback = fb_qs.count()

    # Latest performance level per outcome
    for la in tree.values():
        for st in la['strands'].values():
            for ss in st['substrands'].values():
                for entry in ss['outcomes'].values():
                    latest = None
                    for cba in sorted(entry['assessments'], key=lambda x: x.updated_at, reverse=True):
                        if cba.overall_level:
                            latest = cba.overall_level
                            break
                    entry['latest_level'] = latest

    context = {
        'student': student,
        'tree': tree,
        'show_all': show_all,
        'current_year': current_year,
        'total_assessments': total_assessments,
        'total_evidence': total_evidence,
        'total_observations': total_observations,
        'total_feedback': total_feedback,
        'has_any_data': (total_assessments + total_evidence + total_observations + total_feedback) > 0,
    }
    return render(request, 'students/portfolio.html', context)
