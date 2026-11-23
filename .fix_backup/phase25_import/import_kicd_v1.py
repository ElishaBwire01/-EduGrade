"""Import KICD curriculum content from CSV.

Usage:
    python manage.py import_kicd path/to/file.csv --dry-run
    python manage.py import_kicd path/to/file.csv

CSV columns (header required):
    curriculum          : 'CBC' (defaults to 'CBC' if blank)
    grade               : exact GradeLevel name, e.g. 'Grade 5', 'PP1'
    learning_area_code  : e.g. 'MATH'
    learning_area_name  : e.g. 'Mathematics'
    strand              : e.g. 'Numbers'
    sub_strand          : e.g. 'Whole Numbers'
    outcome             : learning outcome text (required)
    experience          : suggested learning experience (optional)
    inquiry             : key inquiry question (optional)
    competencies        : semicolon-separated codes e.g. 'CC;CTPS' (optional)
    values              : semicolon-separated codes e.g. 'INTEG;RESP' (optional)
    pcis                : semicolon-separated codes e.g. 'ENV;HEALTH' (optional)

Behaviour:
    * LearningArea     : get_or_create by (curriculum_version, grade_level, code)
    * Strand           : get_or_create by (learning_area, name)
    * SubStrand        : get_or_create by (strand, name)
    * LearningOutcome  : get_or_create by (sub_strand, outcome_text)
    * M2M              : resolved by code; unknown codes logged and skipped
    * Whole import runs in transaction.atomic() by default
    * --dry-run        : validates everything, reports what WOULD change, no writes
"""
import csv
import os
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from school.models import (
    Curriculum, CurriculumVersion, GradeLevel, LearningArea,
    Strand, SubStrand, LearningOutcome, LearningExperience,
    InquiryQuestion, CoreCompetency, CoreValue, PCI,
)


REQUIRED_COLUMNS = {
    'curriculum', 'grade', 'learning_area_code', 'learning_area_name',
    'strand', 'sub_strand', 'outcome',
}


class Command(BaseCommand):
    help = 'Import KICD curriculum content from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Path to CSV file')
        parser.add_argument('--dry-run', action='store_true',
                            help='Validate and report only; no DB changes')
        parser.add_argument('--no-rollback', action='store_true',
                            help='Do not wrap in a transaction (partial imports allowed)')
        parser.add_argument('--strict', action='store_true',
                            help='Fail on first unknown competency/value/PCI code')
        parser.add_argument('--curriculum-version', type=str, default=None,
                            help='CurriculumVersion.version_code (default: current version)')

    # ---------------- helpers ----------------
    def _report(self, status, msg, dry_run):
        prefix = '[DRY] ' if dry_run else ''
        self.stdout.write(f'  {prefix}[{status}] {msg}')

    def _load_csv(self, path):
        p = Path(path)
        if not p.exists():
            raise CommandError(f'File not found: {path}')
        with p.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - headers
            if missing:
                raise CommandError(f'CSV missing required columns: {sorted(missing)}')
            rows = []
            for i, row in enumerate(reader, start=2):
                row['_line'] = i
                rows.append(row)
            return rows

    def _resolve_m2m(self, model, codes_str, label, dry_run):
        """Resolve 'CC;CTPS' -> [CoreCompetency, ...]. Unknown codes are skipped."""
        result = []
        if not codes_str:
            return result
        codes = [c.strip() for c in codes_str.split(';') if c.strip()]
        for code in codes:
            obj = model.objects.filter(code=code).first()
            if obj:
                result.append(obj)
            else:
                msg = f'{label} code {code!r} not found - skipped'
                if self.strict:
                    raise CommandError(msg)
                self.stdout.write(self.style.WARNING(f'    ! {msg}'))
        return result

    def _get_or_create_safe(self, model, lookup, defaults=None, dry_run=False):
        """Return (obj, created). In dry-run, don't touch DB - construct if missing."""
        obj = model.objects.filter(**lookup).first()
        if obj:
            return obj, False
        if dry_run:
            # ephemeral unsaved instance for reporting
            return model(**lookup, **(defaults or {})), True
        obj = model.objects.create(**lookup, **(defaults or {}))
        return obj, True

    # ---------------- main ----------------
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.strict  = options['strict']
        path         = options['csv_path']
        no_rollback  = options['no_rollback']
        version_code = options['curriculum_version']

        rows = self._load_csv(path)
        self.stdout.write(f'Loaded {len(rows)} rows from {path}')

        # Resolve target CurriculumVersion
        if version_code:
            ver = CurriculumVersion.objects.filter(version_code=version_code).first()
            if not ver:
                raise CommandError(f'CurriculumVersion version_code={version_code!r} not found')
        else:
            ver = CurriculumVersion.objects.filter(is_current=True).first()
            if not ver:
                raise CommandError('No current CurriculumVersion found. Create one first.')
        self.stdout.write(f'Target version: {ver} (curriculum={ver.curriculum.code})')

        # Cache lookups
        curricula_by_code  = {c.code: c for c in Curriculum.objects.all()}
        grades_by_curr     = {}  # (curriculum_id, name) -> GradeLevel
        for gl in GradeLevel.objects.all():
            grades_by_curr[(gl.curriculum_id, gl.name)] = gl

        stats = {
            'rows': len(rows),
            'learning_area_created': 0,
            'learning_area_existing': 0,
            'strand_created': 0,
            'strand_existing': 0,
            'substrand_created': 0,
            'substrand_existing': 0,
            'outcome_created': 0,
            'outcome_existing': 0,
            'experience_created': 0,
            'inquiry_created': 0,
            'errors': [],
        }

        def _run():
            for row in rows:
                try:
                    self._process_row(row, ver, grades_by_curr, curricula_by_code, stats)
                except Exception as e:
                    line = row.get('_line', '?')
                    stats['errors'].append(f'line {line}: {type(e).__name__}: {e}')
                    self.stdout.write(self.style.ERROR(f'  [ERR ] line {line}: {e}'))

        if self.dry_run or no_rollback:
            _run()
        else:
            try:
                with transaction.atomic():
                    _run()
                    if stats['errors']:
                        raise CommandError('Errors encountered - rolling back. Use --no-rollback to allow partial.')
            except CommandError:
                raise
            except Exception as e:
                raise CommandError(f'Import failed (rolled back): {e}')

        # ---------------- summary ----------------
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('SUMMARY')
        self.stdout.write('=' * 60)
        self.stdout.write(f"  Rows processed        : {stats['rows']}")
        self.stdout.write(f"  LearningArea created  : {stats['learning_area_created']}")
        self.stdout.write(f"  LearningArea existing : {stats['learning_area_existing']}")
        self.stdout.write(f"  Strand created        : {stats['strand_created']}")
        self.stdout.write(f"  Strand existing       : {stats['strand_existing']}")
        self.stdout.write(f"  SubStrand created     : {stats['substrand_created']}")
        self.stdout.write(f"  SubStrand existing    : {stats['substrand_existing']}")
        self.stdout.write(f"  Outcome created       : {stats['outcome_created']}")
        self.stdout.write(f"  Outcome existing      : {stats['outcome_existing']}")
        self.stdout.write(f"  Experience created    : {stats['experience_created']}")
        self.stdout.write(f"  Inquiry created       : {stats['inquiry_created']}")
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"  ERRORS                : {len(stats['errors'])}"))
            for e in stats['errors'][:10]:
                self.stdout.write(self.style.ERROR(f'    {e}'))
        else:
            self.stdout.write(self.style.SUCCESS('  ERRORS                : 0'))
        if self.dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - no changes were written.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nImport complete.'))

    # ---------------- per-row ----------------
    def _process_row(self, row, default_ver, grades_by_curr, curricula_by_code, stats):
        curr_code = (row.get('curriculum') or default_ver.curriculum.code).strip()
        curriculum = curricula_by_code.get(curr_code)
        if not curriculum:
            raise ValueError(f'Unknown curriculum code {curr_code!r}')

        grade_name = (row.get('grade') or '').strip()
        if not grade_name:
            raise ValueError('grade column empty')
        grade = grades_by_curr.get((curriculum.id, grade_name))
        if not grade:
            raise ValueError(f'GradeLevel {grade_name!r} not found under {curr_code}')

        # LearningArea
        la_code = (row.get('learning_area_code') or '').strip()
        la_name = (row.get('learning_area_name') or '').strip()
        if not la_code or not la_name:
            raise ValueError('learning_area_code and learning_area_name required')
        la, la_created = self._get_or_create_safe(
            LearningArea,
            lookup={
                'curriculum_version': default_ver,
                'grade_level': grade,
                'code': la_code,
            },
            defaults={'name': la_name, 'is_core': True, 'is_active': True},
            dry_run=self.dry_run,
        )
        if la_created:
            stats['learning_area_created'] += 1
        else:
            stats['learning_area_existing'] += 1

        # Strand
        strand_name = (row.get('strand') or '').strip()
        if not strand_name:
            raise ValueError('strand column empty')
        strand, s_created = self._get_or_create_safe(
            Strand,
            lookup={'learning_area': la, 'name': strand_name},
            defaults={'is_active': True},
            dry_run=self.dry_run,
        )
        if s_created: stats['strand_created'] += 1
        else:         stats['strand_existing'] += 1

        # SubStrand
        sub_name = (row.get('sub_strand') or '').strip()
        if not sub_name:
            raise ValueError('sub_strand column empty')
        sub, ss_created = self._get_or_create_safe(
            SubStrand,
            lookup={'strand': strand, 'name': sub_name},
            defaults={'is_active': True},
            dry_run=self.dry_run,
        )
        if ss_created: stats['substrand_created'] += 1
        else:          stats['substrand_existing'] += 1

        # LearningOutcome
        outcome_text = (row.get('outcome') or '').strip()
        if not outcome_text:
            raise ValueError('outcome column empty')
        lo, lo_created = self._get_or_create_safe(
            LearningOutcome,
            lookup={'sub_strand': sub, 'outcome_text': outcome_text},
            defaults={'is_active': True},
            dry_run=self.dry_run,
        )
        if lo_created: stats['outcome_created'] += 1
        else:          stats['outcome_existing'] += 1

        # LearningExperience
        exp_text = (row.get('experience') or '').strip()
        if exp_text:
            if not self.dry_run:
                _, exp_created = LearningExperience.objects.get_or_create(
                    learning_outcome=lo,
                    experience_text=exp_text,
                    defaults={'is_active': True},
                )
                if exp_created: stats['experience_created'] += 1
            else:
                if not LearningExperience.objects.filter(learning_outcome=lo, experience_text=exp_text).exists():
                    stats['experience_created'] += 1

        # InquiryQuestion
        inq_text = (row.get('inquiry') or '').strip()
        if inq_text:
            if not self.dry_run:
                _, inq_created = InquiryQuestion.objects.get_or_create(
                    learning_outcome=lo,
                    question_text=inq_text,
                    defaults={'is_active': True},
                )
                if inq_created: stats['inquiry_created'] += 1
            else:
                if not InquiryQuestion.objects.filter(learning_outcome=lo, question_text=inq_text).exists():
                    stats['inquiry_created'] += 1

        # M2M: competencies, values, pcis (skip in dry-run since lo not persisted)
        comp_codes  = row.get('competencies') or ''
        value_codes = row.get('values') or ''
        pci_codes   = row.get('pcis') or ''

        comp_objs  = self._resolve_m2m(CoreCompetency, comp_codes,  'competency', self.dry_run)
        value_objs = self._resolve_m2m(CoreValue,      value_codes, 'value',      self.dry_run)
        pci_objs   = self._resolve_m2m(PCI,            pci_codes,   'PCI',        self.dry_run)

        if not self.dry_run:
            if comp_objs:  lo.competencies.set(comp_objs)
            if value_objs: lo.core_values.set(value_objs)
            if pci_objs:   lo.pcis.set(pci_objs)


