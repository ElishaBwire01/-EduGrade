from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from school.models import AcademicYear, Curriculum, GradeLevel, Stream

class Student(models.Model):
    """Student model"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('GRADUATED', 'Graduated'),
        ('TRANSFERRED', 'Transferred'),
        ('WITHDRAWN', 'Withdrawn'),
    ]
    
    # Personal Information
    admission_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    nationality = models.CharField(max_length=50, default='Kenyan')
    religion = models.CharField(max_length=50, blank=True, null=True)
    
    # Contact Information
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Academic Information
    admission_date = models.DateField()
    curriculum = models.ForeignKey(Curriculum, on_delete=models.SET_NULL, null=True)
    current_grade_level = models.ForeignKey(GradeLevel, on_delete=models.SET_NULL, null=True, related_name='students')
    current_stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True, related_name='students')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True)
    
    # Guardian Information
    guardian_name = models.CharField(max_length=200, blank=True, null=True)
    guardian_phone = models.CharField(max_length=15, blank=True, null=True)
    guardian_email = models.EmailField(blank=True, null=True)
    guardian_relationship = models.CharField(max_length=50, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_students')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_students')
    
    def __str__(self):
        return f"{self.admission_number} - {self.full_name}"
    
    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    class Meta:
        db_table = 'students'
        ordering = ['admission_number']


class StudentHistory(models.Model):
    """Student academic history"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='history')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True)
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.SET_NULL, null=True)
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.grade_level} - {self.academic_year}"
    
    class Meta:
        db_table = 'student_history'
        ordering = ['-academic_year', '-created_at']

