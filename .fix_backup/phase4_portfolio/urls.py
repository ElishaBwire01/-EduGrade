from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='list'),
    path('create/', views.student_create, name='create'),
    path('bulk-transfer/', views.student_bulk_transfer, name='bulk_transfer'),
    path('<int:student_id>/', views.student_detail, name='detail'),
    path('<int:student_id>/edit/', views.student_edit, name='edit'),
    path('<int:student_id>/delete/', views.student_delete, name='delete'),
    path('<int:student_id>/transfer/', views.student_transfer, name='transfer'),
    path('api/search/', views.api_students_search, name='api_search'),
]
