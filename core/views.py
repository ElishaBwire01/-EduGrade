from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth import get_user_model
from students.models import Student
from teachers.models import TeacherProfile
from teachers.models import ClassTeacher
from examinations.models import Examination
from marks.models import MarkEntry
from core.access import is_admin, class_teacher_assignments
from core.models import Notification

User = get_user_model()

try:
    from grading.models import StudentKCSEGrade, StudentCBAAssessment, StudentOverallCBA
except ImportError:
    StudentKCSEGrade = None
    StudentCBAAssessment = None
    StudentOverallCBA = None

@login_required
def dashboard(request):
    is_admin_user = is_admin(request.user)
    pending_requests = 0
    
    if is_admin_user:
        scoped_students = Student.objects.all()
        total_students = scoped_students.count()
        students_844 = scoped_students.filter(curriculum__code='844').count()
        students_cbc = scoped_students.filter(curriculum__code='CBC').count()
        show_request_button = False
        teacher_assignments = None
        teacher_profile = None
    else:
        teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
        # Get teacher's approved assignments
        try:
            teacher_assignments = teacher_profile.assignments.filter(status='APPROVED').select_related('subject', 'grade_level', 'stream', 'academic_year')
        except Exception:
            teacher_assignments = None
        
        # Get students from approved assignments - match grade+stream pairs
        scoped_students = Student.objects.none()
        assignment_pairs = teacher_assignments.values_list('grade_level', 'stream').distinct()
        if assignment_pairs:
            from django.db.models import Q
            q_objects = Q()
            for grade_id, stream_id in assignment_pairs:
                q_objects |= Q(current_grade_level_id=grade_id, current_stream_id=stream_id)
            scoped_students = Student.objects.filter(q_objects, is_active=True).distinct()
        
        total_students = scoped_students.count()
        students_844 = scoped_students.filter(curriculum__code='844').count()
        students_cbc = scoped_students.filter(curriculum__code='CBC').count()
        show_request_button = teacher_assignments.count() == 0 and teacher_profile is not None
        pending_requests = teacher_profile.requests.filter(status='PENDING').count() if teacher_profile else 0
    
    total_teachers = TeacherProfile.objects.count()
    active_teachers = TeacherProfile.objects.filter(status='ACTIVE', is_active=True).count()
    
    total_exams = Examination.objects.count()
    exams_844 = Examination.objects.filter(curriculum__code='844').count()
    exams_cbc = Examination.objects.filter(curriculum__code='CBC').count()
    
    total_marks = MarkEntry.objects.count()
    kcse_grades = StudentKCSEGrade.objects.count() if StudentKCSEGrade else 0
    cbc_assessments = StudentCBAAssessment.objects.count() if StudentCBAAssessment else 0
    
    recent_students = scoped_students.order_by('-created_at')[:5]
    recent_exams = Examination.objects.all().order_by('-created_at')[:5]

    cbc_analysis = build_cbc_analysis(request)
    
    context = {
        'total_students': total_students,
        'students_844': students_844,
        'students_cbc': students_cbc,
        'total_teachers': total_teachers,
        'active_teachers': active_teachers,
        'total_exams': total_exams,
        'exams_844': exams_844,
        'exams_cbc': exams_cbc,
        'total_marks': total_marks,
        'kcse_grades': kcse_grades,
        'cbc_assessments': cbc_assessments,
        'recent_students': recent_students,
        'recent_exams': recent_exams,
        'unread_notifications': unread_notification_count(request.user),
        'show_request_button': show_request_button,
        'teacher_profile': teacher_profile,
        'teacher_assignments': teacher_assignments,
        'pending_requests': pending_requests,
        **cbc_analysis,
    }
    return render(request, 'core/dashboard.html', context)


def build_cbc_analysis(request):
    """Build role-scoped CBC analytics for the latest assessed examination."""
    empty = {
        'cbc_scope_label': 'School-wide CBC overview',
        'cbc_scope_type': 'school',
        'cbc_exam': None,
        'cbc_total_learners': 0,
        'cbc_assessed_learners': 0,
        'cbc_level_distribution': [],
        'cbc_top_learners': [],
        'cbc_best_boy': None,
        'cbc_best_girl': None,
        'cbc_learning_areas': [],
        'cbc_intervention_count': 0,
        'cbc_insight': 'CBC analytics will appear after assessment results are recorded.',
    }
    if not StudentOverallCBA or not StudentCBAAssessment:
        return empty

    from students.models import Student
    from teachers.models import TeacherProfile, ClassTeacher, TeacherAssignment

    students = Student.objects.filter(is_active=True)
    scope_label = 'School-wide CBC overview'
    scope_type = 'school'
    if not is_admin(request.user):
        teacher = TeacherProfile.objects.filter(user=request.user).first()
        if not teacher:
            students = students.none()
            scope_type = 'restricted'
            scope_label = 'No teacher profile found'
        else:
            scope = Q()

            # Class teacher scope (grade + stream + academic year)
            for assignment in ClassTeacher.objects.filter(
                teacher=teacher, is_active=True
            ).select_related('grade_level', 'stream').order_by('-academic_year__year'):
                scope |= Q(
                    current_grade_level=assignment.grade_level,
                    current_stream=assignment.stream,
                    academic_year=assignment.academic_year,
                )

            # Subject teacher scope (grade + stream + academic year via assignments)
            for assignment in teacher.assignments.filter(
                status='APPROVED'
            ).select_related('grade_level', 'stream', 'academic_year'):
                scope |= Q(
                    current_grade_level=assignment.grade_level,
                    current_stream=assignment.stream,
                    academic_year=assignment.academic_year,
                )

            if scope:
                students = students.filter(scope).distinct()
                scope_type = 'class'
                scope_label = 'Your assigned classes CBC overview'
            else:
                students = students.none()
                scope_type = 'restricted'
                scope_label = 'No assigned class CBC overview'

    latest_exam = Examination.objects.filter(
        curriculum__code='CBC',
        overall_cba__student__in=students,
    ).distinct().order_by('-start_date', '-id').first()
    if not latest_exam:
        result = empty.copy()
        result['cbc_scope_label'] = scope_label
        result['cbc_scope_type'] = scope_type
        result['cbc_total_learners'] = students.count()
        return result

    overall_results = list(StudentOverallCBA.objects.filter(
        examination=latest_exam,
        student__in=students,
    ).select_related('student', 'overall_level').order_by('-total_weighted_score'))
    levels = {'PL4': 'Exceeding Expectations', 'PL3': 'Meeting Expectations', 'PL2': 'Approaching Expectations', 'PL1': 'Below Expectations'}
    counts = {code: 0 for code in levels}
    for result in overall_results:
        if result.overall_level:
            counts[result.overall_level.level_code] = counts.get(result.overall_level.level_code, 0) + 1

    top_learners = []
    for position, result in enumerate(overall_results[:3], 1):
        top_learners.append({
            'position': position,
            'student': result.student,
            'score': float(result.total_weighted_score),
            'level': result.overall_level.level_code if result.overall_level else '-',
        })

    boys = [item for item in overall_results if item.student.gender == 'M']
    girls = [item for item in overall_results if item.student.gender == 'F']

    assessments = StudentCBAAssessment.objects.filter(
        examination=latest_exam,
        student__in=students,
    ).select_related('subject', 'overall_level')
    area_data = {}
    for assessment in assessments:
        entry = area_data.setdefault(assessment.subject_id, {'name': assessment.subject.name, 'total': 0, 'count': 0, 'levels': {code: 0 for code in levels}})
        if assessment.overall_level:
            entry['levels'][assessment.overall_level.level_code] += 1
        if assessment.score is not None:
            entry['total'] += float(assessment.score)
            entry['count'] += 1

    learning_areas = []
    for entry in area_data.values():
        level_total = sum(entry['levels'].values())
        lower_levels = entry['levels']['PL1'] + entry['levels']['PL2']
        entry['average'] = round(entry['total'] / entry['count'], 1) if entry['count'] else None
        entry['support_rate'] = round(lower_levels / level_total * 100, 1) if level_total else 0
        learning_areas.append(entry)
    learning_areas.sort(key=lambda item: (item['support_rate'], -(item['average'] or 0)))

    intervention_count = sum(1 for result in overall_results if result.overall_level and result.overall_level.level_code in {'PL1', 'PL2'})
    best_area = learning_areas[0]['name'] if learning_areas else None
    weakest_area = learning_areas[-1]['name'] if learning_areas else None
    insight = 'No learning-area insight is available yet.'
    if best_area and weakest_area:
        insight = f'{best_area} is currently the strongest learning area, while {weakest_area} has the greatest need for targeted support.'

    return {
        'cbc_scope_label': scope_label,
        'cbc_scope_type': scope_type,
        'cbc_exam': latest_exam,
        'cbc_total_learners': students.count(),
        'cbc_assessed_learners': len(overall_results),
        'cbc_level_distribution': [{'code': code, 'name': name, 'count': counts[code]} for code, name in levels.items()],
        'cbc_top_learners': top_learners,
        'cbc_best_boy': {'student': boys[0].student, 'score': float(boys[0].total_weighted_score), 'level': boys[0].overall_level.level_code if boys[0].overall_level else '-'} if boys else None,
        'cbc_best_girl': {'student': girls[0].student, 'score': float(girls[0].total_weighted_score), 'level': girls[0].overall_level.level_code if girls[0].overall_level else '-'} if girls else None,
        'cbc_learning_areas': learning_areas,
        'cbc_intervention_count': intervention_count,
        'cbc_insight': insight,
    }

class HomeView(TemplateView):
    template_name = 'core/home.html'


# ========================================================
# Notification views
# ========================================================

@login_required
def notifications_list(request):
    """Display all notifications for the current user."""
    notifications = request.user.notifications.all()[:50]
    return render(request, 'core/notifications.html', {'notifications': notifications})


@login_required
def notification_mark_read(request, notification_id):
    """Mark a single notification as read."""
    notification = get_object_or_404(
        Notification, pk=notification_id, recipient=request.user
    )
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'unread_count': unread_notification_count(request.user)})
    return redirect(notification.url or 'core:notifications')


@login_required
def notification_mark_all_read(request):
    """Mark all notifications as read."""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'unread_count': 0})
    messages.success(request, 'All notifications marked as read.')
    return redirect('core:notifications')


def unread_notification_count(user):
    """Return the count of unread notifications for a user."""
    if not user.is_authenticated:
        return 0
    return user.notifications.filter(is_read=False).count()

