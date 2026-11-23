import re, pathlib, textwrap, subprocess
R = pathlib.Path('.').resolve()
def rd(p, n=None):
    try:
        t = p.read_text(errors='replace'); return t[:n] if n else t
    except: return ''
def show(t): print('\n' + '='*72 + '\n' + t + '\n' + '='*72)

# 1. FULL process_marks function body (this is what raised the error)
show('1. process_marks — FULL body with line numbers')
t = rd(R/'grading'/'views.py')
lines = t.splitlines()
start = None
for i, ln in enumerate(lines):
    if re.match(r'\s*def process_marks\b', ln):
        start = i; break
if start is not None:
    # find next top-level def
    end = len(lines)
    for j in range(start+1, len(lines)):
        if re.match(r'(def |class |@)', lines[j]) and not lines[j].startswith(' '):
            end = j; break
    for i in range(start, end):
        print(f'{i+1:4d}| {lines[i]}')
else:
    print('(process_marks not found)')

# 2. Full grading/engine.py _save_results + surrounding
show('2. grading/engine.py — lines 130-250 (the perf["subject"] area)')
t = rd(R/'grading'/'engine.py')
lines = t.splitlines()
for i in range(125, min(260, len(lines))):
    print(f'{i+1:4d}| {lines[i]}')

# 3. Which engine does process_marks call? grep imports + usages
show('3. Engine usage in grading/views.py')
t = rd(R/'grading'/'views.py')
for i, ln in enumerate(t.splitlines(), 1):
    if re.search(r'GradingEngine|KCSEEngine|CBCEngine|process_exam_marks|process_examination', ln):
        print(f'{i:4d}| {ln}')

# 4. SubjectPerformance / GradeRule / GradingSystem — do these models still exist?
show('4. Are legacy models still defined in grading/models.py?')
t = rd(R/'grading'/'models.py')
for name in ['GradingSystem','GradeRule','PerformanceAnalysis','SubjectPerformance','AssessmentScheme','KCSEGradeRule']:
    m = re.search(rf'class {name}\b', t)
    print(f'  class {name}: {"YES" if m else "MISSING"}')

# 5. Live reproduction — call grading.views.process_marks directly
show('5. Live reproduction of the error')
probe = textwrap.dedent('''
    import os, django, traceback
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','edugrade.settings')
    django.setup()
    from django.test import RequestFactory
    from django.contrib.auth import get_user_model
    from examinations.models import Examination
    from school.models import GradeLevel, Stream
    from grading.views import process_marks

    U = get_user_model()
    admin = U.objects.filter(is_staff=True).first() or U.objects.first()
    exam = Examination.objects.first()
    gl = GradeLevel.objects.first()
    st = Stream.objects.first()
    print('admin:', admin, '| exam:', exam, '| grade:', gl, '| stream:', st)

    rf = RequestFactory()
    req = rf.post('/grading/process/', data={
        'examination': exam.id if exam else '',
        'grade_level': gl.id if gl else '',
        'stream': st.id if st else '',
    })
    req.user = admin
    req._messages = []  # in case messages framework needs it
    try:
        resp = process_marks(req)
        print('RESPONSE:', getattr(resp, 'status_code', resp))
        print('REDIRECT:', getattr(resp, 'url', None))
    except Exception:
        print('\\n--- EXCEPTION TRACEBACK ---')
        traceback.print_exc()
    print('\\n--- messages buffer ---')
    try:
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.messages import get_messages
    except Exception:
        pass
''').strip()
script = R/'_probe2.py'
script.write_text(probe, encoding='utf-8')
try:
    r = subprocess.run(['python','_probe2.py'], capture_output=True, text=True, timeout=120)
    print('STDOUT:\n' + r.stdout[:6000])
    print('STDERR:\n' + r.stderr[:3000])
finally:
    try: script.unlink()
    except: pass

# 6. Templates/grading/process.html form fields
show('6. grading/process.html — form field names submitted')
t = rd(R/'templates'/'grading'/'process.html')
for m in re.finditer(r'<form\b.*?</form>', t, re.S | re.I):
    for inp in re.finditer(r'<(?:input|select|textarea)[^>]*name=["\']([^"\']+)["\']', m.group(0)):
        print('  field:', inp.group(1))

print('\nDone.')
