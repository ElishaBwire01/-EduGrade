from django.contrib import admin
from .models import MarkEntry, MarkSubmission, MarkCorrection

@admin.register(MarkEntry)
class MarkEntryAdmin(admin.ModelAdmin):
    list_display = ['student', 'examination', 'subject', 'score', 'grade', 'status']
    list_filter = ['status', 'examination', 'subject', 'grade_level']
    search_fields = ['student__admission_number', 'student__first_name', 'student__last_name']
    readonly_fields = ['entered_at', 'updated_at']

@admin.register(MarkSubmission)
class MarkSubmissionAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'examination', 'subject', 'grade_level', 'stream', 'status']
    list_filter = ['status', 'examination', 'subject', 'grade_level']
    search_fields = ['teacher__first_name', 'teacher__last_name']

@admin.register(MarkCorrection)
class MarkCorrectionAdmin(admin.ModelAdmin):
    list_display = ['mark_entry', 'old_score', 'new_score', 'status', 'requested_at']
    list_filter = ['status']
    search_fields = ['mark_entry__student__admission_number']
