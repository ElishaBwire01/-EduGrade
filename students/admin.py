from django.contrib import admin
from .models import Student, StudentHistory

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'first_name', 'last_name',
                    'current_grade_level', 'current_stream', 'status', 'is_active')
    list_filter = ('status', 'is_active', 'current_grade_level', 'current_stream', 'curriculum')
    search_fields = ('admission_number', 'first_name', 'last_name', 'guardian_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(StudentHistory)
class StudentHistoryAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'grade_level', 'stream', 'is_current')
    list_filter = ('is_current', 'academic_year', 'grade_level')
