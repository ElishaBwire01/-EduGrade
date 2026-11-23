import re, pathlib, textwrap
R = pathlib.Path('.').resolve()
def show(t): print('\n' + '='*72 + '\n' + t + '\n' + '='*72)
def rd(p, n=None):
    try:
        t = p.read_text(errors='replace'); return t[:n] if n else t
    except: return ''

# 1. Home + dashboard templates — what links do they actually render?
show('1. templates/core/home.html')
print(rd(R/'templates'/'core'/'home.html', 3000))

show('2. templates/core/dashboard.html')
print(rd(R/'templates'/'core'/'dashboard.html', 6000))

# 3. base.html — old navigation (before my rewrite was based on)
show('3. templates/base.html — current nav section')
b = rd(R/'templates'/'base.html')
for m in re.finditer(r'(<!-- SIDEBAR -->.*?</aside>)', b, re.S):
    print(m.group(0)[:3000])

# 4. core/views.py — dashboard + HomeView logic (role gating)
show('4. core/views.py — HomeView & dashboard')
t = rd(R/'core'/'views.py')
for name in ('dashboard', 'build_cbc_analysis', 'HomeView'):
    m = re.search(rf'(?:^|\n)(?:class\s+{name}\b.*?(?=\nclass |\ndef |\Z)|def\s+{name}\b.*?(?=\ndef |\nclass |\Z))', t, re.S)
    if m:
        print('\n--- ' + name + ' ---')
        print(textwrap.dedent(m.group(0))[:2500])

# 5. core/access.py — is_admin + role helper
show('5. core/access.py — permission helpers')
print(rd(R/'core'/'access.py', 4000))

# 6. core/models.py — Role.ROLE_CHOICES
show('6. core/models.py — Role choices')
t = rd(R/'core'/'models.py')
m = re.search(r'class Role\b.*?(?=\nclass |\Z)', t, re.S)
print(m.group(0)[:1500] if m else '(not found)')
# also ROLE_CHOICES constant
for ln in t.splitlines():
    if 'ROLE_CHOICES' in ln:
        print('  ' + ln.strip()[:120])

# 7. All templates — links to every view name
show('7. Every template + its {% url %} names')
for f in sorted((R/'templates').rglob('*.html')):
    t = rd(f)
    urls = re.findall(r"{%\s*url\s+[\'\"]([\w:.\-]+)[\'\"]", t)
    if urls:
        print(f'\n{f.relative_to(R/"templates")}')
        for u in sorted(set(urls)):
            print('   ' + u)

# 8. What does dashboard link to and who can see it?
show('8. dashboard.html — conditional blocks {% if user ... %}')
t = rd(R/'templates'/'core'/'dashboard.html')
for m in re.finditer(r'{%\s*if\s+[^%]+%}.*?{%\s*endif\s*%}', t, re.S):
    block = m.group(0)
    # extract first line + any url inside
    first = block.splitlines()[0].strip()
    inner_urls = re.findall(r"{%\s*url\s+['\"]([\w:.\-]+)['\"]", block)
    if inner_urls:
        print(f'  {first}  ->  {", ".join(inner_urls)}')

# 9. Is there a menu/permissions.html partial?
show('9. Any template with role-based menus?')
for f in sorted((R/'templates').rglob('*.html')):
    t = rd(f)
    if 'role' in t.lower() or 'is_staff' in t or 'is_superuser' in t:
        has_url = bool(re.search(r"{%\s*url", t))
        print(f'  {f.relative_to(R/"templates"):55} roles={"yes" if "role" in t.lower() else "no":4} urls={"yes" if has_url else "no"}')

# 10. Router: which view functions are role-gated?
show('10. Views with role/permission decorators')
for vf in R.rglob('views.py'):
    if 'venv' in vf.parts or 'site-packages' in str(vf): continue
    t = rd(vf)
    lines = t.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().startswith('@') and i+1 < len(lines) and lines[i+1].strip().startswith('def '):
            deco = ln.strip()
            if any(k in deco for k in ('user_passes_test','permission_required','is_admin','is_staff','is_superuser')):
                print(f'  {vf.relative_to(R)}: {deco}  ->  {lines[i+1].strip()[:80]}')

print('\nDone.')
