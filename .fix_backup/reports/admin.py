from django.contrib import admin
from .models import ReportTemplate, GeneratedReport, ReportComment

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_default', 'is_active']
    list_filter = ['template_type', 'is_default', 'is_active']
    search_fields = ['name', 'description']

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'student', 'examination', 'status', 'generated_at']
    list_filter = ['report_type', 'status', 'academic_year', 'term']
    search_fields = ['title', 'student__first_name', 'student__last_name']
    readonly_fields = ['generated_at', 'generated_by']

@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    list_display = ['report', 'user', 'created_at']
    search_fields = ['comment']
