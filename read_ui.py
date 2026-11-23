import re, pathlib
R = pathlib.Path('.').resolve()
TPL = R / 'templates'
if not TPL.exists():
    print('No templates/ folder'); raise SystemExit

def show(t): print('\n' + '='*70 + '\n' + t + '\n' + '='*70)
def rd(p):
    try: return p.read_text(errors='replace')
    except: return ''

files = sorted(TPL.rglob('*.html'))
print(f'Found {len(files)} templates under {TPL}\n')

# ---------- 1. OVERVIEW ----------
show('1. OVERVIEW — every template, extends, blocks, size')
for f in files:
    t = rd(f)
    extends  = re.search(r'{%\s*extends\s+[\'"]([^\'"]+)', t)
    blocks   = re.findall(r'{%\s*block\s+(\w+)', t)
    includes = re.findall(r'{%\s*include\s+[\'"]([^\'"]+)', t)
    lines = t.count('\n') + 1
    print('\n' + str(f.relative_to(TPL)))
    print('  lines: %d' % lines)
    if extends:  print('  extends: ' + extends.group(1))
    if blocks:   print('  blocks: ' + ', '.join(blocks))
    if includes: print('  includes: ' + ', '.join(includes))

# ---------- 2. FORMS & INPUTS ----------
show('2. FORMS & INPUTS — what the user can submit')
for f in files:
    t = rd(f)
    forms    = re.findall(r'<form([^>]*)>', t, re.I)
    inputs   = re.findall(r'<input([^>]*)>', t, re.I)
    selects  = re.findall(r'<select([^>]*)>', t, re.I)
    textarea = re.findall(r'<textarea([^>]*)>', t, re.I)
    buttons  = re.findall(r'<button[^>]*>([^<]*)</button>', t, re.I)
    if not (forms or inputs or selects or textarea or buttons):
        continue
    print('\n' + str(f.relative_to(TPL)))
    for attrs in forms:
        act  = re.search(r'action=["\']([^"\']*)', attrs, re.I)
        meth = re.search(r'method=["\']([^"\']*)', attrs, re.I)
        print('  form: action=%s  method=%s' % (
            act.group(1) if act else '(none)',
            meth.group(1) if meth else '(GET default)'))
    for attrs in inputs:
        typ  = re.search(r'type=["\']([^"\']*)', attrs, re.I)
        name = re.search(r'name=["\']([^"\']*)', attrs, re.I)
        if name:
            print('    input[%s] name=%s' % (typ.group(1) if typ else 'text', name.group(1)))
    for attrs in selects:
        name = re.search(r'name=["\']([^"\']*)', attrs, re.I)
        if name: print('    select name=%s' % name.group(1))
    for attrs in textarea:
        name = re.search(r'name=["\']([^"\']*)', attrs, re.I)
        if name: print('    textarea name=%s' % name.group(1))
    for b in buttons:
        if b.strip(): print('    button: ' + b.strip()[:60])

# ---------- 3. LINKS / ACTIONS ----------
show('3. LINKS / ACTIONS — every {% url %} and <a href>')
for f in files:
    t = rd(f)
    urls  = re.findall(r'{%\s*url\s+[\'"]?([\w:.\-]+)[\'"]?', t)
    hrefs = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', t, re.I)
    if not (urls or hrefs):
        continue
    print('\n' + str(f.relative_to(TPL)))
    for u in sorted(set(urls)):
        print('  url: ' + u)
    for href, txt in hrefs:
        if href.startswith('{%'): continue
        print('  href: %-45s -> "%s"' % (href, txt.strip()[:50]))

# ---------- 4. CSRF & PERMISSION GATES ----------
show('4. CSRF & PERMISSION GATES')
for f in files:
    t = rd(f)
    has_csrf = '{% csrf_token %}' in t
    has_user = bool(re.search(r'{%\s*if\s+user\.', t))
    has_perm = bool(re.search(r'{%\s*if\s+perms?\.', t))
    has_role = bool(re.search(r'is_staff|is_superuser|is_teacher|is_student|role', t, re.I))
    loops    = len(re.findall(r'{%\s*for\s+', t))
    if not (has_user or has_perm or has_role or loops):
        continue
    flags = []
    if has_csrf: flags.append('csrf')
    if has_user: flags.append('user.*')
    if has_perm: flags.append('perms.*')
    if has_role: flags.append('role-check')
    if loops:    flags.append('%d for-loop(s)' % loops)
    print('  %-55s %s' % (str(f.relative_to(TPL)), ', '.join(flags)))

# ---------- 5. TABLES & DATA ----------
show('5. TABLES & DATA — what each template renders')
for f in files:
    t = rd(f)
    tables = re.findall(r'<table[^>]*>', t, re.I)
    th     = re.findall(r'<th[^>]*>([^<]*)</th>', t, re.I)
    if tables:
        print('\n' + str(f.relative_to(TPL)))
        print('  tables: %d' % len(tables))
        if th:
            print('  columns: ' + ', '.join(h.strip()[:30] for h in th if h.strip()))

# ---------- 6. MODALS ----------
show('6. MODALS / PARTIALS')
for f in files:
    t = rd(f)
    modals = re.findall(r'(?:class|id)=["\'][^"\']*modal[^"\']*["\']', t, re.I)
    if modals:
        print('  %-55s %d modal marker(s)' % (str(f.relative_to(TPL)), len(modals)))

# ---------- 7. BASE TEMPLATE ----------
show('7. KEY BASE TEMPLATE (templates/base.html)')
base = TPL / 'base.html'
if base.exists():
    t = rd(base)
    blocks   = re.findall(r'{%\s*block\s+(\w+)', t)
    includes = re.findall(r'{%\s*include\s+[\'"]([^\'"]+)', t)
    hrefs    = re.findall(r'href=["\']([^"\']+)', t)
    print('length: %d lines' % (t.count('\n') + 1))
    print('blocks: ' + ', '.join(blocks))
    print('includes: ' + (', '.join(includes) or '(none)'))
    print('first hrefs: ' + ', '.join(hrefs[:10]))

# ---------- 8. MISSING / SUSPICIOUS ----------
show('8. MISSING / SUSPICIOUS')
extended_names = set()
for f in files:
    m = re.search(r'{%\s*extends\s+[\'"]([^\'"]+)', rd(f))
    if m: extended_names.add(m.group(1))

for f in files:
    t = rd(f)
    rel = str(f.relative_to(TPL)).replace('\\', '/')
    if re.search(r'<form[^>]*method=["\']post', t, re.I) and '{% csrf_token %}' not in t:
        print('  ⚠ POST form without CSRF: ' + rel)
    if '{% extends' not in t and f.name != 'base.html' and rel not in extended_names:
        print('  ℹ standalone template (no extends): ' + rel)

print('\nDone.')
