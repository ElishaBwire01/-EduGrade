from django.contrib import admin
from .models import Examination, ExaminationClass, SubjectScoreConfig

@admin.register(Examination)
class ExaminationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'exam_type', 'academic_year', 'term',
                    'curriculum', 'grade_level', 'status', 'is_active')
    list_filter = ('exam_type', 'status', 'is_active', 'academic_year', 'curriculum')
    search_fields = ('name', 'code')
    filter_horizontal = ('subjects',)

@admin.register(ExaminationClass)
class ExaminationClassAdmin(admin.ModelAdmin):
    list_display = ('examination', 'grade_level', 'stream', 'is_active')
    list_filter = ('is_active', 'grade_level')

@admin.register(SubjectScoreConfig)
class SubjectScoreConfigAdmin(admin.ModelAdmin):
    list_display = ('examination', 'subject', 'max_score', 'min_score', 'pass_mark')
