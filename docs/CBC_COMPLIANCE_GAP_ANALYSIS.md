# CBC Compliance Gap Analysis

**Date**: 2026-11-23
**Method**: Requirement-by-requirement comparison between the KENYA_CBC_REQUIREMENTS_SPEC and the EDUGRADE_SYSTEM_AUDIT.
**Status vocabulary**: Implemented & Verified | Partially Implemented | Present but Unverified | Missing | Not Applicable

---

## 1. Severity levels

| Level | Meaning | Action |
|-------|---------|--------|
| **CRITICAL** | Blocks release or violates law | Fix before any production deployment |
| **HIGH** | Breaks core functionality | Fix before first release |
| **MEDIUM** | Limits usefulness but not blocking | Fix within 2 releases |
| **LOW** | Polish / expansion | Defer |

---

## 2. Curriculum requirements (from CBC spec §2)

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| C-01 | Curriculum version model with source traceability | Implemented & Verified | — | `CurriculumVersion.source_document` exists, 2 rows | Extend with checksum + PDF URL |
| C-02 | Education stages (5) | Implemented & Verified | — | 5 rows in EducationStage | None |
| C-03 | All 14 grade levels seeded | Implemented & Verified | — | 14 rows in GradeLevel | None |
| C-04 | Grade 5 Math full curriculum (19 sub-strands, lettered LOs) | Partially Implemented | **CRITICAL** | 4 LOs from sample CSV, missing 80+ official outcomes | Phase 2: Extract complete PDF, import |
| C-05 | All other grades (PP1–Grade 12) | **Missing** | **CRITICAL** | 13 of 14 grades have 0 LearningAreas | Phase 3: Full curriculum extraction |
| C-06 | LearningOutcome detail fields (knowledge/skills/attitudes/values) populated | Present but Unverified | HIGH | 0/4 LOs populated — schema exists | Populate via Phase 2 importer |
| C-07 | 7 core competencies | Implemented & Verified | — | 7 rows match KICD list | None |
| C-08 | 8 core values | Implemented & Verified | — | 8 rows match KICD list | None |
| C-09 | 13 PCIs | Present but Unverified | MEDIUM | 13 rows exist, wording not cross-checked with KICD doc | Verify wording before marking complete |
| C-10 | Source document PDF + checksum per curriculum version | Partially Implemented | HIGH | `source_document` has text but no PDF URL, no checksum | Add fields + download process |
| C-11 | Page-referenced traceability per outcome | **Missing** | HIGH | LearningOutcome has no `source_page` field | Add `source_page` field + populate during extraction |

---

## 3. Teaching & planning requirements

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| T-01 | Scheme of work per learning area per term | Present but Unverified | HIGH | SchemeOfWork model complete, 0 rows | Seed + verify workflow |
| T-02 | Scheme rows with LO links | Present but Unverified | HIGH | SchemeOfWorkRow model complete, 0 rows | Seed + verify |
| T-03 | Lesson plan with curriculum alignment | Present but Unverified | HIGH | LessonPlan model with introduction/development/conclusion, 0 rows | Seed + verify |
| T-04 | Lesson activities | Present but Unverified | MEDIUM | LessonActivity model, 0 rows | Seed + verify |
| T-05 | Curriculum coverage tracking | Present but Unverified | HIGH | CurriculumCoverage model (OneToOne — may be too restrictive) | Verify design + populate |
| T-06 | Teaching resources with KICD approval flag | Present but Unverified | MEDIUM | `kicd_approved` + `kicd_approval_ref` fields exist, 0 rows | Verify KICD resource population workflow |
| T-07 | Teacher reflection | Present but Unverified | MEDIUM | TeacherReflection model, 0 rows | Verify |
| T-08 | Teacher validated against TeacherAssignment | **Missing** | HIGH | No validation found — concern | Add validation in LessonPlan.clean() |
| T-09 | Lesson plan generator from LO | **Missing** | MEDIUM | Not implemented | Phase 7 |

---

## 4. Assessment requirements (KNEC)

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| A-01 | PL1–PL4 performance levels | Implemented & Verified | — | 4 rows | None |
| A-02 | Rubric + criteria + descriptors | Present but Unverified | HIGH | 3 models, 0 rows | Phase 4: Seed + verify |
| A-03 | AssessmentTask → LO link | Implemented & Verified | — | FK exists | Verify single vs multiple LO assessment |
| A-04 | CBA assessment per learner | Present but Unverified | HIGH | `StudentCBAAssessment` model, 0 rows | Phase 4: Seed + verify |
| A-05 | AssessmentEvidence (photos/videos/docs) | Present but Unverified | HIGH | Model exists, 0 rows | Phase 4 |
| A-06 | TeacherObservation | Present but Unverified | HIGH | Model exists, 0 rows; **no link to StudentCBAAssessment** | Verify design intent |
| A-07 | LearnerFeedback | Present but Unverified | HIGH | Model exists, 0 rows | Phase 4 |
| A-08 | Overall CBA per learner | Present but Unverified | HIGH | `StudentOverallCBA` model, 0 rows | Phase 4 |
| A-09 | Diagnostic / formative / SBA / summative distinction | **Missing** | MEDIUM | `AssessmentType` exists (4 rows) but types not verified | Verify types match KNEC categories |
| A-10 | Portfolio evidence collection | Present but Unverified | HIGH | Models exist, no portfolio generation | Phase 4 |
| A-11 | Self-assessment / peer assessment | **Missing** | LOW | No models | Phase 4 extension |
| A-12 | KPSEA/KJSEA/KILEA/KPLEA data models | **Missing** | MEDIUM | None | Later phase |

---

## 5. Learner progress requirements

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| L-01 | Learner profiles | Implemented & Verified | — | 398 students | None |
| L-02 | Longitudinal enrollment history | Implemented & Verified | — | 398 StudentHistory rows | None |
| L-03 | CBA assessment history | **Missing** | **CRITICAL** | 0 CBA records | Phase 4 |
| L-04 | Progress comparison across periods | **Missing** | HIGH | No service built | Phase 4 |
| L-05 | Learning gap identification | **Missing** | HIGH | No model | Phase 6 |
| L-06 | Recommended interventions | **Missing** | HIGH | No model | Phase 6 |

---

## 6. Teacher workflow requirements

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| TW-01 | Teacher profiles | Implemented & Verified | — | 8 rows | None |
| TW-02 | Class teacher assignments | Implemented & Verified | — | 12 rows in ClassTeacher | None |
| TW-03 | Subject/class assignment workflow | Present but Unverified | HIGH | `TeacherAssignment` model, 0 rows | Seed + verify |
| TW-04 | Teacher request workflow | Present but Unverified | MEDIUM | `TeacherRequest` model, 0 rows | Verify |
| TW-05 | Resolve ClassTeacher vs TeacherAssignment.is_class_teacher duplication | **Missing** | MEDIUM | Both exist — unclear which is authoritative | Architecture decision needed |
| TW-06 | Teacher performance tracking | **Missing** | MEDIUM | No appraisal model | Phase 8 |

---

## 7. Competency / Value / PCI integration

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| CV-01 | LO → competencies M2M | Implemented & Verified | — | Schema exists, 4/4 sample LOs populated | None |
| CV-02 | LO → core values M2M | Implemented & Verified | — | 4/4 populated | None |
| CV-03 | LO → PCIs M2M | Implemented & Verified | — | 2/4 populated | None |
| CV-04 | Assessment evidence linked to competency | **Missing** | HIGH | No M2M from AssessmentEvidence to competency | Add if required by KNEC |
| CV-05 | Teacher observation of values | **Missing** | MEDIUM | No model | Phase 6 |
| CV-06 | PCI categories verified against KICD | Present but Unverified | MEDIUM | 13 rows, wording not checked | Verify |

---

## 8. Intervention requirements

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| I-01 | LearningGap model | **Missing** | HIGH | None | Phase 6 |
| I-02 | InterventionPlan model | **Missing** | HIGH | None | Phase 6 |
| I-03 | InterventionActivity model | **Missing** | MEDIUM | None | Phase 6 |
| I-04 | InterventionSession (delivery records) | **Missing** | MEDIUM | None | Phase 6 |
| I-05 | InterventionReview (effectiveness measurement) | **Missing** | HIGH | None | Phase 6 |
| I-06 | Before/after comparison | **Missing** | HIGH | None | Phase 6 |

---

## 9. Analytics requirements

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| AN-01 | Outcome achievement aggregation | Present but Unverified | HIGH | Query possible via `StudentCBAAssessment.overall_level`, no data | Phase 5 after data |
| AN-02 | Per-learner progress | Present but Unverified | HIGH | Foundation exists | Phase 5 |
| AN-03 | Curriculum coverage analytics | **Missing** | HIGH | Needs SchemeOfWorkRow + Coverage data | Phase 7 |
| AN-04 | Teacher progress analytics | **Missing** | MEDIUM | Needs TeacherAssignment + lesson records | Phase 8 |
| AN-05 | Class comparison | **Missing** | MEDIUM | No grouping model | Phase 8 |
| AN-06 | School performance dashboard | **Missing** | MEDIUM | No model | Phase 8 |
| AN-07 | Intervention effectiveness tracking | **Missing** | HIGH | Depends on Phase 6 | Phase 6 |

**Warning from roadmap**: Do not build analytics before assessment data exists. Attractive dashboards with no data are useless.

---

## 10. Reporting requirements

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| R-01 | ReportTemplate model | Present but Unverified | HIGH | Model exists, 0 rows | Seed templates |
| R-02 | GeneratedReport model | Present but Unverified | HIGH | Model exists, 0 rows | Verify generation workflow |
| R-03 | PDF generation | Present but Unverified | HIGH | `pdf_file` field exists, no generation tested | Test end-to-end |
| R-04 | Word generation | Present but Unverified | MEDIUM | `word_file` field exists | Test |
| R-05 | Approval workflow | Present but Unverified | MEDIUM | `approved_by`, `approved_at` fields | Test |
| R-06 | Publication workflow | Present but Unverified | MEDIUM | `published_at` field | Test |
| R-07 | CBC-specific report format | **Missing** | HIGH | No template designed | Phase 8 |

---

## 11. SNE requirements (Domain J)

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| SNE-01 | SNECategory model | **Missing** | **CRITICAL** | None | Phase 9 |
| SNE-02 | SNELevel model (4 levels) | **Missing** | **CRITICAL** | None | Phase 9 |
| SNE-03 | IEP model | **Missing** | HIGH | None | Phase 9 |
| SNE-04 | AssistiveTechnology model | **Missing** | MEDIUM | None | Phase 9 |
| SNE-05 | AdaptedAssessment model | **Missing** | HIGH | None | Phase 9 |
| SNE-06 | KFLEARecord / KILEARecord / KPLEARecord | **Missing** | MEDIUM | None | Phase 9 |
| SNE-07 | SNE flag on Student | **Missing** | **CRITICAL** | `Student.status` has no SNE choice | Phase 9 |
| SNE-08 | Accessibility (10 features) | **Missing** | HIGH | No accessibility implementation | Phase 9 |

---

## 12. Parent engagement requirements (Domain I)

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| P-01 | ParentProfile model | **Missing** | HIGH | No model | Phase 10 |
| P-02 | ParentStudentLink | **Missing** | HIGH | No model | Phase 10 |
| P-03 | Parent login | **Missing** | HIGH | No parent user role | Phase 10 |
| P-04 | Parent dashboard | **Missing** | MEDIUM | No views | Phase 10 |
| P-05 | Parent-teacher messaging | **Missing** | MEDIUM | Notification exists but no parent link | Phase 10 |
| P-06 | ParentConsent | **Missing** | HIGH | Required by DPA 2019 | Phase 10 |
| P-07 | ParentEngagementRecord | **Missing** | LOW | None | Phase 10 |

---

## 13. CSL requirements (Domain VI)

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| CSL-01 | CommunityProject model | **Missing** | MEDIUM | None | Phase 11 |
| CSL-02 | LearnerParticipation | **Missing** | MEDIUM | None | Phase 11 |
| CSL-03 | CommunitySupervision | **Missing** | MEDIUM | None | Phase 11 |
| CSL-04 | CommunityEvidence | **Missing** | MEDIUM | None | Phase 11 |

---

## 14. Quality assurance requirements (Domain L)

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| QA-01 | LessonObservation | **Missing** | MEDIUM | None | Phase 12 |
| QA-02 | SchemeReview | **Missing** | MEDIUM | None | Phase 12 |
| QA-03 | LessonPlanReview | **Missing** | MEDIUM | None | Phase 12 |
| QA-04 | TeacherAppraisal | **Missing** | MEDIUM | None | Phase 12 |
| QA-05 | SchoolSelfEvaluation | **Missing** | LOW | None | Phase 12 |

---

## 15. Multi-tenancy requirements

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| MT-01 | Tenant isolation on shared deployment | **Missing** | **CRITICAL** | No school_id on operational models | Phase 1 (architecture) |
| MT-02 | Shared curriculum accessible to all tenants | **Missing** | HIGH | Not explicitly modelled — curriculum is global by default | Confirm design |
| MT-03 | 36 operational models with school_id | **Missing** | **CRITICAL** | None have school_id | Phase 1 |
| MT-04 | PostgreSQL (not SQLite) for production | **Missing** | **CRITICAL** | SQLite in settings | Phase 1 |
| MT-05 | DEPLOYMENT_MODE configuration | **Missing** | HIGH | Not set | Phase 1 |
| MT-06 | Row-Level Security (PostgreSQL) | **Missing** | HIGH | N/A with SQLite | Phase 1 |
| MT-07 | Two-school access isolation test | **Missing** | **CRITICAL** | Cannot test without multi-tenancy | Phase 1 |

---

## 16. Security requirements

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| SEC-01 | DEBUG=False in production | **Missing** | **CRITICAL** | DEBUG=True | Phase 10 |
| SEC-02 | SECRET_KEY from environment | **Missing** | **CRITICAL** | Insecure default | Phase 10 |
| SEC-03 | SECURE_SSL_REDIRECT=True | **Missing** | **CRITICAL** | False | Phase 10 |
| SEC-04 | HSTS enabled | **Missing** | **CRITICAL** | 0 seconds | Phase 10 |
| SEC-05 | Secure session cookie | **Missing** | **CRITICAL** | False | Phase 10 |
| SEC-06 | Secure CSRF cookie | **Missing** | **CRITICAL** | False | Phase 10 |
| SEC-07 | Structured logging | **Missing** | HIGH | Not configured | Phase 10 |
| SEC-08 | Audit log activated | Present but Unverified | HIGH | Model exists, 0 rows | Phase 10 |
| SEC-09 | Argon2 first password hasher | Partially Implemented | MEDIUM | Argon2 available, PBKDF2 first | Phase 10 |
| SEC-10 | HTTPS in production | **Missing** | **CRITICAL** | False | Phase 10 |
| SEC-11 | Secure file storage (private media) | Present but Unverified | MEDIUM | MEDIA_ROOT set but no access control verified | Phase 10 |
| SEC-12 | Backup / restore documented | **Missing** | HIGH | None | Phase 10 |
| SEC-13 | Data retention policy | **Missing** | HIGH | None | Phase 10 |
| SEC-14 | Parental consent tracking | **Missing** | HIGH | None | Phase 10 |

---

## 17. Test coverage requirements

| # | Requirement | Status | Severity | Evidence | Remediation |
|---|-------------|--------|----------|----------|-------------|
| TC-01 | Tests for all apps | Partially Implemented | HIGH | 3 apps have tests, 6 empty, 1 missing | Add incrementally |
| TC-02 | End-to-end assessment workflow test | **Missing** | **CRITICAL** | None | Phase 4 |
| TC-03 | Multi-tenancy isolation test | **Missing** | **CRITICAL** | None | Phase 1 |
| TC-04 | Security tests | **Missing** | HIGH | None | Phase 10 |
| TC-05 | Accessibility tests | **Missing** | MEDIUM | None | Phase 9 |

---

## 18. Roadmap alignment summary

| Domain | Verified | Unverified | Missing | Coverage |
|--------|----------|-----------|---------|----------|
| A. Curriculum admin | 3 | 3 | 5 | 27% |
| B. Teaching & planning | 0 | 6 | 3 | 0% |
| C. Assessment | 3 | 6 | 3 | 25% |
| D. Learner progress | 2 | 0 | 4 | 33% |
| E. Analytics | 0 | 2 | 5 | 0% |
| F. Intervention | 0 | 0 | 6 | 0% |
| G. Teacher performance | 2 | 2 | 2 | 33% |
| H. School admin | 6+ | 2 | 1 | 67% |
| I. Parent engagement | 0 | 0 | 7 | 0% |
| J. SNE | 0 | 0 | 8 | 0% |
| K. Resources | 0 | 1 | 0 | 0% |
| L. QA | 0 | 0 | 5 | 0% |
| M. Reporting | 0 | 6 | 1 | 0% |
| N. Data protection | 3 | 2 | 9 | 21% |
| O. Institutional analytics | 0 | 1 | 3 | 0% |

**Overall verified: ~25%. Overall implemented but unverified: ~30%. Missing: ~45%.**

This is the honest baseline. Not 59.5% (that was requirement-count only). Not 100%. **Real progress requires executing the workflows, not just having the models.**

---

## 19. Release blockers (must fix before any production)

1. **SEC-01 to SEC-06, SEC-10**: Six security settings
2. **MT-01, MT-03, MT-04, MT-07**: Multi-tenancy architecture
3. **C-04, C-05**: Real curriculum data (currently 4 LOs out of hundreds)
4. **TC-02**: End-to-end assessment workflow test
5. **SNE-07**: SNE flag on Student (legal requirement per DPA 2019 for inclusive education)

These are non-negotiable. Everything else is prioritized by roadmap.
