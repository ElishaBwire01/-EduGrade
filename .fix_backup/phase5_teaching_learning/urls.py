from django.urls import path
from . import views
from . import setup_views

app_name = 'school'

urlpatterns = [
    # Original school structure
    path('structure/', views.school_structure, name='structure'),
    
    # School Setup
    path('setup/', setup_views.school_setup_dashboard, name='setup_dashboard'),
    
    # Curriculum URLs
    path('curriculum/create/', setup_views.curriculum_create, name='curriculum_create'),
    path('curriculum/<int:curriculum_id>/edit/', setup_views.curriculum_edit, name='curriculum_edit'),
    path('curriculum/<int:curriculum_id>/delete/', setup_views.curriculum_delete, name='curriculum_delete'),

    # Term URLs
    path('term/create/', setup_views.term_create, name='term_create'),
    path('term/<int:term_id>/edit/', setup_views.term_edit, name='term_edit'),
    path('term/<int:term_id>/delete/', setup_views.term_delete, name='term_delete'),

    # Academic Year URLs
    path('api/academic-years/', setup_views.academic_year_list, name='academic_year_list'),
    path('academic-year/create/', setup_views.academic_year_create, name='academic_year_create'),
    path('academic-year/<int:year_id>/edit/', setup_views.academic_year_edit, name='academic_year_edit'),
    path('academic-year/<int:year_id>/delete/', setup_views.academic_year_delete, name='academic_year_delete'),
    
    # Grade Level URLs
    path('grade-level/create/', setup_views.grade_level_create, name='grade_level_create'),
    path('grade-level/<int:grade_id>/edit/', setup_views.grade_level_edit, name='grade_level_edit'),
    path('grade-level/<int:grade_id>/delete/', setup_views.grade_level_delete, name='grade_level_delete'),
    
    # Stream URLs
    path('stream/create/', setup_views.stream_create, name='stream_create'),
    path('stream/<int:stream_id>/edit/', setup_views.stream_edit, name='stream_edit'),
    path('stream/<int:stream_id>/delete/', setup_views.stream_delete, name='stream_delete'),
    
    # Subject URLs
    path('subject/create/', setup_views.subject_create, name='subject_create'),
    path('subject/<int:subject_id>/edit/', setup_views.subject_edit, name='subject_edit'),
    path('subject/<int:subject_id>/delete/', setup_views.subject_delete, name='subject_delete'),
    
    # API URLs
    path('api/grade-levels/', setup_views.api_get_grade_levels, name='api_grade_levels'),
    path('api/streams/', setup_views.api_get_streams, name='api_streams'),
]
