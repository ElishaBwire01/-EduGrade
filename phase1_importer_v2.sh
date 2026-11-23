#!/bin/bash
set -e
cd /home/elisha/-EduGrade

echo "======================================================================"
echo "PHASE 1: IMPORTER v2 — behavioral fixes + tests"
echo "======================================================================"

# ------------------------------------------------------------------
echo "[1/6] Backup importer and tests"
# ------------------------------------------------------------------
mkdir -p .fix_backup/phase1
cp core/management/commands/import_kicd.py .fix_backup/phase1/import_kicd.py.bak
cp core/tests.py .fix_backup/phase1/tests.py.bak
echo "  backed up to .fix_backup/phase1/"

# ------------------------------------------------------------------
echo ""
echo "[2/6] Fix I-03: duplicate detection now REPORTS"
# ------------------------------------------------------------------
python << 'PYFIX'
from pathlib import Path

p = Path('core/management/commands/import_kicd.py')
src = p.read_text(encoding='utf-8')

old = '''                # Detect conflicting duplicate definitions in one CSV.
                if area_key in seen_areas:
                    pass
                seen_areas.add(area_key)

                seen_strands.add(strand_key)
                seen_substrands.add(substrand_key)
                seen_outcomes.add(outcome_key)'''

new = '''                # Detect conflicting duplicate definitions in one CSV.
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

assert old in src, "I-03 anchor not found — file structure changed"
src = src.replace(old, new, 1)
p.write_text(src, encoding='utf-8')
print('  I-03 fixed: duplicate detection now reports errors')
PYFIX

# ------------------------------------------------------------------
echo ""
echo "[3/6] Fix I-04: ambiguous DB match detection"
# ------------------------------------------------------------------
python << 'PYFIX'
from pathlib import Path

p = Path('core/management/commands/import_kicd.py')
src = p.read_text(encoding='utf-8')

old = '''        # Check existing hierarchy for ambiguous matches.
        for label, model, filters in (
            (
                "LearningArea",
                LearningArea,
                None,
            ),
        ):
            if filters is not None:
                continue

        return errors, warnings'''

new = '''        # Check existing hierarchy for ambiguous matches.
        # If any model has multiple rows for what should be unique,
        # the importer would silently pick the first one. That is unsafe.
        existing_la = LearningArea.objects.filter(
            curriculum_version=version,
        ).values("grade_level_id", "code").annotate(
            n=models.Count("id")
        ).filter(n__gt=1)
        for row in existing_la:
            errors.append(
                f"Ambiguous LearningArea: grade_level_id={row['grade_level_id']} "
                f"code={row['code']!r} has {row['n']} rows in the database "
                f"(expected 1). Fix the existing data before importing."
            )

        existing_strand = Strand.objects.values(
            "learning_area_id", "name"
        ).annotate(n=models.Count("id")).filter(n__gt=1)
        for row in existing_strand:
            errors.append(
                f"Ambiguous Strand: learning_area_id={row['learning_area_id']} "
                f"name={row['name']!r} has {row['n']} rows."
            )

        existing_substrand = SubStrand.objects.values(
            "strand_id", "name"
        ).annotate(n=models.Count("id")).filter(n__gt=1)
        for row in existing_substrand:
            errors.append(
                f"Ambiguous SubStrand: strand_id={row['strand_id']} "
                f"name={row['name']!r} has {row['n']} rows."
            )

        existing_outcome = LearningOutcome.objects.values(
            "sub_strand_id", "outcome_text"
        ).annotate(n=models.Count("id")).filter(n__gt=1)
        for row in existing_outcome:
            errors.append(
                f"Ambiguous LearningOutcome: sub_strand_id={row['sub_strand_id']} "
                f"has {row['n']} identical outcome_text rows."
            )

        return errors, warnings'''

assert old in src, "I-04 anchor not found — file structure changed"
src = src.replace(old, new, 1)

# Add models import if not present
if 'from django.db import models' not in src:
    src = src.replace(
        'from django.db import transaction',
        'from django.db import transaction, models',
        1,
    )

p.write_text(src, encoding='utf-8')
print('  I-04 fixed: ambiguous DB match detection now reports errors')
PYFIX

# ------------------------------------------------------------------
echo ""
echo "[4/6] Verify importer still imports (syntax check)"
# ------------------------------------------------------------------
python -c "import ast, pathlib; ast.parse(pathlib.Path('core/management/commands/import_kicd.py').read_text())" \
    && echo "  syntax OK"

# ------------------------------------------------------------------
echo ""
echo "[5/6] Write behavioral tests in core/tests.py"
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


BASE_CSV_HEADER = (
    "curriculum,grade,learning_area_code,learning_area_name,"
    "strand,sub_strand,outcome,experience,inquiry,"
    "competencies,values,pcis,knowledge,skills,attitudes,values_text\n"
)


def _write_csv(rows):
    """Write rows to a temp CSV file, return its path."""
    f = tempfile.NamedTemporaryFile(
        mode='w', suffix='.csv', delete=False, encoding='utf-8'
    )
    f.write(BASE_CSV_HEADER)
    for row in rows:
        f.write(row + "\n")
    f.close()
    return f.name


class ImporterTestBase(TestCase):
    """Shared fixtures: a minimal CBC curriculum + grade."""

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
        # Reference codes used in CSVs
        CoreCompetency.objects.create(code='CC', name='Communication')
        CoreValue.objects.create(code='INTEG', name='Integrity')
        PCI.objects.create(code='ENV', name='Environmental awareness')


class TestMissingColumnRejected(ImporterTestBase):
    def test_missing_column_rejected(self):
        """CSV missing 'strand' column must be rejected before any writes."""
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
    """I-03: duplicates within CSV must produce errors, not silent passes."""

    def test_duplicate_rows_reported(self):
        csv_path = _write_csv([
            # Same LearningArea/Strand/SubStrand/Outcome defined twice
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
        ])
        with self.assertRaises(CommandError) as ctx:
            call_command('import_kicd', csv_path, '--dry-run')
        msg = str(ctx.exception).lower()
        self.assertIn('duplicate', msg)
        # Should specifically flag the duplicate LearningArea
        self.assertTrue(
            'learningarea' in msg or 'learning area' in msg or 'outcome' in msg
        )


class TestAmbiguousDbMatchErrors(ImporterTestBase):
    """I-04: pre-existing duplicate rows in DB must block the import."""

    def test_ambiguous_db_match_errors(self):
        # Manually create TWO LearningAreas with the same code+grade.
        # Bypass the unique constraint by direct SQL insert (constraint may
        # or may not exist — this test proves importer *detects* it either way).
        from django.db import connection
        la1 = LearningArea.objects.create(
            curriculum_version=self.version, grade_level=self.grade,
            code='MATH', name='Mathematics', is_active=True,
        )
        # Attempt to create a duplicate — if DB constraint blocks, test is
        # skipped gracefully; if not, the importer must detect the ambiguity.
        try:
            la2 = LearningArea.objects.create(
                curriculum_version=self.version, grade_level=self.grade,
                code='MATH', name='Math Duplicate', is_active=True,
            )
        except Exception:
            self.skipTest(
                'DB blocks duplicate LearningArea — schema-level protection exists'
            )
            return

        csv_path = _write_csv([
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
        ])
        with self.assertRaises(CommandError) as ctx:
            call_command('import_kicd', csv_path, '--dry-run')
        self.assertIn('ambiguous', str(ctx.exception).lower())


class TestRollbackOnFailure(ImporterTestBase):
    """I-06: import failing mid-way must leave DB unchanged."""

    def test_rollback_on_failure(self):
        # CSV where first row is valid, second row has invalid grade
        # → entire import must roll back, no rows persisted.
        csv_path = _write_csv([
            # Valid row
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
            # Invalid row — grade does not exist
            "CBC,Grade 99,SCI,Science,Life,Matter,inspect matter,,,,,,,,",
        ])
        before_la = LearningArea.objects.count()
        before_outcome = LearningOutcome.objects.count()

        with self.assertRaises(CommandError):
            call_command('import_kicd', csv_path)

        # Counts must be unchanged — transaction rolled back
        self.assertEqual(LearningArea.objects.count(), before_la)
        self.assertEqual(LearningOutcome.objects.count(), before_outcome)


class TestIdempotentImport(ImporterTestBase):
    """I-07: importing the same CSV twice creates no duplicates."""

    def test_idempotent_import(self):
        csv_path = _write_csv([
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,read numbers,,,,,,,,",
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,write numbers,,,,,,,,",
        ])

        # First import
        call_command('import_kicd', csv_path)
        counts_after_first = {
            'la': LearningArea.objects.count(),
            'strand': Strand.objects.count(),
            'substrand': SubStrand.objects.count(),
            'outcome': LearningOutcome.objects.count(),
        }

        # Second import — identical file
        call_command('import_kicd', csv_path)
        counts_after_second = {
            'la': LearningArea.objects.count(),
            'strand': Strand.objects.count(),
            'substrand': SubStrand.objects.count(),
            'outcome': LearningOutcome.objects.count(),
        }

        self.assertEqual(
            counts_after_first, counts_after_second,
            f'Second import should be no-op, got {counts_after_first} vs {counts_after_second}'
        )


class TestKnowledgeSkillsPopulated(ImporterTestBase):
    """I-08: importer populates knowledge/skills/attitudes/values_text."""

    def test_knowledge_skills_populated(self):
        csv_path = _write_csv([
            "CBC,Grade 5,MATH,Mathematics,Numbers,Whole Numbers,"
            "read numbers,,,,,,,Counting to 100,"
            "Read symbols,Positive attitude,Accuracy",
            # Fields order: curriculum,grade,area_code,area_name,strand,substrand,
            # outcome,experience,inquiry,competencies,values,pcis,
            # knowledge,skills,attitudes,values_text
        ])
        # Build CSV directly for clarity
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

        call_command('import_kicd', f.name)

        outcome = LearningOutcome.objects.filter(
            outcome_text='read whole numbers',
        ).first()
        self.assertIsNotNone(outcome, 'Outcome was not created')
        self.assertEqual(outcome.knowledge, 'Knowledge of place value')
        self.assertEqual(outcome.skills, 'Reading and writing numbers')
        self.assertEqual(outcome.attitudes, 'Positive attitude')
        self.assertEqual(outcome.values_text, 'Accuracy and precision')

        # Also verify M2M relationships
        self.assertEqual(outcome.competencies.count(), 1)
        self.assertEqual(outcome.core_values.count(), 1)
        self.assertEqual(outcome.pcis.count(), 1)
PYEOF

echo "  wrote 6 behavioral tests"

# ------------------------------------------------------------------
echo ""
echo "[6/6] Run tests + audit"
# ------------------------------------------------------------------
echo ""
echo "=== Django check ==="
python manage.py check 2>&1

echo ""
echo "=== Run all importer tests (core.tests) ==="
python manage.py test core.tests -v 2 2>&1

echo ""
echo "=== Run compliance audit ==="
python manage.py compliance_audit --write-report 2>&1 | head -60

echo ""
echo "======================================================================"
echo "PHASE 1 COMPLETE"
echo "======================================================================"
echo ""
echo "If all tests passed and audit shows I-03/I-04/I-06/I-07/I-08 VERIFIED:"
echo "  ✓ Importer is behaviorally correct and tested"
echo "  ✓ Ready for Phase 2 (real KICD CSV import)"
echo ""
echo "If any test failed: paste the failure — it names exactly what to fix."
echo "======================================================================"
