import re, pathlib, json
R = pathlib.Path('.').resolve()
APPS = ['core','school','students','teachers','authentication','examinations','marks','grading','reports']

def show(t): print('\n' + '='*70 + '\n' + t + '\n' + '='*70)
def rd(p, n=None):
    try: return p.read_text(errors='replace')[:n] if n else p.read_text(errors='replace')
    except: return ''

# 1. Locate every project .py file (skip venv)
proj_files = [p for p in R.rglob('*.py') if 'venv' not in p.parts and '.git' not in p.parts and 'site-packages' not in str(p)]
print('Project .py files:', len(proj_files))
for p in sorted(proj_files): print('  ', p.relative_to(R))

# 2. All URL includes — find where setup_views is wired
show('URL INCLUDES (top-level edugrade/urls.py)')
u = R/'edugrade'/'urls.py'
if u.exists(): print(rd(u))

# 3. setup_views location
show('setup_views.py LOCATION')
for p in proj_files:
    if p.name == 'setup_views.py':
        print('FOUND:', p.relative_to(R))
        head = rd(p, 1500)
        print(head)

# 4. Model choices — extract Choice tuples
show('MODEL CHOICES / CONSTANTS')
for app in APPS:
    mf = R/app/'models.py'
    if not mf.exists(): continue
    t = rd(mf)
    consts = re.findall(r'^([A-Z_]+)\s*=\s*(\[[^\]]*\]|\{[^}]*\})', t, re.M)
    if consts:
        print(f'\n# {app}/models.py')
        for name, val in consts:
            print(f'  {name} = {val[:300]}')

# 5. Decorators on views — reveals permission model
show('VIEW DECORATORS')
for app in APPS:
    vf = R/app/'views.py'
    if not vf.exists(): continue
    t = rd(vf)
    rows = re.findall(r'^(@[\w\.]+(?:\([^)]*\))?\s*\n)+def\s+(\w+)', t, re.M)
    # simpler: look for decorator lines above defs
    lines = t.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith('@') and i+1 < len(lines) and (lines[i+1].startswith('def ') or lines[i+1].startswith('class ')):
            print(f'  {app}: {ln.strip()}  ->  {lines[i+1].strip()[:60]}')

# 6. Middleware & custom auth
show('MIDDLEWARE / AUTH_BACKENDS / INSTALLED_APPS')
s = R/'edugrade'/'settings.py'
if s.exists():
    t = rd(s)
    for k in ['INSTALLED_APPS','MIDDLEWARE','AUTHENTICATION_BACKENDS','AUTH_USER_MODEL','LOGIN_URL','LOGIN_REDIRECT_URL','LOGOUT_REDIRECT_URL','DATABASES','TEMPLATES','STATIC_URL','MEDIA_URL']:
        m = re.search(k + r'\s*=\s*(\[[^\]]*\]|\{[^}]*\}|[\'\"]\S*[\'\"])', t, re.S)
        if m: print(f'\n-- {k} --\n{m.group(1)[:800]}')

# 7. Admin registrations
show('ADMIN REGISTRATIONS')
for app in APPS:
    af = R/app/'admin.py'
    if af.exists():
        t = rd(af)
        regs = re.findall(r'admin\.site\.register\(\s*(\w+)', t)
        print(f'  {app}: {regs}')

# 8. Migrations summary
show('MIGRATIONS')
for app in APPS:
    md = R/app/'migrations'
    if md.exists():
        migs = sorted([p.name for p in md.glob('*.py') if p.name != '__init__.py'])
        print(f'  {app}: {len(migs)} migrations, latest = {migs[-1] if migs else "none"}')

# 9. Full template list (all 54)
show('ALL TEMPLATES')
tp = sorted((R/'templates').rglob('*.html')) if (R/'templates').exists() else []
for p in tp: print('  ', p.relative_to(R))

# 10. Root scripts purpose — first docstring / first comment
show('ROOT SCRIPT PURPOSES')
for p in sorted(R.glob('*.py')):
    t = rd(p, 400)
    doc = re.search(r'^\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', t, re.S)
    first_comment = next((ln for ln in t.splitlines() if ln.strip().startswith('#')), '')
    print(f'\n{p.name}:')
    print('   ', (doc.group(1).strip().splitlines()[0] if doc else first_comment.strip() or '(no docstring)')[:100])

# 11. requirements.txt
show('REQUIREMENTS')
print(rd(R/'requirements.txt'))

# 12. App config names & verbose_name
show('APP CONFIGS')
for app in APPS:
    ac = R/app/'apps.py'
    if ac.exists():
        t = rd(ac)
        m = re.search(r'name\s*=\s*[\'\"]([^\'\"]+)', t)
        v = re.search(r'verbose_name\s*=\s*[\'\"]([^\'\"]+)', t)
        print(f'  {app}: name={m.group(1) if m else "?"}, verbose={v.group(1) if v else "(default)"}')

print('\nDone.')
