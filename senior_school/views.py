from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import (
    SeniorSchoolPathway, PathwayTrack, PathwaySubject,
    SubjectCombination, LearnerPathwayPlacement, LearnerPathwayPreference,
)


@login_required
def pathway_list(request):
    pathways = SeniorSchoolPathway.objects.filter(is_active=True).prefetch_related(
        'tracks__subjects', 'combinations'
    ).order_by('order', 'name')

    data = []
    for p in pathways:
        data.append({
            'pathway': p,
            'track_count': p.tracks.count(),
            'subject_count': PathwaySubject.objects.filter(track__pathway=p).count(),
            'combination_count': p.combinations.count(),
        })

    return render(request, 'senior_school/pathway_list.html', {'pathway_data': data})


@login_required
def pathway_detail(request, pathway_id):
    pathway = get_object_or_404(
        SeniorSchoolPathway.objects.prefetch_related(
            'tracks__subjects', 'combinations__combination_subjects__subject'
        ),
        id=pathway_id,
    )
    return render(request, 'senior_school/pathway_detail.html', {'pathway': pathway})


@login_required
def learner_pathway_detail(request, student_id):
    from students.models import Student
    student = get_object_or_404(Student, id=student_id)

    placement = LearnerPathwayPlacement.objects.filter(
        student=student, is_active=True).first()
    preferences = LearnerPathwayPreference.objects.filter(
        student=student).order_by('-created_at')[:5]
    careers = student.career_interests.filter(is_active=True).order_by('priority')

    return render(request, 'senior_school/learner_pathway.html', {
        'student': student,
        'placement': placement,
        'preferences': preferences,
        'careers': careers,
    })
