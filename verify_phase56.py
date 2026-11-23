#!/usr/bin/env python
"""Phase 5 verify + Phase 6 inspect. Run from project root."""
import sys, os, pathlib

# Ensure project root is on sys.path regardless of invocation method
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse, get_resolver
from django.template.loader import get_template
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.apps import apps as django_apps

SEP = '=' * 70
PASS = '[\u2713]'
FAIL = '[\u2717]'
WARN = '[!]'

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

# =====================================================================
print()
print(SEP); print('PHASE 5 SMOKE TEST'); print(SEP)

print('\n[1] Phase 5 models exist and queryable')
from school.models import (
    SchemeOfWork, SchemeOfWorkRow, LessonPlan, LessonActivity,
    CurriculumCoverage, TeachingResource, TeacherReflection,
)
for m in [SchemeOfWork, SchemeOfWorkRow, LessonPlan, LessonActivity,
          CurriculumCoverage, TeachingResource, TeacherReflection]:
    check(f'{m.__name__} ({m.objects.count()} rows)', lambda: None)

print('\n[2] Phase 5 URLs reverse correctly')
for name, args in [
    ('school:scheme_list', []),
    ('school:scheme_detail', [1]),
    ('school:coverage_dashboard', []),
]:
    check(f'{name}', lambda n=name, a=args: reverse(n, args=a))

print('\n[3] Phase 5 templates load')
for t in ['school/scheme_list.html', 'school/scheme_detail.html', 'school/coverage_dashboard.html']:
    check(t, lambda t=t: get_template(t).name if get_template(t) else None)

print('\n[4] Phase 5 migration applied')
ex = MigrationExecutor(connection)
applied = ex.loader.applied_migrations
phase5_mig = any('phase5_teaching_learning' in str(name) for app, name in applied if app == 'school')
check('school.phase5_teaching_learning applied',
      lambda: 'yes' if phase5_mig else (_ for _ in ()).throw(Exception('not applied')))

print('\n[5] HTTP smoke test (Phase 5 URLs render)')
User = get_user_model()
admin = User.objects.filter(is_staff=True).first()
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
    print(f'  {WARN} no admin user — skipping HTTP test')
    results['warn'] += 1

# =====================================================================
print()
print(SEP); print('PHASE 6 INSPECTION (Senior School pathways)'); print(SEP)

print('\n[6] Existing pathway/track/combination/career models')
found_any = False
keywords = ['pathway', 'track', 'combination', 'career', 'senior', 'placement', 'preference']
for model in django_apps.get_models():
    n = model.__name__.lower()
    if any(k in n for k in keywords):
        print(f'  {PASS} {model._meta.app_label}.{model.__name__}')
        found_any = True
if not found_any:
    print(f'  {WARN} none found — Phase 6 will create new models')

print('\n[7] Student fields relevant to pathway')
from students.models import Student
for fname in ['curriculum', 'current_grade_level', 'current_stream', 'academic_year']:
    try:
        f = Student._meta.get_field(fname)
        target = f.related_model.__name__ if hasattr(f, "related_model") and f.related_model else type(f).__name__
        print(f'  {PASS} Student.{fname} -> {target}')
    except Exception as e:
        print(f'  {FAIL} Student.{fname}: {e}')

print('\n[8] Stream model fields')
from school.models import Stream
for f in Stream._meta.fields:
    print(f'    Stream.{f.name}: {type(f).__name__}')

print('\n[9] Grades 10-12 in CBC')
from school.models import GradeLevel, Curriculum
cbc = Curriculum.objects.filter(code='CBC').first()
if cbc:
    for gname in ['Grade 10', 'Grade 11', 'Grade 12']:
        g = GradeLevel.objects.filter(curriculum=cbc, name=gname).first()
        if g:
            print(f'  {PASS} {gname} exists (level_number={g.level_number})')
        else:
            print(f'  {FAIL} {gname} missing')

print('\n[10] LearningAreas for Grades 10-12')
if cbc:
    g10_12 = GradeLevel.objects.filter(curriculum=cbc, name__in=['Grade 10','Grade 11','Grade 12'])
    from school.models import LearningArea
    la_count = LearningArea.objects.filter(grade_level__in=g10_12).count()
    print(f'  LearningAreas for Grades 10-12: {la_count}')
    if la_count == 0:
        print(f'  {WARN} none yet — curriculum import will be needed')

print('\n[11] Existing Subjects')
from school.models import Subject
for s in Subject.objects.all()[:20]:
    print(f'    {s.code:10} {s.name:30} type={s.subject_type}')

print('\n[12] Career/guidance models')
for app_label in ['students', 'teachers']:
    try:
        app_cfg = django_apps.get_app_config(app_label)
        for model in app_cfg.get_models():
            if any(k in model.__name__.lower() for k in ['career', 'guidance', 'counsel']):
                print(f'  {PASS} {app_label}.{model.__name__}')
    except LookupError:
        pass

print('\n[13] URLs matching senior-school keywords')
def walk(patterns, prefix=''):
    out = []
    for p in patterns:
        if hasattr(p, 'url_patterns'):
            out.extend(walk(p.url_patterns, prefix + str(p.pattern)))
        else:
            out.append((prefix + str(p.pattern), getattr(p, 'name', '?')))
    return out
try:
    all_urls = walk(get_resolver().url_patterns)
    matches = [(u, n) for u, n in all_urls if any(k in u.lower() or k in (n or '').lower() for k in ['pathway','senior','comb','track','career'])]
    if matches:
        for u, n in matches:
            print(f'  {PASS} {u}  -> {n}')
    else:
        print(f'  {WARN} none found')
except Exception as e:
    print(f'  {FAIL} URL scan failed: {e}')

print('\n[14] Templates matching senior-school keywords')
tpl_matches = []
for t in pathlib.Path('templates').rglob('*.html'):
    if any(k in t.name.lower() for k in ['pathway','senior','comb','track','career']):
        tpl_matches.append(str(t))
if tpl_matches:
    for t in tpl_matches:
        print(f'  {PASS} {t}')
else:
    print(f'  {WARN} none found')

print('\n[15] Migration files matching senior-school keywords')
mig_matches = []
for p in pathlib.Path('.').rglob('migrations/*.py'):
    if 'venv' in str(p) or 'site-packages' in str(p):
        continue
    if any(k in p.name.lower() for k in ['pathway','senior','comb','track','career']):
        mig_matches.append(str(p))
if mig_matches:
    for m in mig_matches:
        print(f'  {PASS} {m}')
else:
    print(f'  {WARN} none found')

# =====================================================================
print()
print(SEP); print('SUMMARY'); print(SEP)
print(f'  PASS : {results["pass"]}')
print(f'  WARN : {results["warn"]}')
print(f'  FAIL : {results["fail"]}')
print()
if results['fail'] == 0:
    print(f'{PASS} Phase 5 fully functional')
    print(f'{PASS} Phase 6 inspection complete — ready to design')
else:
    print(f'{FAIL} {results["fail"]} critical failure(s) — fix before Phase 6')
print()
print('========== END ==========')
