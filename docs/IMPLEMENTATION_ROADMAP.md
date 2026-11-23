# EduGrade Implementation Roadmap

**Date**: 2026-11-23
**Basis**: All three audit blocks + the four-document contract
**Principle**: Evidence over assumption. Workflow proof over model existence.

---

## Decisions (recorded from roadmap)

1. **One Django codebase** — independent + centralized deployments share code, differ by config
2. **PostgreSQL as production database** — SQLite for local dev only
3. **Preserve existing project** — no wholesale rewrite, no destructive migrations
4. **Verify before classifying** — model existence ≠ workflow working
5. **Official curriculum evidence** — no fabricated KICD content
6. **Tenant isolation before centralization** — multi-tenancy is a prerequisite, not an add-on

---

## Phase ordering (dependency-based)

| Phase | Name | Blocks | Duration estimate |
|-------|------|--------|-------------------|
| 0 | Compliance register (DONE) | — | ✅ |
| 1 | **Importer reliability** (DONE) | — | ✅ |
| 2 | **Security + multi-tenancy architecture** | Real data ingestion | 1 phase |
| 3 | **PostgreSQL migration + environment** | Production | 1 phase |
| 4 | **End-to-end assessment workflow verification** | Everything downstream | 1 phase |
| 5 | **Real curriculum import (Grade 5 Math first)** | CBC compliance | 1-2 phases |
| 6 | **Intervention engine (Domain F)** | Analytics usefulness | 1 phase |
| 7 | **Teaching verification (Domain B)** | Teacher workflows | 1 phase |
| 8 | **Reporting + KNEC readiness (Domain M)** | Parent portal | 1 phase |
| 9 | **SNE + accessibility (Domain J)** | Legal compliance | 2 phases |
| 10 | **Parent portal + consent (Domain I)** | DPA 2019 | 1 phase |
| 11 | **CSL + QA (Domains VI, L)** | Completeness | 1 phase |
| 12 | **Full curriculum import (all grades)** | National readiness | 2-3 phases |
| 13 | **Analytics + dashboards (Domain E)** | Decision support | 1 phase |

---

## Phase 2 — Security + multi-tenancy architecture (NEXT)

### Why this phase is next

Per the roadmap's critical findings:
- Six security settings are release blockers
- Multi-tenancy must be designed before any centralized deployment
- **BUT** we do NOT need to fix security to continue testing locally

### What this phase does

**Part A: Multi-tenancy design (documentation)**
- Confirm the 28 shared / 36 scoped / 12 unclassified model list
- Resolve the 12 unclassified
- Decide: explicit school_id vs. derived through FK
- Design Row-Level Security policy for PostgreSQL

**Part B: Security hardening (settings only, no deployments yet)**
- Environment-based SECRET_KEY
- DEBUG toggle via env
- SECURE_* settings default to production-safe
- Structured logging setup

**Part C: Do NOT touch models yet**
- No `school_id` columns added
- No model rewrites

### Exit criteria

- [ ] `docs/MULTI_TENANCY_DESIGN.md` produced
- [ ] All 76 models classified with clear rationale
- [ ] `DEPLOYMENT_MODE` documented
- [ ] Security settings ready for production
- [ ] No migration yet

---

## Phase 3 — PostgreSQL migration + environment

### What this phase does

- Configure `django-environ` or `python-decouple`
- Migrate data from SQLite to PostgreSQL (with backup + restore plan)
- Test locally on PostgreSQL
- Set up RLS policies (per Phase 2 design)

### Exit criteria

- [ ] Application runs on PostgreSQL
- [ ] All 398 students, 8 teachers, 38 curiculum models migrated intact
- [ ] Row counts match
- [ ] Tests pass on PostgreSQL

---

## Phase 4 — End-to-end assessment workflow verification

### Why this phase is critical

The audit proved:
- Models exist for the entire chain
- **Zero rows** in the chain
- Cannot claim the workflow works without proof

### What this phase does

Create **one test school** with:
- 1 teacher
- 5 students
- 1 Grade 5 Math LO (from existing 4)
- 1 assessment task
- 1 CBA assessment per student
- 1 evidence upload per student
- 1 observation per student
- 1 feedback per student
- 1 generated report per student

**Then query the chain to prove it works end-to-end.**

### Exit criteria

- [ ] `test_end_to_end_cba_workflow` test passes
- [ ] All 8 tables have ≥1 row
- [ ] Portfolio view renders correctly
- [ ] Report generates (even if template is basic)
- [ ] Compliance audit shows A-04 through A-08 all VERIFIED

---

## Phase 5 — Real curriculum import (Grade 5 Math)

### Prerequisite

- Grade 5 Mathematics KICD PDF downloaded
- Extracted CSV prepared (19 sub-strands, all lettered LOs)

### What this phase does

- Build complete Grade 5 Math CSV from official KICD PDF
- Run importer with `--dry-run` first
- Run importer for real
- Verify 19 sub-strands all present
- Verify all lettered outcomes extracted
- Add `source_page` field to LearningOutcome (migration)

### Exit criteria

- [ ] 19 sub-strands match PDF
- [ ] All LOs have source_page populated
- [ ] All LOs have knowledge/skills/attitudes/values_text (if PDF provides them)
- [ ] No fabricated content (all traceable to PDF)
- [ ] Compliance: C-04, C-06 verified for Grade 5

---

## Phase 6 — Intervention engine (Domain F)

### New app: `intervention`

Models:
- `LearningGap` (student + LO + current level + evidence)
- `InterventionPlan` (gap + strategy + teacher + start date)
- `InterventionActivity` (plan + activity + session date)
- `InterventionSession` (activity + duration + attendance)
- `InterventionReview` (plan + reassessment + outcome)

### What this phase does

- Build intervention models
- Add admin
- Add views: list gaps, create plan, deliver session, review
- Add tests
- Seed from Phase 4's test data

### Exit criteria

- [ ] Test: identify gap → plan → deliver → reassess → measure change
- [ ] Domain F compliance moves from 0% to 60%+

---

## Phase 7 — Teaching verification (Domain B)

- Seed 1 scheme of work per learning area
- Generate 5 lesson plans
- Record 5 lesson deliveries with coverage
- Add 5 teacher reflections
- Test teacher validation against assignment

### Exit criteria

- [ ] Full scheme → lesson → coverage → reflection workflow verified
- [ ] `TeacherAssignment` validation in `LessonPlan.clean()`
- [ ] Domain B compliance moves from 0% to 50%+

---

## Phase 8 — Reporting (Domain M)

- Design CBC-specific report template
- Implement PDF generation (reportlab or WeasyPrint)
- Implement Word export
- Implement approval workflow
- Implement publication workflow

### Exit criteria

- [ ] Test: generate → approve → publish report for 1 student
- [ ] CBC report format matches KNEC requirements
- [ ] Domain M compliance moves from 0% to 70%+

---

## Phase 9 — SNE + accessibility (Domain J)

### New app: `special_needs`

Models:
- `SNECategory` (8 categories)
- `SNELevel` (4 levels: Foundation, Intermediate, Prevocational, Vocational)
- `SNEProfile` (student + category + level + start date)
- `IEP` (student + goals + evaluation + services)
- `AssistiveTechnology`
- `AdaptedAssessment`
- `KFLEARecord`, `KILEARecord`, `KPLEARecord`

Add `SNE` choice to `Student.status`.

Accessibility:
- Screen reader tags
- Keyboard navigation
- High-contrast mode
- Text scaling
- Alt text

### Exit criteria

- [ ] SNE-07 (flag on Student) VERIFIED
- [ ] All 8 SNE models tested
- [ ] Accessibility audit passes (WCAG 2.1 AA)
- [ ] Domain J compliance moves from 0% to 70%+

---

## Phase 10 — Parent portal (Domain I)

### New app: `parents`

Models:
- `ParentProfile`
- `ParentStudentLink`
- `ParentTeacherMessage`
- `ParentConsent` (required for DPA 2019)
- `ParentEngagementRecord`

Parent user role, scoped access to their own children only.

### Exit criteria

- [ ] Parent can log in, view only their child's data
- [ ] Cannot access other students
- [ ] Consent tracking works
- [ ] P-06 (Parental consent) VERIFIED
- [ ] Domain I compliance moves from 0% to 60%+

---

## Phase 11 — CSL + QA (Domains VI, L)

### New apps: `community_learning`, `quality_assurance`

CSL models:
- `CommunityProject`, `LearnerParticipation`, `CommunitySupervision`, `CommunityEvidence`

QA models:
- `LessonObservation`, `SchemeReview`, `LessonPlanReview`, `TeacherAppraisal`, `SchoolSelfEvaluation`

### Exit criteria

- [ ] CSL project → participation → supervision → evidence verified
- [ ] Headteacher can review a lesson plan
- [ ] Domains VI and L compliance move from 0% to 50%+

---

## Phase 12 — Full curriculum import (all grades)

### Prerequisite

- 13 remaining grade PDFs downloaded
- Extracted CSVs prepared

### What this phase does

- Extract KICD PDFs for PP1, PP2, Grades 1-4, 6-12
- Build CSVs (like Phase 5)
- Import grade by grade
- Verify each against PDF

### Exit criteria

- [ ] All 14 grades have ≥1 LearningArea
- [ ] Total LearningOutcome count matches sum of official PDFs
- [ ] All LOs have source_page
- [ ] Compliance: C-04 through C-07 ALL VERIFIED

**This is the phase that makes EduGrade genuinely CBC-complete.**

---

## Phase 13 — Analytics + dashboards (Domain E)

### Prerequisite

- Phase 4-12 complete (real assessment data exists)

### What this phase does

- Outcome achievement aggregation
- Per-learner progress charts
- Curriculum coverage dashboards
- Teacher progress views
- Class comparison
- School performance dashboard
- Intervention effectiveness

### Exit criteria

- [ ] 10+ dashboards functional with real data
- [ ] No dashboard without data
- [ ] Domain E compliance moves from 0% to 80%+

---

## Cross-phase concerns

### Testing discipline

Every phase adds tests. Target:
- Phase 2-3: security tests
- Phase 4+: workflow tests
- Phase 9: accessibility tests
- Phase 10: security penetration tests

### Compliance audit

Run `python manage.py compliance_audit` after every phase. Track VERIFIED % increase.

### Documentation

Every phase produces:
- Migration files
- Tests
- Updated compliance register
- Updated requirements spec if KICD requirements change

### Release gates

Before any production deployment:
- All CRITICAL requirements VERIFIED
- All release blockers resolved
- All phases at least 60% verified
- Security audit passed

---

## Migration policy

- Never drop tables before verifying dependencies
- Never rewrite user model after migrations exist
- Never migrate to PostgreSQL in production without a tested backup + restore
- Every migration tested on a copy of the database first
- Rollback plan documented for each migration

---

## What "done" means

EduGrade is production-ready when:

1. All Phase 2-13 complete
2. Compliance audit shows ≥90% VERIFIED
3. All release blockers resolved
4. Two-school isolation test passes
5. All workflows tested end-to-end
6. Real curriculum imported (all 14 grades)
7. Security audit passed
8. Accessibility audit passed
9. Backup + restore tested
10. Documentation complete

**Even then, EduGrade is NOT KICD-approved.** That requires formal submission per the 2018 digital standards (which may need re-confirmation for current applicability).

**KICD approval is a separate phase (Phase 14) not covered here.**
