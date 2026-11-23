import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edugrade.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
from datetime import date, timedelta
import random
from decimal import Decimal

# Import all models
from school.models import AcademicYear, Term, Curriculum, GradeLevel, Stream, Subject
from students.models import Student, StudentHistory
from teachers.models import TeacherProfile, TeacherAssignment, TeacherRequest, ClassTeacher
from examinations.models import Examination, ExaminationClass, SubjectScoreConfig
from marks.models import MarkEntry, MarkSubmission
from grading.models import (
    AssessmentScheme, KCSEGradeRule, KCSEOverallCalculation, 
    PerformanceLevel, StudentKCSEGrade, StudentOverallKCSE
)

# Import CBC models if they exist, otherwise skip
try:
    from grading.models import StudentCBAAssessment, StudentOverallCBA
    CBC_MODELS_AVAILABLE = True
except ImportError:
    CBC_MODELS_AVAILABLE = False
    print("⚠️ CBC models not available, skipping CBC assessments")

print("=" * 70)
print("  EDUGRADE - GENERATING TEST DATA (FIXED)")
print("=" * 70)

# ============================================
# 1. CREATE ACADEMIC YEARS AND TERMS
# ============================================
print("\n📚 Creating Academic Years and Terms...")

year_2025, _ = AcademicYear.objects.get_or_create(
    year=2025,
    defaults={
        'name': 'Academic Year 2025',
        'start_date': date(2025, 1, 15),
        'end_date': date(2025, 12, 15),
        'is_current': False
    }
)

year_2026, _ = AcademicYear.objects.get_or_create(
    year=2026,
    defaults={
        'name': 'Academic Year 2026',
        'start_date': date(2026, 1, 15),
        'end_date': date(2026, 12, 15),
        'is_current': True
    }
)

terms_data = [
    {'number': 1, 'name': 'Term 1', 'start': date(2026, 1, 15), 'end': date(2026, 3, 31)},
    {'number': 2, 'name': 'Term 2', 'start': date(2026, 4, 15), 'end': date(2026, 7, 31)},
    {'number': 3, 'name': 'Term 3', 'start': date(2026, 8, 15), 'end': date(2026, 11, 30)},
]

terms = []
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
    if created:
        print(f"  ✅ Created {term.name} ({year_2026.year})")

# ============================================
# 2. GET CURRICULUMS AND SUBJECTS
# ============================================
print("\n📚 Getting Curriculums and Subjects...")

curriculum_844 = Curriculum.objects.get(code='844')
curriculum_cbc = Curriculum.objects.get(code='CBC')

# Get subjects
subjects_844 = list(Subject.objects.filter(curriculum=curriculum_844, is_active=True))
subjects_cbc = list(Subject.objects.filter(curriculum=curriculum_cbc, is_active=True))

print(f"  ✅ Found {len(subjects_844)} subjects for 8-4-4")
print(f"  ✅ Found {len(subjects_cbc)} subjects for CBC")

# ============================================
# 3. CREATE GRADE LEVELS AND STREAMS
# ============================================
print("\n📚 Creating Grade Levels and Streams...")

# Get or create grade levels
grade_levels = {}
stream_names = ['East', 'West', 'North', 'South']

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
    grade_levels[f'Form_{i}'] = grade
    print(f"  ✅ {grade.name} exists")

# Create streams for each form
streams = {}
for form_name, grade in grade_levels.items():
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
        streams[f"{form_name}_{stream_name}"] = stream
        if created:
            print(f"  ✅ Created stream: {stream.name} ({stream.code})")

# ============================================
# 4. CREATE TEACHERS
# ============================================
print("\n👨‍🏫 Creating Teachers...")

teacher_names = [
    ('John', 'Kamau'), ('Mary', 'Wanjiru'), ('Peter', 'Ochieng'),
    ('Grace', 'Akinyi'), ('James', 'Mwangi'), ('Sarah', 'Njeri'),
    ('David', 'Mutua'), ('Esther', 'Wambui'), ('Samuel', 'Kiprop'),
    ('Ruth', 'Chebet'), ('Michael', 'Omondi'), ('Faith', 'Mwende'),
    ('Daniel', 'Kariuki'), ('Rose', 'Achieng'), ('Simon', 'Ngugi'),
    ('Jane', 'Wangari'), ('Paul', 'Ndegwa'), ('Susan', 'Atieno'),
    ('Mark', 'Kiptoo'), ('Ann', 'Muthoni')
]

teachers = []
gender_choices = ['M', 'F']
status_choices = ['ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ON_LEAVE']
qualifications = [
    'B.Ed (Science)', 'B.Ed (Arts)', 'B.Ed (Mathematics)',
    'M.Ed (Educational Leadership)', 'B.Ed (Languages)',
    'B.Ed (Special Needs)', 'PGDE', 'M.Ed (Curriculum Design)'
]
specializations = [
    'Mathematics and Science', 'Languages and Humanities',
    'Business Studies', 'ICT', 'Creative Arts',
    'Physical Education', 'Special Education', 'Guidance and Counseling'
]

for i, (first_name, last_name) in enumerate(teacher_names, 1):
    staff_number = f"TCH{2026:04d}{i:03d}"
    username = staff_number.lower()
    
    # Create user account
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
    
    # Set password
    user.set_password('password123')
    user.save()
    
    # Create teacher profile
    teacher, created = TeacherProfile.objects.get_or_create(
        staff_number=staff_number,
        defaults={
            'user': user,
            'first_name': first_name,
            'last_name': last_name,
            'gender': random.choice(gender_choices),
            'date_of_birth': date(1980, random.randint(1, 12), random.randint(1, 28)),
            'phone_number': f"07{random.randint(10000000, 99999999)}",
            'email': f"{first_name.lower()}.{last_name.lower()}@school.com",
            'address': f"Teacher's House, Nairobi, Kenya",
            'employment_date': date(2020, random.randint(1, 12), random.randint(1, 28)),
            'qualification': random.choice(qualifications),
            'specialization': random.choice(specializations),
            'status': random.choice(status_choices),
            'is_active': True
        }
    )
    
    if created:
        print(f"  ✅ Created teacher: {teacher.full_name} ({teacher.staff_number})")
    teachers.append(teacher)

# ============================================
# 5. CREATE STUDENTS
# ============================================
print("\n👨‍🎓 Creating Students...")

student_first_names = [
    'John', 'Mary', 'Peter', 'Grace', 'James', 'Sarah', 'David', 'Esther',
    'Samuel', 'Ruth', 'Michael', 'Faith', 'Daniel', 'Rose', 'Simon', 'Jane',
    'Paul', 'Susan', 'Mark', 'Ann', 'Joseph', 'Alice', 'Robert', 'Margaret',
    'Patrick', 'Catherine', 'Stephen', 'Lucy', 'Anthony', 'Dorothy',
    'Martin', 'Elizabeth', 'Nicholas', 'Agnes', 'Kevin', 'Veronica',
    'Brian', 'Joyce', 'George', 'Helen', 'Richard', 'Irene', 'Timothy', 'Judy',
    'Vincent', 'Mildred', 'Oscar', 'Susan', 'Gerald', 'Pauline'
]

student_last_names = [
    'Kamau', 'Wanjiru', 'Ochieng', 'Akinyi', 'Mwangi', 'Njeri',
    'Mutua', 'Wambui', 'Kiprop', 'Chebet', 'Omondi', 'Mwende',
    'Kariuki', 'Achieng', 'Ngugi', 'Wangari', 'Ndegwa', 'Atieno',
    'Kiptoo', 'Muthoni', 'Odhiambo', 'Njoroge', 'Oduor', 'Nyokabi',
    'Maina', 'Wangui', 'Ouma', 'Kinyua', 'Otieno', 'Wanjiku',
    'Ochieng', 'Auma', 'Gichuru', 'Khadija', 'Kariuki', 'Achieng'
]

students = []
student_statuses = ['ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'INACTIVE']
genders = ['M', 'F', 'M', 'F', 'M', 'F', 'M', 'F']

for form_name, grade in grade_levels.items():
    for stream_name, stream in streams.items():
        if f"{form_name}" in stream_name:
            num_students = random.randint(30, 40)
            
            for i in range(num_students):
                first_name = random.choice(student_first_names)
                last_name = random.choice(student_last_names)
                
                # Generate admission number
                year_part = random.choice([2025, 2026])
                number_part = f"{random.randint(1, 999):03d}"
                admission_number = f"{year_part}/{number_part}"
                
                # Avoid duplicates
                while Student.objects.filter(admission_number=admission_number).exists():
                    number_part = f"{random.randint(1, 999):03d}"
                    admission_number = f"{year_part}/{number_part}"
                
                birth_year = random.randint(2005, 2012)
                gender = random.choice(genders)
                
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
                        'status': random.choice(student_statuses),
                        'is_active': True
                    }
                )
                
                if created:
                    # Create history entry
                    StudentHistory.objects.create(
                        student=student,
                        academic_year=year_2026,
                        grade_level=grade,
                        stream=stream,
                        is_current=True
                    )
                    students.append(student)
    
    print(f"  ✅ Created {len([s for s in students if s.current_grade_level == grade])} students in {grade.name}")

print(f"  ✅ Total students created: {len(students)}")

# ============================================
# 6. CREATE TEACHER ASSIGNMENTS
# ============================================
print("\n📚 Creating Teacher Assignments...")

# Assign teachers to subjects and classes
assignment_subjects = subjects_844[:8]  # Use first 8 subjects

for teacher in teachers[:15]:  # First 15 teachers get assignments
    num_assignments = random.randint(2, 4)
    assigned_subjects = random.sample(assignment_subjects, min(num_assignments, len(assignment_subjects)))
    
    for subject in assigned_subjects:
        # Randomly select a grade and stream
        grade = random.choice(list(grade_levels.values()))
        streams_for_grade = [s for s in streams.values() if s.grade_level == grade]
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
# 7. CREATE CLASS TEACHERS
# ============================================
print("\n📚 Assigning Class Teachers...")

# Assign class teachers to streams
class_teacher_pool = teachers[:10]  # First 10 teachers

for stream in streams.values():
    teacher = random.choice(class_teacher_pool)
    class_teacher, created = ClassTeacher.objects.get_or_create(
        teacher=teacher,
        grade_level=stream.grade_level,
        stream=stream,
        academic_year=year_2026,
        defaults={
            'is_active': True,
            'assigned_date': date(2026, 1, 15)
        }
    )
    if created:
        print(f"  ✅ {teacher.full_name} → Class Teacher for {stream.grade_level.name} {stream.name}")

# ============================================
# 8. CREATE EXAMINATIONS
# ============================================
print("\n📝 Creating Examinations...")

exam_names = [
    'End of Term 1 Examination',
    'Mid-Term 2 Assessment',
    'End of Term 2 Examination',
    'Mock Examination',
    'End of Year Assessment'
]

examination_statuses = ['LOCKED', 'PUBLISHED', 'ACTIVE', 'ACTIVE']

created_examinations = []

for grade in grade_levels.values():
    for exam_name in exam_names[:2]:  # Create 2 exams per grade
        exam_code = f"EXAM{2026}{grade.level_number}{random.randint(1, 99):02d}"
        
        exam, created = Examination.objects.get_or_create(
            code=exam_code,
            defaults={
                'name': exam_name,
                'exam_type': random.choice(['END_TERM', 'MID_TERM', 'MOCK']),
                'academic_year': year_2026,
                'term': random.choice(terms),
                'curriculum': curriculum_844,
                'grade_level': grade,
                'start_date': date(2026, random.randint(1, 10), random.randint(1, 28)),
                'end_date': date(2026, random.randint(1, 10), random.randint(1, 28)),
                'results_date': date(2026, random.randint(1, 10), random.randint(1, 28)),
                'status': random.choice(examination_statuses),
                'max_score': 100,
                'pass_mark': 40,
                'is_active': True
            }
        )
        
        if created:
            # Add subjects to examination
            exam_subjects = random.sample(subjects_844, min(8, len(subjects_844)))
            exam.subjects.add(*exam_subjects)
            
            # Create subject configs
            for subject in exam_subjects:
                SubjectScoreConfig.objects.create(
                    examination=exam,
                    subject=subject,
                    max_score=100,
                    min_score=0,
                    pass_mark=40
                )
            
            created_examinations.append(exam)
            print(f"  ✅ Created {exam.name} ({exam.code}) for {grade.name}")

print(f"  ✅ Total examinations created: {len(created_examinations)}")

# ============================================
# 9. CREATE MARKS
# ============================================
print("\n📊 Creating Marks...")

marks_created = 0
mark_statuses = ['SUBMITTED', 'LOCKED', 'DRAFT']

for exam in created_examinations[:10]:  # Process first 10 exams
    # Get students for this grade
    grade_students = Student.objects.filter(
        current_grade_level=exam.grade_level,
        is_active=True
    )[:20]  # Limit to 20 students per exam
    
    if not grade_students:
        continue
    
    # Get teacher for this exam's grade level
    teacher = teachers[random.randint(0, len(teachers)-1)] if teachers else None
    
    for student in grade_students:
        # Get subjects for this exam
        subjects_for_exam = exam.subjects.all()
        
        for subject in subjects_for_exam[:6]:  # Limit to 6 subjects
            # Generate realistic marks
            if random.random() < 0.85:  # 85% of marks exist
                mark_value = random.randint(20, 95)
                
                # Check if mark already exists
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
                    marks_created += 1
    
    print(f"  ✅ Created marks for {exam.code}")

print(f"  ✅ Total marks created: {marks_created}")

# ============================================
# 10. CREATE TEACHER REQUESTS
# ============================================
print("\n📋 Creating Teacher Requests...")

request_types = ['NEW', 'TRANSFER', 'REMOVE']
request_statuses = ['PENDING', 'APPROVED', 'REJECTED']

for i, teacher in enumerate(teachers[:5]):
    subject = random.choice(subjects_844[:5])
    grade = random.choice(list(grade_levels.values()))
    
    request, created = TeacherRequest.objects.get_or_create(
        teacher=teacher,
        request_type=random.choice(request_types),
        defaults={
            'subject': subject,
            'grade_level': grade,
            'stream': random.choice([s for s in streams.values() if s.grade_level == grade]),
            'academic_year': year_2026,
            'reason': f'Requesting additional teaching assignment to enhance student performance.',
            'status': random.choice(request_statuses),
            'requested_date': date(2026, random.randint(1, 6), random.randint(1, 28))
        }
    )
    if created:
        print(f"  ✅ Created request: {teacher.full_name} - {subject.name}")

# ============================================
# 11. CREATE KCSE GRADES
# ============================================
print("\n📊 Generating KCSE Grades for students...")

kcse_grades_created = 0

for student in students[:30]:  # First 30 students
    for exam in created_examinations[:3]:  # First 3 exams
        subjects_for_exam = exam.subjects.all()[:6]
        total_points = 0
        subject_count = 0
        
        for subject in subjects_for_exam:
            # Generate realistic mark
            mark_value = random.randint(20, 95)
            
            # Calculate grade based on mark
            if mark_value >= 80:
                grade = 'A'
                points = 12
            elif mark_value >= 75:
                grade = 'A-'
                points = 11
            elif mark_value >= 70:
                grade = 'B+'
                points = 10
            elif mark_value >= 65:
                grade = 'B'
                points = 9
            elif mark_value >= 60:
                grade = 'B-'
                points = 8
            elif mark_value >= 55:
                grade = 'C+'
                points = 7
            elif mark_value >= 45:
                grade = 'C'
                points = 6
            elif mark_value >= 40:
                grade = 'C-'
                points = 5
            elif mark_value >= 35:
                grade = 'D+'
                points = 4
            elif mark_value >= 30:
                grade = 'D'
                points = 3
            elif mark_value >= 25:
                grade = 'D-'
                points = 2
            else:
                grade = 'E'
                points = 1
            
            # Create KCSE grade
            kcse_grade, created = StudentKCSEGrade.objects.get_or_create(
                student=student,
                examination=exam,
                subject=subject,
                defaults={
                    'raw_mark': mark_value,
                    'grade': grade,
                    'points': points,
                    'is_core': subject.name in ['Mathematics', 'English', 'Kiswahili'],
                    'is_best_subject': False
                }
            )
            
            if created:
                kcse_grades_created += 1
                total_points += points
                subject_count += 1
        
        # Create overall KCSE result
        if subject_count > 0:
            mean_score = (total_points / subject_count) * 10 if subject_count > 0 else 0
            
            # Determine mean grade
            if mean_score >= 80:
                mean_grade = 'A'
            elif mean_score >= 75:
                mean_grade = 'A-'
            elif mean_score >= 70:
                mean_grade = 'B+'
            elif mean_score >= 65:
                mean_grade = 'B'
            elif mean_score >= 60:
                mean_grade = 'B-'
            elif mean_score >= 55:
                mean_grade = 'C+'
            elif mean_score >= 45:
                mean_grade = 'C'
            elif mean_score >= 40:
                mean_grade = 'C-'
            elif mean_score >= 35:
                mean_grade = 'D+'
            elif mean_score >= 30:
                mean_grade = 'D'
            elif mean_score >= 25:
                mean_grade = 'D-'
            else:
                mean_grade = 'E'
            
            overall, created = StudentOverallKCSE.objects.get_or_create(
                student=student,
                examination=exam,
                defaults={
                    'total_points': total_points,
                    'mean_grade': mean_grade,
                    'mean_score': mean_score,
                    'core_subjects_count': 3,
                    'best_subjects_count': min(5, subject_count),
                    'total_subjects_used': subject_count,
                    'position': random.randint(1, 30)
                }
            )
            if created:
                kcse_grades_created += 1

print(f"  ✅ Total KCSE grades created: {kcse_grades_created}")

# ============================================
# 12. DATA SUMMARY
# ============================================
print("\n" + "=" * 70)
print("  📊 DATA GENERATION SUMMARY")
print("=" * 70)

print(f"""
📚 School Structure:
  ├── Academic Years: {AcademicYear.objects.count()}
  ├── Terms: {Term.objects.count()}
  ├── Curriculums: {Curriculum.objects.count()}
  ├── Grade Levels: {GradeLevel.objects.count()}
  ├── Streams: {Stream.objects.count()}
  └── Subjects: {Subject.objects.count()}

👨‍🏫 Teachers & Staff:
  ├── Teachers: {TeacherProfile.objects.count()}
  ├── Teacher Assignments: {TeacherAssignment.objects.count()}
  ├── Class Teachers: {ClassTeacher.objects.count()}
  └── Teacher Requests: {TeacherRequest.objects.count()}

👨‍🎓 Students:
  ├── Students: {Student.objects.count()}
  └── Student History: {StudentHistory.objects.count()}

📝 Examinations:
  ├── Examinations: {Examination.objects.count()}
  └── Subject Configs: {SubjectScoreConfig.objects.count()}

📊 Marks & Grades:
  ├── Marks Entered: {MarkEntry.objects.count()}
  ├── Mark Submissions: {MarkSubmission.objects.count()}
  ├── KCSE Grades: {StudentKCSEGrade.objects.count()}
  └── Overall KCSE Results: {StudentOverallKCSE.objects.count()}

📋 Grading System:
  ├── Assessment Schemes: {AssessmentScheme.objects.count()}
  ├── KCSE Grade Rules: {KCSEGradeRule.objects.count()}
  ├── KCSE Calculations: {KCSEOverallCalculation.objects.count()}
  └── Performance Levels: {PerformanceLevel.objects.count()}
""")

print("=" * 70)
print("  ✅ TEST DATA GENERATION COMPLETE!")
print("=" * 70)
print("\n🌐 Login at: http://127.0.0.1:8000/")
print("👤 Admin Username: barakamrimi")
print("🔑 Teacher Password: password123 (for all teachers)")
print("📊 Total Students: {}".format(Student.objects.count()))
print("📊 Total Teachers: {}".format(TeacherProfile.objects.count()))
print("📊 Total Exams: {}".format(Examination.objects.count()))
print("📊 Total Marks: {}".format(MarkEntry.objects.count()))
print("=" * 70)

