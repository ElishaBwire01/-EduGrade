from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from examinations.models import Examination
from school.models import Subject, GradeLevel, Stream
from students.models import Student

class MarkEntry(models.Model):
    """Individual mark entry for a student"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('LOCKED', 'Locked'),
        ('APPROVED', 'Approved'),
    ]
    
    # Relationships
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='marks')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    
    # Marks
    score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    grade = models.CharField(max_length=5, blank=True, null=True)
    points = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_active = models.BooleanField(default=True)
    
    # Audit
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='entered_marks')
    entered_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_marks')
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_marks')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'mark_entries'
        unique_together = ['student', 'examination', 'subject']
        ordering = ['student', 'subject']

    def __str__(self):
        return f"{self.student.admission_number} - {self.examination.code} - {self.subject.name}"


class MarkSubmission(models.Model):
    """Track mark submissions by teachers"""
    SUBMISSION_STATUS = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('LOCKED', 'Locked'),
        ('APPROVED', 'Approved'),
    ]
    
    teacher = models.ForeignKey('teachers.TeacherProfile', on_delete=models.CASCADE, related_name='mark_submissions')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='submissions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='submissions')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=SUBMISSION_STATUS, default='DRAFT')
    notes = models.TextField(blank=True, null=True)
    
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='submitted_marks')
    submitted_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='locked_marks')
    locked_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_submissions')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'mark_submissions'
        unique_together = ['teacher', 'examination', 'subject', 'grade_level', 'stream']
        ordering = ['-submission_date']

    def __str__(self):
        return f"{self.teacher.full_name} - {self.examination.code} - {self.subject.name}"


class MarkCorrection(models.Model):
    """Track mark corrections"""
    CORRECTION_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    mark_entry = models.ForeignKey(MarkEntry, on_delete=models.CASCADE, related_name='corrections')
    old_score = models.DecimalField(max_digits=5, decimal_places=1)
    new_score = models.DecimalField(max_digits=5, decimal_places=1)
    reason = models.TextField()
    
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_corrections')
    requested_at = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(max_length=20, choices=CORRECTION_STATUS, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_corrections')
    approved_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'mark_corrections'
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.mark_entry.student.admission_number} - {self.old_score} -> {self.new_score}"

