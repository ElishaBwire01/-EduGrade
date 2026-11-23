from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Max, Min, Count, Q
from django.core.paginator import Paginator
from .models import AssessmentScheme, KCSEGradeRule, PerformanceLevel, StudentKCSEGrade, StudentCBAAssessment
from .kcse_engine import KCSEEngine
from .cbc_engine import CBCEngine
from examinations.models import Examination
from school.models import GradeLevel, Stream, Curriculum
from students.models import Student

@login_required
def process_marks(request):
    """Process marks using the appropriate engine based on curriculum"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can process marks!')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        examination_id = request.POST.get('examination')
        grade_level_id = request.POST.get('grade_level')
        stream_id = request.POST.get('stream')
        
        if not all([examination_id, grade_level_id, stream_id]):
            messages.error(request, 'Please select examination, grade, and stream.')
            return redirect('grading:process')
        
        examination = get_object_or_404(Examination, id=examination_id)
        grade_level = get_object_or_404(GradeLevel, id=grade_level_id)
        stream = get_object_or_404(Stream, id=stream_id)
        
        # Check if marks exist
        from marks.models import MarkEntry
        has_marks = MarkEntry.objects.filter(
            examination=examination,
            grade_level=grade_level,
            stream=stream
        ).exists()
        
        if not has_marks:
            messages.error(request, 'No marks found for this examination!')
            return redirect('grading:process')
        
        # Process based on curriculum
        try:
            if examination.curriculum.code == '844':
                # Use KCSE engine
                engine = KCSEEngine(examination, grade_level, stream)
                results = engine.process_class()
                messages.success(request, f'KCSE marks processed for {len(results)} students!')
                
            elif examination.curriculum.code == 'CBC':
                # Use CBC engine
                engine = CBCEngine(examination, grade_level, stream)
                results = engine.process_class()
                messages.success(request, f'CBC assessments processed for {len(results)} students!')
            else:
                messages.error(request, 'Unknown curriculum!')
                return redirect('grading:process')
            
            # Store exam ID for report generation
            request.session['exam_id'] = examination.id
            return redirect('grading:class_report')
            
        except Exception as e:
            messages.error(request, f'Error processing marks: {str(e)}')
            return redirect('grading:process')
    
    # GET request - show form
    context = {
        'examinations': Examination.objects.filter(status__in=['DRAFT', 'ACTIVE', 'LOCKED', 'PUBLISHED']).order_by('-created_at'),
        'grade_levels': GradeLevel.objects.filter(is_active=True),
        'streams': Stream.objects.filter(is_active=True),
    }
    return render(request, 'grading/process.html', context)


@login_required
def class_report(request):
    """View class performance report with curriculum-specific display"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can view class reports!')
        return redirect('core:dashboard')
    
    exam_id = request.GET.get('exam_id') or request.session.get('exam_id')
    
    if not exam_id:
        messages.warning(request, 'Please process marks first!')
        return redirect('grading:process')
    
    examination = get_object_or_404(Examination, id=exam_id)
    
    # Determine curriculum and get appropriate data
    if examination.curriculum.code == '844':
        return _kcse_class_report(request, examination)
    elif examination.curriculum.code == 'CBC':
        return _cbc_class_report(request, examination)
    else:
        messages.error(request, 'Unknown curriculum!')
        return redirect('grading:process')


def _kcse_class_report(request, examination):
    """Generate KCSE class report"""
    from .models import StudentOverallKCSE
    
    overalls = StudentOverallKCSE.objects.filter(
        examination=examination
    ).select_related('student')
    
    if not overalls.exists():
        messages.warning(request, 'No KCSE results found! Please process marks first.')
        return redirect('grading:process')
    
    # Calculate statistics
    total_students = overalls.count()
    avg_score = overalls.aggregate(Avg('mean_score'))['mean_score__avg'] or 0
    highest_score = overalls.aggregate(Max('mean_score'))['mean_score__max'] or 0
    lowest_score = overalls.aggregate(Min('mean_score'))['mean_score__min'] or 0
    
    pass_count = overalls.filter(mean_score__gte=40).count()
    pass_rate = (pass_count / total_students * 100) if total_students > 0 else 0
    
    # Grade distribution
    grade_distribution = {}
    for overall in overalls:
        grade = overall.mean_grade or 'N/A'
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
    
    # Subject performance
    subject_performances = StudentKCSEGrade.objects.filter(
        examination=examination
    ).values('subject__name').annotate(
        avg_score=Avg('raw_mark'),
        max_score=Max('raw_mark'),
        min_score=Min('raw_mark'),
    ).order_by('-avg_score')

    top_students = overalls.order_by('-mean_score')[:10].select_related('student')

    context = {
        'examination': examination,
        'curriculum_type': 'KCSE',
        'overalls': overalls,
        'total_students': total_students,
        'avg_score': avg_score,
        'highest_score': highest_score,
        'lowest_score': lowest_score,
        'pass_count': pass_count,
        'pass_rate': pass_rate,
        'grade_distribution': grade_distribution.items(),
        'subject_performances': subject_performances,
        'top_students': top_students,
        'is_kcse': True,
    }
    return render(request, 'grading/class_report.html', context)


def _cbc_class_report(request, examination):
    """Generate CBC class report"""
    from .models import StudentOverallCBA, PerformanceLevel
    
    overalls = StudentOverallCBA.objects.filter(
        examination=examination
    ).select_related('student', 'overall_level')
    
    if not overalls.exists():
        messages.warning(request, 'No CBC results found! Please process marks first.')
        return redirect('grading:process')
    
    # Calculate statistics
    total_students = overalls.count()
    avg_score = overalls.aggregate(Avg('total_score'))['total_score__avg'] or 0
    highest_score = overalls.aggregate(Max('total_score'))['total_score__max'] or 0
    lowest_score = overalls.aggregate(Min('total_score'))['total_score__min'] or 0
    
    # Level distribution
    level_distribution = {}
    for overall in overalls:
        level_code = overall.overall_level.level_code if overall.overall_level else 'N/A'
        level_distribution[level_code] = level_distribution.get(level_code, 0) + 1
    
    # Subject performance
    subject_performances = StudentCBAAssessment.objects.filter(
        examination=examination
    ).values('subject__name').annotate(
        avg_score=Avg('score'),
        max_score=Max('score'),
        min_score=Min('score'),
    ).order_by('-avg_score')

    top_students = overalls.order_by('-total_score')[:10].select_related('student')

    context = {
        'examination': examination,
        'curriculum_type': 'CBC',
        'overalls': overalls,
        'total_students': total_students,
        'avg_score': avg_score,
        'highest_score': highest_score,
        'lowest_score': lowest_score,
        'level_distribution': level_distribution.items(),
        'subject_performances': subject_performances,
        'top_students': top_students,
        'is_cbc': True,
    }
    return render(request, 'grading/class_report.html', context)


@login_required
def student_report(request, student_id):
    """View individual student report"""
    student = get_object_or_404(Student, id=student_id)
    examination_id = request.GET.get('exam_id')
    
    if examination_id:
        examination = get_object_or_404(Examination, id=examination_id)
    else:
        examination = None
    
    if examination and examination.curriculum.code == '844':
        return _kcse_student_report(request, student, examination)
    elif examination and examination.curriculum.code == 'CBC':
        return _cbc_student_report(request, student, examination)
    else:
        messages.warning(request, 'Please select an examination with a valid curriculum.')
        return redirect('students:detail', student_id=student.id)


def _kcse_student_report(request, student, examination):
    """Generate KCSE student report"""
    from .models import StudentKCSEGrade, StudentOverallKCSE
    
    grades = StudentKCSEGrade.objects.filter(
        student=student,
        examination=examination
    ).select_related('subject')
    
    overall = StudentOverallKCSE.objects.filter(
        student=student,
        examination=examination
    ).first()
    
    context = {
        'student': student,
        'examination': examination,
        'grades': grades,
        'overall': overall,
        'is_kcse': True,
    }
    return render(request, 'grading/student_report.html', context)


def _cbc_student_report(request, student, examination):
    """Generate CBC student report"""
    from .models import StudentCBAAssessment, StudentOverallCBA
    
    assessments = StudentCBAAssessment.objects.filter(
        student=student,
        examination=examination
    ).select_related('rubric', 'subject')
    
    overall = StudentOverallCBA.objects.filter(
        student=student,
        examination=examination
    ).first()
    
    context = {
        'student': student,
        'examination': examination,
        'assessments': assessments,
        'overall': overall,
        'is_cbc': True,
    }
    return render(request, 'grading/student_report.html', context)


@login_required
def grading_system_list(request):
    """List grading systems"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can manage grading systems!')
        return redirect('core:dashboard')
    
    schemes = AssessmentScheme.objects.all()
    
    context = {'schemes': schemes}
    return render(request, 'grading/systems.html', context)
