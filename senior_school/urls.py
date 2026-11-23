from django.urls import path
from . import views

app_name = 'senior_school'

urlpatterns = [
    path('pathways/', views.pathway_list, name='pathway_list'),
    path('pathways/<int:pathway_id>/', views.pathway_detail, name='pathway_detail'),
    path('learner/<int:student_id>/', views.learner_pathway_detail, name='learner_pathway_detail'),
]
