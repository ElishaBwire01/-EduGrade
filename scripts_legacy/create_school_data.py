import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')
import django
django.setup()
from school.models import Curriculum, GradeLevel, Subject

# Create Curriculums
curriculums_data = [
    {'code': '844', 'name': '8-4-4', 'description': 'Traditional 8-4-4 curriculum for forms 1-4'},
    {'code': 'CBC', 'name': 'CBC', 'description': 'Competency Based Curriculum for grades 1-12'},
]

for data in curriculums_data:
    curriculum, created = Curriculum.objects.get_or_create(
        code=data['code'],
        defaults={'name': data['name'], 'description': data['description']}
    )
    if created:
        print(f"✅ Created curriculum: {curriculum.name}")

# Create Grade Levels for 8-4-4
curriculum_844 = Curriculum.objects.get(code='844')
grade_levels_data = [
    {'level_type': 'FORM', 'level_number': 1, 'name': 'Form 1', 'order': 1},
    {'level_type': 'FORM', 'level_number': 2, 'name': 'Form 2', 'order': 2},
    {'level_type': 'FORM', 'level_number': 3, 'name': 'Form 3', 'order': 3},
    {'level_type': 'FORM', 'level_number': 4, 'name': 'Form 4', 'order': 4},
]

for data in grade_levels_data:
    grade, created = GradeLevel.objects.get_or_create(
        curriculum=curriculum_844,
        level_type=data['level_type'],
        level_number=data['level_number'],
        defaults={'name': data['name'], 'order': data['order']}
    )
    if created:
        print(f"✅ Created grade level: {grade.name}")

# Create Grade Levels for CBC
curriculum_cbc = Curriculum.objects.get(code='CBC')
cbc_grades = []
for i in range(7, 13):
    cbc_grades.append({
        'level_type': 'GRADE',
        'level_number': i,
        'name': f'Grade {i}',
        'order': i
    })

for data in cbc_grades:
    grade, created = GradeLevel.objects.get_or_create(
        curriculum=curriculum_cbc,
        level_type=data['level_type'],
        level_number=data['level_number'],
        defaults={'name': data['name'], 'order': data['order']}
    )
    if created:
        print(f"✅ Created grade level: {grade.name}")

# Create Subjects for 8-4-4
subjects_844 = [
    {'code': 'MATH', 'name': 'Mathematics', 'short_name': 'Math'},
    {'code': 'ENG', 'name': 'English', 'short_name': 'Eng'},
    {'code': 'KISW', 'name': 'Kiswahili', 'short_name': 'Kisw'},
    {'code': 'BIO', 'name': 'Biology', 'short_name': 'Bio'},
    {'code': 'CHEM', 'name': 'Chemistry', 'short_name': 'Chem'},
    {'code': 'PHY', 'name': 'Physics', 'short_name': 'Phy'},
    {'code': 'HIST', 'name': 'History', 'short_name': 'Hist'},
    {'code': 'GEO', 'name': 'Geography', 'short_name': 'Geo'},
    {'code': 'CRE', 'name': 'CRE', 'short_name': 'CRE'},
    {'code': 'BUS', 'name': 'Business Studies', 'short_name': 'Bus'},
]

for data in subjects_844:
    subject, created = Subject.objects.get_or_create(
        curriculum=curriculum_844,
        code=data['code'],
        defaults={
            'name': data['name'],
            'short_name': data['short_name'],
            'subject_type': 'CORE'
        }
    )
    if created:
        print(f"✅ Created subject: {subject.name}")

# Create Subjects for CBC
subjects_cbc = [
    {'code': 'CBC_MATH', 'name': 'Mathematics', 'short_name': 'Math'},
    {'code': 'CBC_ENG', 'name': 'English', 'short_name': 'Eng'},
    {'code': 'CBC_KISW', 'name': 'Kiswahili', 'short_name': 'Kisw'},
    {'code': 'CBC_SCI', 'name': 'Science', 'short_name': 'Sci'},
    {'code': 'CBC_SST', 'name': 'Social Studies', 'short_name': 'SST'},
    {'code': 'CBC_CRE', 'name': 'CRE', 'short_name': 'CRE'},
    {'code': 'CBC_ART', 'name': 'Art & Design', 'short_name': 'Art'},
    {'code': 'CBC_MUSIC', 'name': 'Music', 'short_name': 'Music'},
    {'code': 'CBC_PE', 'name': 'Physical Education', 'short_name': 'PE'},
]

for data in subjects_cbc:
    subject, created = Subject.objects.get_or_create(
        curriculum=curriculum_cbc,
        code=data['code'],
        defaults={
            'name': data['name'],
            'short_name': data['short_name'],
            'subject_type': 'CORE'
        }
    )
    if created:
        print(f"✅ Created subject: {subject.name}")

print("\n✅ Initial school data setup complete!")
