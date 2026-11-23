from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from school.models import AcademicYear, Term, Curriculum, GradeLevel, Stream, Subject

class Examination(models.Model):
    """Examination model"""
    EXAM_TYPES = [
        ('MID_TERM', 'Mid-Term'),
        ('END_TERM', 'End of Term'),
        ('MOCK', 'Mock Examination'),
        ('FINAL', 'Final Examination'),
        ('CAT', 'Continuous Assessment Test'),
        ('ASSIGNMENT', 'Assignment'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('LOCKED', 'Locked'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    description = models.TextField(blank=True, null=True)
    
    # Academic Information
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject, related_name='examinations')
    
    # Date Information
    start_date = models.DateField()
    end_date = models.DateField()
    results_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_active = models.BooleanField(default=True)
    
    # Marks Configuration
    max_score = models.IntegerField(default=100)
    pass_mark = models.IntegerField(default=40)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_examinations')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_examinations')
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.academic_year.year})"
    
    @property
    def subject_count(self):
        return self.subjects.count()
    
    class Meta:
        db_table = 'examinations'
        ordering = ['-academic_year', '-start_date']
        unique_together = ['academic_year', 'term', 'grade_level', 'code']


class ExaminationClass(models.Model):
    """Examination class/stream association"""
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='exam_classes')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.examination.code} - {self.grade_level.name} {self.stream.name}"
    
    class Meta:
        db_table = 'examination_classes'
        unique_together = ['examination', 'grade_level', 'stream']


class SubjectScoreConfig(models.Model):
    """Configure score ranges and grading for subjects"""
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='subject_configs')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    max_score = models.IntegerField(default=100)
    min_score = models.IntegerField(default=0)
    pass_mark = models.IntegerField(default=40)
    
    def __str__(self):
        return f"{self.examination.code} - {self.subject.name}"
    
    class Meta:
        db_table = 'subject_score_configs'
        unique_together = ['examination', 'subject']

