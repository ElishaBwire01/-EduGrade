from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from school.models import Curriculum, GradeLevel, Subject, AcademicYear, Term
from students.models import Student
from examinations.models import Examination

# ============ CURRICULUM & ASSESSMENT SCHEMES ============

class AssessmentScheme(models.Model):
    """Assessment scheme for a curriculum"""
    CURRICULUM_CHOICES = [
        ('844', '8-4-4 / KCSE'),
        ('CBC', 'CBC / CBA'),
    ]
    
    name = models.CharField(max_length=100)
    curriculum = models.CharField(max_length=10, choices=CURRICULUM_CHOICES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Which grade levels this applies to
    grade_levels = models.ManyToManyField(GradeLevel, related_name='assessment_schemes', blank=True)
    
    # Academic year range
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.get_curriculum_display()} - {self.name}"
    
    class Meta:
        db_table = 'assessment_schemes'
        ordering = ['curriculum', 'name']


# ============ KCSE / 8-4-4 MODELS ============

class KCSEGradeRule(models.Model):
    """KCSE grade boundaries and points"""
    SUBJECT_CHOICES = [
        ('ALL', 'All Subjects'),
        ('SPECIFIC', 'Specific Subject'),
    ]
    
    scheme = models.ForeignKey(AssessmentScheme, on_delete=models.CASCADE, related_name='kcse_rules')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    subject_scope = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='ALL')
    
    # Grade definition
    grade = models.CharField(max_length=3)  # A, A-, B+, etc.
    grade_name = models.CharField(max_length=50)  # Very Good, Good, etc.
    points = models.DecimalField(max_digits=3, decimal_places=1)  # 12, 11, 10, etc.
    
    # Mark boundaries
    min_score = models.IntegerField()
    max_score = models.IntegerField()
    
    # Descriptor
    descriptor = models.CharField(max_length=100, blank=True, null=True)
    
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.grade}: {self.min_score}-{self.max_score} ({self.points} pts)"
    
    class Meta:
        db_table = 'kcse_grade_rules'
        ordering = ['scheme', 'order', 'min_score']


class KCSEOverallCalculation(models.Model):
    """KCSE overall grade calculation methodology"""
    CALCULATION_TYPES = [
        ('STANDARD', 'Standard - Best 5 + Core Subjects'),
        ('CUSTOM', 'Custom Configuration'),
    ]
    
    scheme = models.ForeignKey(AssessmentScheme, on_delete=models.CASCADE, related_name='kcse_calculations')
    name = models.CharField(max_length=100)
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES, default='STANDARD')
    
    # Core subjects required
    core_subjects = models.ManyToManyField(Subject, related_name='kcse_core', blank=True)
    
    # Number of best subjects to include beyond core
    best_subject_count = models.IntegerField(default=5)
    
    # Minimum subjects required
    min_subjects = models.IntegerField(default=7)
    max_subjects = models.IntegerField(default=9)
    
    # Grade boundaries for overall result
    grade_boundaries = models.JSONField(default=dict, blank=True)
    # Example: {"A": 80, "A-": 75, "B+": 70, ...}
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.calculation_type}"
    
    class Meta:
        db_table = 'kcse_overall_calculations'


# ============ CBC / CBA MODELS ============

class PerformanceLevel(models.Model):
    """CBC/CBA performance levels (PL1-PL4)"""
    LEVEL_CODES = [
        ('PL4', 'Exceeding Expectations'),
        ('PL3', 'Meeting Expectations'),
        ('PL2', 'Approaching Expectations'),
        ('PL1', 'Below Expectations'),
    ]
    
    scheme = models.ForeignKey(AssessmentScheme, on_delete=models.CASCADE, related_name='cbc_levels')
    level_code = models.CharField(max_length=3, choices=LEVEL_CODES)
    level_name = models.CharField(max_length=50)
    descriptor = models.TextField()
    order = models.IntegerField(default=0)
    
    # Numeric equivalent for reporting (optional)
    numeric_value = models.IntegerField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.level_code}: {self.level_name}"
    
    class Meta:
        db_table = 'performance_levels'
        ordering = ['scheme', 'order']


class AssessmentType(models.Model):
    """CBC assessment types"""
    ASSESSMENT_CATEGORIES = [
        ('FORMATIVE', 'Formative Assessment'),
        ('SUMMATIVE', 'Summative Assessment'),
        ('SBA', 'School-Based Assessment'),
        ('KJSEA', 'KJSEA Assessment'),
    ]
    
    scheme = models.ForeignKey(AssessmentScheme, on_delete=models.CASCADE, related_name='cbc_assessment_types')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=ASSESSMENT_CATEGORIES)
    description = models.TextField(blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.weight}%)"
    
    class Meta:
        db_table = 'cbc_assessment_types'


class Rubric(models.Model):
    """CBC assessment rubric"""
    scheme = models.ForeignKey(AssessmentScheme, on_delete=models.CASCADE, related_name='cbc_rubrics')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    assessment_type = models.ForeignKey(AssessmentType, on_delete=models.SET_NULL, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'cbc_rubrics'


class RubricCriterion(models.Model):
    """Individual rubric criteria"""
    rubric = models.ForeignKey(Rubric, on_delete=models.CASCADE, related_name='criteria')
    criterion = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    max_level = models.ForeignKey(PerformanceLevel, on_delete=models.SET_NULL, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.rubric.name} - {self.criterion}"
    
    class Meta:
        db_table = 'cbc_rubric_criteria'
        ordering = ['rubric', 'order']


class RubricDescriptor(models.Model):
    """Performance descriptions for each level in a criterion"""
    criterion = models.ForeignKey(RubricCriterion, on_delete=models.CASCADE, related_name='descriptors')
    level = models.ForeignKey(PerformanceLevel, on_delete=models.CASCADE)
    descriptor = models.TextField()
    
    def __str__(self):
        return f"{self.criterion.criterion} - {self.level.level_code}"
    
    class Meta:
        db_table = 'cbc_rubric_descriptors'
        unique_together = ['criterion', 'level']


# ============ ASSESSMENT COMPONENT AGGREGATION ============

class AssessmentComponent(models.Model):
    """Components that make up an assessment (e.g., SBA, Summative)"""
    COMPONENT_TYPES = [
        ('SBA', 'School-Based Assessment'),
        ('SUMMATIVE', 'Summative Assessment'),
        ('PROJECT', 'Project'),
        ('EXAMINATION', 'Examination'),
        ('PRACTICAL', 'Practical'),
        ('OTHER', 'Other'),
    ]
    
    scheme = models.ForeignKey(AssessmentScheme, on_delete=models.CASCADE, related_name='components')
    name = models.CharField(max_length=100)
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.weight}%)"
    
    class Meta:
        db_table = 'assessment_components'


class ComponentAggregation(models.Model):
    """How to aggregate components for final result"""
    AGGREGATION_TYPES = [
        ('WEIGHTED', 'Weighted Average'),
        ('SUM', 'Sum of Scores'),
        ('CUSTOM', 'Custom Formula'),
    ]
    
    scheme = models.ForeignKey(AssessmentScheme, on_delete=models.CASCADE, related_name='aggregations')
    name = models.CharField(max_length=100)
    aggregation_type = models.CharField(max_length=20, choices=AGGREGATION_TYPES, default='WEIGHTED')
    components = models.ManyToManyField(AssessmentComponent, related_name='aggregations')
    formula = models.TextField(blank=True, null=True)  # For custom formulas
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'component_aggregations'


# ============ STUDENT RESULTS ============

class StudentKCSEGrade(models.Model):
    """Student's KCSE grade for a subject"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='kcse_grades')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='kcse_grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    
    raw_mark = models.DecimalField(max_digits=5, decimal_places=1)
    grade = models.CharField(max_length=3)
    points = models.DecimalField(max_digits=3, decimal_places=1)
    
    # Whether this subject is counted in overall calculation
    is_core = models.BooleanField(default=False)
    is_best_subject = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.subject.name}: {self.grade} ({self.points})"
    
    class Meta:
        db_table = 'student_kcse_grades'
        unique_together = ['student', 'examination', 'subject']


class StudentOverallKCSE(models.Model):
    """Student's overall KCSE result"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='overall_kcse')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='overall_kcse')
    
    total_points = models.DecimalField(max_digits=5, decimal_places=1)
    mean_grade = models.CharField(max_length=3)
    mean_score = models.DecimalField(max_digits=5, decimal_places=1)
    
    # Breakdown
    core_subjects_count = models.IntegerField(default=0)
    best_subjects_count = models.IntegerField(default=0)
    total_subjects_used = models.IntegerField(default=0)
    
    position = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.mean_grade} ({self.total_points})"
    
    class Meta:
        db_table = 'student_overall_kcse'
        unique_together = ['student', 'examination']


class StudentCBAAssessment(models.Model):
    """Student's CBC assessment result for a rubric"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='cbc_assessments')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='cbc_assessments')
    rubric = models.ForeignKey(Rubric, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    learning_outcome = models.ForeignKey('school.LearningOutcome', on_delete=models.SET_NULL, null=True, blank=True, related_name='cba_assessments')
    
    # Results per criterion
    criterion_results = models.JSONField(default=dict)
    # Example: {"criterion_1": "PL3", "criterion_2": "PL4", ...}
    
    # Overall result
    overall_level = models.ForeignKey(PerformanceLevel, on_delete=models.SET_NULL, null=True, related_name='cbc_results')
    teacher_notes = models.TextField(blank=True, null=True)
    
    # For component aggregation
    component = models.ForeignKey(AssessmentComponent, on_delete=models.SET_NULL, null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.rubric.name}"
    
    class Meta:
        db_table = 'student_cbc_assessments'
        unique_together = ['student', 'examination', 'rubric']


class StudentOverallCBA(models.Model):
    """Student's overall CBC/CBA result"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='overall_cba')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='overall_cba')
    
    # Overall performance level
    overall_level = models.ForeignKey(PerformanceLevel, on_delete=models.SET_NULL, null=True)
    
    # Component scores
    component_scores = models.JSONField(default=dict)
    # Example: {"SBA": 78.5, "Summative": 82.0}
    
    # Aggregated results
    total_score = models.DecimalField(max_digits=5, decimal_places=1)
    total_weighted_score = models.DecimalField(max_digits=5, decimal_places=1)
    
    # Grade equivalent (optional - for reporting)
    grade_equivalent = models.CharField(max_length=3, blank=True, null=True)
    
    position = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.overall_level.level_code if self.overall_level else 'N/A'}"
    
    class Meta:
        db_table = 'student_overall_cba'
        unique_together = ['student', 'examination']


# ============================================================
# PHASE 3: ASSESSMENT EVIDENCE LAYER
# Adds discrete tasks, evidence files, observations, feedback.
# Links existing StudentCBAAssessment to LearningOutcome.
# ============================================================

class AssessmentTask(models.Model):
    """A discrete assessment task created by a teacher.

    Examples: "Classroom measurement exercise", "Oral reading",
    "Group project on water cycle".
    """
    TASK_TYPES = [
        ('OBSERVATION', 'Observation'),
        ('ORAL', 'Oral Assessment'),
        ('WRITTEN', 'Written Assessment'),
        ('PRACTICAL', 'Practical Assessment'),
        ('PROJECT', 'Project'),
        ('GROUP', 'Group Activity'),
        ('EXPERIMENT', 'Experiment'),
        ('PORTFOLIO', 'Portfolio'),
        ('PERFORMANCE', 'Performance'),
        ('PRESENTATION', 'Presentation'),
        ('PEER', 'Peer Assessment'),
        ('SELF', 'Self Assessment'),
    ]
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='OBSERVATION')
    scheme = models.ForeignKey(AssessmentScheme, on_delete=models.CASCADE, related_name='tasks')
    learning_outcome = models.ForeignKey(
        'school.LearningOutcome', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assessment_tasks'
    )
    rubric = models.ForeignKey(
        Rubric, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks'
    )
    subject = models.ForeignKey('school.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    grade_level = models.ForeignKey('school.GradeLevel', on_delete=models.SET_NULL, null=True, blank=True)
    academic_year = models.ForeignKey('school.AcademicYear', on_delete=models.SET_NULL, null=True, blank=True)
    term = models.ForeignKey('school.Term', on_delete=models.SET_NULL, null=True, blank=True)
    assessment_date = models.DateField()
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='created_assessment_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'assessment_tasks'
        ordering = ['-assessment_date', 'name']

    def __str__(self):
        return f'{self.name} ({self.assessment_date})'


class AssessmentEvidence(models.Model):
    """A piece of evidence (file, photo, video, doc) attached to a
    StudentCBAAssessment record. Optionally linked to a specific
    LearningOutcome for traceability.
    """
    EVIDENCE_TYPES = [
        ('PHOTO', 'Photograph'),
        ('VIDEO', 'Video'),
        ('DOCUMENT', 'Document'),
        ('AUDIO', 'Audio'),
        ('OTHER', 'Other'),
    ]
    student_assessment = models.ForeignKey(
        StudentCBAAssessment, on_delete=models.CASCADE,
        related_name='evidence_items'
    )
    evidence_type = models.CharField(max_length=20, choices=EVIDENCE_TYPES, default='PHOTO')
    file = models.FileField(upload_to='evidence/%Y/%m/')
    caption = models.CharField(max_length=300, blank=True, null=True)
    learning_outcome = models.ForeignKey(
        'school.LearningOutcome', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evidence_items'
    )
    uploaded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='uploaded_evidence')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'assessment_evidence'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.get_evidence_type_display()} - {self.caption or self.file.name}'


class TeacherObservation(models.Model):
    """A qualitative observation about a learner's progress on a
    specific learning outcome. This is NOT converted into a mark —
    it captures the evidence of learning per CBC guidance.
    """
    OBSERVATION_TYPES = [
        ('STRENGTH', 'Strength Observed'),
        ('PROGRESS', 'Progress Noted'),
        ('CONCERN', 'Concern Noted'),
        ('NEUTRAL', 'Neutral Observation'),
    ]
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='observations')
    learning_outcome = models.ForeignKey(
        'school.LearningOutcome', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='observations'
    )
    observation_type = models.CharField(max_length=20, choices=OBSERVATION_TYPES, default='NEUTRAL')
    observation_text = models.TextField()
    observed_on = models.DateField()
    recorded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='recorded_observations')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'teacher_observations'
        ordering = ['-observed_on', '-created_at']

    def __str__(self):
        return f'{self.get_observation_type_display()} — {self.student.full_name if hasattr(self.student, "full_name") else self.student}'


class LearnerFeedback(models.Model):
    """Feedback given to a learner about an assessment — separate
    from the score/grade. Can be shown on reports.
    """
    FEEDBACK_TYPES = [
        ('GENERAL', 'General Feedback'),
        ('IMPROVEMENT', 'Area for Improvement'),
        ('SUPPORT', 'Recommended Support'),
        ('PRAISE', 'Recognition / Praise'),
    ]
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='feedback_items')
    student_assessment = models.ForeignKey(
        StudentCBAAssessment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='feedback_items'
    )
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, default='GENERAL')
    feedback_text = models.TextField()
    given_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='given_feedback')
    given_on = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'learner_feedback'
        ordering = ['-given_on', '-created_at']

    def __str__(self):
        return f'{self.get_feedback_type_display()} — {self.feedback_text[:60]}'

