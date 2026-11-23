import urllib.request, urllib.error, pathlib
BASE = 'http://127.0.0.1:8000'
URLS = [
    '/auth/login/', '/auth/register/',
    '/', '/dashboard/', '/notifications/',
    '/students/', '/teachers/', '/examinations/', '/marks/entry/',
    '/reports/', '/school/', '/school/setup/',
    '/grading/process/', '/grading/systems/',
]
for u in URLS:
    try:
        r = urllib.request.urlopen(BASE + u, timeout=5)
        print(f'  200  {u}  ({len(r.read())} bytes)')
    except urllib.error.HTTPError as e:
        print(f'  {e.code}  {u}')
    except Exception as e:
        print(f'  ERR  {u}  {e}')
