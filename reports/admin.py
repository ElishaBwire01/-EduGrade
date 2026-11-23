from django.contrib import admin
from .models import ReportTemplate, GeneratedReport, ReportComment

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_default', 'is_active')
    list_filter = ('template_type', 'is_default', 'is_active')

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'student', 'examination',
                    'status', 'generated_by', 'generated_at')
    list_filter = ('report_type', 'status', 'academic_year', 'term')
    search_fields = ('title',)
    readonly_fields = ('generated_at', 'approved_at', 'published_at')

@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    list_display = ('report', 'user', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
