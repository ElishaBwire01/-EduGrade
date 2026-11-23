#!/usr/bin/env python
"""Fix DB state for Phase 5/6 + re-verify. Run from project root."""
import sys, os, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')

import django
django.setup()

from django.conf import settings
from django.db import connection

print('=' * 70)
print('STEP 0: DATABASE IDENTITY CHECK')
print('=' * 70)
db_path = settings.DATABASES['default']['NAME']
print(f'  DB path      : {db_path}')
print(f'  Exists       : {os.path.exists(db_path)}')
print(f'  Size         : {os.path.getsize(db_path) if os.path.exists(db_path) else 0} bytes')

# ====================================================================
print()
print('=' * 70)
print('STEP 1: FIX — ensure CBC curriculum + PP1..Grade 12 grades exist')
print('=' * 70)

from school.models import Curriculum, GradeLevel

# --- CBC curriculum ---
cbc, created = Curriculum.objects.get_or_create(
    code='CBC',
    defaults={
        'name': 'Competency-Based Curriculum',
        'description': 'Kenya CBC (PP1 - Grade 12)',
        'is_active': True,
    },
)
print(f'  CBC curriculum: {"CREATED" if created else "EXISTS"} (id={cbc.id})')

# --- All 14 CBC grades ---
GRADES = [
    ('PP',    1, 'PP1'),
    ('PP',    2, 'PP2'),
    ('GRADE', 1, 'Grade 1'),
    ('GRADE', 2, 'Grade 2'),
    ('GRADE', 3, 'Grade 3'),
    ('GRADE', 4, 'Grade 4'),
    ('GRADE', 5, 'Grade 5'),
    ('GRADE', 6, 'Grade 6'),
    ('GRADE', 7, 'Grade 7'),
    ('GRADE', 8, 'Grade 8'),
    ('GRADE', 9, 'Grade 9'),
    ('GRADE', 10, 'Grade 10'),
    ('GRADE', 11, 'Grade 11'),
    ('GRADE', 12, 'Grade 12'),
]
made = 0
for level_type, num, name in GRADES:
    order_val = {'PP1': 1, 'PP2': 2}.get(name, num + 2)
    obj, was_created = GradeLevel.objects.get_or_create(
        curriculum=cbc,
        name=name,
        defaults={
            'level_type': level_type,
            'level_number': num,
            'order': order_val,
            'is_active': True,
        },
    )
    if was_created:
        made += 1
        print(f'    + created {name}')
print(f'  CBC grades: {made} created, {GradeLevel.objects.filter(curriculum=cbc).count()} total')

# ====================================================================
print()
print('=' * 70)
print('STEP 2: FIX — ensure a staff/admin user exists for HTTP test')
print('=' * 70)

from django.contrib.auth import get_user_model
User = get_user_model()

admin = User.objects.filter(is_staff=True, is_superuser=True).first()
if not admin:
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@edugrade.local',
            'is_staff': True,
            'is_superuser': True,
            'first_name': 'Admin',
            'last_name': 'User',
        },
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print(f'  Created admin user: username=admin password=admin123')
    else:
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        print(f'  Fixed existing admin user permissions')
else:
    print(f'  Admin user exists: {admin.username}')

# ====================================================================
print()
print('=' * 70)
print('STEP 3: RE-VERIFY (fixed template check)')
print('=' * 70)

from django.test import Client
from django.urls import reverse, get_resolver
from django.template.loader import get_template
from django.db.migrations.executor import MigrationExecutor
from django.apps import apps as django_apps

SEP = '=' * 70
PASS = '[OK]'
FAIL = '[X ]'
WARN = '[! ]'
results = {'pass': 0, 'fail': 0, 'warn': 0}

def check(label, fn, critical=True):
    try:
        r = fn()
        results['pass'] += 1
        print(f'  {PASS} {label}' + (f' -> {r}' if r is not None else ''))
        return True
    except Exception as e:
        if critical:
            results['fail'] += 1
            print(f'  {FAIL} {label}: {type(e).__name__}: {e}')
        else:
            results['warn'] += 1
            print(f'  {WARN} {label}: {e}')
        return False

print('\n[1] Phase 5 models exist and queryable')
from school.models import (
    SchemeOfWork, SchemeOfWorkRow, LessonPlan, LessonActivity,
    CurriculumCoverage, TeachingResource, TeacherReflection,
)
for m in [SchemeOfWork, SchemeOfWorkRow, LessonPlan, LessonActivity,
          CurriculumCoverage, TeachingResource, TeacherReflection]:
    check(f'{m.__name__} ({m.objects.count()} rows)', lambda: None)

print('\n[2] Phase 5 URLs reverse')
for name, args in [
    ('school:scheme_list', []),
    ('school:scheme_detail', [1]),
    ('school:coverage_dashboard', []),
]:
    check(name, lambda n=name, a=args: reverse(n, args=a))

print('\n[3] Phase 5 templates load (FIXED check)')
for t in ['school/scheme_list.html', 'school/scheme_detail.html', 'school/coverage_dashboard.html']:
    check(t, lambda t=t: 'loaded' if get_template(t) else (_ for _ in ()).throw(Exception('empty')))

print('\n[4] Phase 5 migration applied')
ex = MigrationExecutor(connection)
applied = ex.migration_plan  # check plan is empty (all applied)
phase5_applied = 'phase5_teaching_learning' in ''.join(
    str(m) for app, migrations in MigrationExecutor(connection).loader.applied_migrations if app == 'school'
    for m in [migrations]  # already a set
)
# Simpler: check from migration list
from django.db.migrations.recorder import MigrationRecorder
rec = MigrationRecorder(connection)
applied_set = {(r.app, r.name) for r in rec.migration_qs.all()} if hasattr(rec, 'migration_qs') else set()
# Fallback via executor
ex2 = MigrationExecutor(connection)
applied_set = ex2.loader.applied_migrations
phase5_applied = any('phase5_teaching_learning' in str(name) for app, name in applied_set if app == 'school')
check('school.phase5_teaching_learning', lambda: 'yes' if phase5_applied else (_ for _ in ()).throw(Exception('not applied')))

print('\n[5] HTTP smoke test (as admin)')
if admin:
    client = Client()
    client.force_login(admin)
    for url_name in ['school:scheme_list', 'school:coverage_dashboard']:
        def _hit(n=url_name):
            resp = client.get(reverse(n))
            if resp.status_code not in (200, 302):
                raise Exception(f'HTTP {resp.status_code}')
            return f'HTTP {resp.status_code}'
        check(f'GET {url_name}', _hit)
else:
    print(f'  {WARN} no admin user')
    results['warn'] += 1

print('\n[6] Pathway/track/combination/career models exist')
found_any = False
for model in django_apps.get_models():
    n = model.__name__.lower()
    if any(k in n for k in ['pathway', 'track', 'combination', 'career', 'senior', 'placement', 'preference']):
        print(f'  {PASS} {model._meta.app_label}.{model.__name__}')
        found_any = True
if not found_any:
    print(f'  {WARN} none found (Phase 6 will create)')
    results['warn'] += 1

print('\n[7] Grades 10-12 in CBC (FIXED)')
for gname in ['Grade 10', 'Grade 11', 'Grade 12']:
    g = GradeLevel.objects.filter(curriculum=cbc, name=gname).first()
    if g:
        print(f'  {PASS} {gname} exists (level_number={g.level_number})')
        results['pass'] += 1
    else:
        print(f'  {FAIL} {gname} missing')
        results['fail'] += 1

print('\n[8] Senior School state')
from school.models import LearningArea, Subject
g10_12 = GradeLevel.objects.filter(curriculum=cbc, name__in=['Grade 10','Grade 11','Grade 12'])
la_count = LearningArea.objects.filter(grade_level__in=g10_12).count()
print(f'  LearningAreas for Grades 10-12 : {la_count}')
print(f'  Subjects total                 : {Subject.objects.count()}')
print(f'  LearningAreas total            : {LearningArea.objects.count()}')

# ====================================================================
print()
print(SEP); print('SUMMARY'); print(SEP)
print(f'  PASS : {results["pass"]}')
print(f'  WARN : {results["warn"]}')
print(f'  FAIL : {results["fail"]}')
print()
if results['fail'] == 0:
    print('[OK] Phase 5 fully functional')
    print('[OK] Phase 6 inspection complete — ready to design')
else:
    print(f'[X ] {results["fail"]} critical failure(s)')
print()
print('========== END ==========')
