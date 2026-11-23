from django.contrib import admin
from .models import Student, StudentHistory

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'full_name', 'gender', 'current_grade_level', 'current_stream', 'status', 'is_active']
    list_filter = ['gender', 'status', 'is_active', 'current_grade_level', 'current_stream', 'academic_year']
    search_fields = ['admission_number', 'first_name', 'last_name', 'email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Personal Information', {
            'fields': ('admission_number', 'first_name', 'last_name', 'middle_name', 'date_of_birth', 'gender', 'nationality', 'religion')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'address')
        }),
        ('Academic Information', {
            'fields': ('admission_date', 'curriculum', 'current_grade_level', 'current_stream', 'academic_year')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_phone', 'guardian_email', 'guardian_relationship')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(StudentHistory)
class StudentHistoryAdmin(admin.ModelAdmin):
    list_display = ['student', 'academic_year', 'grade_level', 'stream', 'is_current']
    list_filter = ['is_current', 'academic_year', 'grade_level']
    search_fields = ['student__admission_number', 'student__first_name', 'student__last_name']
