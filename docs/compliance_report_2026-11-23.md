# EduGrade Compliance Report — 2026-11-23

**Verified**: 22 / 37 (59.5%)
**Implemented**: 9
**Partial**: 0
**Missing**: 6

## Method

This report uses **behavioral verification**, not keyword matching.
A requirement is only VERIFIED if:
- a database query confirms the behavior, AND
- a named test proves it passes (for importer-related checks).

| ID | Status | Actual/Expected | Test | Requirement |
|----|--------|-----------------|------|-------------|
| C-01 | VERIFIED | 2/2 | - | CurriculumVersion unique per (curriculum, version_code) |
| C-02 | VERIFIED | 5/5 | - | EducationStage seeded (ECE, LP, UP, MIDDLE, SENIOR) |
| C-03 | VERIFIED | 14/14 | - | GradeLevel seeded (PP1-PP2 + 1-12 = 14) |
| C-04 | VERIFIED | 1/1 | - | LearningArea content present |
| C-05 | VERIFIED | 2/1 | - | Strand content present |
| C-06 | VERIFIED | 3/1 | - | SubStrand content present |
| C-07 | VERIFIED | 4/1 | - | LearningOutcome content present |
| C-10 | VERIFIED | 7/7 | - | CoreCompetency seeded (7) |
| C-11 | VERIFIED | 8/8 | - | CoreValue seeded (8) |
| C-12 | VERIFIED | 13/13 | - | PCI seeded (13) |
| I-01 | VERIFIED | 1/1 | - | import_kicd command present |
| I-03 | VERIFIED | 1/1 | test_duplicate_rows_reported | Importer detects AND reports CSV duplicates |
| I-04 | VERIFIED | 1/1 | test_ambiguous_db_match_errors | Importer detects ambiguous DB matches |
| I-06 | VERIFIED | 1/1 | test_rollback_on_failure | Importer rolls back on error (tested) |
| I-07 | VERIFIED | 1/1 | test_idempotent_import | Importer idempotent (tested) |
| I-08 | VERIFIED | 1/1 | test_knowledge_skills_populated | Importer populates knowledge/skills/attitudes/values |
| A-01 | VERIFIED | 4/4 | - | PerformanceLevel seeded (4) |
| A-02 | MISSING | 0/1 | - | Rubric content present |
| A-04 | IMPLEMENTED | 0 | - | AssessmentTask model present |
| A-05 | IMPLEMENTED | 0 | - | StudentCBAAssessment model present |
| A-06 | IMPLEMENTED | 0 | - | AssessmentEvidence model present |
| A-07 | IMPLEMENTED | 0 | - | TeacherObservation model present |
| A-08 | IMPLEMENTED | 0 | - | LearnerFeedback model present |
| S-01 | VERIFIED | 3/3 | - | SeniorSchoolPathway seeded (3) |
| S-02 | VERIFIED | 8/1 | - | PathwayTrack seeded |
| S-03 | VERIFIED | 25/1 | - | PathwaySubject seeded |
| S-04 | VERIFIED | 7/1 | - | SubjectCombination seeded |
| S-05 | MISSING | None/1 | - | CSL modelled |
| T-01 | IMPLEMENTED | 0 | - | SchemeOfWork model present |
| T-03 | IMPLEMENTED | 0 | - | LessonPlan model present |
| E-01 | MISSING | None/1 | - | SNE categories modelled |
| E-02 | MISSING | None/4 | - | SNE levels modelled (4) |
| E-03 | MISSING | None/1 | - | IEP modelled |
| E-09 | MISSING | None/1 | - | SNE flag on Student |
| R-01 | IMPLEMENTED | 0 | - | ReportTemplate model present |
| P-02 | IMPLEMENTED | 0 | - | AuditLog model present |
| P-03 | VERIFIED | 3/3 | - | Role/PermissionCode/PermissionAssignment models present |