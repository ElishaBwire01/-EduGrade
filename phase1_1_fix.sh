#!/bin/bash
set -e
cd /home/elisha/-EduGrade

echo "======================================================================"
echo "PHASE 1.1: FIX I-03 SCOPE + TEST BUGS"
echo "======================================================================"

# ------------------------------------------------------------------
echo "[1/4] Fix I-03: only flag duplicates WITHIN the current CSV"
# ------------------------------------------------------------------
python << 'PYFIX'
from pathlib import Path

p = Path('core/management/commands/import_kicd.py')
src = p.read_text(encoding='utf-8')

# The bug: seen_areas/seen_strands/etc are local to _validate_rows()
# (correct — they start empty each run). But on the SECOND import of the
# same CSV, the first run created rows in DB, then validation on the second
# run... wait, no. seen_* only tracks THIS run's rows. So why did the second
# import fail?

# Look at what's actually happening. The second import creates the same
# keys. First row: adds MATH. Second row: also MATH → duplicate error.
# But that's for a CSV with 2 rows having the same key.
#
# The real bug is different: in test_idempotent_import, the CSV has TWO
# DIFFERENT outcomes under the same LearningArea. So:
# row 1: area=MATH, strand=Numbers, substrand=Whole Numbers, outcome=read
# row 2: area=MATH, strand=Numbers, substrand=Whole Numbers, outcome=write
#
# Area/strand/substrand keys are the same for both rows — but that's NORMAL
# and EXPECTED. Multiple outcomes share the same LearningArea.
#
# So the I-03 fix is WRONG: it treats shared parents as duplicates.
# Correct semantics:
#   - Duplicate LearningArea = same key with conflicting name
#   - Duplicate Strand = same key with conflicting attributes
#   - Duplicate SubStrand = same key with conflicting attributes
#   - Duplicate LearningOutcome = same key with conflicting detail fields
#
# Actually, the simplest correct semantic: only check DUPLICATE OUTCOME keys.
# Because LearningArea/Strand/SubStrand are reused across rows by design.
# Only LearningOutcome should be unique per (substrand, outcome_text).
#
# But then I-03's "duplicate LearningArea" requirement makes no sense...
# unless the requirement is: same LearningArea appearing with DIFFERENT
# names in the same CSV is a conflict.

# Let's re-read the user's original concern:
# "Two CSV rows could define conflicting information for the same curriculum
#  item without validation catching it."
#
# So the check should be: same key BUT different name → error.
# Same key AND same name → OK (it's just the parent of another outcome).

# Rewrite the fix properly: track key→name mapping, error only if names conflict.

old = '''                # Detect conflicting duplicate definitions in one CSV.
                if area_key in seen_areas:
                    errors.append(
                        f"line {line}: duplicate LearningArea definition "
                        f"for {area_key[2]!r} (already defined earlier)."
                    )
                seen_areas.add(area_key)

                if strand_key in seen_strands:
                    errors.append(
                        f"line {line}: duplicate Strand definition "
                        f"for {strand_key[1]!r} under "
                        f"LearningArea {area_key[2]!r}."
                    )
                seen_strands.add(strand_key)

                if substrand_key in seen_substrands:
                    errors.append(
                        f"line {line}: duplicate SubStrand definition "
                        f"for {substrand_key[1]!r} under "
                        f"Strand {strand_key[1]!r}."
                    )
                seen_substrands.add(substrand_key)

                if outcome_key in seen_outcomes:
                    errors.append(
                        f"line {line}: duplicate LearningOutcome definition "
                        f"(exact same outcome already defined earlier)."
                    )
                seen_outcomes.add(outcome_key)'''

new = '''                # Detect CONFLICTING duplicate definitions in one CSV.
                # Reusing the same LearningArea/Strand/SubStrand across rows
                # is normal — that's how multiple outcomes share parents.
                # Only flag when the SAME key appears with DIFFERENT content.
                area_name = row.get("learning_area_name", "").strip()
                if area_key in seen_areas:
                    previous_name = seen_areas[area_key]
                    if previous_name != area_name:
                        errors.append(
                            f"line {line}: conflicting LearningArea definition "
                            f"for {area_key[2]!r}: name was {previous_name!r}, "
                            f"now {area_name!r}."
                        )
                else:
                    seen_areas[area_key] = area_name

                if strand_key in seen_strands:
                    # Strand has no separate display name — the key IS the name.
                    # If the key matches, it's the same strand. No conflict.
                    pass
                else:
                    seen_strands[strand_key] = True

                if substrand_key in seen_substrands:
                    pass
                else:
                    seen_substrands[substrand_key] = True

                # LearningOutcome: same (substrand, outcome_text) is the
                # PRIMARY KEY. It must appear only once per CSV. This is
                # the true duplicate check.
                if outcome_key in seen_outcomes:
                    errors.append(
                        f"line {line}: duplicate LearningOutcome definition "
                        f"(exact same outcome_text already defined earlier "
                        f"in this CSV)."
                    )
                else:
                    seen_outcomes[outcome_key] = True'''

assert old in src, "I-03 anchor not found"
src = src.replace(old, new, 1)

# Change seen_areas/seen_strands/seen_substrands/seen_outcomes from set to dict
old_init = '''        seen_areas = set()
        seen_strands = set()
        seen_substrands = set()
        seen_outcomes = set()'''

new_init = '''        seen_areas = {}
        seen_strands = {}
        seen_substrands = {}
        seen_outcomes = {}'''

assert old_init in src, "seen_* init anchor not found"
src = src.replace(old_init, new_init, 1)

p.write_text(src, encoding='utf-8')
print('  I-03 refixed: only flags CONFLICTING duplicates, allows shared parents')
PYFIX

# ------------------------------------------------------------------
echo ""
echo "[2/4] Verify importer still parses"
# ------------------------------------------------------------------
python -c "import ast, pathlib; ast.parse(pathlib.Path('core/management/commands/import_kicd.py').read_text())" \
    && echo "  syntax OK"

# ------------------------------------------------------------------
echo ""
echo "[3/4] Rewrite tests — fix stdout capture, idempotency, ambiguity"
# ------------------------------------------------------------------
cat > core/tests.py << 'PYEOF'
"""Behavioral tests for the KICD importer.

These tests prove the requirements the compliance audit checks.
They must pass for I-03, I-04, I-06, I-07, I-08 to be marked VERIFIED.
"""
import io
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from school.models import (
    Curriculum, CurriculumVersion, GradeLevel,
    LearningArea, Strand, SubStrand, LearningOutcome,
    LearningExperience, InquiryQuestion,
    CoreCompetency, CoreValue, PCI,
)


CSV_HEADER = (
    "curriculum,grade,learning_area_code,learning_area_name,"
    "strand,sub_strand,outcome,experience,inquiry,"
    "competencies,values,pcis,knowledge,skills,attitudes,values_text\n"
)


def _write_csv(rows):
    f = tempfile.NamedTemporaryFile(
        mode='w', suffix='.csv', delete=False, encoding='utf-8'
    )
    f.write(CSV_HEADER)
    for row in rows:
        f.write(row + "\n")
    f.close()
    return f.name


class ImporterTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cbc = Curriculum.objects.create(
            code='CBC', name='CBC', is_active=True,
        )
        cls.version = CurriculumVersion.objects.create(
            curriculum=cls.cbc,
            version_code='TEST2025',
            name='Test Version',
            is_current=True,
            is_active=True,
        )
        cls.grade = GradeLevel.objects.create(
            curriculum=cls.cbc,
            level_type='GRADE',
            level_number=5,
            name='Grade 5',
            order=5,
            is_active=True,
        )
        CoreCompetency.objects.create(code='CC', name='Communication')
        CoreValue.objects.create(code='INTEG', name='Integrity')
        PCI.objects.create(code='ENV', name='Environmental awareness')


class TestMissingColumnRejected(ImporterTestBase):
    def test_missing_column_rejected(self):
        f = tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False, encoding='utf-8'
        )
        f.write(
            "curriculum,grade,learning_area_code,learning_area_name,"
            "sub_strand,outcome\n"
            "CBC,Grade 5,MATH,Mathematics,Whole Numbers,read numbers\n"
        )
        f.close()
        with self.assertRaises(CommandError) as ctx:
            call_command('import_kicd', f.name, '--dry-run')
        self.assertIn('strand', str(ctx.exception).lower())


class TestDuplicateRowsReported(ImporterTestBase):
    """I-03: exact duplicate outcomes within one CSV must error, with detail."""

    def test_duplicate_rows_reported(self):
        csv_path = _write_csv([
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
        ])
        # Capture stdout to find the detail message
        out = io.StringIO()
        with self.assertRaises(CommandError) as ctx:
            call_command('import_kicd', csv_path, '--dry-run', stdout=out)
        output = out.getvalue().lower()
        # The detail is printed to stdout via self.style.ERROR
        self.assertIn('duplicate', output,
                      f'Expected "duplicate" in importer output, got: {out.getvalue()}')
        # The exception itself says validation failed
        self.assertIn('validation failed', str(ctx.exception).lower())


class TestConflictingNamesReported(ImporterTestBase):
    """I-03 additional case: same area code but different names = conflict."""

    def test_conflicting_names_reported(self):
        csv_path = _write_csv([
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
            "CBC,Grade 5,MATH,MATHS,Numbers,Whole Numbers,write numbers,,,,,,,,",
            # Same code MATH but name "Mathematics" vs "MATHS" → conflict
        ])
        out = io.StringIO()
        with self.assertRaises(CommandError):
            call_command('import_kicd', csv_path, '--dry-run', stdout=out)
        output = out.getvalue().lower()
        self.assertIn('conflicting', output)
        self.assertIn('math', output)


class TestAmbiguousDbMatchErrors(ImporterTestBase):
    """I-04: pre-existing duplicates in DB must block import.
    Use Strand (no unique constraint) since LearningArea has one."""

    def test_ambiguous_db_match_errors(self):
        # Create a LearningArea, then TWO Strand rows with same name via
        # direct SQL — bypassing any unique_together that might exist.
        from django.db import connection
        la = LearningArea.objects.create(
            curriculum_version=self.version, grade_level=self.grade,
            code='MATH', name='Mathematics', is_active=True,
        )
        # Strand model has no unique constraint on (learning_area, name)
        # so we can create duplicates directly
        s1 = Strand.objects.create(learning_area=la, name='Numbers', is_active=True)
        s2 = Strand.objects.create(learning_area=la, name='Numbers', is_active=True)

        csv_path = _write_csv([
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
        ])
        out = io.StringIO()
        with self.assertRaises(CommandError) as ctx:
            call_command('import_kicd', csv_path, '--dry-run', stdout=out)
        output = out.getvalue().lower()
        self.assertIn('ambiguous', output)


class TestRollbackOnFailure(ImporterTestBase):
    """I-06: import failing mid-way must leave DB unchanged."""

    def test_rollback_on_failure(self):
        csv_path = _write_csv([
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
            "CBC,Grade 99,SCI,Science,Life,Matter,inspect matter,,,,,,,,",
        ])
        before_la = LearningArea.objects.count()
        before_outcome = LearningOutcome.objects.count()

        with self.assertRaises(CommandError):
            call_command('import_kicd', csv_path)

        self.assertEqual(LearningArea.objects.count(), before_la)
        self.assertEqual(LearningOutcome.objects.count(), before_outcome)


class TestIdempotentImport(ImporterTestBase):
    """I-07: re-importing the same CSV produces no duplicates.
    Each import runs from a FRESH state — seen_* dict resets.
    So same file twice = second is no-op (get_or_create finds existing)."""

    def test_idempotent_import(self):
        # Two DIFFERENT outcomes under same parent — no conflict
        csv_path = _write_csv([
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,write numbers,,,,,,,,",
        ])

        call_command('import_kicd', csv_path, stdout=io.StringIO())
        counts_first = (
            LearningArea.objects.count(),
            Strand.objects.count(),
            SubStrand.objects.count(),
            LearningOutcome.objects.count(),
        )

        # Re-run same CSV — should be no-op
        call_command('import_kicd', csv_path, stdout=io.StringIO())
        counts_second = (
            LearningArea.objects.count(),
            Strand.objects.count(),
            SubStrand.objects.count(),
            LearningOutcome.objects.count(),
        )

        self.assertEqual(counts_first, counts_second,
                         f'Idempotent import failed: {counts_first} vs {counts_second}')
        self.assertEqual(counts_first[3], 2, 'Should have exactly 2 outcomes')


class TestKnowledgeSkillsPopulated(ImporterTestBase):
    """I-08: importer populates knowledge/skills/attitudes/values_text."""

    def test_knowledge_skills_populated(self):
        header = (
            "curriculum,grade,learning_area_code,learning_area_name,"
            "strand,sub_strand,outcome,experience,inquiry,"
            "competencies,values,pcis,knowledge,skills,attitudes,values_text\n"
        )
        row = (
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,"
            "read whole numbers,,,CC,INTEG,ENV,"
            "Knowledge of place value,Reading and writing numbers,"
            "Positive attitude,Accuracy and precision\n"
        )
        f = tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False, encoding='utf-8'
        )
        f.write(header + row)
        f.close()

        call_command('import_kicd', f.name, stdout=io.StringIO())

        outcome = LearningOutcome.objects.filter(
            outcome_text='read whole numbers',
        ).first()
        self.assertIsNotNone(outcome, 'Outcome was not created')
        self.assertEqual(outcome.knowledge, 'Knowledge of place value')
        self.assertEqual(outcome.skills, 'Reading and writing numbers')
        self.assertEqual(outcome.attitudes, 'Positive attitude')
        self.assertEqual(outcome.values_text, 'Accuracy and precision')

        self.assertEqual(outcome.competencies.count(), 1)
        self.assertEqual(outcome.core_values.count(), 1)
        self.assertEqual(outcome.pcis.count(), 1)
PYEOF

echo "  rewrote tests with proper I-03 semantics"

# ------------------------------------------------------------------
echo ""
echo "[4/4] Run tests + audit"
# ------------------------------------------------------------------
echo ""
echo "=== Django check ==="
python manage.py check 2>&1

echo ""
echo "=== Importer tests ==="
python manage.py test core.tests -v 2 2>&1

echo ""
echo "=== Compliance audit ==="
python manage.py compliance_audit --write-report 2>&1 | head -50

echo ""
echo "======================================================================"
echo "PHASE 1.1 COMPLETE"
echo "======================================================================"
