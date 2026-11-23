from django.urls import path
from . import views

app_name = 'marks'

urlpatterns = [
    path('entry/', views.mark_entry, name='entry'),
    path('view/', views.mark_view, name='view'),
    path('correction/', views.mark_correction, name='correction'),
    path('api/classes/', views.api_get_classes, name='api_classes'),
    
    # Admin mark management
    path('admin/', views.admin_mark_management, name='admin_mark_management'),
    path('admin/edit/<int:mark_entry_id>/', views.admin_mark_edit, name='admin_mark_edit'),
]
