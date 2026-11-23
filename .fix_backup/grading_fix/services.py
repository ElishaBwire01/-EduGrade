"""
Grading services — pure analysis functions and data-seeding helpers.

Pure functions (no DB side-effects)
    get_performance_level            score -> PL code
    get_performance_level_name       PL code -> readable name
    assessment_completion            completion-rate summary
    performance_distribution         PL counts from result list
    top_learners                     sorted top-N by score
    best_gender                      top scorer for a given gender
    calculate_improvement            delta between two scores
    most_improved                    learners with biggest gain
    learners_requiring_support       PL1/PL2 students
    learning_area_average            mean score per learning area
    best_learning_areas              highest-scoring areas
    weakest_learning_areas           lowest-scoring areas
    generate_general_insight         human-readable summary

Database helpers (create / seed data)
    create_kcse_assessment_scheme    full 8-4-4 grading scheme
    create_cbc_assessment_scheme     full CBC grading scheme
    seed_student_assessments         generate MarkEntry /
                                       StudentKCSEGrade /
                                       StudentOverallKCSE records
    seed_cbc_assessments             generate StudentCBAAssessment /
                                       StudentOverallCBA records

Mark-edit helpers
    recalculate_student_kcse_grade   update a single KCSE grade row
    recalculate_student_cba_grade    update a single CBC assessment row
    recalculate_overall_for_student  update StudentOverallKCSE/CBA
    recalculate_for_mark_change      full pipeline when a MarkEntry changes
"""

from decimal import Decimal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CBC_LEVELS = {
    "PL4": "Exceeding Expectations",
    "PL3": "Meeting Expectations",
    "PL2": "Approaching Expectations",
    "PL1": "Below Expectations",
}

CBC_LEVEL_ORDER = {"PL4": 4, "PL3": 3, "PL2": 2, "PL1": 1}

KCSE_GRADES = [
    ("A",  "Excellent",  12, 80, 100),
    ("A-", "Very Good",  11, 75, 79),
    ("B+", "Good",       10, 70, 74),
    ("B",  "Good",        9, 65, 69),
    ("B-", "Fair",        8, 60, 64),
    ("C+", "Fair",        7, 55, 59),
    ("C",  "Average",     6, 45, 54),
    ("C-", "Pass",        5, 40, 44),
    ("D+", "Pass",        4, 35, 39),
    ("D",  "Poor",        3, 30, 34),
    ("D-", "Poor",        2, 25, 29),
    ("E",  "Poor",        1,  0, 24),
]

# ---------------------------------------------------------------------------
# Pure analysis functions  (tested by grading/tests.py)
# ---------------------------------------------------------------------------

def get_performance_level(score):
    """Map a numeric score to a CBC performance-level code (PL1–PL4).

    Returns None when *score* is None or empty.
    """
    if score is None:
        return None
    try:
        score = float(score)
    except (TypeError, ValueError):
        return None

    if score >= 80:
        return "PL4"
    if score >= 60:
        return "PL3"
    if score >= 30:
        return "PL2"
    if score >= 0:
        return "PL1"
    return None


def get_performance_level_name(code):
    """Return the display name for a PL code."""
    return CBC_LEVELS.get(code, "Unknown")


def assessment_completion(total_learners, assessed_learners):
    """Return a summary dict describing how many learners were assessed."""
    not_assessed = max(total_learners - assessed_learners, 0)
    completion_rate = round(assessed_learners / total_learners * 100, 1) if total_learners else 0
    return {
        "expected": total_learners,
        "assessed": assessed_learners,
        "not_assessed": not_assessed,
        "completion_rate": completion_rate,
    }


def performance_distribution(results):
    """Count how many learners fall into each performance level.

    *results* is a list of dicts, each with a ``level`` key.
    """
    distribution = {code: 0 for code in CBC_LEVELS}
    for item in results:
        level = item.get("level")
        if level in distribution:
            distribution[level] += 1
    return distribution


def top_learners(results, limit=3):
    """Return the top *limit* learners sorted by score (desc)."""
    scored = [r for r in results if r.get("score") is not None]
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:limit]


def best_gender(results, gender):
    """Return learners of *gender* sorted by score (desc)."""
    filtered = [r for r in results if r.get("gender") == gender and r.get("score") is not None]
    filtered.sort(key=lambda r: r["score"], reverse=True)
    return filtered


def calculate_improvement(current_score, previous_score):
    """Return the absolute improvement (current − previous)."""
    if current_score is None or previous_score is None:
        return 0
    return current_score - previous_score


def most_improved(results, limit=5):
    """Return the *limit* learners with the greatest score gain.

    Each result dict must contain ``current_score`` and ``previous_score``.
    """
    improved = []
    for r in results:
        gain = calculate_improvement(r.get("current_score"), r.get("previous_score"))
        improved.append({**r, "improvement": gain})
    improved.sort(key=lambda r: r["improvement"], reverse=True)
    return improved[:limit]


def learners_requiring_support(results):
    """Return learners whose level is PL1 or PL2 (needing intervention)."""
    return [r for r in results if r.get("level") in ("PL1", "PL2")]


def learning_area_average(results):
    """Return a dict mapping learning-area name → average score."""
    totals = {}
    counts = {}
    for r in results:
        area = r.get("learning_area")
        score = r.get("score")
        if area is None or score is None:
            continue
        totals[area] = totals.get(area, 0) + score
        counts[area] = counts.get(area, 0) + 1
    return {area: round(totals[area] / counts[area], 1) for area in totals}


def best_learning_areas(results, limit=3):
    """Return the *limit* learning areas with the highest average score.

    Each entry is a ``(name, average)`` tuple.
    """
    averages = learning_area_average(results)
    items = sorted(averages.items(), key=lambda x: x[1], reverse=True)
    return items[:limit]


def weakest_learning_areas(results, limit=3):
    """Return the *limit* learning areas with the lowest average score."""
    averages = learning_area_average(results)
    items = sorted(averages.items(), key=lambda x: x[1])
    return items[:limit]


def generate_general_insight(results):
    """Produce a one-sentence insight from a list of level results."""
    if not results:
        return "No assessment data is available."
    distribution = performance_distribution(results)
    total = sum(distribution.values())
    meeting_or_exceeding = distribution["PL3"] + distribution["PL4"]
    if total == 0:
        return "No assessment data is available."
    pct = round(meeting_or_exceeding / total * 100, 1)
    if pct >= 60:
        return f"{pct}% of learners are meeting or exceeding expectations (PL3/PL4)."
    return (
        f"Only {pct}% of learners are meeting or exceeding expectations (PL3/PL4). "
        f"{distribution['PL1']} learners are below expectations and need targeted support."
    )


# ---------------------------------------------------------------------------
# Database helpers — assessment scheme creation
# ---------------------------------------------------------------------------

def _create_kcse_rules(scheme, core_subjects):
    """Create KCSE grade rules for every grade band."""
    from .models import KCSEGradeRule

    for order, (grade, grade_name, points, min_score, max_score) in enumerate(KCSE_GRADES):
        KCSEGradeRule.objects.create(
            scheme=scheme,
            subject_scope="ALL",
            grade=grade,
            grade_name=grade_name,
            points=Decimal(points),
            min_score=min_score,
            max_score=max_score,
            descriptor=grade_name,
            order=order,
            is_active=True,
        )


def create_kcse_assessment_scheme(academic_year=None, created_by=None):
    """Create a complete 8-4-4 / KCSE assessment scheme.

    Returns the created ``AssessmentScheme`` instance.
    """
    from .models import AssessmentScheme, KCSEOverallCalculation
    from school.models import Curriculum

    kcse_curriculum = Curriculum.objects.filter(code="844").first()
    if not kcse_curriculum:
        raise RuntimeError("Curriculum '844' not found. Run school setup first.")

    scheme = AssessmentScheme.objects.create(
        name="KCSE Standard Grading",
        curriculum="844",
        description="Standard KCSE 8-4-4 grading scheme with A-E grades and weighted points.",
        is_active=True,
        academic_year=academic_year,
        effective_from=academic_year.start_date if academic_year else None,
        effective_to=academic_year.end_date if academic_year else None,
        created_by=created_by,
    )

    # Attach all grade levels belonging to the 844 curriculum
    scheme.grade_levels.set(
        kcse_curriculum.grade_levels.filter(is_active=True)
    )

    # Core subjects for KCSE (English, Kiswahili, Mathematics, Sciences)
    core_subject_names = {"English", "Kiswahili", "Mathematics", "Biology", "Chemistry", "Physics"}
    core_subjects = kcse_curriculum.subjects.filter(
        name__in=core_subject_names
    )

    # Grade rules
    _create_kcse_rules(scheme, core_subjects)

    # Overall calculation — Best 5 + core subjects
    calculation = KCSEOverallCalculation.objects.create(
        scheme=scheme,
        name="KCSE Standard Calculation",
        calculation_type="STANDARD",
        best_subject_count=5,
        min_subjects=7,
        max_subjects=9,
        grade_boundaries={
            "A": 80, "A-": 75, "B+": 70, "B": 65, "B-": 60,
            "C+": 55, "C": 45, "C-": 40, "D+": 35, "D": 30,
            "D-": 25, "E": 0,
        },
        is_active=True,
    )
    calculation.core_subjects.set(core_subjects)

    return scheme


def create_cbc_assessment_scheme(academic_year=None, created_by=None):
    """Create a complete CBC / CBA assessment scheme.

    Returns the created ``AssessmentScheme`` instance.
    """
    from .models import (
        AssessmentScheme, PerformanceLevel, AssessmentType,
        Rubric, RubricCriterion, RubricDescriptor,
        AssessmentComponent, ComponentAggregation,
    )
    from school.models import Curriculum

    cbc_curriculum = Curriculum.objects.filter(code="CBC").first()
    if not cbc_curriculum:
        raise RuntimeError("Curriculum 'CBC' not found. Run school setup first.")

    scheme = AssessmentScheme.objects.create(
        name="CBC Standard Assessment",
        curriculum="CBC",
        description="Standard CBC / CBA assessment scheme with PL1–PL4 performance levels.",
        is_active=True,
        academic_year=academic_year,
        effective_from=academic_year.start_date if academic_year else None,
        effective_to=academic_year.end_date if academic_year else None,
        created_by=created_by,
    )

    scheme.grade_levels.set(
        cbc_curriculum.grade_levels.filter(is_active=True)
    )

    # Performance levels (PL1–PL4)
    level_defs = [
        ("PL4", "Exceeding Expectations", 90, "Learner demonstrates comprehensive understanding."),
        ("PL3", "Meeting Expectations",   70, "Learner demonstrates satisfactory understanding."),
        ("PL2", "Approaching Expectations", 50, "Learner demonstrates partial understanding."),
        ("PL1", "Below Expectations",     0,  "Learner requires significant support."),
    ]
    levels = []
    for order, (code, name, numeric_value, description) in enumerate(level_defs):
        level = PerformanceLevel.objects.create(
            scheme=scheme,
            level_code=code,
            level_name=name,
            descriptor=description,
            order=order,
            numeric_value=numeric_value,
            is_active=True,
        )
        levels.append(level)

    # Assessment types
    assessment_types = [
        ("Formative Assessment",    "FORMATIVE",  20),
        ("Summative Assessment",    "SUMMATIVE",  30),
        ("School-Based Assessment", "SBA",        25),
        ("KJSEA Assessment",        "KJSEA",      25),
    ]
    for at_name, at_cat, weight in assessment_types:
        AssessmentType.objects.create(
            scheme=scheme,
            name=at_name,
            category=at_cat,
            weight=Decimal(weight),
            is_active=True,
        )

    # Rubrics per subject for each grade level
    subjects = list(cbc_curriculum.subjects.filter(is_active=True))
    grade_levels = list(cbc_curriculum.grade_levels.filter(is_active=True))

    criteria_defs = [
        ("Knowledge and Understanding",
         ["Identifies and recalls key facts and information",
          "Shows adequate knowledge of some facts and concepts",
          "Shows limited knowledge with some errors",
          "Shows minimal or inaccurate knowledge"]),
        ("Application of Knowledge",
         ["Applies knowledge accurately in new contexts",
          "Applies knowledge with some accuracy",
          "Applies knowledge with limited accuracy",
          "Unable to apply knowledge"]),
    ]

    for subject in subjects:
        for gl in grade_levels:
            rubric = Rubric.objects.create(
                scheme=scheme,
                name=f"{subject.name} — {gl.name} Rubric",
                description=f"CBC rubric for {subject.name} in {gl.name}.",
                subject=subject,
                grade_level=gl,
                is_active=True,
            )

            for crit_order, (crit_name, desc_list) in enumerate(criteria_defs):
                criterion = RubricCriterion.objects.create(
                    rubric=rubric,
                    criterion=crit_name,
                    description=desc_list[1],  # default to PL3 description
                    max_level=levels[0],  # PL4
                    order=crit_order,
                    is_active=True,
                )
                for level, desc in zip(levels, desc_list):
                    RubricDescriptor.objects.create(
                        criterion=criterion,
                        level=level,
                        descriptor=desc,
                    )

    # Assessment components
    components = [
        ("SBA",          "SBA",          40),
        ("Summative",    "SUMMATIVE",    35),
        ("KJSEA",        "KJSEA",        25),
    ]
    comp_objs = []
    for comp_name, comp_type, weight in components:
        comp = AssessmentComponent.objects.create(
            scheme=scheme,
            name=comp_name,
            component_type=comp_type,
            weight=Decimal(weight),
            is_active=True,
        )
        comp_objs.append(comp)

    aggregation = ComponentAggregation.objects.create(
        scheme=scheme,
        name="CBC Weighted Average",
        aggregation_type="WEIGHTED",
        is_active=True,
    )
    aggregation.components.set(comp_objs)

    return scheme


# ---------------------------------------------------------------------------
# Database helpers — student assessment generation
# ---------------------------------------------------------------------------

def seed_student_assessments(examination, students=None, score_range=(40, 95)):
    """Generate KCSE / 8-4-4 student results for *examination*.

    Parameters
    ----------
    examination : Examination
        Must belong to the 8-4-4 curriculum.
    students : iterable of Student, or None (all active students in the
        examination's grade level / stream).
    score_range : (min, max)
        Random score range used when no MarkEntry exists.

    Returns
    -------
    dict with counts of created KCSE grades and overalls.
    """
    from .models import (
        StudentKCSEGrade, StudentOverallKCSE,
        AssessmentScheme, KCSEGradeRule, KCSEOverallCalculation,
    )
    from marks.models import MarkEntry

    if examination.curriculum.code != "844":
        raise ValueError("seed_student_assessments expects an 8-4-4 examination.")

    scheme = AssessmentScheme.objects.filter(curriculum="844", is_active=True).first()
    if not scheme:
        raise RuntimeError("No active KCSE assessment scheme. Call create_kcse_assessment_scheme first.")

    rules = KCSEGradeRule.objects.filter(scheme=scheme, is_active=True).order_by("order")
    calculation = KCSEOverallCalculation.objects.filter(scheme=scheme, is_active=True).first()

    if students is None:
        students = examination.grade_level.students.filter(is_active=True)

    kcse_grade_count = 0
    overall_count = 0

    # Determine subject list from the examination
    exam_subjects = list(examination.subjects.all())

    import random
    random.seed(42)  # reproducible results

    for student in students:
        grades_data = []
        core_points = []
        best_points = []

        for subject in exam_subjects:
            # Try to read existing mark; otherwise generate one
            existing_mark = MarkEntry.objects.filter(
                student=student, examination=examination, subject=subject
            ).first()

            if existing_mark and existing_mark.score is not None:
                raw_mark = float(existing_mark.score)
            else:
                raw_mark = round(random.uniform(*score_range), 1)

            # Determine grade / points
            grade_result = _match_kcse_grade(rules, raw_mark)
            is_core = calculation and calculation.core_subjects.filter(id=subject.id).exists()

            StudentKCSEGrade.objects.update_or_create(
                student=student,
                examination=examination,
                subject=subject,
                defaults={
                    "raw_mark": raw_mark,
                    "grade": grade_result["grade"],
                    "points": Decimal(grade_result["points"]),
                    "is_core": is_core,
                },
            )
            kcse_grade_count += 1
            grades_data.append(grade_result)

            if is_core:
                core_points.append(grade_result["points"])
            else:
                best_points.append(grade_result["points"])

        # Calculate overall
        best_points.sort(reverse=True)
        best_count = min(calculation.best_subject_count, len(best_points)) if calculation else 5
        selected_best = best_points[:best_count]
        total_points = sum(core_points) + sum(selected_best)
        total_subjects = len(core_points) + len(selected_best)
        mean_score = round(total_points / total_subjects, 1) if total_subjects else 0

        mean_grade = _kcse_mean_grade(calculation, mean_score)

        StudentOverallKCSE.objects.update_or_create(
            student=student,
            examination=examination,
            defaults={
                "total_points": total_points,
                "mean_grade": mean_grade,
                "mean_score": mean_score,
                "core_subjects_count": len(core_points),
                "best_subjects_count": len(selected_best),
                "total_subjects_used": total_subjects,
            },
        )
        overall_count += 1

    _assign_positions(examination, StudentOverallKCSE, "mean_score")

    return {"kcse_grades": kcse_grade_count, "overalls": overall_count}


def seed_cbc_assessments(examination, students=None, assessment_data=None):
    """Generate CBC / CBA student results for *examination*.

    Parameters
    ----------
    examination : Examination
        Must belong to the CBC curriculum.
    students : iterable of Student, or None.
    assessment_data : dict
        Optional override — maps subject_id → PL level code.
        If not provided, levels are derived from random scores (seeded).

    Returns
    -------
    dict with counts of created CBC assessments and overalls.
    """
    from .models import (
        StudentCBAAssessment, StudentOverallCBA,
        AssessmentScheme, PerformanceLevel, Rubric,
    )

    if examination.curriculum.code != "CBC":
        raise ValueError("seed_cbc_assessments expects a CBC examination.")

    scheme = AssessmentScheme.objects.filter(curriculum="CBC", is_active=True).first()
    if not scheme:
        raise RuntimeError("No active CBC assessment scheme. Call create_cbc_assessment_scheme first.")

    levels = {lvl.level_code: lvl for lvl in
              PerformanceLevel.objects.filter(scheme=scheme, is_active=True)}

    if students is None:
        students = examination.grade_level.students.filter(is_active=True)

    # Get rubrics for the examination's subjects / grade level
    rubrics = Rubric.objects.filter(
        scheme=scheme,
        grade_level=examination.grade_level,
        is_active=True,
    ).select_related("subject")

    if not rubrics.exists():
        rubrics = Rubric.objects.filter(scheme=scheme, is_active=True).select_related("subject")

    import random
    random.seed(42)

    cba_assessment_count = 0
    overall_count = 0

    for student in students:
        component_scores = {}
        subject_scores = {}

        for rubric in rubrics:
            subject = rubric.subject
            criteria = rubric.criteria.filter(is_active=True)

            criterion_results = {}
            scores = []

            for criterion in criteria:
                if assessment_data and subject.id in assessment_data:
                    level_code = assessment_data[subject.id]
                else:
                    # Derive level from a seeded random score
                    score_val = random.uniform(20, 95)
                    level_code = get_performance_level(score_val)

                criterion_results[f"criterion_{criterion.id}"] = level_code
                level = levels.get(level_code)
                if level and level.numeric_value is not None:
                    scores.append(level.numeric_value)

            # Determine overall level via majority rule
            level_counts = {}
            for code in criterion_results.values():
                level_counts[code] = level_counts.get(code, 0) + 1
            overall_code = max(level_counts, key=level_counts.get) if level_counts else "PL1"
            overall_level = levels.get(overall_code)

            # Score for this rubric (average of criterion numeric values)
            subject_score = round(sum(scores) / len(scores), 1) if scores else 0
            subject_scores[subject.name] = subject_score

            StudentCBAAssessment.objects.update_or_create(
                student=student,
                examination=examination,
                rubric=rubric,
                defaults={
                    "criterion_results": criterion_results,
                    "overall_level": overall_level,
                    "score": Decimal(subject_score),
                    "teacher_notes": "Auto-generated assessment.",
                },
            )
            cba_assessment_count += 1

        # Calculate overall CBA result
        total_score = round(sum(subject_scores.values()) / len(subject_scores), 1) if subject_scores else 0
        overall_level = levels.get(get_performance_level(total_score))

        StudentOverallCBA.objects.update_or_create(
            student=student,
            examination=examination,
            defaults={
                "overall_level": overall_level,
                "component_scores": subject_scores,
                "total_score": Decimal(total_score),
                "total_weighted_score": Decimal(total_score),
            },
        )
        overall_count += 1

    _assign_positions(examination, StudentOverallCBA, "total_weighted_score")

    return {"cbc_assessments": cba_assessment_count, "overalls": overall_count}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _match_kcse_grade(rules, score):
    """Find the KCSE grade rule whose range contains *score*."""
    for rule in rules:
        if rule.min_score <= score <= rule.max_score:
            return {
                "grade": rule.grade,
                "grade_name": rule.grade_name,
                "points": float(rule.points),
                "descriptor": rule.descriptor or "",
            }
    return {"grade": "E", "grade_name": "Poor", "points": 1.0, "descriptor": "Below minimum"}


def _kcse_mean_grade(calculation, mean_score):
    """Map a mean_score to a KCSE mean grade."""
    if calculation and calculation.grade_boundaries:
        for grade, threshold in calculation.grade_boundaries.items():
            if mean_score >= threshold:
                return grade
    # Fallback to standard boundaries
    if mean_score >= 80:
        return "A"
    if mean_score >= 75:
        return "A-"
    if mean_score >= 70:
        return "B+"
    if mean_score >= 65:
        return "B"
    if mean_score >= 60:
        return "B-"
    if mean_score >= 55:
        return "C+"
    if mean_score >= 45:
        return "C"
    if mean_score >= 40:
        return "C-"
    if mean_score >= 35:
        return "D+"
    if mean_score >= 30:
        return "D"
    if mean_score >= 25:
        return "D-"
    return "E"


def _assign_positions(examination, model, score_field):
    """Assign ranking positions to all student overalls for an examination.

    Higher scores get lower (better) position numbers.
    Ties share the same position.
    """
    overalls = list(model.objects.filter(examination=examination).order_by(f"-{score_field}"))
    if not overalls:
        return

    position = 1
    prev_score = None
    for overall in overalls:
        current_score = getattr(overall, score_field)
        if prev_score is not None and current_score == prev_score:
            overall.position = position
        else:
            overall.position = position
            prev_score = current_score
        overall.save(update_fields=["position"])
        position += 1


def get_scheme_for_curriculum(curriculum_code):
    """Return the active AssessmentScheme for a curriculum code."""
    from .models import AssessmentScheme
    return AssessmentScheme.objects.filter(curriculum=curriculum_code, is_active=True).first()


# ---------------------------------------------------------------------------
# Mark-change pipeline — recalculate grades when a MarkEntry is edited
# ---------------------------------------------------------------------------

def recalculate_student_kcse_grade(mark_entry):
    """Recalculate a single ``StudentKCSEGrade`` row from a ``MarkEntry``.

    Looks up the active KCSE rules for the examination's curriculum and
    updates ``raw_mark``, ``grade``, ``points`` and ``is_core``.
    Returns the updated ``StudentKCSEGrade`` or ``None`` if no row exists.
    """
    from .models import StudentKCSEGrade, AssessmentScheme, KCSEGradeRule, KCSEOverallCalculation

    exam = mark_entry.examination
    if exam.curriculum.code != "844":
        return None

    scheme = get_scheme_for_curriculum("844")
    if not scheme:
        return None

    rules = KCSEGradeRule.objects.filter(scheme=scheme, is_active=True).order_by("order")
    rule = _match_kcse_grade(rules, float(mark_entry.score or 0))

    calculation = KCSEOverallCalculation.objects.filter(scheme=scheme, is_active=True).first()
    is_core = calculation and calculation.core_subjects.filter(id=mark_entry.subject.id).exists() if calculation else False

    grade_obj, _ = StudentKCSEGrade.objects.update_or_create(
        student=mark_entry.student,
        examination=exam,
        subject=mark_entry.subject,
        defaults={
            "raw_mark": mark_entry.score,
            "grade": rule["grade"],
            "points": Decimal(rule["points"]),
            "is_core": is_core,
        },
    )
    return grade_obj


def recalculate_student_cba_grade(mark_entry):
    """Recalculate a single ``StudentCBAAssessment`` row from a ``MarkEntry``.

    For CBC, the mark score maps to a performance level using
    ``get_performance_level``.
    """
    from .models import StudentCBAAssessment, AssessmentScheme, PerformanceLevel

    exam = mark_entry.examination
    if exam.curriculum.code != "CBC":
        return None

    scheme = get_scheme_for_curriculum("CBC")
    if not scheme:
        return None

    levels = {lvl.level_code: lvl for lvl in
              PerformanceLevel.objects.filter(scheme=scheme, is_active=True)}

    score_val = float(mark_entry.score or 0)
    level_code = get_performance_level(score_val)
    overall_level = levels.get(level_code)

    assessment, _ = StudentCBAAssessment.objects.update_or_create(
        student=mark_entry.student,
        examination=exam,
        defaults={
            "overall_level": overall_level,
            "score": Decimal(score_val),
            "teacher_notes": f"Updated by admin. Score: {mark_entry.score}",
        },
    )
    return assessment


def recalculate_overall_for_student(examination, student):
    """Recalculate the overall result (``StudentOverallKCSE`` or
    ``StudentOverallCBA``) for a single student after their marks changed.
    """
    from .models import (
        StudentKCSEGrade, StudentOverallKCSE,
        StudentCBAAssessment, StudentOverallCBA,
        AssessmentScheme, KCSEOverallCalculation, PerformanceLevel,
    )

    if examination.curriculum.code == "844":
        return _recalculate_kcse_overall(examination, student)
    elif examination.curriculum.code == "CBC":
        return _recalculate_cba_overall(examination, student)
    return None


def _recalculate_kcse_overall(examination, student):
    """Recalculate the overall KCSE result for one student."""
    from .models import (
        StudentKCSEGrade, StudentOverallKCSE,
        AssessmentScheme, KCSEOverallCalculation, KCSEGradeRule,
    )

    scheme = get_scheme_for_curriculum("844")
    if not scheme:
        return None

    calculation = KCSEOverallCalculation.objects.filter(scheme=scheme, is_active=True).first()
    rules = None
    if calculation:
        rules = KCSEGradeRule.objects.filter(scheme=scheme, is_active=True).order_by("order")

    grades = StudentKCSEGrade.objects.filter(
        student=student, examination=examination
    ).select_related("subject")

    core_points = []
    best_points = []

    for grade in grades:
        if grade.is_core:
            core_points.append(float(grade.points))
        else:
            best_points.append(float(grade.points))

    best_points.sort(reverse=True)
    best_count = min(calculation.best_subject_count, len(best_points)) if calculation else 5
    selected_best = best_points[:best_count]
    total_points = sum(core_points) + sum(selected_best)
    total_subjects = len(core_points) + len(selected_best)
    mean_score = round(total_points / total_subjects, 1) if total_subjects else 0
    mean_grade = _kcse_mean_grade(calculation, mean_score)

    return StudentOverallKCSE.objects.update_or_create(
        student=student,
        examination=examination,
        defaults={
            "total_points": total_points,
            "mean_grade": mean_grade,
            "mean_score": mean_score,
            "core_subjects_count": len(core_points),
            "best_subjects_count": len(selected_best),
            "total_subjects_used": total_subjects,
        },
    )[0]


def _recalculate_cba_overall(examination, student):
    """Recalculate the overall CBC / CBA result for one student."""
    from .models import (
        StudentCBAAssessment, StudentOverallCBA,
        AssessmentScheme, PerformanceLevel,
    )

    scheme = get_scheme_for_curriculum("CBC")
    if not scheme:
        return None

    levels = {lvl.level_code: lvl for lvl in
              PerformanceLevel.objects.filter(scheme=scheme, is_active=True)}

    assessments = StudentCBAAssessment.objects.filter(
        student=student, examination=examination
    ).select_related("subject", "overall_level")

    subject_scores = {}
    component_scores = {}

    for assessment in assessments:
        if assessment.score is not None:
            subject_scores[assessment.subject.name] = float(assessment.score)

    total_score = round(sum(subject_scores.values()) / len(subject_scores), 1) if subject_scores else 0
    overall_level = levels.get(get_performance_level(total_score))

    return StudentOverallCBA.objects.update_or_create(
        student=student,
        examination=examination,
        defaults={
            "overall_level": overall_level,
            "component_scores": subject_scores,
            "total_score": Decimal(total_score),
            "total_weighted_score": Decimal(total_score),
        },
    )[0]


def recalculate_for_mark_change(mark_entry):
    """Full pipeline: when a ``MarkEntry`` is edited (by admin or teacher),
    recalculate the dependent grade rows and the student's overall result.

    Parameters
    ----------
    mark_entry : MarkEntry
        The mark that was just saved (already has the new score).

    Returns
    -------
    dict with keys ``subject_grade`` and ``overall`` (the recalculated rows,
    or None if the examination's curriculum is not supported).
    """
    subject_grade = None
    overall = None

    if mark_entry.examination.curriculum.code == "844":
        subject_grade = recalculate_student_kcse_grade(mark_entry)
    elif mark_entry.examination.curriculum.code == "CBC":
        subject_grade = recalculate_student_cba_grade(mark_entry)

    overall = recalculate_overall_for_student(mark_entry.examination, mark_entry.student)

    return {"subject_grade": subject_grade, "overall": overall}
