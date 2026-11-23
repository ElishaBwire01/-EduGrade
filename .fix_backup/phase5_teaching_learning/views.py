from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from .models import AcademicYear, Term, Curriculum, GradeLevel, Stream, Subject

@login_required
def school_structure(request):
    """School structure overview"""
    context = {
        'academic_years': AcademicYear.objects.all().order_by('-year'),
        'terms': Term.objects.select_related('academic_year').all(),
        'curriculums': Curriculum.objects.filter(is_active=True),
        'grade_levels': GradeLevel.objects.select_related('curriculum').filter(is_active=True),
        'streams': Stream.objects.select_related('grade_level').filter(is_active=True),
        'subjects': Subject.objects.select_related('curriculum').filter(is_active=True),
    }
    return render(request, 'school/structure.html', context)


@login_required
def get_grade_levels(request):
    """API endpoint to get grade levels by curriculum"""
    curriculum_id = request.GET.get('curriculum_id')
    if curriculum_id:
        grade_levels = GradeLevel.objects.filter(
            curriculum_id=curriculum_id,
            is_active=True
        ).values('id', 'name', 'level_number')
        return JsonResponse({'grade_levels': list(grade_levels)})
    return JsonResponse({'grade_levels': []})


@login_required
def get_streams(request):
    """API endpoint to get streams by grade level"""
    grade_level_id = request.GET.get('grade_level_id')
    if grade_level_id:
        streams = Stream.objects.filter(
            grade_level_id=grade_level_id,
            is_active=True
        ).values('id', 'name', 'code')
        return JsonResponse({'streams': list(streams)})
    return JsonResponse({'streams': []})
