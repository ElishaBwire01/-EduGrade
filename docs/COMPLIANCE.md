# EduGrade Compliance Register

**Purpose**: Every functional requirement in EduGrade must trace to an authoritative
Kenyan source, be implemented, and be verifiable. This register is the single source
of truth for that traceability.

**Status vocabulary**:
- `MISSING` — not implemented
- `PARTIAL` — schema exists but not populated / not verified
- `IMPLEMENTED` — code present, not yet verified end-to-end
- `VERIFIED` — implementation tested and evidence captured
- `N/A` — does not apply

**Last updated**: see `python manage.py compliance_audit`

---

## 1. Authority map

| Authority | Domain | Official URL |
|-----------|--------|--------------|
| KICD (Kenya Institute of Curriculum Development) | Curriculum designs, learning outcomes, teaching guidelines | https://kicd.ac.ke/cbc-materials/curriculum-designs/ |
| KICD — SNE | Adapted and stage-based curriculum | https://kicd.ac.ke/cbc-materials/curriculum-designs/sne-curriculum-designs/ |
| KNEC (Kenya National Examinations Council) | Competency-Based Assessment, national assessments | https://www.knec.ac.ke/ |
| KNEC — CBA | CBA framework and procedures | https://www.knec.ac.ke/competency-based-assessment-cba/ |
| Ministry of Education | Education policy, school structures, implementation guidelines | https://www.education.go.ke/ |
| ODPC (Office of the Data Protection Commissioner) | Data Protection Act 2019 — children's data | https://www.odpc.go.ke/ |

---

## 2. Requirement traceability

Each row: **Requirement** → **Source** → **Model** → **Test** → **Status**.

### 2.1 Curriculum structure (KICD)

| # | Requirement | Source | Model | Test | Status |
|---|-------------|--------|-------|------|--------|
| C-01 | Curriculum versions tracked with effective dates | KICD design revisions | `school.CurriculumVersion` | `school.tests.test_curriculum_version_uniqueness` | PARTIAL |
| C-02 | Education stages: ECE, Lower Primary, Upper Primary, Middle, Senior | KICD Basic Education structure | `school.EducationStage` | `school.tests.test_education_stages_seeded` | PARTIAL |
| C-03 | Grade levels PP1–PP2, 1–12 | KICD Basic Education structure | `school.GradeLevel` | `school.tests.test_grade_levels_seeded` | PARTIAL |
| C-04 | Learning areas per grade | KICD curriculum designs | `school.LearningArea` | (content import) | PARTIAL |
| C-05 | Strands per learning area | KICD curriculum designs | `school.Strand` | (content import) | PARTIAL |
| C-06 | Sub-strands per strand | KICD curriculum designs | `school.SubStrand` | (content import) | PARTIAL |
| C-07 | Learning outcomes per sub-strand, including knowledge/skills/attitudes/values | KICD curriculum designs | `school.LearningOutcome` | (content import) | PARTIAL |
| C-08 | Learning experiences per outcome | KICD curriculum designs | `school.LearningExperience` | (content import) | PARTIAL |
| C-09 | Key inquiry questions per outcome | KICD curriculum designs | `school.InquiryQuestion` | (content import) | PARTIAL |
| C-10 | Seven core competencies mapped to outcomes | KICD Basic Education Framework | `school.CoreCompetency` + M2M on LO | (content import) | PARTIAL |
| C-11 | Eight core values mapped to outcomes | KICD Basic Education Framework | `school.CoreValue` + M2M on LO | (content import) | PARTIAL |
| C-12 | PCIs (Pertinent and Contemporary Issues) mapped | KICD Basic Education Framework | `school.PCI` + M2M on LO | (content import) | PARTIAL |

### 2.2 Curriculum importer (KICD content)

| # | Requirement | Source | Model | Test | Status |
|---|-------------|--------|-------|------|--------|
| I-01 | Import from CSV with required columns | project spec | `core.management.commands.import_kicd` | `core.tests.test_import_kicd_columns` | IMPLEMENTED |
| I-02 | Reject missing required columns | project spec | (validation) | (to add) | PARTIAL |
| I-03 | Detect duplicate rows within CSV | project spec | (validation) | (to add) | MISSING |
| I-04 | Detect ambiguous existing DB matches | project spec | (validation) | (to add) | MISSING |
| I-05 | Strict mode: unknown reference codes = error | project spec | (validation) | (to add) | PARTIAL |
| I-06 | Rollback all changes on any error | project spec | (transaction) | (to add) | IMPLEMENTED |
| I-07 | Idempotent — importing same CSV twice = no duplicates | project spec | (get_or_create) | (to add) | PARTIAL |
| I-08 | Populate knowledge/skills/attitudes/values_text | KICD learning outcome schema | `import_kicd` | (to add) | MISSING |
| I-09 | Populate order fields | project spec | `import_kicd` | (to add) | MISSING |
| I-10 | `--validate-only` mode | project spec | `import_kicd` | (to add) | PARTIAL |
| I-11 | `--dry-run` mode | project spec | `import_kicd` | (to add) | IMPLEMENTED |
| I-12 | `--update-existing` controlled updates | project spec | `import_kicd` | (to add) | PARTIAL |

### 2.3 Competency-Based Assessment (KNEC)

| # | Requirement | Source | Model | Test | Status |
|---|-------------|--------|-------|------|--------|
| A-01 | Performance levels (BE/AE/ME/EE) | KICD assessment guidance | `grading.PerformanceLevel` | (to add) | PARTIAL |
| A-02 | Rubrics per learning area | KNEC CBA framework | `grading.Rubric` | (to add) | MISSING |
| A-03 | Rubric criteria + descriptors | KNEC CBA framework | `grading.RubricCriterion`, `RubricDescriptor` | (to add) | MISSING |
| A-04 | Assessment tasks linked to learning outcomes | KICD assessment guidance | `grading.AssessmentTask` | (to add) | IMPLEMENTED |
| A-05 | CBA assessment records per learner | KNEC CBA framework | `grading.StudentCBAAssessment` | (to add) | IMPLEMENTED |
| A-06 | Assessment evidence (photos/videos/docs) | KICD CBC assessment guidance | `grading.AssessmentEvidence` | (to add) | IMPLEMENTED |
| A-07 | Teacher observations | KICD assessment guidance | `grading.TeacherObservation` | (to add) | IMPLEMENTED |
| A-08 | Learner feedback | KICD assessment guidance | `grading.LearnerFeedback` | (to add) | IMPLEMENTED |
| A-09 | Overall CBA per learner per term/year | KICD report structure | `grading.StudentOverallCBA` | (to add) | IMPLEMENTED |

### 2.4 Senior School (KICD Grades 10–12)

| # | Requirement | Source | Model | Test | Status |
|---|-------------|--------|-------|------|--------|
| S-01 | Three pathways: STEM, Social Sciences, Arts & Sports Science | KICD Senior School designs | `senior_school.SeniorSchoolPathway` | (to add) | IMPLEMENTED |
| S-02 | Tracks per pathway | KICD Senior School designs | `senior_school.PathwayTrack` | (to add) | PARTIAL |
| S-03 | Subjects per track (full KICD list) | KICD Senior School designs | `senior_school.PathwaySubject` | (to add) | PARTIAL |
| S-04 | Approved subject combinations | KICD Senior School designs | `senior_school.SubjectCombination` | (to add) | PARTIAL |
| S-05 | Community Service Learning (CSL) as required | KICD Senior School designs | (to add) | (to add) | MISSING |
| S-06 | Learner pathway preference | MoE placement policy | `senior_school.LearnerPathwayPreference` | (to add) | IMPLEMENTED |
| S-07 | Learner pathway placement | MoE placement policy | `senior_school.LearnerPathwayPlacement` | (to add) | IMPLEMENTED |
| S-08 | Career interests and guidance | MoE career guidance | `senior_school.CareerInterest`, `CareerGuidanceRecord` | (to add) | IMPLEMENTED |

### 2.5 Inclusive Education — SNE (KICD)

| # | Requirement | Source | Model | Test | Status |
|---|-------------|--------|-------|------|--------|
| E-01 | SNE categories (Visual, Hearing, Physical, Intellectual, etc.) | KICD SNE designs | (to add) | (to add) | MISSING |
| E-02 | Four stage-based levels: Foundation, Intermediate, Prevocational, Vocational | KICD SNE designs | (to add) | (to add) | MISSING |
| E-03 | Individualized Education Programme (IEP) | KICD SNE designs | (to add) | (to add) | MISSING |
| E-04 | Assistive technology tracking | KICD SNE designs | (to add) | (to add) | MISSING |
| E-05 | Adapted assessment methods | KICD SNE designs | (to add) | (to add) | MISSING |
| E-06 | KFLEA (Foundation Level assessment) | KNEC | (to add) | (to add) | MISSING |
| E-07 | KILEA (Intermediate Level assessment) | KNEC | (to add) | (to add) | MISSING |
| E-08 | KPLEA (Prevocational Level assessment) | KNEC | (to add) | (to add) | MISSING |
| E-09 | Learner SNE flag | KICD SNE designs | `students.Student.status` (add choice) | (to add) | MISSING |

### 2.6 Teaching & curriculum delivery (KICD)

| # | Requirement | Source | Model | Test | Status |
|---|-------------|--------|-------|------|--------|
| T-01 | Schemes of work per learning area per term | KICD teaching guidance | `school.SchemeOfWork` | (to add) | IMPLEMENTED |
| T-02 | Scheme rows per week with learning outcome links | KICD teaching guidance | `school.SchemeOfWorkRow` | (to add) | IMPLEMENTED |
| T-03 | Lesson plans linked to scheme rows | KICD teaching guidance | `school.LessonPlan` | (to add) | IMPLEMENTED |
| T-04 | Lesson activities per plan | KICD teaching guidance | `school.LessonActivity` | (to add) | IMPLEMENTED |
| T-05 | Curriculum coverage tracking | KICD teaching guidance | `school.CurriculumCoverage` | (to add) | IMPLEMENTED |
| T-06 | Teaching resources | KICD recommended resources | `school.TeachingResource` | (to add) | IMPLEMENTED |
| T-07 | Teacher reflections | KICD reflective teaching | `school.TeacherReflection` | (to add) | IMPLEMENTED |

### 2.7 Reporting

| # | Requirement | Source | Model | Test | Status |
|---|-------------|--------|-------|------|--------|
| R-01 | Report templates | KICD report structure | `reports.ReportTemplate` | (to add) | PARTIAL |
| R-02 | Generated reports per learner | KICD report structure | `reports.GeneratedReport` | (to add) | PARTIAL |
| R-03 | Report comments | KICD report structure | `reports.ReportComment` | (to add) | PARTIAL |

### 2.8 Data protection (ODPC / Data Protection Act 2019)

| # | Requirement | Source | Model | Test | Status |
|---|-------------|--------|-------|------|--------|
| P-01 | Authentication on all learner-data views | DPA 2019 | `django.contrib.auth` | (to add) | PARTIAL |
| P-02 | Audit log of sensitive operations | DPA 2019 | `core.AuditLog` | (to add) | PARTIAL |
| P-03 | Role-based access control | DPA 2019 | `core.Role`, `PermissionAssignment` | (to add) | PARTIAL |
| P-04 | Secure cookies + HSTS in production | DPA 2019 | `settings.py` | (to add) | MISSING |
| P-05 | Retention policy for student records | DPA 2019 | (policy doc) | (to add) | MISSING |
| P-06 | Parental/guardian consent tracking | DPA 2019 (children's data) | (to add) | (to add) | MISSING |

---

## 3. Change log

Every phase appends one row here.

| Date | Phase | Change | By |
|------|-------|--------|-----|
| 2026-11-23 | 0 | Compliance register initialized | Phase 0 script |
