from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class AcademicYear(models.Model):
    """Academic year model"""
    name = models.CharField(max_length=50, unique=True)
    year = models.IntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.year} - {self.name}"
    
    class Meta:
        db_table = 'academic_years'
        ordering = ['-year']


class Term(models.Model):
    """School term model"""
    TERM_CHOICES = [
        (1, 'Term 1'),
        (2, 'Term 2'),
        (3, 'Term 3'),
    ]
    
    term_number = models.IntegerField(choices=TERM_CHOICES)
    name = models.CharField(max_length=20)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.academic_year.year} - {self.name}"
    
    class Meta:
        db_table = 'terms'
        ordering = ['academic_year', 'term_number']
        unique_together = ['academic_year', 'term_number']


class Curriculum(models.Model):
    """Curriculum model (8-4-4 or CBC)"""
    CURRICULUM_CHOICES = [
        ('844', '8-4-4'),
        ('CBC', 'CBC'),
    ]
    
    code = models.CharField(max_length=10, choices=CURRICULUM_CHOICES, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'curriculums'
        verbose_name_plural = 'Curriculums'


class GradeLevel(models.Model):
    """Grade/Form level model"""
    LEVEL_CHOICES = [
        ('FORM', 'Form'),
        ('GRADE', 'Grade'),
    ]
    
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='grade_levels')
    level_type = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    level_number = models.IntegerField()  # 1-4 for forms, 1-9+ for grades
    name = models.CharField(max_length=50)  # e.g., "Form 1", "Grade 7"
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.curriculum.code} - {self.name}"
    
    class Meta:
        db_table = 'grade_levels'
        ordering = ['curriculum', 'order']
        unique_together = ['curriculum', 'level_type', 'level_number']


class Stream(models.Model):
    """Stream/Class model"""
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)  # e.g., "2E", "1W"
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='streams')
    capacity = models.IntegerField(default=40)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.grade_level.name} - {self.name}"
    
    class Meta:
        db_table = 'streams'
        ordering = ['grade_level', 'name']
        unique_together = ['grade_level', 'name']


class Subject(models.Model):
    """Subject/Learning Area model"""
    SUBJECT_TYPES = [
        ('CORE', 'Core Subject'),
        ('ELECTIVE', 'Elective'),
        ('EXTRA', 'Extra-curricular'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)
    subject_type = models.CharField(max_length=20, choices=SUBJECT_TYPES, default='CORE')
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='subjects')
    grade_levels = models.ManyToManyField(GradeLevel, related_name='subjects', blank=True)
    max_score = models.IntegerField(default=100)
    min_score = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        db_table = 'subjects'
        ordering = ['name']
        unique_together = ['curriculum', 'code']


class SchoolInfo(models.Model):
    """School information model"""
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    motto = models.CharField(max_length=200, blank=True, null=True)
    logo = models.ImageField(upload_to='school/', blank=True, null=True)
    current_academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'school_info'
        verbose_name_plural = 'School Information'
        
    def save(self, *args, **kwargs):
        if not self.pk and SchoolInfo.objects.exists():
            raise ValueError('Only one SchoolInfo instance allowed')
        super().save(*args, **kwargs)

