import re, pathlib, textwrap, traceback
R = pathlib.Path('.').resolve()
def show(t): print('\n' + '='*72 + '\n' + t + '\n' + '='*72)
def rd(p, n=None):
    try:
        t = p.read_text(errors='replace'); return t[:n] if n else t
    except: return ''

# 1. process_marks view — where "'subject'" error likely comes from
show('1. grading/views.py — process_marks + helpers')
t = rd(R/'grading'/'views.py')
for name in ('process_marks','_kcse_class_report','_cbc_class_report','grading_system_list'):
    m = re.search(rf'(?:^|\n)(?:@[\w\.\(\)\s,]+\n)*def {name}\b.*?(?=\ndef |\nclass |\Z)', t, re.S)
    if m:
        print('\n--- ' + name + ' ---')
        print(textwrap.dedent(m.group(0))[:3500])

# 2. grading/services.py — full pipeline
show('2. grading/services.py (full)')
print(rd(R/'grading'/'services.py')[:8000])

# 3. grading/engine.py
show('3. grading/engine.py (full)')
print(rd(R/'grading'/'engine.py')[:5000])

# 4. grading/kcse_engine.py
show('4. grading/kcse_engine.py')
print(rd(R/'grading'/'kcse_engine.py')[:6000])

# 5. grading/cbc_engine.py
show('5. grading/cbc_engine.py')
print(rd(R/'grading'/'cbc_engine.py')[:6000])

# 6. Examination STATUS enforcement — where is status checked?
show('6. Every reference to exam.status / status__in / LOCKED / PUBLISHED')
for f in R.rglob('*.py'):
    if 'venv' in f.parts or 'site-packages' in str(f): continue
    t = rd(f)
    for i, ln in enumerate(t.splitlines(), 1):
        if re.search(r"\bstatus__in\b|\bstatus\s*==\s*['\"](?:LOCKED|PUBLISHED|ACTIVE|DRAFT|ARCHIVED)|exam\.status|examination\.status", ln):
            print(f'  {f.relative_to(R)}:{i}: {ln.strip()[:120]}')

# 7. MarkEntry saves — do they check exam.status?
show('7. mark save / update sites')
for f in [R/'marks'/'views.py', R/'marks'/'models.py']:
    t = rd(f)
    for i, ln in enumerate(t.splitlines(), 1):
        if re.search(r'mark_entry\.save|MarkEntry\.objects\.(create|update|get_or_create)|mark\.save', ln):
            print(f'  {f.relative_to(R)}:{i}: {ln.strip()[:120]}')

# 8. Where does "'subject'" KeyError come from? find any dict access ['subject']
show('8. Places doing ["subject"] / .get("subject") / ["score"] etc.')
for f in R.rglob('*.py'):
    if 'venv' in f.parts or 'site-packages' in str(f): continue
    t = rd(f)
    for i, ln in enumerate(t.splitlines(), 1):
        if re.search(r"""\[\s*['"](?:subject|score|exam|student|grade)['"]\s*\]""", ln):
            print(f'  {f.relative_to(R)}:{i}: {ln.strip()[:120]}')

# 9. What does _kcse_engine expect as input? show signatures
show('9. Engine function signatures')
for f in [R/'grading'/'engine.py', R/'grading'/'kcse_engine.py', R/'grading'/'cbc_engine.py', R/'grading'/'services.py']:
    t = rd(f)
    if not t: continue
    print(f'\n### {f.relative_to(R)}')
    for m in re.finditer(r'^def (\w+)\(([^)]*)\):', t, re.M):
        print(f'  def {m.group(1)}({m.group(2).strip()})')

# 10. Run process_marks in a real Django shell with the failing exam to catch the exact traceback
show('10. Reproduce the error (read-only)')
import subprocess, textwrap as tw
probe = tw.dedent('''
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','edugrade.settings')
    django.setup()
    from django.test import RequestFactory
    from django.contrib.auth import get_user_model
    from examinations.models import Examination
    from grading.views import process_marks
    from grading.services import process_exam_marks
    U = get_user_model()
    admin = U.objects.filter(is_staff=True).first() or U.objects.first()
    exam = Examination.objects.filter(status__in=['ACTIVE','LOCKED']).first() \
           or Examination.objects.first()
    print('admin:', admin)
    print('exam :', exam)
    if not exam: raise SystemExit('no exams')
    try:
        process_exam_marks(exam, admin)
        print('process_exam_marks OK')
    except Exception as e:
        import traceback; traceback.print_exc()
''').strip()
script = R/'_probe_process.py'
script.write_text(probe, encoding='utf-8')
try:
    r = subprocess.run(['python','_probe_process.py'], capture_output=True, text=True, timeout=90)
    print('STDOUT:\n' + r.stdout[:4000])
    print('STDERR:\n' + r.stderr[:4000])
finally:
    try: script.unlink()
    except: pass

print('\nDone.')
