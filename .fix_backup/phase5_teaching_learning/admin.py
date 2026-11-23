from django.contrib import admin
from .models import (
    AcademicYear, Term, Curriculum, GradeLevel, Stream, Subject, SchoolInfo,
)

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'term_number', 'academic_year', 'is_active')
    list_filter = ('is_active', 'academic_year')

@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    list_filter = ('is_active',)

@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'curriculum', 'level_type', 'level_number', 'order', 'is_active')
    list_filter = ('curriculum', 'level_type', 'is_active')

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'grade_level', 'capacity', 'is_active')
    list_filter = ('grade_level', 'is_active')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'short_name', 'curriculum', 'subject_type', 'is_active')
    list_filter = ('curriculum', 'subject_type', 'is_active')
    filter_horizontal = ('grade_levels',)

@admin.register(SchoolInfo)
class SchoolInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'current_academic_year')

# ---- Phase 2: curriculum content hierarchy ----
from .models import (
    LearningArea, Strand, SubStrand,
    CoreCompetency, CoreValue, PCI,
    LearningOutcome, LearningExperience, InquiryQuestion,
)

class StrandInline(admin.TabularInline):
    model = Strand
    extra = 0
    fields = ('order', 'name', 'code', 'is_active')

@admin.register(LearningArea)
class LearningAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade_level', 'curriculum_version', 'code', 'is_core', 'is_active')
    list_filter = ('curriculum_version', 'grade_level', 'is_core', 'is_active')
    search_fields = ('name', 'code')
    inlines = [StrandInline]

class SubStrandInline(admin.TabularInline):
    model = SubStrand
    extra = 0
    fields = ('order', 'name', 'code', 'is_active')

@admin.register(Strand)
class StrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'learning_area', 'order', 'is_active')
    list_filter = ('learning_area__grade_level', 'learning_area__curriculum_version', 'is_active')
    search_fields = ('name',)
    inlines = [SubStrandInline]

class LearningOutcomeInline(admin.TabularInline):
    model = LearningOutcome
    extra = 0
    fields = ('order', 'outcome_text', 'is_active')
    show_change_link = True

@admin.register(SubStrand)
class SubStrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'strand', 'order', 'is_active')
    list_filter = ('strand__learning_area__grade_level', 'is_active')
    search_fields = ('name',)
    inlines = [LearningOutcomeInline]

class LearningExperienceInline(admin.TabularInline):
    model = LearningExperience
    extra = 0
    fields = ('order', 'experience_text')

class InquiryQuestionInline(admin.TabularInline):
    model = InquiryQuestion
    extra = 0
    fields = ('order', 'question_text')

@admin.register(LearningOutcome)
class LearningOutcomeAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'sub_strand', 'order', 'is_active')
    list_filter = ('sub_strand__strand__learning_area__grade_level', 'is_active')
    search_fields = ('outcome_text',)
    filter_horizontal = ('competencies', 'core_values', 'pcis')
    inlines = [LearningExperienceInline, InquiryQuestionInline]

    def short_text(self, obj):
        return obj.outcome_text[:60]

@admin.register(CoreCompetency)
class CoreCompetencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')

@admin.register(CoreValue)
class CoreValueAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')

@admin.register(PCI)
class PCIAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')

@admin.register(LearningExperience)
class LearningExperienceAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'learning_outcome', 'order')
    search_fields = ('experience_text',)

    def short_text(self, obj):
        return obj.experience_text[:60]

@admin.register(InquiryQuestion)
class InquiryQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'learning_outcome', 'order')
    search_fields = ('question_text',)
