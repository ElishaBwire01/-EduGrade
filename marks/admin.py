from django.contrib import admin
from .models import MarkEntry, MarkSubmission, MarkCorrection

@admin.register(MarkEntry)
class MarkEntryAdmin(admin.ModelAdmin):
    list_display = ('student', 'examination', 'subject', 'score', 'grade',
                    'points', 'status', 'entered_by')
    list_filter = ('status', 'examination', 'subject', 'grade_level', 'stream')
    search_fields = ('student__admission_number', 'student__first_name', 'student__last_name')
    readonly_fields = ('entered_at', 'updated_at', 'approved_at')

@admin.register(MarkSubmission)
class MarkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'examination', 'subject', 'grade_level',
                    'stream', 'status', 'submission_date')
    list_filter = ('status', 'examination', 'grade_level', 'stream')

@admin.register(MarkCorrection)
class MarkCorrectionAdmin(admin.ModelAdmin):
    list_display = ('mark_entry', 'old_score', 'new_score', 'status', 'requested_at')
    list_filter = ('status',)
    readonly_fields = ('requested_at', 'approved_at')
