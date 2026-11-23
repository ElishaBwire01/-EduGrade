from django.contrib import admin
from .models import (
    AssessmentScheme, KCSEGradeRule, KCSEOverallCalculation, PerformanceLevel,
    AssessmentType, Rubric, RubricCriterion, RubricDescriptor,
    AssessmentComponent, ComponentAggregation,
    StudentKCSEGrade, StudentOverallKCSE,
    StudentCBAAssessment, StudentOverallCBA,
)

@admin.register(AssessmentScheme)
class AssessmentSchemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'curriculum', 'is_active', 'effective_from', 'effective_to')
    list_filter = ('curriculum', 'is_active')
    filter_horizontal = ('grade_levels',)

@admin.register(KCSEGradeRule)
class KCSEGradeRuleAdmin(admin.ModelAdmin):
    list_display = ('scheme', 'grade', 'grade_name', 'points', 'min_score', 'max_score')
    list_filter = ('scheme', 'subject_scope')

@admin.register(KCSEOverallCalculation)
class KCSEOverallCalculationAdmin(admin.ModelAdmin):
    list_display = ('scheme', 'name', 'calculation_type', 'best_subject_count',
                    'min_subjects', 'max_subjects')
    filter_horizontal = ('core_subjects',)

@admin.register(PerformanceLevel)
class PerformanceLevelAdmin(admin.ModelAdmin):
    list_display = ('scheme', 'level_code', 'level_name', 'order')
    list_filter = ('scheme',)

@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = ('scheme', 'name', 'category', 'weight')
    list_filter = ('scheme', 'category')

@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ('scheme', 'name', 'assessment_type', 'subject', 'grade_level', 'is_active')

@admin.register(RubricCriterion)
class RubricCriterionAdmin(admin.ModelAdmin):
    list_display = ('rubric', 'criterion', 'max_level', 'order')

@admin.register(RubricDescriptor)
class RubricDescriptorAdmin(admin.ModelAdmin):
    list_display = ('criterion', 'level', 'descriptor')

@admin.register(AssessmentComponent)
class AssessmentComponentAdmin(admin.ModelAdmin):
    list_display = ('scheme', 'name', 'component_type', 'weight')

@admin.register(ComponentAggregation)
class ComponentAggregationAdmin(admin.ModelAdmin):
    list_display = ('scheme', 'name', 'aggregation_type')
    filter_horizontal = ('components',)

@admin.register(StudentKCSEGrade)
class StudentKCSEGradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'examination', 'subject', 'raw_mark',
                    'grade', 'points', 'is_core', 'is_best_subject')
    list_filter = ('examination', 'grade', 'is_core', 'is_best_subject')

@admin.register(StudentOverallKCSE)
class StudentOverallKCSEAdmin(admin.ModelAdmin):
    list_display = ('student', 'examination', 'total_points', 'mean_grade',
                    'mean_score', 'position')
    list_filter = ('examination', 'mean_grade')

@admin.register(StudentCBAAssessment)
class StudentCBAAssessmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'examination', 'subject', 'rubric',
                    'overall_level', 'score')
    list_filter = ('examination', 'overall_level')

@admin.register(StudentOverallCBA)
class StudentOverallCBAAdmin(admin.ModelAdmin):
    list_display = ('student', 'examination', 'overall_level', 'total_score',
                    'total_weighted_score', 'position')
    list_filter = ('examination', 'overall_level')

# ---- Phase 3: assessment evidence ----
from .models import AssessmentTask, AssessmentEvidence, TeacherObservation, LearnerFeedback

class AssessmentEvidenceInline(admin.TabularInline):
    model = AssessmentEvidence
    extra = 0
    fields = ('evidence_type', 'file', 'caption', 'learning_outcome')
    readonly_fields = ('uploaded_at',)

@admin.register(AssessmentTask)
class AssessmentTaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'task_type', 'scheme', 'grade_level', 'subject', 'assessment_date', 'is_active')
    list_filter = ('task_type', 'scheme', 'grade_level', 'is_active')
    search_fields = ('name', 'description')
    date_hierarchy = 'assessment_date'

@admin.register(AssessmentEvidence)
class AssessmentEvidenceAdmin(admin.ModelAdmin):
    list_display = ('caption', 'evidence_type', 'student_assessment', 'uploaded_by', 'uploaded_at')
    list_filter = ('evidence_type', 'is_active')
    search_fields = ('caption',)

@admin.register(TeacherObservation)
class TeacherObservationAdmin(admin.ModelAdmin):
    list_display = ('student', 'observation_type', 'observed_on', 'recorded_by')
    list_filter = ('observation_type', 'is_active')
    search_fields = ('observation_text',)
    date_hierarchy = 'observed_on'

@admin.register(LearnerFeedback)
class LearnerFeedbackAdmin(admin.ModelAdmin):
    list_display = ('student', 'feedback_type', 'given_on', 'given_by')
    list_filter = ('feedback_type', 'is_active')
    search_fields = ('feedback_text',)
    date_hierarchy = 'given_on'
