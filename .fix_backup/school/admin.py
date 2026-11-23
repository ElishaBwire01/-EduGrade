from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from .models import (
    AcademicYear, Term, Curriculum, GradeLevel, 
    Stream, Subject, SchoolInfo
)
from .services import reallocate_and_delete

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['year', 'name', 'is_current', 'start_date', 'end_date']
    list_filter = ['is_current']
    search_fields = ['year', 'name']
    ordering = ['-year']

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'term_number', 'is_active', 'start_date', 'end_date']
    list_filter = ['academic_year', 'is_active']
    search_fields = ['name']
    ordering = ['academic_year', 'term_number']

@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']

@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'curriculum', 'level_type', 'level_number', 'order', 'is_active']
    list_filter = ['curriculum', 'level_type', 'is_active']
    search_fields = ['name']

    def delete_view(self, request, object_id, extra_context=None):
        grade = self.get_object(request, object_id)
        if not grade:
            return super().delete_view(request, object_id, extra_context)
        has_dependants = grade.students.exists() or grade.streams.filter(is_active=True).exists()
        if not has_dependants:
            return super().delete_view(request, object_id, extra_context)
        if request.method == 'POST':
            destination_grade = GradeLevel.objects.filter(
                pk=request.POST.get('destination_grade'), is_active=True
            ).exclude(pk=grade.pk).first()
            destination_stream = Stream.objects.filter(
                pk=request.POST.get('destination_stream'), is_active=True,
                grade_level=destination_grade,
            ).first() if destination_grade else None
            if not destination_grade or not destination_stream:
                messages.error(request, 'Select a valid destination grade and stream.')
            else:
                reallocate_and_delete(grade, destination_grade, destination_stream, request.user)
                messages.success(request, f'{grade} deleted and its learners and teachers reallocated.')
                return redirect(reverse('admin:school_gradelevel_changelist'))
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'object': grade,
            'destination_grades': GradeLevel.objects.filter(is_active=True).exclude(pk=grade.pk),
            'destination_streams': Stream.objects.filter(is_active=True).exclude(grade_level=grade),
            'title': f'Reallocate dependants before deleting {grade}',
        }
        return TemplateResponse(request, 'admin/reallocate_grade_delete.html', context)

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'grade_level', 'capacity', 'is_active']
    list_filter = ['grade_level', 'is_active']
    search_fields = ['name', 'code']

    def delete_view(self, request, object_id, extra_context=None):
        stream = self.get_object(request, object_id)
        if not stream:
            return super().delete_view(request, object_id, extra_context)
        has_dependants = (
            stream.students.exists()
            or stream.classteacher_set.exists()
            or stream.teacherassignment_set.exists()
        )
        if not has_dependants:
            return super().delete_view(request, object_id, extra_context)
        if request.method == 'POST':
            destination_stream = Stream.objects.filter(
                pk=request.POST.get('destination_stream'), is_active=True,
            ).exclude(pk=stream.pk).select_related('grade_level').first()
            if not destination_stream:
                messages.error(request, 'Select a valid destination stream.')
            else:
                reallocate_and_delete(stream, destination_stream.grade_level, destination_stream, request.user)
                messages.success(request, f'{stream} deleted and its learners and teachers reallocated.')
                return redirect(reverse('admin:school_stream_changelist'))
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'object': stream,
            'destination_streams': Stream.objects.filter(is_active=True).exclude(pk=stream.pk),
            'title': f'Reallocate dependants before deleting {stream}',
        }
        return TemplateResponse(request, 'admin/reallocate_stream_delete.html', context)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'short_name', 'curriculum', 'subject_type', 'is_active']
    list_filter = ['curriculum', 'subject_type', 'is_active']
    search_fields = ['code', 'name']
    filter_horizontal = ['grade_levels']

@admin.register(SchoolInfo)
class SchoolInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'current_academic_year']
