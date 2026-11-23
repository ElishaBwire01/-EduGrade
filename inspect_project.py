import re, pathlib
R = pathlib.Path('.').resolve()

def show(t): print('\n' + '='*60 + '\n' + t + '\n' + '='*60)
def rd(p, n=None):
    try: return p.read_text(errors='replace')[:n] if n else p.read_text(errors='replace')
    except: return ''

show('README'); print(rd(R/'README.md', 1500) or '(none)')
show('REQUIREMENTS'); print(rd(R/'requirements.txt') or '(none)')

show('SETTINGS')
s = R/'edugrade'/'settings.py'
if s.exists():
    t = rd(s)
    for k in ['INSTALLED_APPS', 'DATABASES', 'AUTH_USER_MODEL', 'ROOT_URLCONF']:
        m = re.search(k + r'\s*=\s*(\[[^\]]*\]|\{.*?\}|[\'\"]\S+[\'\"])', t, re.S)
        if m: print('\n--', k, '--\n', m.group(1)[:600])

show('URL ROUTES')
for u in R.rglob('urls.py'):
    print('\n#', u.relative_to(R))
    for m in re.finditer(r'path\(\s*[\'\"]([^\'\"]*)[\'\"]\s*,\s*([^,)]+)', rd(u)):
        print('  ', (m.group(1) or '/')[:35].ljust(35), '->', m.group(2).strip()[:50])

show('MODELS')
for mf in R.rglob('models.py'):
    t = rd(mf)
    cls = re.findall(r'class\s+(\w+)\s*\(([^)]*)\)', t)
    if not cls: continue
    print('\n#', mf.relative_to(R))
    for name, bases in cls:
        print('  class', name, '(', bases.strip(), ')')
        body = re.search(r'class\s+' + name + r'\b.*?(?=\nclass\s|\Z)', t, re.S)
        if body:
            for f in re.finditer(r'^\s{4}(\w+)\s*=\s*models\.(\w+)\(([^)]*)\)', body.group(0), re.M):
                print('     -', f.group(1) + ':', 'models.' + f.group(2), '(', f.group(3)[:50], ')')

show('VIEWS')
for vf in R.rglob('views.py'):
    t = rd(vf)
    fns = re.findall(r'^def\s+(\w+)\s*\(', t, re.M)
    cls = re.findall(r'^class\s+(\w+)\s*\(([^)]*)\)', t, re.M)
    if fns or cls:
        print('\n#', vf.relative_to(R))
        for f in fns: print('  def', f)
        for n, b in cls: print('  class', n, '(', b, ')')

show('TEMPLATES')
tp = list((R/'templates').rglob('*.html')) if (R/'templates').exists() else []
print(len(tp), 'templates')
for p in tp[:30]: print(' ', p.relative_to(R))
print('\nDone.')
