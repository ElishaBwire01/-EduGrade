from django.contrib import admin
from .models import TeacherProfile, TeacherAssignment, TeacherRequest, ClassTeacher

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['staff_number', 'full_name', 'gender', 'status', 'is_active']
    list_filter = ['gender', 'status', 'is_active']
    search_fields = ['staff_number', 'first_name', 'last_name', 'email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('staff_number', 'first_name', 'last_name', 'middle_name', 'gender', 'date_of_birth', 'phone_number', 'email', 'address')
        }),
        ('Employment Information', {
            'fields': ('employment_date', 'qualification', 'specialization')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'subject', 'grade_level', 'stream', 'status', 'is_class_teacher']
    list_filter = ['status', 'is_class_teacher', 'academic_year', 'grade_level']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'subject__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TeacherRequest)
class TeacherRequestAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'request_type', 'subject', 'grade_level', 'status', 'requested_date']
    list_filter = ['request_type', 'status', 'academic_year']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'reason']
    readonly_fields = ['requested_date']

@admin.register(ClassTeacher)
class ClassTeacherAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'grade_level', 'stream', 'academic_year', 'is_active']
    list_filter = ['is_active', 'academic_year', 'grade_level']
    search_fields = ['teacher__first_name', 'teacher__last_name']
