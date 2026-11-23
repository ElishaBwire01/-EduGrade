from django.contrib import admin
from .models import (
    AssessmentScheme, KCSEGradeRule, KCSEOverallCalculation,
    PerformanceLevel, AssessmentType, Rubric, RubricCriterion,
    RubricDescriptor, AssessmentComponent, ComponentAggregation,
    StudentKCSEGrade, StudentOverallKCSE, StudentCBAAssessment, StudentOverallCBA
)

@admin.register(AssessmentScheme)
class AssessmentSchemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'curriculum', 'is_active']
    list_filter = ['curriculum', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['grade_levels']

@admin.register(KCSEGradeRule)
class KCSEGradeRuleAdmin(admin.ModelAdmin):
    list_display = ['scheme', 'grade', 'min_score', 'max_score', 'points', 'subject_scope']
    list_filter = ['scheme', 'subject_scope', 'is_active']
    search_fields = ['grade', 'grade_name']

@admin.register(KCSEOverallCalculation)
class KCSEOverallCalculationAdmin(admin.ModelAdmin):
    list_display = ['scheme', 'name', 'calculation_type', 'best_subject_count', 'is_active']
    list_filter = ['scheme', 'calculation_type', 'is_active']
    search_fields = ['name']
    filter_horizontal = ['core_subjects']

@admin.register(PerformanceLevel)
class PerformanceLevelAdmin(admin.ModelAdmin):
    list_display = ['scheme', 'level_code', 'level_name', 'order', 'is_active']
    list_filter = ['scheme', 'is_active']
    search_fields = ['level_code', 'level_name']

@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = ['scheme', 'name', 'category', 'weight', 'is_active']
    list_filter = ['scheme', 'category', 'is_active']
    search_fields = ['name']

@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ['name', 'scheme', 'subject', 'grade_level', 'is_active']
    list_filter = ['scheme', 'is_active', 'subject', 'grade_level']
    search_fields = ['name', 'description']

@admin.register(RubricCriterion)
class RubricCriterionAdmin(admin.ModelAdmin):
    list_display = ['rubric', 'criterion', 'order', 'is_active']
    list_filter = ['rubric', 'is_active']
    search_fields = ['criterion']

@admin.register(RubricDescriptor)
class RubricDescriptorAdmin(admin.ModelAdmin):
    list_display = ['criterion', 'level']
    search_fields = ['descriptor']

@admin.register(AssessmentComponent)
class AssessmentComponentAdmin(admin.ModelAdmin):
    list_display = ['scheme', 'name', 'component_type', 'weight', 'is_active']
    list_filter = ['scheme', 'component_type', 'is_active']
    search_fields = ['name']

@admin.register(ComponentAggregation)
class ComponentAggregationAdmin(admin.ModelAdmin):
    list_display = ['scheme', 'name', 'aggregation_type', 'is_active']
    list_filter = ['scheme', 'aggregation_type', 'is_active']
    search_fields = ['name']
    filter_horizontal = ['components']

@admin.register(StudentKCSEGrade)
class StudentKCSEGradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'examination', 'subject', 'raw_mark', 'grade', 'points']
    list_filter = ['examination', 'subject']
    search_fields = ['student__admission_number', 'student__first_name', 'student__last_name']

@admin.register(StudentOverallKCSE)
class StudentOverallKCSEAdmin(admin.ModelAdmin):
    list_display = ['student', 'examination', 'total_points', 'mean_grade', 'mean_score', 'position']
    list_filter = ['examination']
    search_fields = ['student__admission_number', 'student__first_name', 'student__last_name']

@admin.register(StudentCBAAssessment)
class StudentCBAAssessmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'examination', 'rubric', 'subject', 'overall_level']
    list_filter = ['examination', 'rubric', 'subject']
    search_fields = ['student__admission_number', 'student__first_name', 'student__last_name']

@admin.register(StudentOverallCBA)
class StudentOverallCBAAdmin(admin.ModelAdmin):
    list_display = ['student', 'examination', 'overall_level', 'total_score', 'position']
    list_filter = ['examination', 'overall_level']
    search_fields = ['student__admission_number', 'student__first_name', 'student__last_name']
