from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('auth/', include('authentication.urls')),
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('examinations/', include('examinations.urls')),
    path('marks/', include('marks.urls')),
    path('grading/', include('grading.urls')),
    path('reports/', include('reports.urls')),
    path('school/', include('school.urls')),
]
