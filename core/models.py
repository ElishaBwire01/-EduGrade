from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils import timezone


class Role(models.Model):
    """User roles for the system"""
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('TEACHER', 'Teacher'),
        ('CLASS_TEACHER', 'Class Teacher'),
        ('PARENT', 'Parent'),
        ('STUDENT', 'Student'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        db_table = 'roles'
        ordering = ['name']


class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role.get_name_display() if self.role else 'No Role'}"
    
    @property
    def is_suspended(self):
        """True if the user has an active suspension."""
        return self.suspensions.filter(
            status='ACTIVE',
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date(),
        ).exists()

    def effective_permissions(self):
        """Return queryset of active, non-expired PermissionAssignment rows."""
        now = timezone.now()
        return self.permission_assignments.filter(
            is_active=True,
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )

    class Meta:
        db_table = 'user_profiles'
        ordering = ['user__first_name', 'user__last_name']


class PermissionCode(models.Model):
    """Catalog of all permission codes available in the system."""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default='General')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'permission_codes'
        ordering = ['category', 'name']


class PermissionAssignment(models.Model):
    """Links a UserProfile to a PermissionCode with optional scope.

    A null scope on a globally-allowed permission means the permission
    applies school-wide.  Non-null scope fields restrict the permission
    to that subject + grade + stream + academic-year + term combination.
    """
    profile = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='permission_assignments'
    )
    permission = models.ForeignKey(
        PermissionCode, on_delete=models.CASCADE, related_name='assignments'
    )

    # Optional scope — restricts where the permission applies
    subject = models.ForeignKey(
        'school.Subject', on_delete=models.SET_NULL, null=True, blank=True
    )
    grade_level = models.ForeignKey(
        'school.GradeLevel', on_delete=models.SET_NULL, null=True, blank=True
    )
    stream = models.ForeignKey(
        'school.Stream', on_delete=models.SET_NULL, null=True, blank=True
    )
    academic_year = models.ForeignKey(
        'school.AcademicYear', on_delete=models.SET_NULL, null=True, blank=True
    )
    term = models.ForeignKey(
        'school.Term', on_delete=models.SET_NULL, null=True, blank=True
    )
    examination = models.ForeignKey(
        'examinations.Examination', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Temporal controls
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    granted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='granted_permissions'
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        scope = self.scope_label or "school-wide"
        return f"{self.profile.user.username} — {self.permission.code} @ {scope}"

    @property
    def scope_label(self):
        parts = []
        if self.subject:
            parts.append(self.subject.name)
        if self.grade_level:
            parts.append(self.grade_level.name)
        if self.stream:
            parts.append(self.stream.name)
        if self.academic_year:
            parts.append(str(self.academic_year.year))
        if self.term:
            parts.append(self.term.name)
        return ", ".join(parts) if parts else None

    class Meta:
        db_table = 'permission_assignments'
        ordering = ['-granted_at']


class AuditLog(models.Model):
    """Audit log for system actions"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('LOCK', 'Lock'),
        ('UNLOCK', 'Unlock'),
        ('GRANT', 'Grant Permission'),
        ('REVOKE', 'Revoke Permission'),
        ('WARN', 'Warning'),
        ('SUSPEND', 'Suspend'),
        ('ARCHIVE', 'Archive'),
        ('NOTIFY', 'Notification Sent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    changes = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']


class Notification(models.Model):
    """In-system notification for a user."""
    NOTIFICATION_TYPES = [
        ('ASSIGNMENT',  'New Assignment'),
        ('APPROVAL',    'Request Approved'),
        ('REJECTION',   'Request Rejected'),
        ('WARNING',     'Warning Issued'),
        ('SUSPENSION',  'Suspension'),
        ('MARK_EDIT',   'Mark Edit Approved'),
        ('REPORT',      'Report Status Change'),
        ('SYSTEM',      'System Message'),
        ('REMINDER',    'Reminder'),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    related_object_id = models.CharField(max_length=100, blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    url = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient.username} — {self.title} — {'read' if self.is_read else 'unread'}"

    @property
    def age_display(self):
        from datetime import timedelta
        diff = timezone.now() - self.created_at
        if diff < timedelta(minutes=1):
            return "just now"
        if diff < timedelta(hours=1):
            return f"{int(diff.total_seconds() // 60)}m ago"
        if diff < timedelta(days=1):
            return f"{int(diff.total_seconds() // 3600)}h ago"
        return f"{diff.days}d ago"

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']


class WarningRecord(models.Model):
    """A warning issued to a teacher."""
    SEVERITY_CHOICES = [
        ('LOW',      'Low'),
        ('MEDIUM',   'Medium'),
        ('HIGH',     'High'),
        ('CRITICAL', 'Critical'),
    ]

    teacher_profile = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='warnings'
    )
    reason = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    issued_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='issued_warnings'
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.teacher_profile.user.username} — {self.severity} — {self.reason}"

    class Meta:
        db_table = 'warning_records'
        ordering = ['-issued_at']


class SuspensionRecord(models.Model):
    """A temporary suspension of a teacher account."""
    STATUS_CHOICES = [
        ('PENDING',   'Pending'),
        ('ACTIVE',    'Active'),
        ('EXPIRED',   'Expired'),
        ('REVOKED',   'Revoked'),
    ]

    teacher_profile = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='suspensions'
    )
    reason = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    issued_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='issued_suspensions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='revoked_suspensions'
    )

    def __str__(self):
        return f"{self.teacher_profile.user.username} — {self.status} — {self.start_date} to {self.end_date}"

    @property
    def is_current(self):
        today = timezone.now().date()
        return self.status == 'ACTIVE' and self.start_date <= today <= self.end_date

    class Meta:
        db_table = 'suspension_records'
        ordering = ['-created_at']
