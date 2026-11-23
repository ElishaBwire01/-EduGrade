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

# ============================================================
# PHASE 5: TEACHING & LEARNING VIEWS
# ============================================================
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from .models import (
    SchemeOfWork, SchemeOfWorkRow, LessonPlan,
    CurriculumCoverage, TeachingResource,
)


@login_required
def scheme_list(request):
    """List all schemes of work visible to the current user."""
    qs = SchemeOfWork.objects.select_related(
        'learning_area', 'grade_level', 'term', 'academic_year', 'teacher__user'
    ).order_by('-academic_year__year', 'term__name', 'learning_area__name')

    # Filter by teacher if the user is a TeacherProfile
    user = request.user
    teacher_profile = getattr(user, 'teacher_profile', None) if hasattr(user, 'teacher_profile') else None
    mine_only = request.GET.get('mine') == '1'
    if mine_only and teacher_profile:
        qs = qs.filter(teacher=teacher_profile)

    schemes = qs.annotate(
        row_count=Count('rows', distinct=True),
        covered_count=Count('rows', filter=Q(rows__coverage__is_complete=True), distinct=True),
    )

    context = {
        'schemes': schemes,
        'mine_only': mine_only,
        'has_teacher_profile': teacher_profile is not None,
    }
    return render(request, 'school/scheme_list.html', context)


@login_required
def scheme_detail(request, scheme_id):
    """Detail tree for one scheme: strand -> substrand -> outcome -> coverage."""
    scheme = get_object_or_404(
        SchemeOfWork.objects.select_related(
            'learning_area', 'grade_level', 'term', 'academic_year', 'teacher__user'
        ),
        id=scheme_id,
    )

    rows = SchemeOfWorkRow.objects.filter(scheme=scheme).select_related(
        'strand', 'sub_strand', 'learning_outcome',
    ).prefetch_related('coverage', 'lesson_plans').order_by('strand__order', 'sub_strand__order', 'order')

    # Group rows into a tree
    tree = {}
    for row in rows:
        la = row.strand.learning_area
        tree.setdefault(la.id, {'la': la, 'strands': {}})
        tree[la.id]['strands'].setdefault(row.strand.id, {'strand': row.strand, 'substrands': {}})
        tree[la.id]['strands'][row.strand.id]['substrands'].setdefault(
            row.sub_strand.id, {'substrand': row.sub_strand, 'rows': []}
        )
        tree[la.id]['strands'][row.strand.id]['substrands'][row.sub_strand.id]['rows'].append(row)

    total = rows.count()
    covered = rows.filter(coverage__is_complete=True).count()
    coverage_pct = round(covered * 100 / total, 1) if total else 0

    context = {
        'scheme': scheme,
        'tree': tree,
        'total_rows': total,
        'covered_rows': covered,
        'coverage_pct': coverage_pct,
    }
    return render(request, 'school/scheme_detail.html', context)


@login_required
def coverage_dashboard(request):
    """Bar chart of coverage per scheme."""
    schemes = SchemeOfWork.objects.select_related(
        'learning_area', 'grade_level', 'term', 'academic_year'
    ).annotate(
        row_count=Count('rows', distinct=True),
        covered_count=Count('rows', filter=Q(rows__coverage__is_complete=True), distinct=True),
    ).order_by('-academic_year__year', 'term__name')

    for s in schemes:
        s.pct = round(s.covered_count * 100 / s.row_count, 1) if s.row_count else 0

    context = {'schemes': schemes}
    return render(request, 'school/coverage_dashboard.html', context)
