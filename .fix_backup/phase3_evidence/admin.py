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
