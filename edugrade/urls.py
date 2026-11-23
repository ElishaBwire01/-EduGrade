from django.conf.urls.static import static
from django.conf import settings
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
    path('senior-school/', include('senior_school.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

