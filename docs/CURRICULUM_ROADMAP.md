# EduGrade CBC/CBE Readiness Roadmap

Development and verification stages — not an official certification score.

Every stage is **complete only when `compliance_audit` shows the relevant
requirements as VERIFIED**. Nothing is claimed complete without evidence.

## Stage 0 — Compliance register (this phase)

**Goal**: Establish traceability instrument.

**Deliverables**:
- `docs/COMPLIANCE.md` — requirement table
- `core/management/commands/compliance_audit.py` — automated evaluation
- `docs/CURRICULUM_ROADMAP.md` — this file

**Exit criteria**: `python manage.py compliance_audit --write-report` produces a report.

---

## Stage 1 — Importer reliability

**Goal**: `import_kicd` safe for full curriculum imports.

**Deliverables**:
- Fix duplicate detection within CSV
- Fix ambiguous DB match detection
- Fix unknown reference code handling (strict by default)
- Populate `knowledge`, `skills`, `attitudes`, `values_text`
- Populate `order` fields
- Automated tests:
  - test_missing_column_rejected
  - test_duplicate_rows_detected
  - test_ambiguous_db_match_errors
  - test_rollback_on_failure
  - test_idempotent_import
  - test_knowledge_skills_populated

**Exit criteria**: All I-* requirements in compliance_audit show VERIFIED.

---

## Stage 2 — Import one grade (proof of concept)

**Goal**: Replace sample with real Grade 5 Mathematics KICD content.

**Source**: KICD Grade 5 Mathematics curriculum design.

**Exit criteria**:
- Grade 5 Math has ≥ minimum KICD LO count
- All 10 LO fields populated
- Compliance_audit shows C-04 through C-07 verified for Grade 5

---

## Stage 3 — Full curriculum import

**Goal**: All grades PP1–Grade 12 populated with KICD content.

**Source**: KICD curriculum designs portal (one CSV per grade per learning area).

**Exit criteria**:
- Every grade has all applicable learning areas
- Every learning area has all strands per KICD
- Every strand has all sub-strands per KICD
- Every sub-strand has all outcomes per KICD
- Compliance_audit shows C-01 through C-12 VERIFIED

---

## Stage 4 — Rubrics & assessment schema

**Goal**: Assessment layer per KNEC CBA framework.

**Deliverables**:
- Seed default rubrics per learning area
- Link AssessmentTask → Rubric
- Rubric editor in admin
- Performance descriptors per outcome
- Tests for rubric creation and application

**Exit criteria**: A-01 through A-09 VERIFIED

---

## Stage 5 — Senior School completion

**Goal**: All 3 pathways match KICD subject lists; CSL modelled.

**Deliverables**:
- Add 27 missing subjects
- Add CSL as required learning area
- Validate combinations against KICD rules
- Test for pathway/track/subject integrity

**Exit criteria**: S-01 through S-08 VERIFIED

---

## Stage 6 — Inclusive Education (SNE)

**Goal**: Support adapted + stage-based curriculum.

**Deliverables**:
- New `special_needs` app
- Models: SNECategory, SNELevel (4), IEP, AdaptiveTarget, AssistiveTechnology, AdaptedAssessment
- Student.status gets SNE choice
- Stage assessments: KFLEA, KILEA, KPLEA
- Admin + views
- Tests

**Exit criteria**: E-01 through E-09 VERIFIED

---

## Stage 7 — Teaching & delivery verification

**Goal**: Schemes of work, lesson plans, coverage tracking usable end-to-end.

**Deliverables**:
- Sample scheme of work per learning area
- Lesson plan generator from LO
- Coverage dashboard shows % complete
- Tests

**Exit criteria**: T-01 through T-07 VERIFIED

---

## Stage 8 — Reporting & KNEC readiness

**Goal**: Report cards, CBC summaries, KNEC export.

**Deliverables**:
- Report template per grade level
- Generated report per learner per term
- KNEC-compatible export format
- Privacy controls on exports

**Exit criteria**: R-01 through R-03 VERIFIED

---

## Stage 9 — Operations

**Goal**: Attendance, timetable, library.

**Deliverables**:
- Attendance app: registers, records, absence reasons, summaries
- Timetable app: periods, slots, rooms, teacher allocation
- Library app: books, borrows, inventory

**Exit criteria**: New compliance rows added and VERIFIED

---

## Stage 10 — Security & data protection

**Goal**: ODPC / Data Protection Act 2019 compliance.

**Deliverables**:
- `SECURE_SSL_REDIRECT = True` (production)
- `SECURE_HSTS_SECONDS` set
- Secure cookies
- AuditLog activated
- Retention policy doc
- Parental consent tracking
- Security tests

**Exit criteria**: P-01 through P-06 VERIFIED

---

## Certification note

Stages 0–10 achieve **technical readiness** and **curriculum alignment**.
They do **not** confer official recognition by KICD, KNEC, or the Ministry of
Education. That requires a separate approval process with each authority.
