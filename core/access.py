"""
EduGrade Access-Control & Notification Helpers
===============================================

Replaces simple role-based checks with a full RBAC + scoped-permission
system.  Admin / staff users automatically have every permission.
Non-admin users must have an active (non-expired) ``PermissionAssignment``
that matches the requested permission code and scope.
"""

from django.db.models import Q
from django.utils import timezone

from students.models import Student
from teachers.models import ClassTeacher, TeacherProfile, TeacherAssignment
from core.permissions import Permission
from core.models import PermissionAssignment, Notification


# ========================================================
# Simple admin check (used everywhere as a fast-path)
# ========================================================

def is_admin(user):
    """True for staff / superuser users."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ========================================================
# Class-teacher assignment queries (unchanged)
# ========================================================

def class_teacher_assignments(user):
    """Return active ClassTeacher rows for the logged-in teacher."""
    if not user.is_authenticated:
        return ClassTeacher.objects.none()

    if is_admin(user):
        return ClassTeacher.objects.filter(is_active=True).select_related(
            'teacher', 'grade_level', 'stream', 'academic_year'
        )

    teacher = TeacherProfile.objects.filter(user=user, is_active=True).first()
    if not teacher:
        return ClassTeacher.objects.none()

    return ClassTeacher.objects.filter(
        teacher=teacher,
        is_active=True,
    ).select_related('grade_level', 'stream', 'academic_year')


def subject_teacher_assignments(user):
    """Return approved TeacherAssignment rows for the logged-in teacher."""
    if not user.is_authenticated:
        return TeacherAssignment.objects.none()

    if is_admin(user):
        return TeacherAssignment.objects.filter(status='APPROVED').select_related(
            'teacher', 'subject', 'grade_level', 'stream', 'academic_year'
        )

    teacher = TeacherProfile.objects.filter(user=user, is_active=True).first()
    if not teacher:
        return TeacherAssignment.objects.none()

    return TeacherAssignment.objects.filter(
        teacher=teacher,
        status='APPROVED',
    ).select_related('subject', 'grade_level', 'stream', 'academic_year')


# ========================================================
# Scoped student queryset
# ========================================================

def permitted_student_queryset(user):
    """All authenticated teachers can VIEW students in their assigned classes.

    Admins see all students.
    Class teachers see students in their assigned grade/stream/year.
    Subject teachers see students in the classes/subjects they are assigned to.
    """
    students = Student.objects.all()
    if is_admin(user):
        return students

    # Class teacher scope (grade + stream + academic year)
    ct_scope = Q()
    for assignment in class_teacher_assignments(user):
        ct_scope |= Q(
            current_grade_level=assignment.grade_level,
            current_stream=assignment.stream,
            academic_year=assignment.academic_year,
        )

    # Subject teacher scope (grade + stream + academic year via assignments)
    subject_scope = Q()
    for assignment in subject_teacher_assignments(user):
        subject_scope |= Q(
            current_grade_level=assignment.grade_level,
            current_stream=assignment.stream,
            academic_year=assignment.academic_year,
        )

    scope = ct_scope | subject_scope
    return students.filter(scope) if scope else Student.objects.none()


def can_manage_student(user, student):
    """Can the user EDIT a particular student?

    Admins and class teachers can edit students in their scope.
    Subject teachers can VIEW but NOT EDIT students.
    """
    if is_admin(user):
        return True

    # Only class teachers (or users with class-level permission) can edit
    assignments = class_teacher_assignments(user)
    scope = Q()
    for assignment in assignments:
        scope |= Q(
            current_grade_level=assignment.grade_level,
            current_stream=assignment.stream,
            academic_year=assignment.academic_year,
        )
    return Student.objects.filter(scope).filter(pk=student.pk).exists()


def can_edit_student(user, student):
    """Alias for can_manage_student — explicit edit check."""
    return can_manage_student(user, student)


# ========================================================
# Scoped permission checking
# ========================================================

def _resolve_profile(user):
    """Return the UserProfile for *user*, or None."""
    if not user.is_authenticated:
        return None
    try:
        return user.profile
    except Exception:
        return None


def has_permission(user, permission_code, scope=None):
    """Check whether *user* has *permission_code* at the given *scope*.

    Parameters
    ----------
    user : User
        The authenticated Django user.
    permission_code : str
        One of the constants from ``core.permissions.Permission``.
    scope : dict, optional
        Keys may include ``subject``, ``grade_level``, ``stream``,
        ``academic_year``, ``term``, ``examination``.
        May be omitted for global-only permissions.

    Returns
    -------
    bool
    """
    # Admins / staff have every permission
    if is_admin(user):
        return True

    if not user.is_authenticated:
        return False

    # Check if user is suspended
    profile = _resolve_profile(user)
    if profile is None:
        return False

    if profile.is_suspended:
        return False

    scope = scope or {}

    # Check PermissionAssignment records
    queryset = profile.effective_permissions().filter(permission__code=permission_code)

    # Try to match scope
    # A permission assignment with null scope fields matches any scope
    # A permission assignment with specific scope fields requires those to match
    matched = False
    for assignment in queryset:
        if _scope_matches(assignment, scope):
            matched = True
            break

    return matched


def _scope_matches(assignment, scope):
    """True if the assignment's scope is compatible with the requested scope.

    An assignment with no scope (all null) matches any request.
    An assignment with a specific scope must match all its specified fields.
    """
    for field_name in ('subject', 'grade_level', 'stream',
                        'academic_year', 'term', 'examination'):
        assignee_val = getattr(assignment, field_name, None)
        requested_val = scope.get(field_name)

        if assignee_val is None:
            # Assignment is global for this scope dimension — matches anything
            continue

        if requested_val is None:
            # Assignment has a specific scope but request doesn't specify it
            # For global-only permissions this is fine; for scoped permissions
            # we require the request to match. We allow it here because the
            # assignment was explicitly granted.
            continue

        if assignee_val != requested_val:
            return False

    return True


def has_permission_or_403(user, permission_code, scope=None):
    """Check permission and return True / False (does not raise)."""
    return has_permission(user, permission_code, scope)


# ========================================================
# Convenience scope checkers
# ========================================================

def can_use_class(user, grade_level_id, stream_id, academic_year_id=None):
    """Can the user operate on a specific class (grade + stream + year)?"""
    if is_admin(user):
        return True

    assignments = class_teacher_assignments(user).filter(
        grade_level_id=grade_level_id,
        stream_id=stream_id,
    )
    if academic_year_id:
        assignments = assignments.filter(academic_year_id=academic_year_id)
    return assignments.exists()


def can_enter_marks(user, examination=None, subject=None, grade_level=None,
                     stream=None, academic_year=None, term=None):
    """Check ENTER_MARKS permission with optional scope."""
    scope = {}
    if examination:
        scope['examination'] = examination
    if subject:
        scope['subject'] = subject
    if grade_level:
        scope['grade_level'] = grade_level
    if stream:
        scope['stream'] = stream
    if academic_year:
        scope['academic_year'] = academic_year
    if term:
        scope['term'] = term
    return has_permission(user, Permission.ENTER_MARKS, scope=scope)


def can_edit_marks(user, examination=None, subject=None, student=None):
    """Check EDIT_MARKS permission for a specific exam/subject/student."""
    scope = {}
    if examination:
        scope['examination'] = examination
    if subject:
        scope['subject'] = subject
    if student:
        scope['grade_level'] = student.current_grade_level
        scope['stream'] = student.current_stream
    return has_permission(user, Permission.EDIT_MARKS, scope=scope)


def can_create_teacher(user):
    """Only admins can create teacher accounts."""
    return has_permission(user, Permission.CREATE_TEACHER)


def can_create_student(user):
    """Check CREATE_STUDENT permission."""
    return has_permission(user, Permission.CREATE_STUDENT)


def can_approve_request(user):
    """Check APPROVE_TEACHER_REQUEST permission."""
    return has_permission(user, Permission.APPROVE_TEACHER_REQUEST)


def can_generate_report(user):
    """Check GENERATE_REPORT permission."""
    return has_permission(user, Permission.GENERATE_REPORT)


def can_view_school_analytics(user):
    """Check VIEW_SCHOOL_ANALYTICS permission."""
    return has_permission(user, Permission.VIEW_SCHOOL_ANALYTICS)


def can_configure_grading(user):
    """Check CONFIGURE_ASSESSMENT_SCHEME permission."""
    return has_permission(user, Permission.CONFIGURE_ASSESSMENT_SCHEME)


# ========================================================
# Notification helpers
# ========================================================

def send_notification(user, title, message, notification_type="SYSTEM",
                       url=None, related_object_id=None,
                       related_object_type=None):
    """Create an in-system notification for *user*.

    Parameters
    ----------
    user : User
        Recipient user instance.
    title : str
        Short subject line.
    message : str
        Full message body.
    notification_type : str
        One of Notification.NOTIFICATION_TYPES choices.
    url : str, optional
        URL the user is directed to when clicking the notification.
    related_object_id : str, optional
        ID of the related object (e.g. teacher_request id).
    related_object_type : str, optional
        Model name of the related object.
    """
    return Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        notification_type=notification_type,
        url=url,
        related_object_id=str(related_object_id) if related_object_id else None,
        related_object_type=related_object_type,
    )


def notify_assignment(profile, subject, grade_level, stream,
                      academic_year, term=None, granted_by=None):
    """Send a notification when a teacher is assigned to a subject/class."""
    stream_label = stream.name if stream else "all streams"
    term_label = f" (Term {term.term_number})" if term else ""

    title = "New Assignment"
    message = (
        f"You have been assigned as a Subject Teacher for {subject.name}.\n\n"
        f"Grade: {grade_level.name}\n"
        f"Stream: {stream_label}\n"
        f"Academic Year: {academic_year.year}{term_label}\n\n"
        f"Permissions:\n"
        f"  - View assigned learners\n"
        f"  - Enter assessment marks\n"
        f"  - View subject analytics\n"
    )

    return send_notification(
        profile.user,
        title=title,
        message=message,
        notification_type="ASSIGNMENT",
        url="/marks/entry/",
    )


def notify_request_result(request_obj, approved, admin_notes=None, granted_by=None):
    """Send approval or rejection notification for a request."""
    teacher = request_obj.teacher
    if approved:
        title = "Request Approved"
        message = (
            f"Your request for {request_obj.get_request_type_display()}"
            f" has been approved.\n\n"
        )
        if admin_notes:
            message += f"Admin notes: {admin_notes}\n\n"
        message += "You can now perform the requested function."
        notification_type = "APPROVAL"
    else:
        title = "Request Rejected"
        message = (
            f"Your request for {request_obj.get_request_type_display()}"
            f" has been rejected.\n\n"
        )
        if admin_notes:
            message += f"Admin notes: {admin_notes}\n\n"
        message += "Please contact an administrator if you have questions."
        notification_type = "REJECTION"

    return send_notification(
        teacher.user,
        title=title,
        message=message,
        notification_type=notification_type,
        url="/teachers/requests/",
    )


def notify_warning(teacher_profile, warning_obj):
    """Send a notification when a warning is issued."""
    title = f"Warning Issued — {warning_obj.severity}"
    message = (
        f"A warning has been issued to your account.\n\n"
        f"Reason: {warning_obj.reason}\n"
        f"Severity: {warning_obj.get_severity_display()}\n\n"
        f"Please review the details and acknowledge."
    )
    return send_notification(
        teacher_profile.user,
        title=title,
        message=message,
        notification_type="WARNING",
        url="/authentication/profile/",
    )


def notify_suspension(teacher_profile, suspension_obj):
    """Send a notification when a teacher is suspended."""
    title = "Account Suspended"
    message = (
        f"Your account has been temporarily suspended.\n\n"
        f"Reason: {suspension_obj.reason}\n"
        f"Start date: {suspension_obj.start_date}\n"
        f"End date: {suspension_obj.end_date}\n"
    )
    return send_notification(
        teacher_profile.user,
        title=title,
        message=message,
        notification_type="SUSPENSION",
        url="/authentication/profile/",
    )


# ========================================================
# Notification count for context processors
# ========================================================

def unread_notification_count(user):
    """Return the count of unread notifications for *user* (template context)."""
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(recipient=user, is_read=False).count()


# ========================================================
# Approval-reminder helper
# ========================================================

def send_approval_reminder(user):
    """Notify all admin users that *user* is requesting account approval/role assignment."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admins = User.objects.filter(is_staff=True, is_active=True)
    teacher_name = user.get_full_name() or user.username
    for admin in admins:
        send_notification(
            admin,
            title="Teacher Approval Request",
            message=(
                f"{teacher_name} is requesting account approval and role assignment.\n\n"
                f"Please review their profile and assign an appropriate role.\n\n"
                f"User: {user.username}\n"
                f"Name: {teacher_name}"
            ),
            notification_type="APPROVAL_REQUEST",
            url="/teachers/",
        )
# ========================================================
# Exam-status enforcement (Option 2: admin override)
# ========================================================

def assert_exam_editable(exam, user, action='edit'):
    """Raise PermissionDenied when a mark action is not allowed on this exam.

    Rules (Option 2 - admin override):
      DRAFT      : no mark entry at all (setup phase)         -> blocked for everyone
      ACTIVE     : allowed                                     -> all
      LOCKED     : read-only for teachers, admin can edit      -> non-admin blocked
      PUBLISHED  : read-only for teachers, admin can edit      -> non-admin blocked
      ARCHIVED   : frozen for everyone (historical)            -> blocked for everyone

    Returns None on success; raises PermissionDenied otherwise.
    """
    from django.core.exceptions import PermissionDenied
    status = (exam.status or '').upper()
    is_admin_user = is_admin(user)

    if status == 'DRAFT':
        raise PermissionDenied(
            f'Examination "{exam.code}" is still in DRAFT. '
            f'Activate it before entering or changing marks.'
        )
    if status == 'ARCHIVED':
        raise PermissionDenied(
            f'Examination "{exam.code}" is ARCHIVED and locked for history. '
            f'It cannot be changed.'
        )
    if status in ('LOCKED', 'PUBLISHED') and not is_admin_user:
        raise PermissionDenied(
            f'Examination "{exam.code}" is {status}. '
            f'Only administrators can change marks in this state.'
        )
    return None
