import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')
import django
django.setup()

from django.contrib.auth.models import User
from datetime import date, timedelta
import random
from decimal import Decimal

# Import all models
from school.models import AcademicYear, Term, Curriculum, GradeLevel, Stream, Subject
from students.models import Student, StudentHistory
from teachers.models import TeacherProfile, TeacherAssignment, TeacherRequest, ClassTeacher
from examinations.models import Examination, ExaminationClass, SubjectScoreConfig
from marks.models import MarkEntry, MarkSubmission

print("=" * 70)
print("  EDUGRADE - COMPLETE TEST DATA GENERATION")
print("  INCLUDING FULL CBC SUPPORT")
print("=" * 70)

# ============================================
# 0. CHECK AND CREATE BASE DATA
# ============================================
print("\n📚 Setting up base data...")

# Get or create Academic Year
year_2026, _ = AcademicYear.objects.get_or_create(
    year=2026,
    defaults={
        'name': 'Academic Year 2026',
        'start_date': date(2026, 1, 15),
        'end_date': date(2026, 12, 15),
        'is_current': True
    }
)

# Get or create Terms
terms = []
terms_data = [
    {'number': 1, 'name': 'Term 1', 'start': date(2026, 1, 15), 'end': date(2026, 3, 31)},
    {'number': 2, 'name': 'Term 2', 'start': date(2026, 4, 15), 'end': date(2026, 7, 31)},
    {'number': 3, 'name': 'Term 3', 'start': date(2026, 8, 15), 'end': date(2026, 11, 30)},
]

for term_data in terms_data:
    term, created = Term.objects.get_or_create(
        academic_year=year_2026,
        term_number=term_data['number'],
        defaults={
            'name': term_data['name'],
            'start_date': term_data['start'],
            'end_date': term_data['end'],
            'is_active': term_data['number'] == 1
        }
    )
    terms.append(term)

# ============================================
# 1. GET CURRICULUMS AND SUBJECTS
# ============================================
print("\n📚 Getting Curriculums and Subjects...")

curriculum_844 = Curriculum.objects.get(code='844')
curriculum_cbc = Curriculum.objects.get(code='CBC')

subjects_844 = list(Subject.objects.filter(curriculum=curriculum_844, is_active=True))
subjects_cbc = list(Subject.objects.filter(curriculum=curriculum_cbc, is_active=True))

print(f"  ✅ Found {len(subjects_844)} subjects for 8-4-4")
print(f"  ✅ Found {len(subjects_cbc)} subjects for CBC")

# ============================================
# 2. CREATE GRADE LEVELS AND STREAMS
# ============================================
print("\n📚 Creating Grade Levels and Streams...")

# 8-4-4 Grade Levels
grade_levels_844 = {}
for i in range(1, 5):
    grade, _ = GradeLevel.objects.get_or_create(
        curriculum=curriculum_844,
        level_type='FORM',
        level_number=i,
        defaults={
            'name': f'Form {i}',
            'order': i,
            'is_active': True
        }
    )
    grade_levels_844[f'Form_{i}'] = grade

# CBC Grade Levels
grade_levels_cbc = {}
for i in range(7, 10):
    grade, _ = GradeLevel.objects.get_or_create(
        curriculum=curriculum_cbc,
        level_type='GRADE',
        level_number=i,
        defaults={
            'name': f'Grade {i}',
            'order': i,
            'is_active': True
        }
    )
    grade_levels_cbc[f'Grade_{i}'] = grade

print(f"  ✅ Created {len(grade_levels_844)} 8-4-4 grade levels")
print(f"  ✅ Created {len(grade_levels_cbc)} CBC grade levels")

# Create streams
stream_names = ['East', 'West', 'North', 'South']

# 8-4-4 Streams
streams_844 = {}
for form_name, grade in grade_levels_844.items():
    for stream_name in stream_names:
        code = f"{grade.level_number}{stream_name[0]}"
        stream, created = Stream.objects.get_or_create(
            grade_level=grade,
            name=stream_name,
            defaults={
                'code': code,
                'capacity': 40,
                'is_active': True
            }
        )
        streams_844[f"{form_name}_{stream_name}"] = stream

# CBC Streams
streams_cbc = {}
for grade_name, grade in grade_levels_cbc.items():
    for stream_name in stream_names:
        code = f"{grade.level_number}{stream_name[0]}"
        stream, created = Stream.objects.get_or_create(
            grade_level=grade,
            name=stream_name,
            defaults={
                'code': code,
                'capacity': 35,
                'is_active': True
            }
        )
        streams_cbc[f"{grade_name}_{stream_name}"] = stream

print(f"  ✅ Created {len(streams_844)} 8-4-4 streams")
print(f"  ✅ Created {len(streams_cbc)} CBC streams")

# ============================================
# 3. CREATE TEACHERS
# ============================================
print("\n👨‍🏫 Creating Teachers...")

# 8-4-4 Teachers
teacher_names_844 = [
    ('John', 'Kamau'), ('Mary', 'Wanjiru'), ('Peter', 'Ochieng'),
    ('Grace', 'Akinyi'), ('James', 'Mwangi'), ('Sarah', 'Njeri'),
    ('David', 'Mutua'), ('Esther', 'Wambui'), ('Samuel', 'Kiprop'),
    ('Ruth', 'Chebet'), ('Michael', 'Omondi'), ('Faith', 'Mwende'),
    ('Daniel', 'Kariuki'), ('Rose', 'Achieng'), ('Simon', 'Ngugi'),
]

teachers_844 = []

for first_name, last_name in teacher_names_844:
    staff_number = f"TCH{2026:04d}{random.randint(1, 999):03d}"
    username = staff_number.lower()
    
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'email': f"{first_name.lower()}.{last_name.lower()}@school.com",
            'is_staff': False,
            'is_active': True
        }
    )
    user.set_password('password123')
    user.save()
    
    teacher, created = TeacherProfile.objects.get_or_create(
        staff_number=staff_number,
        defaults={
            'user': user,
            'first_name': first_name,
            'last_name': last_name,
            'gender': random.choice(['M', 'F']),
            'date_of_birth': date(1980, random.randint(1, 12), random.randint(1, 28)),
            'phone_number': f"07{random.randint(10000000, 99999999)}",
            'email': f"{first_name.lower()}.{last_name.lower()}@school.com",
            'address': f"Teacher's House, Nairobi, Kenya",
            'employment_date': date(2020, random.randint(1, 12), random.randint(1, 28)),
            'qualification': random.choice(['B.Ed (Science)', 'B.Ed (Arts)', 'M.Ed']),
            'specialization': random.choice(['Mathematics', 'Languages', 'Sciences']),
            'status': 'ACTIVE',
            'is_active': True
        }
    )
    
    if created:
        teachers_844.append(teacher)

# CBC Teachers
teacher_names_cbc = [
    ('Catherine', 'Njeri'), ('Stephen', 'Ochieng'), ('Monica', 'Wanjiku'),
    ('Fred', 'Kiprop'), ('Lilian', 'Akinyi'), ('Sammy', 'Omondi'),
    ('Virginia', 'Wambui'), ('Charles', 'Mwangi')
]

teachers_cbc = []

for first_name, last_name in teacher_names_cbc:
    staff_number = f"CBC{2026:04d}{random.randint(1, 999):03d}"
    username = staff_number.lower()
    
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'email': f"{first_name.lower()}.{last_name.lower()}@cbc.school.com",
            'is_staff': False,
            'is_active': True
        }
    )
    user.set_password('cbcpassword123')
    user.save()
    
    teacher, created = TeacherProfile.objects.get_or_create(
        staff_number=staff_number,
        defaults={
            'user': user,
            'first_name': first_name,
            'last_name': last_name,
            'gender': random.choice(['M', 'F']),
            'date_of_birth': date(1985, random.randint(1, 12), random.randint(1, 28)),
            'phone_number': f"07{random.randint(10000000, 99999999)}",
            'email': f"{first_name.lower()}.{last_name.lower()}@cbc.school.com",
            'address': f"CBC Teacher, Nairobi, Kenya",
            'employment_date': date(2020, random.randint(1, 12), random.randint(1, 28)),
            'qualification': random.choice(['B.Ed (CBC)', 'M.Ed (Competency-Based)', 'PGDE (CBC)']),
            'specialization': random.choice(['CBC Pedagogy', 'Competency-Based Assessment']),
            'status': 'ACTIVE',
            'is_active': True
        }
    )
    
    if created:
        teachers_cbc.append(teacher)

print(f"  ✅ Created {len(teachers_844)} 8-4-4 teachers")
print(f"  ✅ Created {len(teachers_cbc)} CBC teachers")

# ============================================
# 4. CREATE 8-4-4 STUDENTS
# ============================================
print("\n👨‍🎓 Creating 8-4-4 Students...")

student_first_names = [
    'John', 'Mary', 'Peter', 'Grace', 'James', 'Sarah', 'David', 'Esther',
    'Samuel', 'Ruth', 'Michael', 'Faith', 'Daniel', 'Rose', 'Simon', 'Jane',
    'Paul', 'Susan', 'Mark', 'Ann', 'Joseph', 'Alice', 'Robert', 'Margaret',
    'Patrick', 'Catherine', 'Stephen', 'Lucy', 'Anthony', 'Dorothy'
]

student_last_names = [
    'Kamau', 'Wanjiru', 'Ochieng', 'Akinyi', 'Mwangi', 'Njeri',
    'Mutua', 'Wambui', 'Kiprop', 'Chebet', 'Omondi', 'Mwende',
    'Kariuki', 'Achieng', 'Ngugi', 'Wangari', 'Ndegwa', 'Atieno',
    'Odhiambo', 'Njoroge', 'Oduor', 'Nyokabi', 'Maina', 'Wangui'
]

students_844 = []

for form_name, grade in grade_levels_844.items():
    for stream_name, stream in streams_844.items():
        if form_name in stream_name:
            num_students = random.randint(30, 40)
            
            for i in range(num_students):
                first_name = random.choice(student_first_names)
                last_name = random.choice(student_last_names)
                
                number_part = f"{random.randint(1, 999):03d}"
                admission_number = f"{2026}/{number_part}"
                
                while Student.objects.filter(admission_number=admission_number).exists():
                    number_part = f"{random.randint(1, 999):03d}"
                    admission_number = f"{2026}/{number_part}"
                
                birth_year = random.randint(2005, 2012)
                gender = random.choice(['M', 'F'])
                
                student, created = Student.objects.get_or_create(
                    admission_number=admission_number,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'date_of_birth': date(birth_year, random.randint(1, 12), random.randint(1, 28)),
                        'gender': gender,
                        'nationality': 'Kenyan',
                        'admission_date': date(2025, random.randint(1, 12), random.randint(1, 28)),
                        'curriculum': curriculum_844,
                        'current_grade_level': grade,
                        'current_stream': stream,
                        'academic_year': year_2026,
                        'guardian_name': f"{random.choice(['Mr.', 'Mrs.', 'Dr.'])} {random.choice(student_last_names)}",
                        'guardian_phone': f"07{random.randint(10000000, 99999999)}",
                        'guardian_relationship': random.choice(['Father', 'Mother', 'Guardian']),
                        'status': 'ACTIVE',
                        'is_active': True
                    }
                )
                
                if created:
                    StudentHistory.objects.create(
                        student=student,
                        academic_year=year_2026,
                        grade_level=grade,
                        stream=stream,
                        is_current=True
                    )
                    students_844.append(student)
    
    print(f"  ✅ Created {len([s for s in students_844 if s.current_grade_level == grade])} students in {form_name}")

print(f"  ✅ Total 8-4-4 students created: {len(students_844)}")

# ============================================
# 5. CREATE CBC STUDENTS
# ============================================
print("\n👨‍🎓 Creating CBC Students...")

cbc_first_names = [
    'Amina', 'Brian', 'Cynthia', 'Daniel', 'Eunice', 'Felix', 'Grace', 'Henry',
    'Irene', 'James', 'Karen', 'Leon', 'Mary', 'Nathan', 'Olivia', 'Peter',
    'Rose', 'Samuel', 'Tracy', 'Vera', 'William', 'Yvonne', 'Zachary', 'Faith',
    'George', 'Helen', 'Isaac', 'Joy', 'Kevin', 'Linda', 'Moses', 'Nancy'
]

cbc_last_names = [
    'Adhiambo', 'Bwire', 'Chepkurui', 'Dida', 'Etyang', 'Furaha', 'Gikonyo',
    'Hassan', 'Ireri', 'Juma', 'Kiplagat', 'Lubanga', 'Makena', 'Ndungu',
    'Odhiambo', 'Pesa', 'Ruto', 'Sitati', 'Toroitich', 'Wanjala'
]

students_cbc = []

for grade_name, grade in grade_levels_cbc.items():
    for stream_name, stream in streams_cbc.items():
        if grade_name in stream_name:
            num_students = random.randint(25, 35)
            
            for i in range(num_students):
                first_name = random.choice(cbc_first_names)
                last_name = random.choice(cbc_last_names)
                
                number_part = f"{random.randint(1000, 9999):04d}"
                admission_number = f"CBC{2026}/{number_part}"
                
                while Student.objects.filter(admission_number=admission_number).exists():
                    number_part = f"{random.randint(1000, 9999):04d}"
                    admission_number = f"CBC{2026}/{number_part}"
                
                birth_year = 2014 - (grade.level_number - 7)
                gender = random.choice(['M', 'F'])
                
                student, created = Student.objects.get_or_create(
                    admission_number=admission_number,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'date_of_birth': date(birth_year, random.randint(1, 12), random.randint(1, 28)),
                        'gender': gender,
                        'nationality': 'Kenyan',
                        'admission_date': date(2026, random.randint(1, 6), random.randint(1, 28)),
                        'curriculum': curriculum_cbc,
                        'current_grade_level': grade,
                        'current_stream': stream,
                        'academic_year': year_2026,
                        'guardian_name': f"{random.choice(['Mr.', 'Mrs.', 'Dr.'])} {random.choice(cbc_last_names)}",
                        'guardian_phone': f"07{random.randint(10000000, 99999999)}",
                        'guardian_relationship': random.choice(['Father', 'Mother', 'Guardian']),
                        'status': 'ACTIVE',
                        'is_active': True
                    }
                )
                
                if created:
                    StudentHistory.objects.create(
                        student=student,
                        academic_year=year_2026,
                        grade_level=grade,
                        stream=stream,
                        is_current=True
                    )
                    students_cbc.append(student)
    
    print(f"  ✅ Created {len([s for s in students_cbc if s.current_grade_level == grade])} students in {grade_name}")

print(f"  ✅ Total CBC students created: {len(students_cbc)}")

# ============================================
# 6. CREATE TEACHER ASSIGNMENTS (8-4-4)
# ============================================
print("\n📚 Creating 8-4-4 Teacher Assignments...")

for teacher in teachers_844[:10]:
    num_assignments = random.randint(2, 4)
    assigned_subjects = random.sample(subjects_844, min(num_assignments, len(subjects_844)))
    
    for subject in assigned_subjects:
        grade = random.choice(list(grade_levels_844.values()))
        streams_for_grade = [s for s in streams_844.values() if s.grade_level == grade]
        if streams_for_grade:
            stream = random.choice(streams_for_grade)
            
            assignment, created = TeacherAssignment.objects.get_or_create(
                teacher=teacher,
                subject=subject,
                grade_level=grade,
                stream=stream,
                academic_year=year_2026,
                defaults={
                    'curriculum': curriculum_844,
                    'status': 'APPROVED',
                    'is_class_teacher': False,
                    'assigned_date': date(2026, 1, 1)
                }
            )
            if created:
                print(f"  ✅ {teacher.full_name} → {subject.name} ({grade.name} {stream.name})")

# ============================================
# 7. CREATE TEACHER ASSIGNMENTS (CBC)
# ============================================
print("\n📚 Creating CBC Teacher Assignments...")

for teacher in teachers_cbc[:5]:
    assigned_subjects = random.sample(subjects_cbc, min(3, len(subjects_cbc)))
    
    for subject in assigned_subjects:
        grade = random.choice(list(grade_levels_cbc.values()))
        streams_for_grade = [s for s in streams_cbc.values() if s.grade_level == grade]
        if streams_for_grade:
            stream = random.choice(streams_for_grade)
            
            assignment, created = TeacherAssignment.objects.get_or_create(
                teacher=teacher,
                subject=subject,
                grade_level=grade,
                stream=stream,
                academic_year=year_2026,
                defaults={
                    'curriculum': curriculum_cbc,
                    'status': 'APPROVED',
                    'is_class_teacher': False,
                    'assigned_date': date(2026, 1, 1)
                }
            )
            if created:
                print(f"  ✅ {teacher.full_name} → {subject.name} ({grade.name} {stream.name})")

# ============================================
# 8. CREATE CLASS TEACHERS (8-4-4)
# ============================================
print("\n📚 Assigning 8-4-4 Class Teachers...")

for stream in streams_844.values():
    if teachers_844:
        teacher = random.choice(teachers_844)
        class_teacher, created = ClassTeacher.objects.update_or_create(
            grade_level=stream.grade_level,
            stream=stream,
            academic_year=year_2026,
            defaults={
                'teacher': teacher,
                'is_active': True,
                'assigned_date': date(2026, 1, 15)
            }
        )
        if created:
            print(f"  ✅ {teacher.full_name} → Class Teacher for {stream.grade_level.name} {stream.name}")

# ============================================
# 9. CREATE CLASS TEACHERS (CBC)
# ============================================
print("\n📚 Assigning CBC Class Teachers...")

for stream in streams_cbc.values():
    if teachers_cbc:
        teacher = random.choice(teachers_cbc)
        class_teacher, created = ClassTeacher.objects.update_or_create(
            grade_level=stream.grade_level,
            stream=stream,
            academic_year=year_2026,
            defaults={
                'teacher': teacher,
                'is_active': True,
                'assigned_date': date(2026, 1, 15)
            }
        )
        if created:
            print(f"  ✅ {teacher.full_name} → Class Teacher for {stream.grade_level.name} {stream.name}")

# ============================================
# 10. CREATE EXAMINATIONS (8-4-4)
# ============================================
print("\n📝 Creating 8-4-4 Examinations...")

exam_names_844 = ['End of Term 1 Examination', 'Mid-Term 2 Assessment', 'End of Term 2 Examination']
exams_844 = []

for grade in grade_levels_844.values():
    for exam_name in exam_names_844[:2]:
        exam_code = f"EXAM{2026}{grade.level_number}{random.randint(10, 99)}"
        
        exam, created = Examination.objects.get_or_create(
            code=exam_code,
            defaults={
                'name': exam_name,
                'exam_type': random.choice(['END_TERM', 'MID_TERM']),
                'academic_year': year_2026,
                'term': random.choice(terms) if terms else None,
                'curriculum': curriculum_844,
                'grade_level': grade,
                'start_date': date(2026, random.randint(1, 10), random.randint(1, 28)),
                'end_date': date(2026, random.randint(1, 10), random.randint(1, 28)),
                'results_date': date(2026, random.randint(1, 10), random.randint(1, 28)),
                'status': 'LOCKED',
                'max_score': 100,
                'pass_mark': 40,
                'is_active': True
            }
        )
        
        if created:
            exam_subjects = random.sample(subjects_844, min(8, len(subjects_844)))
            exam.subjects.add(*exam_subjects)
            exams_844.append(exam)
            print(f"  ✅ Created {exam.name} ({exam.code}) for {grade.name}")

# ============================================
# 11. CREATE EXAMINATIONS (CBC)
# ============================================
print("\n📝 Creating CBC Examinations...")

exam_names_cbc = ['CBC Term 1 Assessment', 'CBC Term 2 Assessment', 'CBC Year End Assessment']
exams_cbc = []

for grade in grade_levels_cbc.values():
    for exam_name in exam_names_cbc[:2]:
        exam_code = f"CBC{2026}{grade.level_number}{random.randint(10, 99)}"
        
        exam, created = Examination.objects.get_or_create(
            code=exam_code,
            defaults={
                'name': exam_name,
                'exam_type': 'ASSESSMENT',
                'academic_year': year_2026,
                'term': random.choice(terms) if terms else None,
                'curriculum': curriculum_cbc,
                'grade_level': grade,
                'start_date': date(2026, random.randint(1, 10), random.randint(1, 28)),
                'end_date': date(2026, random.randint(1, 10), random.randint(1, 28)),
                'results_date': date(2026, random.randint(1, 10), random.randint(1, 28)),
                'status': 'PUBLISHED',
                'max_score': 100,
                'pass_mark': 50,
                'is_active': True
            }
        )
        
        if created:
            exam_subjects = random.sample(subjects_cbc, min(6, len(subjects_cbc)))
            exam.subjects.add(*exam_subjects)
            exams_cbc.append(exam)
            print(f"  ✅ Created {exam.name} ({exam.code}) for {grade.name}")

# ============================================
# 12. CREATE MARKS (8-4-4)
# ============================================
print("\n📊 Creating 8-4-4 Marks...")

marks_844_created = 0
mark_statuses = ['SUBMITTED', 'LOCKED']

for exam in exams_844[:6]:
    grade_students = Student.objects.filter(
        current_grade_level=exam.grade_level,
        curriculum=curriculum_844,
        is_active=True
    )[:20]
    
    if not grade_students:
        continue
    
    for student in grade_students:
        subjects_for_exam = exam.subjects.all()
        
        for subject in subjects_for_exam[:6]:
            if random.random() < 0.85:
                mark_value = random.randint(20, 95)
                
                mark_entry, created = MarkEntry.objects.get_or_create(
                    student=student,
                    examination=exam,
                    subject=subject,
                    defaults={
                        'grade_level': exam.grade_level,
                        'stream': student.current_stream,
                        'score': mark_value,
                        'status': random.choice(mark_statuses),
                        'entered_by': User.objects.first(),
                        'is_active': True
                    }
                )
                
                if created:
                    marks_844_created += 1
    
    print(f"  ✅ Created marks for {exam.code}")

print(f"  ✅ Total 8-4-4 marks created: {marks_844_created}")

# ============================================
# 13. CREATE MARKS (CBC)
# ============================================
print("\n📊 Creating CBC Marks...")

marks_cbc_created = 0

for exam in exams_cbc[:4]:
    grade_students = Student.objects.filter(
        current_grade_level=exam.grade_level,
        curriculum=curriculum_cbc,
        is_active=True
    )[:15]
    
    if not grade_students:
        continue
    
    for student in grade_students:
        subjects_for_exam = exam.subjects.all()
        
        for subject in subjects_for_exam[:5]:
            if random.random() < 0.80:
                mark_value = random.randint(30, 90)
                
                mark_entry, created = MarkEntry.objects.get_or_create(
                    student=student,
                    examination=exam,
                    subject=subject,
                    defaults={
                        'grade_level': exam.grade_level,
                        'stream': student.current_stream,
                        'score': mark_value,
                        'status': 'SUBMITTED',
                        'entered_by': User.objects.first(),
                        'is_active': True
                    }
                )
                
                if created:
                    marks_cbc_created += 1
    
    print(f"  ✅ Created marks for {exam.code}")

print(f"  ✅ Total CBC marks created: {marks_cbc_created}")

# ============================================
# 14. DATA SUMMARY
# ============================================
print("\n" + "=" * 70)
print("  📊 COMPLETE DATA GENERATION SUMMARY")
print("=" * 70)

print(f"""
📚 SCHOOL STRUCTURE:
  ├── Academic Years: {AcademicYear.objects.count()}
  ├── Terms: {Term.objects.count()}
  ├── Curriculums: {Curriculum.objects.count()}
  ├── Grade Levels (8-4-4): {len(grade_levels_844)}
  ├── Grade Levels (CBC): {len(grade_levels_cbc)}
  ├── Streams (8-4-4): {len(streams_844)}
  ├── Streams (CBC): {len(streams_cbc)}
  └── Subjects: {Subject.objects.count()}

👨‍🏫 TEACHERS & STAFF:
  ├── Teachers (8-4-4): {len(teachers_844)}
  ├── Teachers (CBC): {len(teachers_cbc)}
  ├── Total Teachers: {TeacherProfile.objects.count()}
  ├── Teacher Assignments: {TeacherAssignment.objects.count()}
  └── Class Teachers: {ClassTeacher.objects.count()}

👨‍🎓 STUDENTS:
  ├── Students (8-4-4): {len(students_844)}
  ├── Students (CBC): {len(students_cbc)}
  └── Total Students: {Student.objects.count()}

📝 EXAMINATIONS:
  ├── Examinations (8-4-4): {len(exams_844)}
  ├── Examinations (CBC): {len(exams_cbc)}
  └── Total Examinations: {Examination.objects.count()}

📊 MARKS:
  ├── Marks (8-4-4): {marks_844_created}
  ├── Marks (CBC): {marks_cbc_created}
  └── Total Marks: {MarkEntry.objects.count()}
""")

print("=" * 70)
print("  ✅ COMPLETE TEST DATA GENERATION FINISHED!")
print("=" * 70)
print("\n🌐 Login at: http://127.0.0.1:8000/")
print("👤 Admin: barakamrimi (or your admin username)")
print("🔑 8-4-4 Teachers: password123")
print("🔑 CBC Teachers: cbcpassword123")
print("📊 Total Students: {}".format(Student.objects.count()))
print("📊 Total Teachers: {}".format(TeacherProfile.objects.count()))
print("📊 Total Exams: {}".format(Examination.objects.count()))
print("📊 Total Marks: {}".format(MarkEntry.objects.count()))
print("=" * 70)
