#!/bin/bash
set -e
cd /home/elisha/-EduGrade

echo "======================================================================"
echo "PHASE 2 INSPECTION — what's in Grade 5 Math now, what's needed"
echo "======================================================================"

echo ""
echo "[1/4] Current Grade 5 Mathematics content in DB"
python manage.py shell <<'PY'
from school.models import (
    Curriculum, CurriculumVersion, GradeLevel,
    LearningArea, Strand, SubStrand, LearningOutcome,
    LearningExperience, InquiryQuestion,
)

cbc = Curriculum.objects.filter(code='CBC').first()
version = CurriculumVersion.objects.filter(curriculum=cbc, is_current=True).first()
g5 = GradeLevel.objects.get(curriculum=cbc, name='Grade 5')

print(f'CBC version: {version.version_code}')
print(f'Grade 5: id={g5.id}')
print()

las = LearningArea.objects.filter(curriculum_version=version, grade_level=g5)
print(f'LearningAreas in Grade 5: {las.count()}')
for la in las:
    print(f'  [{la.code}] {la.name} (is_core={la.is_core})')
    strands = Strand.objects.filter(learning_area=la)
    print(f'    Strands: {strands.count()}')
    for s in strands:
        sss = SubStrand.objects.filter(strand=s)
        lo_total = LearningOutcome.objects.filter(sub_strand__strand=s).count()
        print(f'      Strand "{s.name}" → {sss.count()} SubStrands, {lo_total} LOs')
        for ss in sss:
            los = LearningOutcome.objects.filter(sub_strand=ss)
            print(f'        SubStrand "{ss.name}" → {los.count()} LOs')
            for lo in los:
                k = (lo.knowledge or '')[:30]
                sk = (lo.skills or '')[:30]
                at = (lo.attitudes or '')[:30]
                vt = (lo.values_text or '')[:30]
                has_detail = '✓' if any([lo.knowledge, lo.skills, lo.attitudes, lo.values_text]) else '✗'
                print(f'          - "{lo.outcome_text[:60]}"')
                print(f'              [detail: {has_detail}] K="{k}" S="{sk}" A="{at}" V="{vt}"')

print()
print(f'Experiences: {LearningExperience.objects.filter(learning_outcome__sub_strand__strand__learning_area__in=las).count()}')
print(f'InquiryQ:    {InquiryQuestion.objects.filter(learning_outcome__sub_strand__strand__learning_area__in=las).count()}')
PY

echo ""
echo "[2/4] Official KICD Grade 5 Mathematics reference (curriculum design)"
echo "---"
echo "KICD Grade 5 Mathematics curriculum design content (per KICD website):"
echo "  Learning Area: Mathematics"
echo "  Grade: 5"
echo "  Strands:"
echo "    1. Numbers        (SubStrands: Whole Numbers, Fractions, Decimals, Squares and Square Roots)"
echo "    2. Measurement    (SubStrands: Length, Mass, Area, Volume and Capacity, Time, Money)"
echo "    3. Geometry       (SubStrands: Lines, Angles, Shapes)"
echo "    4. Data Handling  (SubStrands: Data Representation, Interpretation)"
echo "  Total: ~4 Strands, ~15 SubStrands, ~50-70 Learning Outcomes (varies by design version)"
echo "---"
echo "Source: KICD curriculum designs portal"
echo "        https://kicd.ac.ke/cbc-materials/curriculum-designs/"
echo "        Note: exact LO count and wording must come from the official PDF."
echo "        The importer will accept whatever CSV we supply."

echo ""
echo "[3/4] Sample CSV present in repo"
if [ -f samples/maths_grade5_sample.csv ]; then
    echo "  File: samples/maths_grade5_sample.csv"
    echo "  Rows: $(( $(wc -l < samples/maths_grade5_sample.csv) - 1 )) data rows"
    echo "  Content preview:"
    head -3 samples/maths_grade5_sample.csv | sed 's/^/    /'
    echo ""
    echo "  All outcome texts currently loaded:"
    tail -n +2 samples/maths_grade5_sample.csv | cut -d',' -f7 | sed 's/^/    - /'
else
    echo "  NOT FOUND"
fi

echo ""
echo "[4/4] Backup DB before any import"
mkdir -p .fix_backup/phase2
cp edugrade_db.sqlite3 .fix_backup/phase2/edugrade_db_before_phase2.sqlite3
echo "  DB backed up to .fix_backup/phase2/"
ls -la .fix_backup/phase2/

echo ""
echo "======================================================================"
echo "PHASE 2 INSPECTION COMPLETE"
echo "======================================================================"
echo ""
echo "Decision points:"
echo "  A) Current Grade 5 has 4 LOs from sample — replace with real KICD data?"
echo "  B) Or extend the existing 4 LOs with more from KICD designs?"
echo ""
echo "Next step: I'll source the official KICD Grade 5 Math outcomes"
echo "           and write a CSV with source attribution."
echo "           Or you can paste the KICD Grade 5 Math LO list here."
echo "======================================================================"
