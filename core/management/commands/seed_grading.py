"""Seed KCSE and CBC grading systems (ASCII-only for Windows compatibility)."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create KCSE and CBC assessment schemes with grade rules / performance levels'

    def handle(self, *args, **options):
        from grading.services import (
            create_kcse_assessment_scheme,
            create_cbc_assessment_scheme,
        )
        from grading.models import AssessmentScheme

        print('\n' + '=' * 50)
        print('CREATING GRADING SYSTEMS')
        print('=' * 50)

        # ---- KCSE / 8-4-4 ----
        print('\n[1] Creating KCSE / 8-4-4 scheme...')
        try:
            kcse = AssessmentScheme.objects.filter(curriculum='844', is_active=True).first()
            if kcse:
                print('    [SKIP] KCSE scheme already exists: ' + kcse.name)
            else:
                create_kcse_assessment_scheme()
                print('    [OK] KCSE scheme created')
        except Exception as e:
            print('    [FAIL] ' + str(e))

        # ---- CBC / CBA ----
        print('\n[2] Creating CBC / CBA scheme...')
        try:
            cbc = AssessmentScheme.objects.filter(curriculum='CBC', is_active=True).first()
            if cbc:
                print('    [SKIP] CBC scheme already exists: ' + cbc.name)
            else:
                create_cbc_assessment_scheme()
                print('    [OK] CBC scheme created')
        except Exception as e:
            print('    [FAIL] ' + str(e))

        print('\n' + '=' * 50)
        print('DONE')
        print('=' * 50)

        # Final tally
        from grading.models import KCSEGradeRule, PerformanceLevel
        print('\nFinal state:')
        print('  Schemes         : ' + str(AssessmentScheme.objects.count()))
        print('  KCSEGradeRule   : ' + str(KCSEGradeRule.objects.count()))
        print('  PerformanceLevel: ' + str(PerformanceLevel.objects.count()))
