from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_teacher', 'is_student', 'is_staff', 'is_active')
    list_filter = ('is_teacher', 'is_student', 'is_staff', 'is_active', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('EduGrade Roles', {'fields': ('phone_number', 'is_teacher', 'is_student')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('EduGrade Roles', {'fields': ('phone_number', 'is_teacher', 'is_student')}),
    )
