"""Senior School pathways — Grades 10-12 CBC."""
from django.db import models


class SeniorSchoolPathway(models.Model):
    CODE_CHOICES = [
        ('STEM', 'STEM'),
        ('SOCIAL', 'Social Sciences'),
        ('ARTS_SPORTS', 'Arts and Sports Science'),
    ]
    code = models.CharField(max_length=20, choices=CODE_CHOICES, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    career_hint = models.TextField(blank=True, null=True,
        help_text='Typical careers associated with this pathway')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'senior_school_pathway'
        ordering = ['order', 'name']
        verbose_name = 'Senior School Pathway'

    def __str__(self):
        return self.name


class PathwayTrack(models.Model):
    pathway = models.ForeignKey(
        SeniorSchoolPathway, on_delete=models.CASCADE, related_name='tracks')
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'pathway_track'
        unique_together = [('pathway', 'code')]
        ordering = ['pathway__order', 'order', 'name']

    def __str__(self):
        return f'{self.pathway.code} / {self.name}'


class PathwaySubject(models.Model):
    SUBJECT_TYPES = [
        ('CORE', 'Core'),
        ('ELECTIVE', 'Elective'),
        ('APPLIED', 'Applied'),
        ('TECHNICAL', 'Technical'),
    ]
    track = models.ForeignKey(
        PathwayTrack, on_delete=models.CASCADE, related_name='subjects')
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    subject_type = models.CharField(max_length=20, choices=SUBJECT_TYPES, default='CORE')
    is_compulsory = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'pathway_subject'
        unique_together = [('track', 'code')]
        ordering = ['track', 'order', 'name']

    def __str__(self):
        return f'{self.code} — {self.name}'


class SubjectCombination(models.Model):
    pathway = models.ForeignKey(
        SeniorSchoolPathway, on_delete=models.CASCADE, related_name='combinations')
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    min_subjects = models.IntegerField(default=3)
    max_subjects = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subject_combination'
        ordering = ['pathway__order', 'code']

    def __str__(self):
        return f'{self.code} — {self.name}'


class CombinationSubject(models.Model):
    combination = models.ForeignKey(
        SubjectCombination, on_delete=models.CASCADE, related_name='combination_subjects')
    subject = models.ForeignKey(
        PathwaySubject, on_delete=models.CASCADE, related_name='in_combinations')
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'combination_subject'
        unique_together = [('combination', 'subject')]
        ordering = ['combination', 'order']

    def __str__(self):
        return f'{self.combination.code} / {self.subject.name}'


class LearnerPathwayPreference(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, related_name='pathway_preferences')
    pathway = models.ForeignKey(
        SeniorSchoolPathway, on_delete=models.CASCADE, related_name='learner_preferences')
    track = models.ForeignKey(
        PathwayTrack, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='learner_preferences')
    combination = models.ForeignKey(
        SubjectCombination, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='learner_preferences')
    preferred_subjects = models.ManyToManyField(
        PathwaySubject, blank=True, related_name='learner_preferences')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, null=True)
    submitted_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='submitted_pathway_preferences')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_pathway_preferences')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'learner_pathway_preference'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student} — {self.pathway.code}'


class LearnerPathwayPlacement(models.Model):
    student = models.OneToOneField(
        'students.Student', on_delete=models.CASCADE, related_name='pathway_placement')
    pathway = models.ForeignKey(
        SeniorSchoolPathway, on_delete=models.CASCADE, related_name='learner_placements')
    track = models.ForeignKey(
        PathwayTrack, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='learner_placements')
    combination = models.ForeignKey(
        SubjectCombination, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='learner_placements')
    academic_year = models.ForeignKey(
        'school.AcademicYear', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pathway_placements')
    confirmed_on = models.DateField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='confirmed_pathway_placements')
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'learner_pathway_placement'
        ordering = ['-confirmed_on']

    def __str__(self):
        return f'{self.student} → {self.pathway.code}'


class CareerInterest(models.Model):
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, related_name='career_interests')
    career_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    related_pathway = models.ForeignKey(
        SeniorSchoolPathway, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='career_interests')
    priority = models.IntegerField(default=1, help_text='1 = top choice')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'career_interest'
        ordering = ['student', 'priority']

    def __str__(self):
        return f'{self.student} — {self.career_name}'


class CareerGuidanceRecord(models.Model):
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, related_name='career_guidance')
    session_date = models.DateField()
    topic = models.CharField(max_length=250)
    notes = models.TextField()
    recommendations = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='career_guidance_records')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'career_guidance_record'
        ordering = ['-session_date']

    def __str__(self):
        return f'{self.student} — {self.topic} ({self.session_date})'
