from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import datetime
from django.utils import timezone
from .models import MarkEntry, MarkSubmission, MarkCorrection
from examinations.models import Examination
from school.models import Subject, GradeLevel, Stream
from students.models import Student
from teachers.models import TeacherProfile
from core.access import is_admin
from core.access import assert_exam_editable
from core.models import AuditLog
from core.access import send_notification
from grading.services import recalculate_for_mark_change

User = get_user_model()


def _is_admin_user(user):
    return is_admin(user)



@login_required
def mark_entry(request):
    """Main mark entry interface"""
    # Get teacher profile
    try:
        teacher = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'You do not have a teacher profile!')
        return redirect('core:dashboard')
    
    # Get teacher's approved assignments
    assignments = teacher.assignments.filter(
        status='APPROVED'
    ).select_related('subject', 'grade_level', 'stream', 'academic_year')
    
    # Get examination filters
    exam_id = request.GET.get('exam_id')
    subject_id = request.GET.get('subject_id')
    grade_level_id = request.GET.get('grade_level_id')
    stream_id = request.GET.get('stream_id')
    
    # Get students based on selection
    students = []
    selected_exam = None
    selected_subject = None
    selected_grade = None
    selected_stream = None
    
    if exam_id and subject_id and grade_level_id and stream_id:
        selected_exam = get_object_or_404(Examination, id=exam_id)
        selected_subject = get_object_or_404(Subject, id=subject_id)
        selected_grade = get_object_or_404(GradeLevel, id=grade_level_id)
        selected_stream = get_object_or_404(Stream, id=stream_id)
        
        # Get students in this class
        students = Student.objects.filter(
            current_grade_level=selected_grade,
            current_stream=selected_stream,
            is_active=True
        ).order_by('admission_number')
        
        # Check if marks already exist
        existing_marks = MarkEntry.objects.filter(
            examination=selected_exam,
            subject=selected_subject,
            grade_level=selected_grade,
            stream=selected_stream
        ).select_related('student')
        
        # Check if teacher is authorized
        is_authorized = teacher.assignments.filter(
            subject=selected_subject,
            grade_level=selected_grade,
            stream=selected_stream,
            status='APPROVED'
        ).exists()
        
        if not is_authorized and not request.user.is_staff and not request.user.is_superuser:
            messages.error(request, 'You are not authorized to enter marks for this class!')
            return redirect('marks:entry')
        
        # If marks exist, use them
        if existing_marks.exists():
            # Create a dict of existing marks
            marks_dict = {mark.student_id: mark for mark in existing_marks}
            
            # Add score to each student
            for student in students:
                if student.id in marks_dict:
                    student.mark = marks_dict[student.id]
                else:
                    student.mark = None
        else:
            # No marks yet
            for student in students:
                student.mark = None
    
    # Handle POST (mark submission)
    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        subject_id = request.POST.get('subject_id')
        grade_level_id = request.POST.get('grade_level_id')
        stream_id = request.POST.get('stream_id')
        
        if exam_id and subject_id and grade_level_id and stream_id:
            exam = get_object_or_404(Examination, id=exam_id)
            from core.access import assert_exam_editable as _ae
            try:
                _ae(exam, request.user)
            except Exception as _e:
                messages.error(request, str(_e))
                return redirect('marks:entry')
            subject = get_object_or_404(Subject, id=subject_id)
            grade_level = get_object_or_404(GradeLevel, id=grade_level_id)
            stream = get_object_or_404(Stream, id=stream_id)
            
            # Get all students in this class
            students_list = Student.objects.filter(
                current_grade_level=grade_level,
                current_stream=stream,
                is_active=True
            )
            
            # Process marks
            for student in students_list:
                score = request.POST.get(f'mark_{student.id}')
                mark_status = request.POST.get(f'status_{student.id}', 'DRAFT')
                
                if score is not None and score != '':
                    try:
                        score_value = float(score)
                        if 0 <= score_value <= 100:
                            # Check if mark exists
                            mark_entry, created = MarkEntry.objects.get_or_create(
                                student=student,
                                examination=exam,
                                subject=subject,
                                grade_level=grade_level,
                                stream=stream,
                                defaults={
                                    'score': score_value,
                                    'status': mark_status,
                                    'entered_by': request.user
                                }
                            )
                            if not created:
                                mark_entry.score = score_value
                                mark_entry.status = mark_status
                                mark_entry.updated_by = request.user
                                mark_entry.save()
                        else:
                            messages.error(request, f'Invalid score for {student.full_name}. Score must be between 0 and 100.')
                    except ValueError:
                        messages.error(request, f'Invalid score format for {student.full_name}.')
            
            # Create or update submission record
            submission, created = MarkSubmission.objects.get_or_create(
                teacher=teacher,
                examination=exam,
                subject=subject,
                grade_level=grade_level,
                stream=stream,
                defaults={
                    'status': 'SUBMITTED',
                    'submitted_by': request.user,
                    'submitted_at': timezone.now()
                }
            )
            if not created:
                submission.status = 'SUBMITTED'
                submission.submitted_by = request.user
                submission.submitted_at = timezone.now()
                submission.save()
            
            messages.success(request, 'Marks saved successfully!')
            return redirect('marks:entry')
    
    # Get available examinations for the teacher
    available_exams = Examination.objects.filter(
        status__in=['ACTIVE', 'LOCKED'],
        grade_level__in=assignments.values_list('grade_level', flat=True)
    ).distinct()
    
    context = {
        'teacher': teacher,
        'assignments': assignments,
        'available_exams': available_exams,
        'students': students,
        'selected_exam': selected_exam,
        'selected_subject': selected_subject,
        'selected_grade': selected_grade,
        'selected_stream': selected_stream,
        'exam_id': exam_id,
        'subject_id': subject_id,
        'grade_level_id': grade_level_id,
        'stream_id': stream_id,
    }
    return render(request, 'marks/entry.html', context)


@login_required
def mark_view(request):
    """View marks for an examination"""
    exam_id = request.GET.get('exam_id')
    grade_level_id = request.GET.get('grade_level_id')
    stream_id = request.GET.get('stream_id')

    try:
        exam_id = int(exam_id) if exam_id else None
        grade_level_id = int(grade_level_id) if grade_level_id else None
        stream_id = int(stream_id) if stream_id else None
    except (ValueError, TypeError):
        exam_id = None
        grade_level_id = None
        stream_id = None

    if not all([exam_id, grade_level_id, stream_id]):
        messages.error(request, 'Please select examination, grade, and stream.')
        return redirect('marks:entry')

    exam = get_object_or_404(Examination, id=exam_id)
    grade_level = get_object_or_404(GradeLevel, id=grade_level_id)
    stream = get_object_or_404(Stream, id=stream_id)
    
    # Get all marks for this exam and class
    marks = MarkEntry.objects.filter(
        examination=exam,
        grade_level=grade_level,
        stream=stream
    ).select_related('student', 'subject')
    
    # Get subjects
    subjects = exam.subjects.all()
    
    # Prepare data for display
    students = Student.objects.filter(
        current_grade_level=grade_level,
        current_stream=stream,
        is_active=True
    ).order_by('admission_number')
    
    # Create a matrix of marks
    mark_matrix = {}
    for student in students:
        mark_matrix[student.id] = {'student': student, 'marks': {}}
        for subject in subjects:
            mark = marks.filter(student=student, subject=subject).first()
            mark_matrix[student.id]['marks'][subject.id] = mark.score if mark else None
    
    context = {
        'exam': exam,
        'grade_level': grade_level,
        'stream': stream,
        'subjects': subjects,
        'students': students,
        'mark_matrix': mark_matrix,
    }
    return render(request, 'marks/view.html', context)


@login_required
def mark_correction(request):
    """Request or approve mark corrections"""
    # Check if user is admin
    is_admin = request.user.is_staff or request.user.is_superuser
    
    if is_admin:
        corrections = MarkCorrection.objects.filter(status='PENDING').select_related(
            'mark_entry', 'mark_entry__student', 'mark_entry__subject', 'requested_by'
        )
    else:
        # Teachers can only see their own correction requests
        corrections = MarkCorrection.objects.filter(
            requested_by=request.user
        ).select_related('mark_entry', 'mark_entry__student', 'mark_entry__subject')
    
    if request.method == 'POST':
        if is_admin:
            correction_id = request.POST.get('correction_id')
            action = request.POST.get('action')
            admin_notes = request.POST.get('admin_notes', '')
            
            correction = get_object_or_404(MarkCorrection, id=correction_id)
            
            if action == 'approve':
                correction.status = 'APPROVED'
                correction.approved_by = request.user
                correction.approved_at = timezone.now()
                correction.admin_notes = admin_notes
                
                # Update the mark
                mark_entry = correction.mark_entry
                mark_entry.score = correction.new_score
                mark_entry.updated_by = request.user
                mark_entry.save(update_fields=['score', 'updated_by'])

                # Recalculate dependent grades
                try:
                    result = recalculate_for_mark_change(mark_entry)
                    if result.get('subject_grade'):
                        messages.success(request, 'Correction approved! Grade recalculated.')
                    else:
                        messages.success(request, 'Correction approved!')
                except Exception:
                    messages.success(request, 'Correction approved! (Grade recalculation skipped.)')

                send_notification(
                    mark_entry.entered_by,
                    title="Mark Correction Approved",
                    message=(
                        f"Your correction request for {mark_entry.student.full_name} "
                        f"({mark_entry.subject.name}) has been approved.\n\n"
                        f"New score: {correction.new_score}\n"
                        f"Notes: {admin_notes}" if admin_notes else
                        f"Your correction request for {mark_entry.student.full_name} "
                        f"({mark_entry.subject.name}) has been approved.\n\n"
                        f"New score: {correction.new_score}"
                    ),
                    notification_type="MARK_EDIT",
                    url=reverse('marks:correction'),
                )
                
            elif action == 'reject':
                correction.status = 'REJECTED'
                correction.approved_by = request.user
                correction.approved_at = timezone.now()
                correction.admin_notes = admin_notes
                messages.warning(request, 'Correction rejected!')
            
            correction.save()
            return redirect('marks:correction')
        else:
            # Teacher requesting correction
            mark_entry_id = request.POST.get('mark_entry_id')
            new_score = request.POST.get('new_score')
            reason = request.POST.get('reason')
            
            mark_entry = get_object_or_404(MarkEntry, id=mark_entry_id)
            
            # Check if teacher is authorized to request correction for this mark
            is_authorized = mark_entry.entered_by == request.user or \
                teacher.assignments.filter(
                    subject=mark_entry.subject,
                    grade_level=mark_entry.grade_level,
                    stream=mark_entry.stream,
                    status='APPROVED'
                ).exists()
            
            if not is_authorized:
                messages.error(request, 'You can only request corrections for marks you entered or are assigned to.')
                return redirect('marks:correction')
            
            # Check if correction already exists
            if MarkCorrection.objects.filter(mark_entry=mark_entry, status='PENDING').exists():
                messages.error(request, 'A correction request is already pending for this mark!')
                return redirect('marks:correction')
            
            MarkCorrection.objects.create(
                mark_entry=mark_entry,
                old_score=mark_entry.score,
                new_score=new_score,
                reason=reason,
                requested_by=request.user
            )
            
            messages.success(request, 'Correction request submitted!')
            return redirect('marks:correction')
    
    context = {
        'corrections': corrections,
        'is_admin': is_admin,
    }
    return render(request, 'marks/correction.html', context)


# ========================================================
# Admin mark management — direct mark correction
# ========================================================

@login_required
@user_passes_test(_is_admin_user)
def admin_mark_management(request):
    """Admin view to search, list, and directly edit student marks."""
    exam_id = request.GET.get('exam_id')
    subject_id = request.GET.get('subject_id')
    grade_level_id = request.GET.get('grade_level_id')
    stream_id = request.GET.get('stream_id')
    student_search = request.GET.get('student_search', '').strip()

    marks = MarkEntry.objects.select_related(
        'student', 'examination', 'subject', 'entered_by'
    ).order_by('-updated_at')

    if exam_id:
        marks = marks.filter(examination_id=exam_id)
    if subject_id:
        marks = marks.filter(subject_id=subject_id)
    if grade_level_id:
        marks = marks.filter(grade_level_id=grade_level_id)
    if stream_id:
        marks = marks.filter(stream_id=stream_id)
    if student_search:
        marks = marks.filter(
            Q(student__first_name__icontains=student_search) |
            Q(student__last_name__icontains=student_search) |
            Q(student__admission_number__icontains=student_search)
        )

    exams = Examination.objects.all().order_by('-start_date')
    subjects = Subject.objects.all().order_by('name')
    grade_levels = GradeLevel.objects.all().order_by('name')
    streams = Stream.objects.all().order_by('name')

    paginator = Paginator(marks, 50)
    page_number = request.GET.get('page')
    marks_page = paginator.get_page(page_number)

    context = {
        'marks': marks_page,
        'exams': exams,
        'subjects': subjects,
        'grade_levels': grade_levels,
        'streams': streams,
        'exam_id': exam_id or '',
        'subject_id': subject_id or '',
        'grade_level_id': grade_level_id or '',
        'stream_id': stream_id or '',
        'student_search': student_search,
        'is_admin': True,
    }
    return render(request, 'marks/admin_mark_management.html', context)


@login_required
@user_passes_test(_is_admin_user)
def admin_mark_edit(request, mark_entry_id):
    """Admin view to directly edit a single mark entry.

    Allows the admin to change the score, and optionally recalculate
    dependent grades automatically.
    """
    mark_entry = get_object_or_404(
        MarkEntry.objects.select_related(
            'student', 'examination', 'subject', 'entered_by'
        ),
        id=mark_entry_id
    )

    old_score = mark_entry.score

    if request.method == 'POST':
        new_score_str = request.POST.get('score')
        reason = request.POST.get('reason', '').strip()
        recalculate_grades = request.POST.get('recalculate', 'on') == 'on'

        if new_score_str:
            try:
                new_score = float(new_score_str)
                if not (0 <= new_score <= 100):
                    messages.error(request, 'Score must be between 0 and 100.')
                    return redirect('marks:admin_mark_edit', mark_entry_id=mark_entry_id)
            except ValueError:
                messages.error(request, 'Invalid score value.')
                return redirect('marks:admin_mark_edit', mark_entry_id=mark_entry_id)

            if new_score != float(old_score or 0):
                if not reason:
                    messages.error(request, 'Reason is required when changing the score.')
                    return redirect('marks:admin_mark_edit', mark_entry_id=mark_entry_id)

                mark_entry.score = new_score
                mark_entry.updated_by = request.user
                mark_entry.save(update_fields=['score', 'updated_by'])

                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='MarkEntry',
                    object_id=str(mark_entry.id),
                    object_repr=str(mark_entry),
                    changes={
                        'old_score': str(old_score),
                        'new_score': str(new_score),
                        'reason': reason,
                    },
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )

                if recalculate_grades:
                    try:
                        result = recalculate_for_mark_change(mark_entry)
                        if result.get('subject_grade'):
                            messages.success(
                                request,
                                f'Score updated from {old_score} to {new_score}. '
                                f'Grade recalculated: {result["subject_grade"]}.'
                            )
                        else:
                            messages.success(request, f'Score updated from {old_score} to {new_score}.')
                    except Exception:
                        messages.success(
                            request,
                            f'Score updated from {old_score} to {new_score}. '
                            f'(Grade recalculation failed — check grading scheme configuration.)'
                        )
                else:
                    messages.success(request, f'Score updated from {old_score} to {new_score}.')

                send_notification(
                    mark_entry.entered_by,
                    title="Mark Correction — Admin Edit",
                    message=(
                        f"Your mark entry for {mark_entry.student.full_name} "
                        f"({mark_entry.subject.name}) has been corrected by an administrator.\n\n"
                        f"Old: {old_score} → New: {new_score}\n"
                        f"Reason: {reason}"
                    ),
                    notification_type="MARK_EDIT",
                    url=reverse('marks:admin_mark_edit', args=[mark_entry_id]) if request.user.is_staff else None,
                )
        else:
            messages.error(request, 'A score value is required.')
            return redirect('marks:admin_mark_edit', mark_entry_id=mark_entry_id)

        return redirect('marks:admin_mark_management')

    context = {
        'mark_entry': mark_entry,
        'old_score': old_score,
        'is_admin': True,
    }
    return render(request, 'marks/admin_mark_edit.html', context)



@login_required
def api_get_classes(request):
    """API endpoint to get classes for a teacher"""
    try:
        teacher = TeacherProfile.objects.get(user=request.user)
        assignments = teacher.assignments.filter(status='APPROVED')
        
        classes = []
        for assignment in assignments:
            class_data = {
                'grade_level_id': assignment.grade_level.id,
                'grade_level_name': assignment.grade_level.name,
                'stream_id': assignment.stream.id,
                'stream_name': assignment.stream.name,
                'subject_id': assignment.subject.id,
                'subject_name': assignment.subject.name,
                'academic_year': assignment.academic_year.year
            }
            # Avoid duplicates
            key = f"{class_data['grade_level_id']}_{class_data['stream_id']}"
            if key not in [f"{c['grade_level_id']}_{c['stream_id']}" for c in classes]:
                classes.append(class_data)
        
        return JsonResponse({'classes': classes})
    except TeacherProfile.DoesNotExist:
        return JsonResponse({'classes': []})


# ============================================================
# ADMIN: create / upsert a mark for ANY student x exam x subject
# ============================================================
@login_required
@user_passes_test(_is_admin_user)
def admin_mark_create(request):
    """Admin: create or overwrite a mark for ANY student x exam x subject.

    Does NOT require a TeacherProfile. The MarkEntry inherits the student's
    CURRENT grade_level / stream placement (same as mark_entry).
    One mark per (student, exam, subject) enforced by unique_together,
    so this view upserts.
    """
    # ---- POST: create or update ----
    if request.method == 'POST':
        student_id  = request.POST.get('student_id')
        exam_id     = request.POST.get('examination_id')
        subject_id  = request.POST.get('subject_id')
        score_str   = request.POST.get('score')
        status      = request.POST.get('status', 'DRAFT')
        reason      = (request.POST.get('reason') or '').strip()
        recalculate = request.POST.get('recalculate') == 'on'

        if not (student_id and exam_id and subject_id and score_str):
            messages.error(request, 'Student, examination, subject and score are required.')
            return redirect('marks:admin_mark_create')

        student = get_object_or_404(Student, id=student_id)
        exam    = get_object_or_404(Examination, id=exam_id)
        from core.access import assert_exam_editable as _ae
        try:
            _ae(exam, request.user)
        except Exception as _e:
            messages.error(request, str(_e))
            return redirect('marks:admin_mark_create')
        subject = get_object_or_404(Subject, id=subject_id)

        # Subject must belong to the examination
        if not exam.subjects.filter(id=subject.id).exists():
            messages.error(request, 'That subject is not part of the selected examination.')
            return redirect('marks:admin_mark_create')

        try:
            score = float(score_str)
            if not (0 <= score <= 100):
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, 'Score must be a number between 0 and 100.')
            return redirect('marks:admin_mark_create')

        grade_level = student.current_grade_level
        stream      = student.current_stream
        if not grade_level or not stream:
            messages.error(request, 'Student has no current grade / stream placement.')
            return redirect('marks:admin_mark_create')

        existing = MarkEntry.objects.filter(
            student=student, examination=exam, subject=subject
        ).first()

        if existing:
            if not reason:
                messages.error(request, 'A reason is required when overwriting an existing mark.')
                return redirect('marks:admin_mark_create')
            old = existing.score
            existing.score       = score
            existing.status      = status
            existing.grade_level = grade_level
            existing.stream      = stream
            existing.updated_by  = request.user
            existing.save()
            AuditLog.objects.create(
                user=request.user, action='UPDATE',
                model_name='MarkEntry', object_id=str(existing.id),
                object_repr=str(existing),
                changes={'old_score': str(old), 'new_score': str(score), 'reason': reason},
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            messages.success(
                request,
                f'Mark updated: {student.full_name} — {subject.name}: {old} -> {score}'
            )
        else:
            existing = MarkEntry.objects.create(
                student=student, examination=exam, subject=subject,
                grade_level=grade_level, stream=stream,
                score=score, status=status,
                entered_by=request.user, updated_by=request.user,
            )
            AuditLog.objects.create(
                user=request.user, action='CREATE',
                model_name='MarkEntry', object_id=str(existing.id),
                object_repr=str(existing),
                changes={'score': str(score), 'reason': reason or 'admin created'},
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            messages.success(
                request,
                f'Mark created: {student.full_name} — {subject.name}: {score}'
            )

        if recalculate:
            try:
                recalculate_for_mark_change(existing)
            except Exception:
                pass

        return redirect('marks:admin_mark_create')

    # ---- GET: render form ----
    students = (Student.objects
                .filter(is_active=True)
                .select_related('current_grade_level', 'current_stream')
                .order_by('admission_number')[:2000])
    examinations = (Examination.objects
                    .select_related('academic_year', 'grade_level', 'curriculum')
                    .order_by('-start_date'))
    subjects = Subject.objects.filter(is_active=True).order_by('name')

    # Subjects grouped by exam id (JSON for the template's dependent dropdown)
    import json
    exam_subjects = {str(e.id): [{'id': s.id, 'name': s.name}
                                 for s in e.subjects.all()]
                     for e in examinations}

    recent = (MarkEntry.objects
              .select_related('student', 'examination', 'subject', 'updated_by')
              .order_by('-updated_at')[:10])

    context = {
        'students':     students,
        'examinations': examinations,
        'subjects':     subjects,
        'exam_subjects_json': json.dumps(exam_subjects),
        'recent':       recent,
        'status_choices': MarkEntry.STATUS_CHOICES,
        'is_admin':     True,
    }
    return render(request, 'marks/admin_mark_create.html', context)


