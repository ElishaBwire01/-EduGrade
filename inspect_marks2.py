import re, pathlib, textwrap
R = pathlib.Path('.').resolve()

def show(t): print('\n' + '='*72 + '\n' + t + '\n' + '='*72)
def rd(p, n=None):
    try:
        t = p.read_text(errors='replace'); return t[:n] if n else t
    except: return ''

# 1. mark_view body
show('1. mark_view body (read-only view?)')
t = rd(R/'marks'/'views.py')
m = re.search(r'def mark_view\b.*?(?=\ndef |\nclass |\Z)', t, re.S)
print(textwrap.dedent(m.group(0)) if m else '(not found)')

# 2. imports at top of marks/views.py
show('2. marks/views.py imports')
print('\n'.join(rd(R/'marks'/'views.py').splitlines()[:40]))

# 3. Examination model constraints (status, subject M2M)
show('3. Examination model — status choices, subjects M2M, subject config')
t = rd(R/'examinations'/'models.py')
m = re.search(r'class Examination\b.*?(?=\nclass |\Z)', t, re.S)
print(m.group(0)[:2500] if m else '(not found)')

# 4. Student.current_grade_level vs historical placement
show('4. Student model — current placement fields')
t = rd(R/'students'/'models.py')
m = re.search(r'class Student\b.*?(?=\nclass |\Z)', t, re.S)
print(m.group(0)[:2200] if m else '(not found)')

# 5. Does mark_entry use Student.academic_year? Or current_grade_level?
show('5. Which exam-level filters mark_entry exposes')
t = rd(R/'marks'/'views.py')
m = re.search(r'def mark_entry\b.*?(?=\ndef |\nclass |\Z)', t, re.S)
body = m.group(0) if m else ''
print('available_exams filter:')
mm = re.search(r'available_exams\s*=\s*Examination\.objects\.filter\([^)]*\)', body, re.S)
print('  ' + (mm.group(0) if mm else '(not found)'))
print('\nStudent filter:')
mm = re.search(r'students\s*=\s*Student\.objects\.filter\([^)]*\)', body, re.S)
print('  ' + (mm.group(0) if mm else '(not found)'))

# 6. MarkEntry unique_together — confirms one mark per student/exam/subject
show('6. MarkEntry unique_together')
t = rd(R/'marks'/'models.py')
for ln in t.splitlines():
    if 'unique_together' in ln or 'constraints' in ln:
        print('   ', ln.strip())

# 7. grading/services.py — recalculate_for_mark_change signature
show('7. recalculate_for_mark_change (grading)')
for f in ['grading/services.py','grading/engine.py']:
    t = rd(R/f)
    if not t: continue
    m = re.search(r'def recalculate_for_mark_change\b.*?(?=\ndef |\nclass |\Z)', t, re.S)
    if m:
        print(f'\n### {f}')
        print(textwrap.dedent(m.group(0))[:1500])

# 8. AuditLog + send_notification helpers — confirm import names
show('8. Helper imports used by marks/views.py')
t = rd(R/'marks'/'views.py')
for name in ('AuditLog','send_notification','recalculate_for_mark_change','is_admin','Paginator'):
    for m in re.finditer(rf'^from\s+\S+\s+import\s+.*\b{name}\b', t, re.M):
        print('   ', m.group(0))

# 9. Is admin_mark_management linked in base.html or dashboard?
show('9. Links to admin_mark_management in templates')
for f in (R/'templates').rglob('*.html'):
    t = rd(f)
    if 'admin_mark_management' in t or 'marks:admin' in t:
        print('   ', f.relative_to(R/'templates'))

# 10. TeacherProfile — does admin usually have one?
show('10. Any auto-create TeacherProfile for admin? (signals)')
for f in R.rglob('signals.py'):
    if 'venv' in f.parts: continue
    t = rd(f)
    if 'TeacherProfile' in t:
        print(f'\n### {f.relative_to(R)}')
        for m in re.finditer(r'.*TeacherProfile.*', t):
            print('   ', m.group(0).strip()[:100])

print('\nDone.')
