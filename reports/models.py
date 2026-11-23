from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from school.models import AcademicYear, Term
from students.models import Student
from examinations.models import Examination

class ReportTemplate(models.Model):
    """Report template configuration"""
    TEMPLATE_TYPES = [
        ('STUDENT', 'Student Report'),
        ('CLASS', 'Class Report'),
        ('SCHOOL', 'School Report'),
        ('SUBJECT', 'Subject Report'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    description = models.TextField(blank=True, null=True)
    template_file = models.FileField(upload_to='report_templates/', blank=True, null=True)
    
    # Configuration
    include_school_info = models.BooleanField(default=True)
    include_student_info = models.BooleanField(default=True)
    include_performance = models.BooleanField(default=True)
    include_analysis = models.BooleanField(default=True)
    include_comments = models.BooleanField(default=True)
    include_signatures = models.BooleanField(default=True)
    
    # Styling
    primary_color = models.CharField(max_length=7, default='#1a5276')
    secondary_color = models.CharField(max_length=7, default='#2e86c1')
    font_family = models.CharField(max_length=50, default='Arial')
    font_size = models.IntegerField(default=11)
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    class Meta:
        db_table = 'report_templates'


class GeneratedReport(models.Model):
    """Generated report record"""
    REPORT_TYPES = [
        ('STUDENT', 'Student Report'),
        ('CLASS', 'Class Report'),
        ('SCHOOL', 'School Report'),
        ('SUBJECT', 'Subject Report'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('GENERATED', 'Generated'),
        ('APPROVED', 'Approved'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    
    # Related objects
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    examination = models.ForeignKey(Examination, on_delete=models.SET_NULL, null=True, blank=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True)
    
    # Files
    pdf_file = models.FileField(upload_to='reports/pdf/', blank=True, null=True)
    word_file = models.FileField(upload_to='reports/word/', blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_reports')
    approved_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"
    
    class Meta:
        db_table = 'generated_reports'
        ordering = ['-generated_at']


class ReportComment(models.Model):
    """Comments on reports"""
    report = models.ForeignKey(GeneratedReport, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at}"
    
    class Meta:
        db_table = 'report_comments'
        ordering = ['created_at']

