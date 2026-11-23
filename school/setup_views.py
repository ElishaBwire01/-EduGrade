from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from school.models import AcademicYear, Term, Curriculum, GradeLevel, Stream, Subject
from students.models import Student
from students.views import _record_current_placement
from django.contrib.auth import get_user_model
User = get_user_model()
from .services import bulk_reallocate_students, reallocate_and_delete

@login_required
def school_setup_dashboard(request):
    "School setup main dashboard"
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can access school setup!')
        return redirect('core:dashboard')
    
    context = {
        'academic_years': AcademicYear.objects.all().order_by('-year'),
        'terms': Term.objects.select_related('academic_year').all(),
        'curriculums': Curriculum.objects.all(),
        'grade_levels': GradeLevel.objects.select_related('curriculum').all(),
        'streams': Stream.objects.select_related('grade_level').all(),
        'subjects': Subject.objects.select_related('curriculum').all(),
        'total_years': AcademicYear.objects.count(),
        'total_terms': Term.objects.count(),
        'total_curriculums': Curriculum.objects.count(),
        'total_grades': GradeLevel.objects.count(),
        'total_streams': Stream.objects.count(),
        'total_subjects': Subject.objects.count(),
    }
    return render(request, 'school/setup_dashboard.html', context)


# ============================================
# CURRICULUM CRUD
# ============================================
@login_required
def curriculum_create(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')

    if request.method == 'POST':
        try:
            code = request.POST.get('code')
            name = request.POST.get('name')
            description = request.POST.get('description', '')

            if Curriculum.objects.filter(code=code).exists():
                messages.error(request, f'Curriculum {code} already exists!')
                return redirect('school:setup_dashboard')

            Curriculum.objects.create(
                code=code,
                name=name,
                description=description,
                is_active=True
            )

            messages.success(request, f'Curriculum {name} created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating curriculum: {str(e)}')

        return redirect('school:setup_dashboard')


@login_required
def curriculum_edit(request, curriculum_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')

    curriculum = get_object_or_404(Curriculum, id=curriculum_id)

    if request.method == 'POST':
        try:
            curriculum.name = request.POST.get('name')
            curriculum.description = request.POST.get('description', '')
            curriculum.is_active = request.POST.get('is_active') == 'on'
            curriculum.save()

            messages.success(request, 'Curriculum updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating curriculum: {str(e)}')

        return redirect('school:setup_dashboard')


@login_required
def curriculum_delete(request, curriculum_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')

    curriculum = get_object_or_404(Curriculum, id=curriculum_id)

    if request.method == 'POST':
        curriculum_name = curriculum.name
        # Check if curriculum is in use by grade levels or subjects
        in_use = curriculum.grade_levels.exists() or curriculum.subjects.exists()
        if in_use:
            messages.error(request, f'Curriculum {curriculum_name} cannot be deleted — it is in use by grade levels or subjects.')
            return redirect('school:setup_dashboard')

        curriculum.delete()
        messages.success(request, f'Curriculum {curriculum_name} deleted successfully!')
        return redirect('school:setup_dashboard')


# ============================================
# ACADEMIC YEAR CRUD
# ============================================
@login_required
def academic_year_list(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    years = AcademicYear.objects.all().order_by('-year')
    data = [{
        'id': y.id,
        'year': y.year,
        'name': y.name,
        'start_date': y.start_date.strftime('%Y-%m-%d'),
        'end_date': y.end_date.strftime('%Y-%m-%d'),
        'is_current': y.is_current
    } for y in years]
    return JsonResponse({'years': data})


@login_required
def academic_year_create(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    if request.method == 'POST':
        try:
            year = request.POST.get('year')
            name = request.POST.get('name')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            is_current = request.POST.get('is_current') == 'on'
            
            if is_current:
                AcademicYear.objects.filter(is_current=True).update(is_current=False)
            
            academic_year = AcademicYear.objects.create(
                year=year,
                name=name,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current
            )
            
            messages.success(request, f'Academic Year {year} created successfully!')
            return redirect('school:setup_dashboard')
        except Exception as e:
            messages.error(request, f'Error creating academic year: {str(e)}')
            return redirect('school:setup_dashboard')
    
    return redirect('school:setup_dashboard')


@login_required
def academic_year_edit(request, year_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    
    if request.method == 'POST':
        try:
            academic_year.year = request.POST.get('year')
            academic_year.name = request.POST.get('name')
            academic_year.start_date = request.POST.get('start_date')
            academic_year.end_date = request.POST.get('end_date')
            is_current = request.POST.get('is_current') == 'on'
            
            if is_current:
                AcademicYear.objects.filter(is_current=True).update(is_current=False)
                academic_year.is_current = True
            else:
                academic_year.is_current = False
            
            academic_year.save()
            messages.success(request, 'Academic Year updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating academic year: {str(e)}')
        
        return redirect('school:setup_dashboard')
    
    context = {'year': academic_year}
    return render(request, 'school/setup_dashboard.html', context)


@login_required
def academic_year_delete(request, year_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    
    if request.method == 'POST':
        year_name = str(academic_year.year)
        academic_year.delete()
        messages.success(request, f'Academic Year {year_name} deleted successfully!')
        return redirect('school:setup_dashboard')
    
    context = {'year': academic_year}
    return render(request, 'school/setup_dashboard.html', context)


# ============================================
# TERM CRUD
# ============================================
@login_required
def term_create(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')

    if request.method == 'POST':
        try:
            term_number = request.POST.get('term_number')
            name = request.POST.get('name')
            academic_year_id = request.POST.get('academic_year')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            is_active = request.POST.get('is_active') == 'on'

            academic_year = get_object_or_404(AcademicYear, id=academic_year_id)

            if Term.objects.filter(
                term_number=term_number,
                academic_year=academic_year
            ).exists():
                messages.error(request, f'Term {term_number} already exists for {academic_year}!')
                return redirect('school:setup_dashboard')

            Term.objects.create(
                term_number=term_number,
                name=name,
                academic_year=academic_year,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active
            )

            messages.success(request, f'Term {name} created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating term: {str(e)}')

        return redirect('school:setup_dashboard')


@login_required
def term_edit(request, term_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')

    term = get_object_or_404(Term, id=term_id)

    if request.method == 'POST':
        try:
            term.term_number = request.POST.get('term_number')
            term.name = request.POST.get('name')
            term.academic_year_id = request.POST.get('academic_year')
            term.start_date = request.POST.get('start_date')
            term.end_date = request.POST.get('end_date')
            term.is_active = request.POST.get('is_active') == 'on'
            term.save()

            messages.success(request, 'Term updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating term: {str(e)}')

        return redirect('school:setup_dashboard')


@login_required
def term_delete(request, term_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')

    term = get_object_or_404(Term, id=term_id)

    if request.method == 'POST':
        term_name = term.name
        term.delete()
        messages.success(request, f'Term {term_name} deleted successfully!')
        return redirect('school:setup_dashboard')


# ============================================
# GRADE LEVEL CRUD
# ============================================
@login_required
def grade_level_create(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    if request.method == 'POST':
        try:
            curriculum_id = request.POST.get('curriculum')
            level_type = request.POST.get('level_type')
            level_number = request.POST.get('level_number')
            name = request.POST.get('name')
            order = request.POST.get('order', 0)
            
            curriculum = get_object_or_404(Curriculum, id=curriculum_id)
            
            grade_level = GradeLevel.objects.create(
                curriculum=curriculum,
                level_type=level_type,
                level_number=level_number,
                name=name,
                order=order,
                is_active=True
            )
            
            messages.success(request, f'Grade Level {name} created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating grade level: {str(e)}')
        
        return redirect('school:setup_dashboard')


@login_required
def grade_level_edit(request, grade_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')

    grade = get_object_or_404(GradeLevel, id=grade_id)

    if request.method == 'POST':
        try:
            reallocate = request.POST.get('reallocate_students') == 'on'
            target_grade_id = request.POST.get('target_grade')
            target_stream_id = request.POST.get('target_stream')

            if reallocate:
                if not target_grade_id or not target_stream_id:
                    messages.error(request, 'Select a destination grade and stream to reallocate students before updating this grade.')
                    return redirect('school:setup_dashboard')
                target_grade = get_object_or_404(GradeLevel, id=target_grade_id)
                target_stream = get_object_or_404(Stream, id=target_stream_id)
                if target_grade.id == grade.id:
                    messages.error(request, 'Choose a different destination grade for the student reallocation.')
                    return redirect('school:setup_dashboard')
                if target_stream.grade_level_id != target_grade.id:
                    messages.error(request, 'The selected destination stream does not belong to the selected grade.')
                    return redirect('school:setup_dashboard')
                bulk_reallocate_students(grade, None, target_grade, target_stream, request.user)

            grade.curriculum_id = request.POST.get('curriculum')
            grade.level_type = request.POST.get('level_type')
            grade.level_number = request.POST.get('level_number')
            grade.name = request.POST.get('name')
            grade.order = request.POST.get('order', 0)
            grade.is_active = request.POST.get('is_active') == 'on'
            grade.save()

            messages.success(request, 'Grade Level updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating grade level: {str(e)}')

        return redirect('school:setup_dashboard')


@login_required
def grade_level_delete(request, grade_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    grade = get_object_or_404(GradeLevel, id=grade_id)
    
    if request.method == 'POST':
        has_dependants = (
            grade.students.exists()
            or grade.streams.exists()
            or grade.classteacher_set.exists()
            or grade.teacherassignment_set.exists()
        )
        target_grade = GradeLevel.objects.filter(
            id=request.POST.get('target_grade'), is_active=True,
        ).exclude(id=grade.id).first()
        target_stream = Stream.objects.filter(
            id=request.POST.get('target_stream'), grade_level=target_grade,
            is_active=True,
        ).first() if target_grade else None
        if has_dependants and (not target_grade or not target_stream):
            messages.error(request, 'Select a destination grade and stream before deleting this grade.')
        elif has_dependants:
            grade_name = grade.name
            reallocate_and_delete(grade, target_grade, target_stream, request.user)
            messages.success(request, f'Grade Level {grade_name} deleted and its dependants reallocated.')
            return redirect('school:setup_dashboard')
        else:
            grade_name = grade.name
            grade.delete()
            messages.success(request, f'Grade Level {grade_name} deleted successfully!')
            return redirect('school:setup_dashboard')

    context = {
        'grade': grade,
        'student_count': grade.students.count(),
        'target_grades': GradeLevel.objects.filter(is_active=True).exclude(id=grade.id),
        'target_streams': Stream.objects.filter(is_active=True).exclude(grade_level=grade),
        'target_years': AcademicYear.objects.all().order_by('-year'),
    }
    return render(request, 'school/grade_reallocate.html', context)


# ============================================
# STREAM CRUD
# ============================================
@login_required
def stream_create(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    if request.method == 'POST':
        try:
            grade_level_id = request.POST.get('grade_level')
            name = request.POST.get('name')
            code = request.POST.get('code')
            capacity = request.POST.get('capacity', 40)
            
            grade_level = get_object_or_404(GradeLevel, id=grade_level_id)
            
            stream = Stream.objects.create(
                grade_level=grade_level,
                name=name,
                code=code,
                capacity=capacity,
                is_active=True
            )
            
            messages.success(request, f'Stream {name} created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating stream: {str(e)}')
        
        return redirect('school:setup_dashboard')


@login_required
def stream_edit(request, stream_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')

    stream = get_object_or_404(Stream, id=stream_id)

    if request.method == 'POST':
        try:
            reallocate = request.POST.get('reallocate_students') == 'on'
            target_stream_id = request.POST.get('target_stream')
            target_grade = None
            source_grade = stream.grade_level

            if reallocate:
                if not target_stream_id:
                    messages.error(request, 'Select a destination stream to reallocate students before updating this stream.')
                    return redirect('school:setup_dashboard')
                target_stream = get_object_or_404(Stream, id=target_stream_id)
                if target_stream.id == stream.id:
                    messages.error(request, 'Choose a different destination stream for the reallocation.')
                    return redirect('school:setup_dashboard')
                target_grade = target_stream.grade_level
                if request.POST.get('grade_level') and int(request.POST.get('grade_level')) != source_grade.id and target_grade.id != int(request.POST.get('grade_level')):
                    messages.error(request, 'The selected destination stream does not match the selected grade level.')
                    return redirect('school:setup_dashboard')
                bulk_reallocate_students(source_grade, stream, target_grade, target_stream, request.user)

            stream.grade_level_id = request.POST.get('grade_level')
            stream.name = request.POST.get('name')
            stream.code = request.POST.get('code')
            stream.capacity = request.POST.get('capacity', 40)
            stream.is_active = request.POST.get('is_active') == 'on'
            stream.save()

            messages.success(request, 'Stream updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating stream: {str(e)}')

        return redirect('school:setup_dashboard')


@login_required
def stream_delete(request, stream_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    stream = get_object_or_404(Stream, id=stream_id)
    
    if request.method == 'POST':
        target_stream = Stream.objects.filter(
            id=request.POST.get('target_stream'), is_active=True,
        ).exclude(id=stream.id).select_related('grade_level').first()
        has_dependants = (
            stream.students.exists()
            or stream.classteacher_set.exists()
            or stream.teacherassignment_set.exists()
        )
        if has_dependants and not target_stream:
            messages.error(request, 'Select a destination stream before deleting this stream.')
        elif has_dependants:
            stream_name = stream.name
            reallocate_and_delete(stream, target_stream.grade_level, target_stream, request.user)
            messages.success(request, f'Stream {stream_name} deleted and its dependants reallocated.')
            return redirect('school:setup_dashboard')
        else:
            stream_name = stream.name
            stream.delete()
            messages.success(request, f'Stream {stream_name} deleted successfully!')
            return redirect('school:setup_dashboard')

    context = {
        'stream': stream,
        'student_count': stream.students.count(),
        'target_streams': Stream.objects.filter(is_active=True).exclude(id=stream.id),
        'target_grades': GradeLevel.objects.filter(is_active=True).exclude(id=stream.grade_level_id),
        'target_years': AcademicYear.objects.all().order_by('-year'),
    }
    return render(request, 'school/stream_reallocate.html', context)


# ============================================
# SUBJECT CRUD
# ============================================
@login_required
def subject_create(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    if request.method == 'POST':
        try:
            curriculum_id = request.POST.get('curriculum')
            code = request.POST.get('code')
            name = request.POST.get('name')
            short_name = request.POST.get('short_name')
            subject_type = request.POST.get('subject_type', 'CORE')
            
            curriculum = get_object_or_404(Curriculum, id=curriculum_id)
            
            subject = Subject.objects.create(
                curriculum=curriculum,
                code=code,
                name=name,
                short_name=short_name,
                subject_type=subject_type,
                max_score=100,
                min_score=0,
                is_active=True
            )
            
            messages.success(request, f'Subject {name} created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating subject: {str(e)}')
        
        return redirect('school:setup_dashboard')


@login_required
def subject_edit(request, subject_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        try:
            subject.curriculum_id = request.POST.get('curriculum')
            subject.code = request.POST.get('code')
            subject.name = request.POST.get('name')
            subject.short_name = request.POST.get('short_name')
            subject.subject_type = request.POST.get('subject_type')
            subject.is_active = request.POST.get('is_active') == 'on'
            subject.save()
            
            messages.success(request, 'Subject updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating subject: {str(e)}')
        
        return redirect('school:setup_dashboard')


@login_required
def subject_delete(request, subject_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        subject_name = subject.name
        subject.delete()
        messages.success(request, f'Subject {subject_name} deleted successfully!')
        return redirect('school:setup_dashboard')


# ============================================
# API ENDPOINTS FOR DYNAMIC LOADING
# ============================================
@login_required
def api_get_grade_levels(request):
    "Get grade levels by curriculum"
    curriculum_id = request.GET.get('curriculum_id')
    if curriculum_id:
        grades = GradeLevel.objects.filter(
            curriculum_id=curriculum_id,
            is_active=True
        ).values('id', 'name', 'level_number')
        return JsonResponse({'grades': list(grades)})
    return JsonResponse({'grades': []})


@login_required
def api_get_streams(request):
    "Get streams by grade level"
    grade_level_id = request.GET.get('grade_level_id')
    if grade_level_id:
        streams = Stream.objects.filter(
            grade_level_id=grade_level_id,
            is_active=True
        ).values('id', 'name', 'code')
        return JsonResponse({'streams': list(streams)})
    return JsonResponse({'streams': []})


@login_required
def _legacy_grade_level_delete(request, grade_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    grade = get_object_or_404(GradeLevel, id=grade_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            grade_name = grade.name
            grade.delete()
            messages.success(request, f'Grade Level {grade_name} deleted successfully!')
            return redirect('school:setup_dashboard')
        
        elif action == 'reallocate':
            target_grade_id = request.POST.get('target_grade')
            target_stream_id = request.POST.get('target_stream')
            target_year_id = request.POST.get('target_year')
            
            if not target_grade_id:
                messages.error(request, 'Select a target grade level for reallocation.')
                return redirect('school:setup_dashboard')
            
            target_grade = get_object_or_404(GradeLevel, id=target_grade_id)
            target_stream = get_object_or_404(Stream, id=target_stream_id) if target_stream_id else None
            target_year = get_object_or_404(AcademicYear, id=target_year_id) if target_year_id else None
            
            if target_stream and target_stream.grade_level_id != target_grade.id:
                messages.error(request, 'Target stream does not belong to target grade level.')
                return redirect('school:setup_dashboard')
            
            students = Student.objects.filter(current_grade_level=grade)
            count = students.count()
            
            if count == 0:
                grade_name = grade.name
                grade.delete()
                messages.success(request, f'Grade Level {grade_name} deleted (no students to reallocate).')
                return redirect('school:setup_dashboard')
            
            with transaction.atomic():
                for student in students:
                    student.current_grade_level = target_grade
                    if target_stream:
                        student.current_stream = target_stream
                    if target_year:
                        student.academic_year = target_year
                    student.updated_by = request.user
                    student.save()
                    _record_current_placement(student, target_grade, target_stream, target_year)
            
            grade_name = grade.name
            grade.delete()
            messages.success(request, f'Grade Level {grade_name} deleted and {count} students reallocated to {target_grade.name}.')
            return redirect('school:setup_dashboard')
    
    target_grades = GradeLevel.objects.filter(is_active=True).exclude(id=grade.id)
    target_streams = Stream.objects.filter(is_active=True)
    target_years = AcademicYear.objects.all()
    student_count = Student.objects.filter(current_grade_level=grade).count()
    
    context = {
        'grade': grade,
        'target_grades': target_grades,
        'target_streams': target_streams,
        'target_years': target_years,
        'student_count': student_count,
    }
    return render(request, 'school/grade_reallocate.html', context)


@login_required
def _legacy_stream_delete(request, stream_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized!')
        return redirect('school:setup_dashboard')
    
    stream = get_object_or_404(Stream, id=stream_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            stream_name = stream.name
            stream.delete()
            messages.success(request, f'Stream {stream_name} deleted successfully!')
            return redirect('school:setup_dashboard')
        
        elif action == 'reallocate':
            target_stream_id = request.POST.get('target_stream')
            target_grade_id = request.POST.get('target_grade')
            target_year_id = request.POST.get('target_year')
            
            if not target_stream_id:
                messages.error(request, 'Select a target stream for reallocation.')
                return redirect('school:setup_dashboard')
            
            target_stream = get_object_or_404(Stream, id=target_stream_id)
            target_grade = get_object_or_404(GradeLevel, id=target_grade_id) if target_grade_id else target_stream.grade_level
            target_year = get_object_or_404(AcademicYear, id=target_year_id) if target_year_id else None
            
            if target_stream.grade_level_id != target_grade.id:
                messages.error(request, 'Target stream does not belong to target grade level.')
                return redirect('school:setup_dashboard')
            
            students = Student.objects.filter(current_stream=stream)
            count = students.count()
            
            if count == 0:
                stream_name = stream.name
                stream.delete()
                messages.success(request, f'Stream {stream_name} deleted (no students to reallocate).')
                return redirect('school:setup_dashboard')
            
            with transaction.atomic():
                for student in students:
                    student.current_stream = target_stream
                    student.current_grade_level = target_grade
                    if target_year:
                        student.academic_year = target_year
                    student.updated_by = request.user
                    student.save()
                    _record_current_placement(student, target_grade, target_stream, target_year)
            
            stream_name = stream.name
            stream.delete()
            messages.success(request, f'Stream {stream_name} deleted and {count} students reallocated to {target_stream.name}.')
            return redirect('school:setup_dashboard')
    
    target_streams = Stream.objects.filter(is_active=True).exclude(id=stream.id)
    target_grades = GradeLevel.objects.filter(is_active=True)
    target_years = AcademicYear.objects.all()
    student_count = Student.objects.filter(current_stream=stream).count()
    
    context = {
        'stream': stream,
        'target_streams': target_streams,
        'target_grades': target_grades,
        'target_years': target_years,
        'student_count': student_count,
    }
    return render(request, 'school/stream_reallocate.html', context)

