from django.contrib import admin
from .models import (
    Role, UserProfile, PermissionCode, PermissionAssignment,
    AuditLog, Notification, WarningRecord, SuspensionRecord,
)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'user__email')

@admin.register(PermissionCode)
class PermissionCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category')
    list_filter = ('category',)
    search_fields = ('code', 'name')

@admin.register(PermissionAssignment)
class PermissionAssignmentAdmin(admin.ModelAdmin):
    list_display = ('profile', 'permission', 'is_active', 'granted_at', 'expires_at')
    list_filter = ('is_active', 'permission__category')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_id')
    list_filter = ('action', 'model_name')
    search_fields = ('object_repr', 'object_id')
    readonly_fields = [f.name for f in AuditLog._meta.fields]

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')

@admin.register(WarningRecord)
class WarningRecordAdmin(admin.ModelAdmin):
    list_display = ('teacher_profile', 'severity', 'issued_by', 'issued_at', 'acknowledged')

@admin.register(SuspensionRecord)
class SuspensionRecordAdmin(admin.ModelAdmin):
    list_display = ('teacher_profile', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
