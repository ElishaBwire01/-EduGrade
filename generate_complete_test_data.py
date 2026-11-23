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
    PerformanceLevel, StudentKCSEGrade, StudentOverallKCSE,
    AssessmentType, Rubric, RubricCriterion, RubricDescriptor,
    AssessmentComponent, ComponentAggregation,
    StudentCBAAssessment, StudentOverallCBA
)

print("=" * 70)
print("  EDUGRADE - COMPLETE TEST DATA GENERATION")
print("  INCLUDING FULL CBC SUPPORT")
print("=" * 70)

# ============================================
# 0. GET OR CREATE BASE DATA
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
# 1. CREATE CBC ASSESSMENT COMPONENTS
# ============================================
print("\n📚 Setting up CBC Assessment Framework...")

# Get CBC scheme
curriculum_cbc = Curriculum.objects.get(code='CBC')
cbc_scheme, _ = AssessmentScheme.objects.get_or_create(
    name='CBC Standard Assessment',
    curriculum='CBC',
    defaults={
        'description': 'Standard CBC/CBA assessment scheme with PL1-PL4 performance levels',
        'is_active': True
    }
)

# Get performance levels
pl4 = PerformanceLevel.objects.filter(level_code='PL4').first()
pl3 = PerformanceLevel.objects.filter(level_code='PL3').first()
pl2 = PerformanceLevel.objects.filter(level_code='PL2').first()
pl1 = PerformanceLevel.objects.filter(level_code='PL1').first()
performance_levels = [pl for pl in [pl4, pl3, pl2, pl1] if pl]

# Create Assessment Types
assessment_types = []
assessment_type_data = [
    {'name': 'Formative Assessment', 'category': 'FORMATIVE', 'weight': 30},
    {'name': 'Summative Assessment', 'category': 'SUMMATIVE', 'weight': 40},
    {'name': 'School-Based Assessment', 'category': 'SBA', 'weight': 30},
    {'name': 'KJSEA Assessment', 'category': 'KJSEA', 'weight': 60},
]

for data in assessment_type_data:
    at, created = AssessmentType.objects.get_or_create(
        scheme=cbc_scheme,
        name=data['name'],
        defaults={
            'category': data['category'],
            'weight': data['weight'],
            'is_active': True
        }
    )
    assessment_types.append(at)
    if created:
        print(f"  ✅ Created Assessment Type: {at.name} ({at.weight}%)")

# Create Assessment Components
components = []
component_data = [
    {'name': 'Classroom Participation', 'component_type': 'SBA', 'weight': 20},
    {'name': 'Projects and Assignments', 'component_type': 'SBA', 'weight': 30},
    {'name': 'End of Term Assessment', 'component_type': 'SUMMATIVE', 'weight': 50},
    {'name': 'KJSEA Examination', 'component_type': 'EXAMINATION', 'weight': 60},
]

for data in component_data:
    comp, created = AssessmentComponent.objects.get_or_create(
        scheme=cbc_scheme,
        name=data['name'],
        defaults={
            'component_type': data['component_type'],
            'weight': data['weight'],
            'is_active': True
        }
    )
    components.append(comp)
    if created:
        print(f"  ✅ Created Assessment Component: {comp.name} ({comp.weight}%)")

# ============================================
# 2. CREATE CBC RUBRICS
# ============================================
print("\n📚 Creating CBC Rubrics...")

cbc_subjects = list(Subject.objects.filter(curriculum=curriculum_cbc, is_active=True))
cbc_grade_levels = list(GradeLevel.objects.filter(curriculum=curriculum_cbc, is_active=True))

rubric_names = [
    'Mathematics Problem Solving',
    'English Writing Skills',
    'Science Investigation',
    'Social Studies Research',
    'Creative Arts Performance',
    'Physical Education Assessment',
    'ICT Skills Assessment',
    'Life Skills Evaluation'
]

rubrics_created = 0

for subject in cbc_subjects[:6]:
    for i in range(2):
        rubric_name = f"{subject.short_name} - {random.choice(rubric_names)}"
        
        rubric, created = Rubric.objects.get_or_create(
            scheme=cbc_scheme,
            name=rubric_name,
            defaults={
                'description': f'Rubric for assessing {subject.name} - CBC Level',
                'assessment_type': random.choice(assessment_types) if assessment_types else None,
                'subject': subject,
                'grade_level': random.choice(cbc_grade_levels) if cbc_grade_levels else None,
                'is_active': True
            }
        )
        
        if created:
            rubrics_created += 1
            print(f"  ✅ Created Rubric: {rubric.name}")
            
            # Create criteria
            criteria_names = ['Content Knowledge', 'Critical Thinking', 'Communication', 'Creativity']
            
            for j, criterion_name in enumerate(criteria_names, 1):
                criterion, created = RubricCriterion.objects.get_or_create(
                    rubric=rubric,
                    criterion=criterion_name,
                    defaults={
                        'description': f'Criterion: {criterion_name}',
                        'max_level': random.choice(performance_levels) if performance_levels else None,
                        'order': j,
                        'is_active': True
                    }
                )
                
                if created and performance_levels:
                    for level in performance_levels:
                        RubricDescriptor.objects.get_or_create(
                            criterion=criterion,
                            level=level,
                            defaults={'descriptor': f"{level.level_name} - {criterion_name}"}
                        )

print(f"  ✅ Total rubrics created: {rubrics_created}")

# ============================================
# 3. CREATE CBC GRADE LEVELS AND STREAMS
# ============================================
print("\n📚 Creating CBC Grade Levels and Streams...")

cbc_grade_levels_dict = {}
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
    cbc_grade_levels_dict[f'Grade_{i}'] = grade
    print(f"  ✅ {grade.name} exists")

cbc_streams_dict = {}
stream_names = ['East', 'West', 'North', 'South']

for grade_name, grade in cbc_grade_levels_dict.items():
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
        cbc_streams_dict[f"{grade_name}_{stream_name}"] = stream

print(f"  ✅ Created {len(cbc_streams_dict)} CBC streams")

# ============================================
# 4. CREATE CBC STUDENTS
# ============================================
print("\n👨‍🎓 Creating CBC Students...")

cbc_first_names = ['Amina', 'Brian', 'Cynthia', 'Daniel', 'Eunice', 'Felix', 'Grace', 'Henry',
    'Irene', 'James', 'Karen', 'Leon', 'Mary', 'Nathan', 'Olivia', 'Peter',
    'Rose', 'Samuel', 'Tracy', 'Vera', 'William', 'Yvonne', 'Zachary', 'Faith',
    'George', 'Helen', 'Isaac', 'Joy', 'Kevin', 'Linda', 'Moses', 'Nancy']

cbc_last_names = ['Adhiambo', 'Bwire', 'Chepkurui', 'Dida', 'Etyang', 'Furaha', 'Gikonyo',
    'Hassan', 'Ireri', 'Juma', 'Kiplagat', 'Lubanga', 'Makena', 'Ndungu',
    'Odhiambo', 'Pesa', 'Ruto', 'Sitati', 'Toroitich', 'Wanjala']

cbc_students = []

for grade_name, grade in cbc_grade_levels_dict.items():
    for stream_name, stream in cbc_streams_dict.items():
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
                    cbc_students.append(student)
    
    grade_students = [s for s in cbc_students if s.current_grade_level == grade]
    print(f"  ✅ Created {len(grade_students)} students in {grade.name}")

print(f"  ✅ Total CBC students created: {len(cbc_students)}")

# ============================================
# 5. CREATE CBC EXAMINATIONS
# ============================================
print("\n📝 Creating CBC Examinations...")

cbc_exams = []
cbc_exam_names = ['CBC Term 1 Assessment', 'CBC Term 2 Assessment', 'CBC Year End Assessment']

for grade in cbc_grade_levels_dict.values():
    for exam_name in cbc_exam_names[:2]:
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
            exam_subjects = random.sample(cbc_subjects, min(6, len(cbc_subjects)))
            exam.subjects.add(*exam_subjects)
            cbc_exams.append(exam)
            print(f"  ✅ Created CBC Exam: {exam.name} ({exam.code})")

print(f"  ✅ Total CBC exams created: {len(cbc_exams)}")

# ============================================
# 6. CREATE CBC ASSESSMENTS
# ============================================
print("\n📊 Creating CBC Assessments...")

cbc_assessments_created = 0
cbc_level_codes = ['PL4', 'PL3', 'PL3', 'PL3', 'PL2', 'PL2', 'PL1']
all_rubrics = Rubric.objects.filter(scheme=cbc_scheme, is_active=True)

for student in cbc_students[:60]:
    grade_rubrics = all_rubrics.filter(grade_level=student.current_grade_level)
    
    if not grade_rubrics.exists():
        continue
    
    for rubric in grade_rubrics[:3]:
        criterion_results = {}
        criteria = rubric.criteria.filter(is_active=True)
        
        for criterion in criteria:
            criterion_results[f"criterion_{criterion.id}"] = random.choice(cbc_level_codes)
        
        level_counts = {}
        for level_code in criterion_results.values():
            level_counts[level_code] = level_counts.get(level_code, 0) + 1
        
        overall_level_code = max(level_counts, key=level_counts.get) if level_counts else 'PL2'
        overall_level = PerformanceLevel.objects.filter(level_code=overall_level_code).first()
        
        if cbc_exams:
            assessment, created = StudentCBAAssessment.objects.get_or_create(
                student=student,
                examination=random.choice(cbc_exams),
                rubric=rubric,
                subject=rubric.subject,
                defaults={
                    'criterion_results': criterion_results,
                    'overall_level': overall_level,
                    'teacher_notes': f"Assessment completed on {date.today().strftime('%Y-%m-%d')}",
                    'component': random.choice(components) if components else None,
                    'score': random.randint(40, 95)
                }
            )
            
            if created:
                cbc_assessments_created += 1

print(f"  ✅ Total CBC assessments created: {cbc_assessments_created}")

# ============================================
# 7. CREATE CBC OVERALL RESULTS
# ============================================
print("\n📊 Creating CBC Overall Results...")

cbc_overall_created = 0

for student in cbc_students[:50]:
    assessments = StudentCBAAssessment.objects.filter(student=student)
    
    if not assessments.exists():
        continue
    
    exam_assessments = {}
    for assessment in assessments:
        if assessment.examination_id not in exam_assessments:
            exam_assessments[assessment.examination_id] = []
        exam_assessments[assessment.examination_id].append(assessment)
    
    for exam_id, exam_assessments_list in exam_assessments.items():
        component_scores = {}
        total_score = 0
        count = 0
        
        for assessment in exam_assessments_list:
            if assessment.component and assessment.score:
                comp_name = assessment.component.name
                if comp_name not in component_scores:
                    component_scores[comp_name] = []
                component_scores[comp_name].append(float(assessment.score))
        
        component_avgs = {}
        for comp_name, scores in component_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            component_avgs[comp_name] = avg_score
            total_score += avg_score
            count += 1
        
        if count > 0:
            overall_total = total_score / count
            
            if overall_total >= 80:
                overall_level = pl4
            elif overall_total >= 60:
                overall_level = pl3
            elif overall_total >= 40:
                overall_level = pl2
            else:
                overall_level = pl1
            
            overall, created = StudentOverallCBA.objects.get_or_create(
                student=student,
                examination_id=exam_id,
                defaults={
                    'overall_level': overall_level,
                    'component_scores': component_avgs,
                    'total_score': overall_total,
                    'total_weighted_score': overall_total * 0.8,
                    'grade_equivalent': overall_level.level_code if overall_level else None,
                    'position': random.randint(1, 30)
                }
            )
            
            if created:
                cbc_overall_created += 1

print(f"  ✅ Total CBC overall results created: {cbc_overall_created}")

# ============================================
# 8. CREATE CBC TEACHERS
# ============================================
print("\n📚 Creating CBC Teachers...")

cbc_teacher_names = [
    ('Catherine', 'Njeri'), ('Stephen', 'Ochieng'), ('Monica', 'Wanjiku'),
    ('Fred', 'Kiprop'), ('Lilian', 'Akinyi'), ('Sammy', 'Omondi'),
    ('Virginia', 'Wambui'), ('Charles', 'Mwangi')
]

cbc_teachers = []

for first_name, last_name in cbc_teacher_names:
    staff_number = f"CBC{2026}{random.randint(100, 999)}"
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
            'specialization': random.choice(['CBC Pedagogy', 'Competency-Based Assessment', 'Learning Areas']),
            'status': 'ACTIVE',
            'is_active': True
        }
    )
    
    if created:
        cbc_teachers.append(teacher)
        print(f"  ✅ Created CBC Teacher: {teacher.full_name} ({teacher.staff_number})")

# ============================================
# 9. CREATE CBC TEACHER ASSIGNMENTS
# ============================================
print("\n📚 Creating CBC Teacher Assignments...")

for teacher in cbc_teachers[:5]:
    assigned_subjects = random.sample(cbc_subjects, min(3, len(cbc_subjects)))
    
    for subject in assigned_subjects:
        grade = random.choice(list(cbc_grade_levels_dict.values()))
        streams_for_grade = [s for s in cbc_streams_dict.values() if s.grade_level == grade]
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
                    'is_class_teacher': random.choice([True, False]),
                    'assigned_date': date(2026, 1, 1)
                }
            )
            if created:
                print(f"  ✅ {teacher.full_name} → {subject.name} ({grade.name} {stream.name})")

# ============================================
# 10. CREATE CBC CLASS TEACHERS (AVOID DUPLICATES)
# ============================================
print("\n📚 Assigning CBC Class Teachers...")

for stream in cbc_streams_dict.values():
    if cbc_teachers:
        teacher = random.choice(cbc_teachers)
        # Use update_or_create to avoid unique constraint errors
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
# 11. DATA SUMMARY
# ============================================
print("\n" + "=" * 70)
print("  📊 COMPLETE DATA GENERATION SUMMARY")
print("=" * 70)

print(f"""
📚 SCHOOL STRUCTURE:
  ├── Academic Years: {AcademicYear.objects.count()}
  ├── Terms: {Term.objects.count()}
  ├── Curriculums: {Curriculum.objects.count()}
  ├── Grade Levels (CBC): {GradeLevel.objects.filter(curriculum__code='CBC').count()}
  ├── Streams (CBC): {Stream.objects.filter(grade_level__curriculum__code='CBC').count()}
  └── Subjects (CBC): {cbc_subjects.count()}

👨‍🏫 CBC TEACHERS & STAFF:
  ├── Teachers (CBC): {len(cbc_teachers)}
  ├── Teacher Assignments: {TeacherAssignment.objects.filter(curriculum__code='CBC').count()}
  └── Class Teachers: {ClassTeacher.objects.filter(academic_year=year_2026).count()}

👨‍🎓 CBC STUDENTS:
  ├── Students (Grade 7): {Student.objects.filter(curriculum__code='CBC', current_grade_level__level_number=7).count()}
  ├── Students (Grade 8): {Student.objects.filter(curriculum__code='CBC', current_grade_level__level_number=8).count()}
  ├── Students (Grade 9): {Student.objects.filter(curriculum__code='CBC', current_grade_level__level_number=9).count()}
  └── Total CBC Students: {len(cbc_students)}

📝 CBC EXAMINATIONS:
  └── Examinations (CBC): {len(cbc_exams)}

📊 CBC MARKS & GRADES:
  ├── CBC Assessments: {StudentCBAAssessment.objects.count()}
  └── CBC Overall Results: {StudentOverallCBA.objects.count()}

📋 CBC FRAMEWORK:
  ├── Assessment Types: {AssessmentType.objects.count()}
  ├── Assessment Components: {AssessmentComponent.objects.count()}
  ├── Rubrics: {Rubric.objects.count()}
  ├── Rubric Criteria: {RubricCriterion.objects.count()}
  └── Rubric Descriptors: {RubricDescriptor.objects.count()}

🎯 TOTAL SYSTEM DATA:
  ├── Total Students (8-4-4 + CBC): {Student.objects.count()}
  ├── Total Teachers (8-4-4 + CBC): {TeacherProfile.objects.count()}
  └── Total Examinations (8-4-4 + CBC): {Examination.objects.count()}
""")

print("=" * 70)
print("  ✅ COMPLETE TEST DATA GENERATION FINISHED!")
print("=" * 70)
print("\n🌐 Login at: http://127.0.0.1:8000/")
print("👤 Admin: barakamrimi")
print("🔑 8-4-4 Teachers: password123")
print("🔑 CBC Teachers: cbcpassword123")
print("📊 Total Students: {}".format(Student.objects.count()))
print("📊 Total Teachers: {}".format(TeacherProfile.objects.count()))
print("📊 Total Exams: {}".format(Examination.objects.count()))
print("📊 CBC Assessments: {}".format(StudentCBAAssessment.objects.count()))
print("=" * 70)

