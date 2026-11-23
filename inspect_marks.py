import re, pathlib, textwrap
R = pathlib.Path('.').resolve()

def show(t): print('\n' + '='*72 + '\n' + t + '\n' + '='*72)
def rd(p, n=None):
    try:
        t = p.read_text(errors='replace')
        return t[:n] if n else t
    except: return ''

# ---------- 1. marks/models.py — constraints ----------
show('1. marks/models.py — MarkEntry constraints & fields')
t = rd(R/'marks'/'models.py')
m = re.search(r'class MarkEntry\b.*?(?=\nclass |\Z)', t, re.S)
print(m.group(0) if m else '(not found)')

# ---------- 2. marks/views.py — full view bodies ----------
show('2. marks/views.py — admin view bodies')
t = rd(R/'marks'/'views.py')
for name in ('admin_mark_management', 'admin_mark_edit', 'mark_entry', 'mark_correction', '_is_admin_user'):
    m = re.search(rf'(?:^|\n)(?:@[\w\.\(\)\s,]+\n)*def {name}\b.*?(?=\n(?:@|def |class |\Z))', t, re.S)
    if m:
        print('\n' + '-'*72 + f'\n### {name}\n' + '-'*72)
        print(textwrap.dedent(m.group(0)))

# ---------- 3. marks/urls.py ----------
show('3. marks/urls.py')
print(rd(R/'marks'/'urls.py'))

# ---------- 4. admin_mark_management.html — form fields ----------
show('4. templates/marks/admin_mark_management.html — forms')
t = rd(R/'templates'/'marks'/'admin_mark_management.html')
# only the <form> blocks
for i, m in enumerate(re.finditer(r'<form\b.*?</form>', t, re.S | re.I), 1):
    block = m.group(0)
    print(f'\n--- form #{i} ({len(block)} chars) ---')
    print(block[:1200])
    if len(block) > 1200: print('…(truncated)')

# ---------- 5. admin_mark_edit.html — form fields ----------
show('5. templates/marks/admin_mark_edit.html — form')
t = rd(R/'templates'/'marks'/'admin_mark_edit.html')
for i, m in enumerate(re.finditer(r'<form\b.*?</form>', t, re.S | re.I), 1):
    block = m.group(0)
    print(f'\n--- form #{i} ---')
    print(block[:1500])

# ---------- 6. marks/entry.html — the normal entry form ----------
show('6. templates/marks/entry.html — first form (entry path)')
t = rd(R/'templates'/'marks'/'entry.html')
for i, m in enumerate(re.finditer(r'<form\b.*?</form>', t, re.S | re.I), 1):
    block = m.group(0)
    print(f'\n--- form #{i} ---')
    print(block[:1200])
    if i >= 2: break

# ---------- 7. Is there an admin "create mark" view? grep urls ----------
show('7. Any admin create-mark route anywhere?')
found = False
for urls in R.rglob('urls.py'):
    if 'venv' in urls.parts or 'site-packages' in str(urls): continue
    txt = rd(urls)
    for m in re.finditer(r'path\([^)]*\)', txt):
        line = m.group(0)
        if re.search(r'mark|admin', line, re.I):
            print(f'{urls.relative_to(R)}: {line.strip()}')
            found = True
if not found: print('  (none found)')

# ---------- 8. What does mark_entry enforce (subject scope)? ----------
show('8. mark_entry — teacher-subject restriction?')
t = rd(R/'marks'/'views.py')
m = re.search(r'def mark_entry\b.*?(?=\ndef |\nclass |\Z)', t, re.S)
if m:
    body = m.group(0)
    for kw in ('is_admin','is_staff','is_superuser','TeacherAssignment','permission','subject','grade','stream'):
        hits = [ln.strip() for ln in body.splitlines() if kw.lower() in ln.lower()]
        if hits:
            print(f'\n-- mentions "{kw}" --')
            for h in hits[:6]: print('   ', h)

# ---------- 9. Permission codes seeded (what gates marks) ----------
show('9. core/permissions.py + core/access.py — marks-related codes')
for f in ['core/permissions.py','core/access.py']:
    t = rd(R/f)
    if not t: continue
    print(f'\n### {f}')
    for m in re.finditer(r'[\'\"]can_[a-z_]+[\'\"]', t):
        print('   ', m.group(0))

print('\nDone.')
