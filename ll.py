"""
DIAGNOSTIC ONLY - READ-ONLY
Traces the source of Total=29.0 / Average=5.8% on the Elisha Bwire report.
No code or DB records are modified.
"""

import os, sys, json, sqlite3, traceback

# ------------------------------------------------------------------
# 0. CONFIG - adjust to your project layout
# ------------------------------------------------------------------
DB_CANDIDATES = [
    "edugrade.db", "school.db", "database.db",
    os.path.join("instance", "edugrade.db"),
    os.path.join("instance", "school.db"),
]
ADM_NO   = "9486"
EXAM     = "Mid term exams"
FORM     = "From 1"
STREAM   = "Mulumba"
REPORT_DATE = "2026-11-22"

SUBJECTS_EXPECTED = ["Mathematics","English","Kiswahili","Computer",
                     "Chemestry","Geography","Biology"]

def hr(t): print("\n" + "="*78 + f"\n{t}\n" + "="*78)

# ------------------------------------------------------------------
# 1. Locate DB
# ------------------------------------------------------------------
hr("1. LOCATING DATABASE")
db_path = next((p for p in DB_CANDIDATES if os.path.exists(p)), None)
if not db_path:
    print("!! No DB found in candidates:", DB_CANDIDATES); sys.exit(1)
print("DB:", os.path.abspath(db_path))

con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

def tables():
    return [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")]

def cols(t):
    return [r[1] for r in cur.execute(f"PRAGMA table_info('{t}')")]

hr("2. TABLES IN DB")
for t in tables(): print(" -", t, "| cols:", cols(t))

# ------------------------------------------------------------------
# 3. Find student row
# ------------------------------------------------------------------
hr("3. STUDENT ROW")
student_tbl = next((t for t in tables() if any(
    c.lower() in ("admission_no","adm_no","admissionno")
    for c in cols(t))), None)
print("student table:", student_tbl)
if student_tbl:
    adm_col = next(c for c in cols(student_tbl)
                   if c.lower() in ("admission_no","adm_no","admissionno"))
    for r in cur.execute(f"SELECT * FROM {student_tbl} WHERE {adm_col}=?", (ADM_NO,)):
        print(dict(r))

# ------------------------------------------------------------------
# 4. Dump ALL saved marks for this admission number + exam
# ------------------------------------------------------------------
hr("4. SAVED MARKS (raw)")
mark_tbls = [t for t in tables() if "mark" in t.lower() or "result" in t.lower() or "score" in t.lower()]
print("mark/result tables:", mark_tbls)

all_marks = []
for t in mark_tbls:
    c = cols(t)
    adm_col = next((x for x in c if "adm" in x.lower()), None)
    sub_col = next((x for x in c if "subject" in x.lower()), None)
    score_col = next((x for x in c if any(k in x.lower() for k in ("score","mark","percent"))), None)
    exam_col  = next((x for x in c if "exam" in x.lower()), None)
    if not (adm_col and score_col):
        print(f"  [skip {t}] missing adm/score cols -> {c}"); continue
    q = f"SELECT * FROM {t} WHERE {adm_col}=?"
    args = [ADM_NO]
    if exam_col:
        q += f" AND {exam_col}=?"; args.append(EXAM)
    print(f"\n--- {t} ---")
    for r in cur.execute(q, args):
        d = dict(r); all_marks.append((t, d))
        print(" ", d)

# ------------------------------------------------------------------
# 5. Reproduce totals under different hypotheses
# ------------------------------------------------------------------
hr("5. HYPOTHESIS TESTS ON OVERALL CALCULATION")
scores = [40,45,45,40,50,30,50]
print("Expected subject scores:", scores, "sum=", sum(scores), "avg=", sum(scores)/len(scores))

# H1: are we summing the *grades/points* column instead of percentages?
#     Points from report: 5,6,6,5,6,3,6  -> sum = 37, not 29
points = [5,6,6,5,6,3,6]
print("H1  Sum of POINTS (5,6,6,5,6,3,6):", sum(points), "avg:", sum(points)/len(points))
print("    29 = sum of points only if we drop 2 subjects ->",
      "e.g. 5+6+6+5+6+3-? nope")
print("    29 fits 6+6+6+5+3+... combinations:",
      [s for s in [sum(points[:i]+points[i+1:]) for i in range(7)] if s==29])

# H2: constant divisor 5  -> 29/5 = 5.8 exactly as reported
print("H2  29 / 5 =", 29/5, "<-- matches reported 5.8% exactly")

# H3: what 7-subject combos of points sum to 29?
import itertools
fits = []
for r in range(1, 8):
    for combo in itertools.combinations(range(7), r):
        s = sum(points[i] for i in combo)
        if s == 29:
            fits.append((combo, [SUBJECTS_EXPECTED[i] for i in combo]))
print("H3  point-subset sums == 29:")
for combo, subs in fits:
    print("   indices", combo, "->", subs, f"(n={len(combo)})")

# H4: what if total is sum of percentages but divided by 10? 300/10=30 (close to 29)
print("H4  sum(percent)/10 =", sum(scores)/10)
print("H4b sum(percent) with one subject dropped /10:",
      [(i, (sum(scores)-scores[i])/10) for i in range(7)])

# ------------------------------------------------------------------
# 6. Grading scheme check
# ------------------------------------------------------------------
hr("6. GRADING SCHEME")
for t in tables():
    if "grade" in t.lower() or "grading" in t.lower() or "scale" in t.lower():
        print(f"--- {t} ---")
        for r in cur.execute(f"SELECT * FROM {t}"):
            print(" ", dict(r))

# ------------------------------------------------------------------
# 7. Class position logic source
# ------------------------------------------------------------------
hr("7. CLASS POSITION - class marks around this student")
if "class" in (student_tbl or "").lower() or True:
    # try to find class/stream column
    if student_tbl:
        class_col = next((c for c in cols(student_tbl)
                          if any(k in c.lower() for k in ("class","form","stream"))), None)
        if class_col:
            q = (f"SELECT * FROM {student_tbl} WHERE {class_col} LIKE ?")
            for r in cur.execute(q, ("%Mulumba%",)):
                print(" ", dict(r))

con.close()
hr("DIAGNOSTIC COMPLETE - no changes written")