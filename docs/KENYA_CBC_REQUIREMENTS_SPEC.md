# Kenya CBC/CBE Requirements Specification

**Version**: 1.0
**Date**: 2026-11-23
**Status**: Evidence-based — distinguishes verified official requirements from proposed EduGrade features
**Source of truth**: KICD, KNEC, MoE, TSC, ODPC official documents

---

## 1. Authority map

| Authority | Domain | Official URL | Verification status |
|-----------|--------|--------------|---------------------|
| KICD | Curriculum designs, learning outcomes, digital material standards | https://kicd.ac.ke/cbc-materials/curriculum-designs/ | Pending — PDFs not yet downloaded |
| KICD SNE | Adapted + stage-based curriculum | https://kicd.ac.ke/cbc-materials/curriculum-designs/sne-curriculum-designs/ | Pending |
| KNEC | Competency-Based Assessment, KPSEA, KJSEA, KILEA, KPLEA | https://www.knec.ac.ke/ | Pending |
| MoE | Education policy, school structure | https://www.education.go.ke/ | Pending |
| TSC | Teacher professional standards | https://www.tsc.go.ke/ | Pending |
| ODPC | Data Protection Act 2019 | https://www.odpc.go.ke/ | Pending |
| KICD Digital Standards | Standards for Competence-Based Digital Course Materials (2018) | https://kicd.ac.ke/wp-content/uploads/2018/05/STANDARDS-FOR-DIGITAL-CONTENT-COURSE-MATERIALS_CBC-2018-Revised.pdf | Pending — 2018 document, must confirm still current |

**Rule**: No requirement is marked VERIFIED until the official PDF has been downloaded, checksummed, and cross-checked against the extracted data.

---

## 2. Official curriculum structure (KICD)

### 2.1 Education levels and grades

| Level | Grades | Verified |
|-------|--------|----------|
| Pre-Primary | PP1, PP2 | Needs KICD confirmation |
| Lower Primary | Grades 1–3 | Needs KICD confirmation |
| Upper Primary | Grades 4–6 | Confirmed via Grade 5 Math PDF |
| Junior School | Grades 7–9 | Needs KICD confirmation |
| Senior School | Grades 10–12 | Confirmed via Phase 6 pathways |

### 2.2 Grade 5 Mathematics — verified official structure (KICD 2024 Revised)

From KICD Grade 5 Mathematics Curriculum Design (Revised 2024), printed page xii:

| Strand | Sub-strands | Suggested Lessons |
|--------|-------------|-------------------|
| 1.0 Numbers | 8 | 64 |
| 2.0 Measurement | 7 | 64 |
| 3.0 Geometry | 3 | 16 |
| 4.0 Data Handling | 1 | 6 |
| **Total** | **19** | **150** |

**Sub-strand list (verified)**:
- Numbers: 1.1 Whole Numbers (20), 1.2 Addition (6), 1.3 Subtraction (6), 1.4 Multiplication (6), 1.5 Division (6), 1.6 Fractions (8), 1.7 Decimals (6), 1.8 Simple Equations (6)
- Measurement: 2.1 Length (12), 2.2 Area (6), 2.3 Volume (6), 2.4 Capacity (12), 2.5 Mass (12), 2.6 Time (8), 2.7 Money (8)
- Geometry: 3.1 Lines (4), 3.2 Angles (6), 3.3 Three Dimension (3-D) Objects (6)
- Data Handling: 4.1 Data Representation (6)

**Critical distinction**: 19 sub-strands ≠ 19 learning outcomes. Each sub-strand contains multiple lettered outcomes (e.g., 1.1 Whole Numbers contains a–h, 1.6 Fractions contains a–h).

**Exact LO count**: Must be calculated from the complete PDF extraction, not estimated.

### 2.3 Core competencies (7) — verified

From KICD Basic Education Curriculum Framework 2019:

1. Communication and Collaboration
2. Critical Thinking and Problem Solving
3. Imagination and Creativity
4. Citizenship
5. Digital Literacy
6. Learning to Learn
7. Self-Efficacy

### 2.4 Core values (8) — verified

From KICD Basic Education Curriculum Framework 2019:

1. Love
2. Responsibility
3. Respect
4. Unity
5. Peace
6. Patriotism
7. Social Justice
8. Integrity

### 2.5 Pertinent and Contemporary Issues (PCIs)

From KICD Basic Education Curriculum Framework 2019:

- Citizenship
- Health education
- Life skills
- Values education
- Education for Sustainable Development
- Community Service Learning
- Parental Empowerment and Engagement
- Global citizenship

**Note**: PCI wording must be cross-checked against official documents before seed.

---

## 3. Assessment requirements (KNEC)

### 3.1 Assessment types (per KNEC CBA framework)

- Diagnostic assessment
- Formative assessment
- School-Based Assessment (SBA)
- Summative assessment
- Portfolio assessment
- Practical assessment
- Project assessment
- Observation
- Oral assessment
- Self-assessment
- Peer assessment

### 3.2 National assessments

| Assessment | Level | Verified |
|-----------|-------|----------|
| KPSEA | End of Grade 6 | Pending KNEC confirmation |
| KJSEA | End of Grade 9 | Pending KNEC confirmation |
| KILEA | Intermediate SNE level | Pending KNEC confirmation |
| KPLEA | Prevocational SNE level | Pending KNEC confirmation |

### 3.3 Performance levels

KICD CBC performance levels:
- PL1: Below Expectations
- PL2: Approaching Expectations
- PL3: Meeting Expectations
- PL4: Exceeding Expectations

---

## 4. School management requirements (MoE)

### 4.1 School structure

- Academic years (term-based, typically 3 terms)
- Terms with defined start/end dates
- Streams per grade level
- Class teachers per stream
- Teacher assignments per subject per stream

### 4.2 Learner records

- Admission records
- Enrollment history
- Grade progression
- Transfer records
- Guardian information
- Academic performance history

### 4.3 Teacher records

- TSC registration
- Professional qualifications
- Subject specializations
- Teaching assignments
- Class teacher responsibilities

---

## 5. Data protection requirements (ODPC / DPA 2019)

### 5.1 Required controls

- Authentication on all learner-data views
- Role-based access control
- Audit logging of sensitive operations
- Encryption in transit (HTTPS)
- Secure cookie settings
- Password hashing (modern hashers)
- Data minimization
- Retention policies
- Parental consent tracking for minors

### 5.2 Children's data — special protections

- Purpose limitation
- Access restriction
- Consent tracking
- Right to erasure
- Cross-border transfer controls

---

## 6. Accessibility requirements (KICD digital standards)

### 6.1 Accessibility features (per KICD 2018 digital standards)

- Keyboard navigation
- Screen-reader compatibility
- Text-to-speech support
- Scalable text
- High-contrast display
- Alternative text for images
- Captions for audio/video
- Braille-compatible material support
- Accessible forms and controls
- Assistive technology support

### 6.2 SNE pathway structure (KICD)

Two parallel pathways:

**Pathway A — Adapted Regular Curriculum**
- For visual, hearing, physical impairments
- Same curriculum with adaptations

**Pathway B — Stage-Based Curriculum**
- Foundation level
- Intermediate level (6 learning areas, KILEA assessment)
- Prevocational level (7 learning areas, KPLEA assessment)
- Vocational level

---

## 7. KICD digital material approval standards (2018)

Ten evaluation areas:

1. Conformity to the curriculum
2. Accuracy and currency
3. Language use
4. Positive values and attitudes
5. Pertinent and contemporary issues
6. Assessment
7. Multimedia elements
8. Technical design
9. User guide
10. Cloud content attributes

**Caution**: 2018 standards — must confirm still current before formal submission.

---

## 8. Requirements traceability (summary)

| # | Requirement | Authority | Verification status |
|---|-------------|-----------|---------------------|
| R-01 | Grade 5 Math: 4 strands, 19 sub-strands, 150 lessons | KICD | Verified (PDF page xii) |
| R-02 | Grade 5 Math: exact LO lettering preserved | KICD | Pending — PDF extraction needed |
| R-03 | 7 core competencies | KICD | Verified |
| R-04 | 8 core values | KICD | Verified |
| R-05 | PCIs list | KICD | Pending — cross-check needed |
| R-06 | KNEC assessment types | KNEC | Pending — official doc download |
| R-07 | Performance levels PL1–PL4 | KICD | Verified |
| R-08 | KPSEA/KJSEA/KILEA/KPLEA | KNEC | Pending |
| R-09 | Data Protection Act controls | ODPC | Pending |
| R-10 | Accessibility (10 features) | KICD | Pending |
| R-11 | SNE four-level pathway | KICD | Pending |
| R-12 | Digital material 10 evaluation areas | KICD 2018 | Pending currency check |

---

## 9. What this specification does NOT claim

- Does NOT claim EduGrade is CBC-compliant
- Does NOT claim KICD approval
- Does NOT claim KNEC integration
- Does NOT treat the 4-outcome sample as sufficient curriculum coverage

**This is a requirements document, not a compliance certificate.**
