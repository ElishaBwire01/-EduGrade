
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse, FileResponse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Avg, Max, Min, Count, Sum
from django.contrib.auth import get_user_model
from .models import ReportTemplate, GeneratedReport, ReportComment
from .generator import ReportGenerator
from students.models import Student
from examinations.models import Examination
from school.models import AcademicYear, Term, GradeLevel, Stream
from teachers.models import TeacherProfile
from marks.models import MarkEntry
from core.access import is_admin, permitted_student_queryset, can_use_class, class_teacher_assignments

User = get_user_model()

# Import grading models with error handling
try:
    from grading.models import StudentKCSEGrade, StudentOverallKCSE, StudentCBAAssessment, StudentOverallCBA
except ImportError:
    StudentKCSEGrade = None
    StudentOverallKCSE = None
    StudentCBAAssessment = None
    StudentOverallCBA = None

@login_required
def report_dashboard(request):
    context = {
        'student_reports': GeneratedReport.objects.filter(report_type='STUDENT'),
        'class_reports': GeneratedReport.objects.filter(report_type='CLASS'),
        'school_reports': GeneratedReport.objects.filter(report_type='SCHOOL'),
        'total_reports': GeneratedReport.objects.count(),
        'published_reports': GeneratedReport.objects.filter(status='PUBLISHED').count(),
    }
    return render(request, 'reports/dashboard.html', context)

@login_required
def report_list(request):
    reports = GeneratedReport.objects.select_related('student', 'examination', 'academic_year', 'term', 'generated_by').all()
    
    status_filter = request.GET.get('status')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    report_type_filter = request.GET.get('report_type')
    if report_type_filter:
        reports = reports.filter(report_type=report_type_filter)
    
    context = {
        'reports': reports,
        'status_choices': GeneratedReport.STATUS_CHOICES,
        'report_type_choices': GeneratedReport.REPORT_TYPES,
    }
    return render(request, 'reports/list.html', context)

@login_required
def generate_student_report(request, student_id):
    student = get_object_or_404(permitted_student_queryset(request.user), id=student_id)
    examination_id = request.GET.get('exam_id')
    
    if not examination_id:
        messages.error(request, 'Please select an examination!')
        return redirect('students:detail', student_id=student.id)
    
    examination = get_object_or_404(Examination, id=examination_id)
    
    report_data = {
        'title': f"Student Report - {student.full_name}",
        'student': {
            'name': student.full_name,
            'admission': student.admission_number,
            'grade': student.current_grade_level.name if student.current_grade_level else '-',
            'stream': student.current_stream.name if student.current_stream else '-',
        },
        'examination': examination.name,
        'subject_performances': [],
        'overall': {},
        'strengths': [],
        'weaknesses': [],
    }
    
    if StudentKCSEGrade and examination.curriculum.code == '844':
        kcse_grades = StudentKCSEGrade.objects.filter(student=student, examination=examination).select_related('subject')
        for grade in kcse_grades:
            report_data['subject_performances'].append({
                'subject_name': grade.subject.name,
                'score': float(grade.raw_mark),
                'grade': grade.grade,
                'points': float(grade.points),
            })
        if StudentOverallKCSE:
            overall = StudentOverallKCSE.objects.filter(student=student, examination=examination).first()
            if overall:
                report_data['overall'] = {
                    'total_score': float(overall.total_points),
                    'average_score': float(overall.mean_score),
                    'grade': overall.mean_grade,
                    'position': overall.position,
                }
    
    elif StudentCBAAssessment and examination.curriculum.code == 'CBC':
        cbc_assessments = StudentCBAAssessment.objects.filter(student=student, examination=examination).select_related('subject')
        for assessment in cbc_assessments:
            report_data['subject_performances'].append({
                'subject_name': assessment.subject.name,
                'score': float(assessment.score) if assessment.score else 0,
                'grade': assessment.overall_level.level_code if assessment.overall_level else '-',
                'points': assessment.overall_level.numeric_value if assessment.overall_level else '-',
            })
        if StudentOverallCBA:
            overall = StudentOverallCBA.objects.filter(student=student, examination=examination).first()
            if overall:
                report_data['overall'] = {
                    'total_score': float(overall.total_score),
                    'average_score': float(overall.total_weighted_score),
                    'grade': overall.overall_level.level_code if overall.overall_level else '-',
                    'position': overall.position,
                }
    
    if not report_data['subject_performances']:
        messages.error(request, 'No performance data found for this student!')
        return redirect('students:detail', student_id=student.id)
    
    generator = ReportGenerator('STUDENT', report_data)
    
    if request.GET.get('format') == 'word':
        word_buffer = generator.generate_word_report(report_data, 'student')
        response = HttpResponse(word_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=student_report_{student.admission_number}_{examination.code}.docx'
        return response
    else:
        pdf_buffer = generator.generate_student_report_pdf(student, report_data, examination)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=student_report_{student.admission_number}_{examination.code}.pdf'
        return response

@login_required
def generate_class_report(request):
    if request.method == 'POST':
        examination_id = request.POST.get('examination')
        grade_level_id = request.POST.get('grade_level')
        stream_id = request.POST.get('stream')
        
        if not all([examination_id, grade_level_id, stream_id]):
            messages.error(request, 'Please select all required fields!')
            return redirect('reports:class_report')

        if not can_use_class(request.user, grade_level_id, stream_id):
            messages.error(request, 'You can only generate reports for your assigned class and stream.')
            return redirect('reports:class_report')
        
        examination = get_object_or_404(Examination, id=examination_id)
        grade_level = get_object_or_404(GradeLevel, id=grade_level_id)
        stream = get_object_or_404(Stream, id=stream_id)
        
        students = Student.objects.filter(current_grade_level=grade_level, current_stream=stream, is_active=True)
        
        if not students.exists():
            messages.error(request, 'No students found in this class!')
            return redirect('reports:class_report')
        
        student_data = []
        total_score = 0
        highest_score = 0
        lowest_score = 100
        
        for student in students:
            student_info = {'name': student.full_name, 'admission': student.admission_number, 'score': 0, 'grade': '-'}
            
            if StudentOverallKCSE and examination.curriculum.code == '844':
                overall = StudentOverallKCSE.objects.filter(student=student, examination=examination).first()
                if overall:
                    student_info['score'] = float(overall.mean_score)
                    student_info['grade'] = overall.mean_grade
            elif StudentOverallCBA and examination.curriculum.code == 'CBC':
                overall = StudentOverallCBA.objects.filter(student=student, examination=examination).first()
                if overall:
                    student_info['score'] = float(overall.total_weighted_score)
                    student_info['grade'] = overall.overall_level.level_code if overall.overall_level else '-'
            
            student_data.append(student_info)
            if student_info['score'] > 0:
                total_score += student_info['score']
                if student_info['score'] > highest_score:
                    highest_score = student_info['score']
                if student_info['score'] < lowest_score:
                    lowest_score = student_info['score']
        
        total_students = len(student_data)
        avg_score = total_score / total_students if total_students > 0 else 0
        pass_count = sum(1 for s in student_data if s['score'] >= 40)
        pass_rate = (pass_count / total_students * 100) if total_students > 0 else 0
        top_students = sorted(student_data, key=lambda x: x['score'], reverse=True)[:10]
        
        report_data = {
            'title': f"Class Report - {grade_level.name} {stream.name}",
            'class_name': f"{grade_level.name} {stream.name}",
            'exam_name': examination.name,
            'statistics': {
                'total_students': total_students,
                'average_score': avg_score,
                'highest_score': highest_score,
                'lowest_score': lowest_score if lowest_score < 100 else 0,
                'pass_rate': pass_rate,
                'pass_count': pass_count,
            },
            'top_students': top_students,
        }
        
        generator = ReportGenerator('CLASS', report_data)
        pdf_buffer = generator.generate_class_report_pdf(report_data)
        
        GeneratedReport.objects.create(
            report_type='CLASS',
            title=f"Class Report - {grade_level.name} {stream.name}",
            examination=examination,
            academic_year=examination.academic_year,
            term=examination.term,
            status='GENERATED',
            generated_by=request.user
        )
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=class_report_{grade_level.name}_{stream.name}_{examination.code}.pdf'
        return response
    
    context = {
        'examinations': Examination.objects.filter(status__in=['LOCKED', 'PUBLISHED']),
        'grade_levels': GradeLevel.objects.filter(is_active=True) if is_admin(request.user) else GradeLevel.objects.filter(id__in=class_teacher_assignments(request.user).values('grade_level_id')),
        'streams': Stream.objects.filter(is_active=True) if is_admin(request.user) else Stream.objects.filter(id__in=class_teacher_assignments(request.user).values('stream_id')),
    }
    return render(request, 'reports/class_report.html', context)

@login_required
def school_report(request):
    "Generate school-wide performance report"
    if not is_admin(request.user):
        messages.error(request, 'Only administrators can view the school-wide report.')
        return redirect('reports:dashboard')
    import django.db.models as models
    
    total_students = Student.objects.count()
    active_students = Student.objects.filter(is_active=True).count()
    
    grade_stats = []
    for grade in GradeLevel.objects.filter(is_active=True):
        student_count = Student.objects.filter(current_grade_level=grade, is_active=True).count()
        if student_count > 0:
            grade_stats.append({
                'name': grade.name,
                'students': student_count,
                'curriculum': grade.curriculum.name
            })
    
    subject_averages = []
    if StudentKCSEGrade:
        kcse_subject_performance = {}
        kcse_grades = StudentKCSEGrade.objects.select_related('subject')
        for grade in kcse_grades:
            subject_name = grade.subject.name
            if subject_name not in kcse_subject_performance:
                kcse_subject_performance[subject_name] = {'total': 0, 'count': 0}
            kcse_subject_performance[subject_name]['total'] += float(grade.raw_mark)
            kcse_subject_performance[subject_name]['count'] += 1
        
        for subject, data in kcse_subject_performance.items():
            if data['count'] > 0:
                subject_averages.append({
                    'name': subject,
                    'average': data['total'] / data['count']
                })
        subject_averages = sorted(subject_averages, key=lambda x: x['average'], reverse=True)
    
    avg_kcse = 0
    pass_rate = 0
    if StudentOverallKCSE:
        overall_kcse = StudentOverallKCSE.objects.all()
        if overall_kcse.exists():
            avg_kcse = overall_kcse.aggregate(models.Avg('mean_score'))['mean_score__avg'] or 0
            pass_rate = overall_kcse.filter(mean_score__gte=40).count() / overall_kcse.count() * 100 if overall_kcse.count() > 0 else 0
    
    avg_cbc = 0
    if StudentOverallCBA:
        cbc_overall = StudentOverallCBA.objects.all()
        if cbc_overall.exists():
            avg_cbc = cbc_overall.aggregate(models.Avg('total_score'))['total_score__avg'] or 0
    
    context = {
        'total_students': total_students,
        'active_students': active_students,
        'grade_stats': grade_stats,
        'subject_averages': subject_averages[:10],
        'avg_kcse': avg_kcse,
        'pass_rate': pass_rate,
        'avg_cbc': avg_cbc,
        'total_teachers': TeacherProfile.objects.count(),
        'total_exams': Examination.objects.count(),
        'total_marks': MarkEntry.objects.count(),
    }
    return render(request, 'reports/school_report.html', context)

@login_required
def report_detail(request, report_id):
    report = get_object_or_404(GeneratedReport, id=report_id)
    comments = report.comments.all()
    
    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        if comment_text:
            ReportComment.objects.create(report=report, user=request.user, comment=comment_text)
            messages.success(request, 'Comment added successfully!')
            return redirect('reports:detail', report_id=report.id)
    
    context = {'report': report, 'comments': comments}
    return render(request, 'reports/detail.html', context)

@login_required
def generate_word_report(request, report_id):
    "Generate Word version of an existing report"
    report = get_object_or_404(GeneratedReport, id=report_id)
    
    if report.report_type == 'STUDENT' and report.student:
        student = report.student
        examination = report.examination
        
        report_data = {
            'title': f"Student Report - {student.full_name}",
            'student': {
                'name': student.full_name,
                'admission': student.admission_number,
                'grade': student.current_grade_level.name if student.current_grade_level else '-',
                'stream': student.current_stream.name if student.current_stream else '-',
            },
            'subject_performances': [],
            'overall': {},
            'strengths': [],
            'weaknesses': [],
        }
        
        if StudentKCSEGrade and examination and examination.curriculum.code == '844':
            kcse_grades = StudentKCSEGrade.objects.filter(student=student, examination=examination).select_related('subject')
            for grade in kcse_grades:
                report_data['subject_performances'].append({
                    'subject_name': grade.subject.name,
                    'score': float(grade.raw_mark),
                    'grade': grade.grade,
                    'points': float(grade.points),
                })
            if StudentOverallKCSE:
                overall = StudentOverallKCSE.objects.filter(student=student, examination=examination).first()
                if overall:
                    report_data['overall'] = {
                        'total_score': float(overall.total_points),
                        'average_score': float(overall.mean_score),
                        'grade': overall.mean_grade,
                        'position': overall.position,
                    }
        
        elif StudentCBAAssessment and examination and examination.curriculum.code == 'CBC':
            cbc_assessments = StudentCBAAssessment.objects.filter(student=student, examination=examination).select_related('subject')
            for assessment in cbc_assessments:
                report_data['subject_performances'].append({
                    'subject_name': assessment.subject.name,
                    'score': float(assessment.score) if assessment.score else 0,
                    'grade': assessment.overall_level.level_code if assessment.overall_level else '-',
                    'points': assessment.overall_level.numeric_value if assessment.overall_level else '-',
                })
            if StudentOverallCBA:
                overall = StudentOverallCBA.objects.filter(student=student, examination=examination).first()
                if overall:
                    report_data['overall'] = {
                        'total_score': float(overall.total_score),
                        'average_score': float(overall.total_weighted_score),
                        'grade': overall.overall_level.level_code if overall.overall_level else '-',
                        'position': overall.position,
                    }
        
        generator = ReportGenerator('STUDENT', report_data)
        word_buffer = generator.generate_word_report(report_data, 'student')
        
        response = HttpResponse(word_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=student_report_{student.admission_number}.docx'
        return response
    
    messages.error(request, 'Word report generation not available for this report type!')
    return redirect('reports:dashboard')

@login_required
def report_approve(request, report_id):
    report = get_object_or_404(GeneratedReport, id=report_id)
    if request.method == 'POST':
        report.status = 'APPROVED'
        report.approved_by = request.user
        report.approved_at = timezone.now()
        report.save()
        messages.success(request, 'Report approved successfully!')
    return redirect('reports:detail', report_id=report.id)

@login_required
def report_publish(request, report_id):
    report = get_object_or_404(GeneratedReport, id=report_id)
    if request.method == 'POST':
        report.status = 'PUBLISHED'
        report.published_at = timezone.now()
        report.save()
        messages.success(request, 'Report published successfully!')
    return redirect('reports:detail', report_id=report.id)


