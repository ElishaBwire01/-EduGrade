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
