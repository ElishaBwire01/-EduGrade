import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')
import django
django.setup()

# Create school report view
school_report_content = """
@login_required
def school_report(request):
    \"\"\"Generate school-wide performance report\"\"\"
    # Get all students
    total_students = Student.objects.count()
    active_students = Student.objects.filter(is_active=True).count()
    
    # Get statistics by grade
    grade_stats = []
    for grade in GradeLevel.objects.filter(is_active=True):
        student_count = Student.objects.filter(current_grade_level=grade, is_active=True).count()
        if student_count > 0:
            grade_stats.append({
                'name': grade.name,
                'students': student_count,
                'curriculum': grade.curriculum.name
            })
    
    # Get subject performance (KCSE)
    kcse_subject_performance = {}
    kcse_grades = StudentKCSEGrade.objects.select_related('subject')
    for grade in kcse_grades:
        subject_name = grade.subject.name
        if subject_name not in kcse_subject_performance:
            kcse_subject_performance[subject_name] = {'total': 0, 'count': 0}
        kcse_subject_performance[subject_name]['total'] += float(grade.raw_mark)
        kcse_subject_performance[subject_name]['count'] += 1
    
    subject_averages = []
    for subject, data in kcse_subject_performance.items():
        if data['count'] > 0:
            subject_averages.append({
                'name': subject,
                'average': data['total'] / data['count']
            })
    subject_averages = sorted(subject_averages, key=lambda x: x['average'], reverse=True)
    
    # Get overall KCSE performance
    overall_kcse = StudentOverallKCSE.objects.all()
    if overall_kcse.exists():
        avg_kcse = overall_kcse.aggregate(models.Avg('mean_score'))['mean_score__avg'] or 0
        pass_rate = overall_kcse.filter(mean_score__gte=40).count() / overall_kcse.count() * 100 if overall_kcse.count() > 0 else 0
    else:
        avg_kcse = 0
        pass_rate = 0
    
    # Get CBC performance
    cbc_overall = StudentOverallCBA.objects.all()
    if cbc_overall.exists():
        avg_cbc = cbc_overall.aggregate(models.Avg('total_score'))['total_score__avg'] or 0
    else:
        avg_cbc = 0
    
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
"""

# Add to reports/views.py
views_path = "reports/views.py"
if os.path.exists(views_path):
    with open(views_path, 'r') as f:
        current = f.read()
    
    # Check if school_report already exists
    if 'def school_report' not in current:
        # Find the last import and add the function
        new_content = current.replace(
            'from django.db.models import Avg, Max, Min, Count, Sum',
            'from django.db.models import Avg, Max, Min, Count, Sum'
        )
        
        # Add the function before the last line
        new_content = new_content.replace(
            'def report_publish(request, report_id):',
            school_report_content + '\n\ndef report_publish(request, report_id):'
        )
        
        with open(views_path, 'w') as f:
            f.write(new_content)
        print("✅ Added school_report to reports/views.py")
    else:
        print("ℹ️ school_report already exists")
