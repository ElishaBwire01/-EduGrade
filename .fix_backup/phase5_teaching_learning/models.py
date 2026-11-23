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
        ('PP', 'Pre-Primary'),
        ('ECDE', 'ECDE'),
        ('GRADE', 'Grade'),
        ('FORM', 'Form'),
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


# ============================================================
# PHASE 1: CBC FOUNDATION
# Added by blueprint phase 1. Do not remove — dependent code.
# ============================================================

class EducationStage(models.Model):
    """Top-level education stage: ECE, Primary, Middle, Senior, etc."""
    STAGE_CHOICES = [
        ('ECE', 'Early Childhood Education'),
        ('LOWER_PRIMARY', 'Lower Primary (Grade 1-3)'),
        ('UPPER_PRIMARY', 'Upper Primary (Grade 4-6)'),
        ('MIDDLE', 'Middle School (Grade 7-9)'),
        ('SENIOR', 'Senior School (Grade 10-12)'),
    ]
    code = models.CharField(max_length=20, choices=STAGE_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'education_stages'
        ordering = ['order']

    def __str__(self):
        return self.name


class CurriculumVersion(models.Model):
    """A specific version of a curriculum (e.g. CBC 2024 revision)."""
    curriculum = models.ForeignKey(
        Curriculum, on_delete=models.CASCADE, related_name='versions'
    )
    version_code = models.CharField(max_length=20)   # e.g. '2024', '2025'
    name = models.CharField(max_length=150)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    source_document = models.CharField(
        max_length=300, blank=True, null=True,
        help_text='KICD design code / filename'
    )
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'curriculum_versions'
        unique_together = ['curriculum', 'version_code']
        ordering = ['-effective_from']

    def __str__(self):
        return f'{self.curriculum.code} v{self.version_code}'


# ============================================================
# PHASE 2: CURRICULUM CONTENT HIERARCHY
# CurriculumVersion -> LearningArea -> Strand -> SubStrand
#   -> LearningOutcome -> (LearningExperience, InquiryQuestion)
#   + 7 CoreCompetencies, 8 CoreValues, PCIs
# ============================================================

class LearningArea(models.Model):
    """A subject / learning area taught in a specific grade (KICD)."""
    curriculum_version = models.ForeignKey(
        CurriculumVersion, on_delete=models.CASCADE, related_name='learning_areas'
    )
    grade_level = models.ForeignKey(
        GradeLevel, on_delete=models.CASCADE, related_name='learning_areas'
    )
    code = models.CharField(max_length=30)           # e.g. 'MATH'
    name = models.CharField(max_length=150)          # e.g. 'Mathematics'
    short_name = models.CharField(max_length=30, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_core = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'learning_areas'
        unique_together = ['curriculum_version', 'grade_level', 'code']
        ordering = ['grade_level__order', 'order', 'name']

    def __str__(self):
        return f'{self.name} ({self.grade_level.name})'


class Strand(models.Model):
    """Main content division within a learning area."""
    learning_area = models.ForeignKey(
        LearningArea, on_delete=models.CASCADE, related_name='strands'
    )
    code = models.CharField(max_length=30, blank=True, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'strands'
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.name}'


class SubStrand(models.Model):
    """Specific content division within a strand."""
    strand = models.ForeignKey(
        Strand, on_delete=models.CASCADE, related_name='sub_strands'
    )
    code = models.CharField(max_length=30, blank=True, null=True)
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sub_strands'
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.name}'


class CoreCompetency(models.Model):
    """The 7 national core competencies."""
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_competencies'
        ordering = ['order']

    def __str__(self):
        return self.name


class CoreValue(models.Model):
    """The 8 national core values."""
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_values'
        ordering = ['order']

    def __str__(self):
        return self.name


class PCI(models.Model):
    """Pertinent and Contemporary Issues."""
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'pcis'
        verbose_name = 'PCI'
        verbose_name_plural = 'PCIs'
        ordering = ['name']

    def __str__(self):
        return self.name


class LearningOutcome(models.Model):
    """Specific learning outcome under a sub-strand."""
    sub_strand = models.ForeignKey(
        SubStrand, on_delete=models.CASCADE, related_name='learning_outcomes'
    )
    order = models.IntegerField(default=0)
    outcome_text = models.TextField(help_text='By the end of the sub-strand the learner should be able to ...')
    knowledge = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    attitudes = models.TextField(blank=True, null=True)
    values_text = models.TextField(blank=True, null=True)

    competencies = models.ManyToManyField(
        CoreCompetency, blank=True, related_name='learning_outcomes'
    )
    core_values = models.ManyToManyField(
        CoreValue, blank=True, related_name='learning_outcomes'
    )
    pcis = models.ManyToManyField(
        PCI, blank=True, related_name='learning_outcomes'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'learning_outcomes'
        ordering = ['order']

    def __str__(self):
        return self.outcome_text[:80]


class LearningExperience(models.Model):
    """Suggested learning / teaching experience for an outcome."""
    learning_outcome = models.ForeignKey(
        LearningOutcome, on_delete=models.CASCADE, related_name='experiences'
    )
    experience_text = models.TextField()
    resources_needed = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'learning_experiences'
        ordering = ['order']

    def __str__(self):
        return self.experience_text[:80]


class InquiryQuestion(models.Model):
    """Key inquiry question guiding learning."""
    learning_outcome = models.ForeignKey(
        LearningOutcome, on_delete=models.CASCADE, related_name='inquiry_questions'
    )
    question_text = models.CharField(max_length=400)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'inquiry_questions'
        ordering = ['order']

    def __str__(self):
        return self.question_text
