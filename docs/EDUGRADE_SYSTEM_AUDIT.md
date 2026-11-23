# EduGrade System Audit

**Date**: 2026-11-23
**Method**: Three read-only inspection blocks covering curriculum, teaching, assessment, learner progress, teacher workflows, competencies, intervention, analytics, reports, security, SNE, parent, CSL, QA, deployment, and tests.
**Principle**: A model's existence does not prove a workflow works. A zero-row table does not prove a feature is broken. Evidence over assumption.

---

## 1. Django applications inventory (10 apps, 76 models)

| App | Models | Purpose |
|-----|--------|---------|
| reports | 3 | Report templates, generated reports, comments |
| grading | 18 | Assessment schemes, rubrics, CBA, evidence, observations, feedback, KCSE |
| marks | 3 | Mark entry, submission, correction |
| examinations | 3 | Examinations, exam classes, subject score config |
| authentication | 0 | Login, logout, register, profile |
| core | 8 | Roles, permissions, audit, notifications, warnings, suspension |
| school | 25 | Curriculum, grade levels, streams, learning outcomes, schemes, lesson plans |
| students | 2 | Students, student history |
| teachers | 5 | Teacher profiles, assignments, requests, class teachers |
| senior_school | 9 | Pathways, tracks, subjects, combinations, career guidance |

---

## 2. Curriculum state

### 2.1 Hierarchy models — PRESERVE

| Model | Fields | Status |
|-------|--------|--------|
| `Curriculum` | code (CBC/844), name, is_active | Well-designed |
| `CurriculumVersion` | version_code, source_document, is_current, effective_from/to | Complete |
| `EducationStage` | 5 stages (ECE, LP, UP, Middle, Senior) | Seeded |
| `GradeLevel` | 14 grades (PP1, PP2, 1–12) | All seeded |
| `LearningArea` | code, name, is_core, grade_level FK | Complete |
| `Strand` | code, name, order | Complete |
| `SubStrand` | code, name, order | Complete |
| `LearningOutcome` | **outcome_text, knowledge, skills, attitudes, values_text** + M2M (competencies, core_values, pcis) | KICD-complete schema |
| `LearningExperience` | experience_text, resources_needed | Complete |
| `InquiryQuestion` | question_text | Complete |
| `CoreCompetency` | 7 rows | Seeded correctly |
| `CoreValue` | 8 rows | Seeded correctly |
| `PCI` | 13 rows | Seeded |

### 2.2 Curriculum data — CRITICAL GAP

| Grade | LearningAreas | LearningOutcomes |
|-------|---------------|------------------|
| PP1 | 0 | 0 |
| PP2 | 0 | 0 |
| Grade 1 | 0 | 0 |
| Grade 2 | 0 | 0 |
| Grade 3 | 0 | 0 |
| Grade 4 | 0 | 0 |
| **Grade 5** | **1 (Mathematics)** | **4** |
| Grade 6 | 0 | 0 |
| Grade 7 | 0 | 0 |
| Grade 8 | 0 | 0 |
| Grade 9 | 0 | 0 |
| Grade 10 | 0 | 0 |
| Grade 11 | 0 | 0 |
| Grade 12 | 0 | 0 |

**13 of 14 grades empty. Grade 5 has 4 LOs with ALL detail fields empty (knowledge, skills, attitudes, values_text = 0/4 filled).**

The 4 LOs match the sample CSV — they are a pipeline demonstration, not real KICD data.

---

## 3. Importer state — BEHAVIORALLY VERIFIED

`core/management/commands/import_kicd.py` — 756 lines

**Behavioral tests (all passing)**:
- ✅ I-03: Duplicate detection reports errors
- ✅ I-04: Ambiguous DB match detection
- ✅ I-06: Transaction rollback on failure
- ✅ I-07: Idempotent (re-import is no-op)
- ✅ I-08: Populates knowledge/skills/attitudes/values_text

**Flags**: `--dry-run`, `--validate-only`, `--strict`, `--update-existing`, `--curriculum-version`

**Verdict**: Importer is production-ready for KICD CSV import once real CSVs are available.

---

## 4. Teaching & planning state — PRESERVE, UNVERIFIED

| Model | Rows | Purpose |
|-------|------|---------|
| `SchemeOfWork` | 0 | Term-based curriculum planning |
| `SchemeOfWorkRow` | 0 | Weekly row: strand → substrand → LO |
| `LessonPlan` | 0 | CBC-format lesson (introduction/development/conclusion) |
| `LessonActivity` | 0 | Activities within a plan |
| `CurriculumCoverage` | 0 | Coverage tracking (OneToOne with scheme_row) |
| `TeachingResource` | 0 | Resources with **kicd_approved + kicd_approval_ref** |
| `TeacherReflection` | 0 | Post-lesson reflection |

**Schema complete. Zero data. Workflow never executed.**

**Concerns to investigate**:
- Does `LessonPlan.teacher` get validated against `TeacherAssignment`? (unverified)
- Is `CurriculumCoverage` OneToOne too restrictive? (a sub-strand may span many lessons)
- Is `TeachingResource.kicd_approved` populated by KICD import or manual entry?

---

## 5. Assessment engine — 18 models, chain CONNECTED, ZERO data

### 5.1 The CBA chain (from LO to evidence to report)

```text
LearningOutcome → AssessmentTask (FK: ✓)
                → StudentCBAAssessment (FK: ✓)
                    ├→ AssessmentEvidence (FK: ✓)
                    ├→ LearnerFeedback (FK: ✓)
                    └→ TeacherObservation (FK: ✗ — links to Student+LO instead)
```

**`TeacherObservation` doesn't have `student_assessment` FK** — it links directly to Student + LearningOutcome. This is **correct design** for observations not tied to a specific assessment task, but the portfolio view must handle both paths.

### 5.2 Assessment model row counts

| Model | Rows |
|-------|------|
| `AssessmentScheme` | 2 |
| `AssessmentType` | 4 |
| `AssessmentComponent` | 4 |
| `PerformanceLevel` | 4 (PL1-PL4) |
| `Rubric` | 0 |
| `RubricCriterion` | 0 |
| `RubricDescriptor` | 0 |
| `AssessmentTask` | 0 |
| `StudentCBAAssessment` | 0 |
| `StudentOverallCBA` | 0 |
| `AssessmentEvidence` | 0 |
| `TeacherObservation` | 0 |
| `LearnerFeedback` | 0 |
| `ComponentAggregation` | 0 |

**Schema complete. Assessment workflow never executed.**

### 5.3 Potential concern: Task → LO cardinality

`AssessmentTask.learning_outcome` is a single FK. Per KNEC CBA, one task can assess **multiple outcomes**. This may need to become a M2M — but only after inspecting actual usage patterns.

---

## 6. Learner progress — 398 students, ZERO CBA records

| Model | Rows |
|-------|------|
| `Student` | 398 |
| `StudentHistory` | 398 |
| `StudentCBAAssessment` | 0 |
| `StudentOverallCBA` | 0 |

**Can identify learners. Cannot show what they've achieved.**

Progress requires:
1. Assessment records exist
2. Assessment periods established
3. Historical achievement records
4. Progress comparison service

Currently at step 0.

---

## 7. Teacher workflows — partial

| Model | Rows |
|-------|------|
| `TeacherProfile` | 8 |
| `ClassTeacher` | 12 |
| `TeacherAssignment` | 0 |
| `TeacherRequest` | 0 |
| `ClassTeacherRequest` | 0 |

**Concern**: `ClassTeacher` and `TeacherAssignment.is_class_teacher` may overlap. Need to determine which is authoritative.

---

## 8. Competencies/Values/PCIs — wired and populated

From sample LOs:
- LOs with competencies: 4/4
- LOs with values: 4/4
- LOs with PCIs: 2/4

Reference data matches KICD exactly:
- 7 CoreCompetencies: CC, SE, CTPS, CI, CIT, DL, LL
- 8 CoreValues: LOVE, RESP, RESPECT, UNITY, PEACE, PATRIOT, SOCJUS, INTEG
- 13 PCIs: including HEALTH, LIFESK, ENV, SOCCOH

**But**: does the assessment engine record evidence **against** a specific competency? Unverified.

---

## 9. Intervention — MISSING

No intervention models exist. Domain F requires building from scratch.

Proposed entities (per roadmap):
- `LearningGap`
- `InterventionPlan`
- `InterventionActivity`
- `InterventionAssignment`
- `InterventionSession`
- `InterventionReview`

**The workflow**: Assessment → identify gap → plan → deliver support → reassess → measure change.

Currently impossible: no CBA records, no intervention tracking.

---

## 10. Analytics — foundation only

Available:
- `PerformanceLevel` (PL1-PL4)
- `StudentCBAAssessment.overall_level` FK
- `StudentOverallCBA`
- `ComponentAggregation`

Queries possible (once data exists):
- Outcome achievement aggregation ✓
- Per-learner progress ✓
- Curriculum coverage analytics ✗ (needs scheme + coverage data)
- Teacher progress analytics ✗ (needs assignment + lesson records)
- Class comparison ✗ (needs class grouping — currently via `current_stream`)

**Do not build dashboards until assessment data exists.**

---

## 11. Reports — models exist, workflow unverified

| Model | Rows |
|-------|------|
| `ReportTemplate` | 0 |
| `GeneratedReport` | 0 |
| `ReportComment` | 0 |

`GeneratedReport` links to student, exam, year, term. Has `pdf_file`/`word_file`, status, approval workflow fields.

**But**: PDF generation, approval workflow, publication — never executed. Zero templates, zero generated reports.

---

## 12. Security — CRITICAL DEFICIENCIES

| Setting | Current value | Required |
|---------|---------------|----------|
| `DEBUG` | **True** | False in production |
| `SECRET_KEY` | Insecure default | Env-based |
| `SECURE_SSL_REDIRECT` | **False** | True |
| `SECURE_HSTS_SECONDS` | **0** | ≥ 31536000 |
| `SESSION_COOKIE_SECURE` | **False** | True |
| `CSRF_COOKIE_SECURE` | **False** | True |
| `SESSION_COOKIE_HTTPONLY` | True ✓ | True |
| `SECURE_CONTENT_TYPE_NOSNIFF` | True ✓ | True |
| `X_FRAME_OPTIONS` | DENY ✓ | DENY |
| `CSRF_TRUSTED_ORIGINS` | Empty | Deployment hosts |
| `ALLOWED_HOSTS` | localhost, 127.0.0.1, testserver | Deployment hosts |
| `PASSWORD_HASHERS` | PBKDF2 first, Argon2 available | Argon2 first |
| `LOGGING` | **Not configured** | Structured logging |
| Database | SQLite | PostgreSQL |

**All except the three ✓ are Phase 10 release blockers.**

---

## 13. SNE — MISSING entirely

No SNE models. `Student.status` choices: ACTIVE, INACTIVE, GRADUATED, TRANSFERRED, WITHDRAWN — no SNE flag.

Required (per KICD):
- `SNECategory` (Visual, Hearing, Physical, Intellectual, Deafblindness, Autism, Cerebral Palsy, Multiple)
- `SNELevel` (Foundation, Intermediate, Prevocational, Vocational)
- `SNEProfile` (per student)
- `IEP` (Individualized Education Programme)
- `IEPGoal`
- `AssistiveTechnology`
- `AdaptedAssessment`
- `KFLEARecord`, `KILEARecord`, `KPLEARecord`
- SNE flag on `Student.status`

Domain J is entirely build-from-scratch.

---

## 14. Parent engagement — MISSING

Guardian data exists as fields on `Student`:
- guardian_name, guardian_phone, guardian_email, guardian_relationship

No parent portal models. `Notification` can deliver messages but has no parent-user link.

Required (Domain I):
- `ParentProfile`
- `ParentStudentLink`
- `ParentTeacherMessage`
- `ParentConsent`
- `ParentEngagementRecord`

---

## 15. CSL — MISSING

No community service / CSL models.

Required (Domain VI):
- `CommunityProject`
- `LearnerParticipation`
- `CommunitySupervision`
- `CommunityEvidence`

---

## 16. Quality Assurance — MISSING

Only `core.AuditLog` (technical security audit).

Required (Domain L):
- `LessonObservation`
- `SchemeReview`
- `LessonPlanReview`
- `TeacherAppraisal`
- `SchoolSelfEvaluation`

---

## 17. Multi-tenancy — MISSING

| Category | Count | Examples |
|----------|-------|----------|
| Shared (national curriculum) | 28 | Curriculum, GradeLevel, LearningArea, Strand, SubStrand, LearningOutcome, CoreCompetency, CoreValue, PCI |
| Tenant-scoped (need school_id) | 36 | Student, TeacherProfile, StudentCBAAssessment, AssessmentEvidence, MarkEntry, GeneratedReport, AcademicYear, Term, Stream |
| Unclassified (need decisions) | 12 | SchemeOfWork, LessonPlan, LessonActivity, CurriculumCoverage, TeacherReflection, TeachingResource, Subject, Role, PermissionCode, ReportTemplate, SubjectScoreConfig |

**Classification per roadmap**:
- National curriculum → shared (no school_id)
- School operations → tenant-scoped (school_id on 36 models)
- 12 unclassified → mostly obvious: SchemeOfWork/LessonPlan/Coverage/Reflection → tenant; Subject/Role/PermissionCode → shared; TeachingResource/ReportTemplate → both with `scope` field

**SQLite has no Row-Level Security. Centralized deployment requires PostgreSQL.**

---

## 18. Deployment infrastructure

| Item | Status |
|------|--------|
| Database | SQLite (not production-suitable for centralized) |
| `DEPLOYMENT_MODE` | NOT SET |
| Secret management | Insecure default |
| Environment config | Not detected (no django-environ/decouple) |
| Background processing | No Celery configured |
| Logging | Not configured |
| Backups | No documented process |

---

## 19. Test coverage

| App | Test lines | Test methods |
|-----|-----------|--------------|
| core | 232 | 7 |
| grading | 429 | 20 |
| school | 134 | 4 |
| authentication | 3 | 0 |
| examinations | 3 | 0 |
| marks | 3 | 0 |
| students | 3 | 0 |
| teachers | 3 | 0 |
| senior_school | 3 | 0 |
| reports | MISSING | MISSING |

**31 tests total. 27 in core+grading. 8 apps with 0 tests.**

---

## 20. URL inventory — 100+ routes

| Namespace | Routes | Notable |
|-----------|--------|---------|
| auth | 5 | login, logout, register, profile |
| dashboard | 1 | dashboard |
| examinations | 9 | list, create, detail, analysis, edit |
| grading | 4 | process, class-report, student-report, systems |
| marks | 7 | entry, view, correction, admin |
| notifications | 3 | list, mark-read |
| reports | 9 | dashboard, list, student, class, school, word, approve, publish |
| school | 26 | schemes, coverage, structure, curriculum, term, academic-year |
| senior-school | 3 | pathway list/detail, learner pathway |
| students | 9 | list, create, detail, edit, transfer, portfolio |
| teachers | 18 | list, detail, assign, requests, class-teachers |

**Every domain has UI entry points.** What's missing is data.

---

## 21. Consolidated verdict

### Preserve (working, well-designed)
- Curriculum hierarchy (13 models)
- Teaching & planning (7 models)
- Assessment engine (18 models)
- Learner/teacher models
- Competency/Value/PCI wiring
- Importer (tested)

### Improve (schema fine, unverified)
- End-to-end assessment workflow
- Learner progress service
- Report generation
- Teacher assignment workflows
- Curriculum data completeness

### Build from scratch (missing)
- Intervention (Domain F)
- Parent portal (Domain I)
- SNE (Domain J)
- CSL (Domain VI)
- Quality assurance (Domain L)
- Multi-tenancy architecture
- Analytics (Domain E full)

### Fix immediately (security)
- 5 critical security settings
- Logging
- PostgreSQL migration
- Environment configuration

### What EduGrade is NOT (yet)
- Not CBC-compliant
- Not KICD-approved
- Not KNEC-integrated
- Not production-ready
- Not multi-school capable
- Not proven end-to-end on a single workflow

**It is a solid foundation with honest gaps.**
