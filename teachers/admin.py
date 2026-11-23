from django.contrib import admin
from .models import (
    TeacherProfile, TeacherAssignment, TeacherRequest,
    ClassTeacher, ClassTeacherRequest,
)

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('staff_number', 'first_name', 'last_name', 'status',
                    'employment_date', 'is_active')
    list_filter = ('status', 'is_active', 'gender', 'created_via')
    search_fields = ('staff_number', 'tsc_number', 'first_name', 'last_name', 'email')

@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'grade_level', 'stream',
                    'academic_year', 'status', 'is_class_teacher')
    list_filter = ('status', 'academic_year', 'grade_level', 'stream', 'is_class_teacher')

@admin.register(TeacherRequest)
class TeacherRequestAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'request_type', 'role', 'status', 'requested_date')
    list_filter = ('request_type', 'status', 'role')

@admin.register(ClassTeacher)
class ClassTeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'grade_level', 'stream', 'academic_year', 'is_active')
    list_filter = ('is_active', 'academic_year', 'grade_level')

@admin.register(ClassTeacherRequest)
class ClassTeacherRequestAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'request_type', 'status', 'requested_at', 'reviewed_by')
    list_filter = ('request_type', 'status')
