from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils import timezone
from school.models import Subject, GradeLevel, Stream, AcademicYear, Curriculum, Term

class TeacherProfile(models.Model):
    """Extended teacher profile"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ON_LEAVE', 'On Leave'),
        ('RESIGNED', 'Resigned'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    
    # Personal Information
    staff_number = models.CharField(max_length=50, unique=True)
    tsc_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='teachers/', blank=True, null=True)
    
    # Employment Information
    employment_date = models.DateField()
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_teachers')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_teachers')
    
    CREATED_VIA_CHOICES = [
        ('SELF_REGISTER', 'Self-Registered'),
        ('MANUAL', 'Manually Added'),
    ]
    created_via = models.CharField(max_length=20, choices=CREATED_VIA_CHOICES, default='SELF_REGISTER')
    
    def __str__(self):
        return f"{self.staff_number} - {self.full_name}"
    
    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def can_manage_students(self):
        return self.class_teacher_assignments.filter(is_active=True).exists()
    
    class Meta:
        db_table = 'teacher_profiles'
        ordering = ['staff_number']


class TeacherAssignment(models.Model):
    """Teacher subject and class assignments"""
    ASSIGNMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    
    is_class_teacher = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS, default='PENDING')
    assigned_date = models.DateField(auto_now_add=True)
    approved_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_assignments')
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.teacher.full_name} - {self.subject.name} - {self.grade_level.name} {self.stream.name}"
    
    class Meta:
        db_table = 'teacher_assignments'
        ordering = ['teacher', 'academic_year', 'subject']
        unique_together = ['teacher', 'subject', 'grade_level', 'stream', 'academic_year']


class TeacherRequest(models.Model):
    """Teacher request for new assignments"""
    REQUEST_TYPES = [
        ('NEW', 'New Assignment'),
        ('TRANSFER', 'Transfer'),
        ('REMOVE', 'Remove Assignment'),
    ]

    ROLES = [
        ('teacher', 'Teacher'),
        ('class_teacher', 'Class Teacher'),
    ]

    REQUEST_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    role = models.CharField(max_length=20, choices=ROLES, default='teacher')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, null=True, blank=True)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)

    reason = models.TextField()
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='PENDING')
    admin_notes = models.TextField(blank=True, null=True)
    requested_date = models.DateTimeField(auto_now_add=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')

    def __str__(self):
        return f"{self.teacher.full_name} - {self.get_request_type_display()} - {self.status}"

    class Meta:
        db_table = 'teacher_requests'
        ordering = ['-requested_date']


class ClassTeacher(models.Model):
    """Class teacher assignments"""
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='class_teacher_assignments')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    assigned_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.teacher.full_name} - {self.grade_level.name} {self.stream.name} ({self.academic_year.year})"
    
    class Meta:
        db_table = 'class_teachers'
        ordering = ['academic_year', 'grade_level', 'stream']
        unique_together = ['grade_level', 'stream', 'academic_year']


class ClassTeacherRequest(models.Model):
    """A class teacher requests a specific function / permission.

    Examples:
      - Request to add learners to their assigned class
      - Request school-wide mark-entry for a specific subject
      - Request to edit marks for specific students
      - Request to generate reports for a broader scope

    The request is REVIEWED by an administrator.  The teacher does NOT
    gain the permission until the admin approves.
    """
    REQUEST_TYPES = [
        ('ADD_LEARNER',      "Add learners to class"),
        ('TRANSFER_LEARNER',  "Transfer learners"),
        ('ENTER_MARKS',       "Enter marks"),
        ('EDIT_MARKS',        "Edit marks"),
        ('SCHOOL_WIDE_MARKS', "School-wide mark entry"),
        ('GENERATE_REPORT',   "Generate reports"),
        ('VIEW_ANALYTICS',    "View analytics"),
        ('OTHER',             "Other (specify)"),
    ]

    REQUEST_STATUS = [
        ('PENDING',  'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name='class_teacher_requests'
    )
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPES)
    
    # Scope — what the teacher is asking to operate on
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.SET_NULL, null=True, blank=True)
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True)

    # Optional list of specific student admission numbers (comma-separated)
    specific_students = models.TextField(
        blank=True,
        help_text="Comma-separated admission numbers (if requesting access to specific learners only)."
    )

    reason = models.TextField()
    description = models.TextField(blank=True, null=True)
    duration_days = models.IntegerField(
        default=7,
        help_text="How long the granted permission should last (in days)."
    )

    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='PENDING')
    admin_notes = models.TextField(blank=True, null=True)

    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_class_teacher_requests'
    )

    # When approved, the system creates a PermissionAssignment with this expiry
    granted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.teacher.full_name} — {self.get_request_type_display()} — {self.status}"

    class Meta:
        db_table = 'class_teacher_requests'
        ordering = ['-requested_at']

