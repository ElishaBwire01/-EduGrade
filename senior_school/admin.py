from django.contrib import admin
from .models import (
    SeniorSchoolPathway, PathwayTrack, PathwaySubject,
    SubjectCombination, CombinationSubject,
    LearnerPathwayPreference, LearnerPathwayPlacement,
    CareerInterest, CareerGuidanceRecord,
)


class PathwayTrackInline(admin.TabularInline):
    model = PathwayTrack
    extra = 0
    fields = ('order', 'code', 'name', 'description', 'is_active')


@admin.register(SeniorSchoolPathway)
class SeniorSchoolPathwayAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    inlines = [PathwayTrackInline]


class PathwaySubjectInline(admin.TabularInline):
    model = PathwaySubject
    extra = 0
    fields = ('order', 'code', 'name', 'subject_type', 'is_compulsory', 'is_active')


@admin.register(PathwayTrack)
class PathwayTrackAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'pathway', 'order', 'is_active')
    list_filter = ('pathway', 'is_active')
    search_fields = ('code', 'name')
    inlines = [PathwaySubjectInline]


class CombinationSubjectInline(admin.TabularInline):
    model = CombinationSubject
    extra = 0
    fields = ('order', 'subject', 'is_required')


@admin.register(SubjectCombination)
class SubjectCombinationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'pathway', 'min_subjects', 'max_subjects', 'is_active')
    list_filter = ('pathway', 'is_active')
    search_fields = ('code', 'name')
    inlines = [CombinationSubjectInline]


@admin.register(PathwaySubject)
class PathwaySubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'track', 'subject_type', 'is_compulsory', 'is_active')
    list_filter = ('track__pathway', 'subject_type', 'is_active')
    search_fields = ('code', 'name')


@admin.register(LearnerPathwayPreference)
class LearnerPathwayPreferenceAdmin(admin.ModelAdmin):
    list_display = ('student', 'pathway', 'track', 'status', 'created_at')
    list_filter = ('pathway', 'status')
    search_fields = ('student__admission_number', 'student__first_name', 'student__last_name')
    filter_horizontal = ('preferred_subjects',)


@admin.register(LearnerPathwayPlacement)
class LearnerPathwayPlacementAdmin(admin.ModelAdmin):
    list_display = ('student', 'pathway', 'track', 'combination', 'confirmed_on', 'is_active')
    list_filter = ('pathway', 'is_active', 'academic_year')
    search_fields = ('student__admission_number', 'student__first_name', 'student__last_name')


@admin.register(CareerInterest)
class CareerInterestAdmin(admin.ModelAdmin):
    list_display = ('student', 'career_name', 'related_pathway', 'priority', 'is_active')
    list_filter = ('related_pathway', 'is_active')
    search_fields = ('career_name', 'student__admission_number')


@admin.register(CareerGuidanceRecord)
class CareerGuidanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'topic', 'session_date', 'recorded_by')
    list_filter = ('session_date',)
    search_fields = ('topic', 'student__admission_number')
    date_hierarchy = 'session_date'


@admin.register(CombinationSubject)
class CombinationSubjectAdmin(admin.ModelAdmin):
    list_display = ('combination', 'subject', 'is_required', 'order')
    list_filter = ('is_required', 'combination__pathway')
    search_fields = ('combination__code', 'subject__name')
