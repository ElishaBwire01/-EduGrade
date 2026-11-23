from django.contrib import admin
from .models import Examination, ExaminationClass, SubjectScoreConfig

@admin.register(Examination)
class ExaminationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'exam_type', 'academic_year', 'term', 'grade_level', 'status', 'is_active']
    list_filter = ['exam_type', 'status', 'is_active', 'academic_year', 'term', 'grade_level']
    search_fields = ['code', 'name', 'description']
    filter_horizontal = ['subjects']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'exam_type', 'description')
        }),
        ('Academic Information', {
            'fields': ('academic_year', 'term', 'curriculum', 'grade_level', 'subjects')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'results_date')
        }),
        ('Configuration', {
            'fields': ('max_score', 'pass_mark')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ExaminationClass)
class ExaminationClassAdmin(admin.ModelAdmin):
    list_display = ['examination', 'grade_level', 'stream', 'is_active']
    list_filter = ['is_active', 'grade_level']
    search_fields = ['examination__code', 'examination__name']

@admin.register(SubjectScoreConfig)
class SubjectScoreConfigAdmin(admin.ModelAdmin):
    list_display = ['examination', 'subject', 'max_score', 'min_score', 'pass_mark']
    list_filter = ['examination']
    search_fields = ['subject__name']
