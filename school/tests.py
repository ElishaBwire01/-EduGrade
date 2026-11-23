from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from datetime import date

from core.models import AuditLog
from students.models import Student, StudentHistory
from teachers.models import ClassTeacher, TeacherProfile
from .models import AcademicYear, Curriculum, GradeLevel, Stream
from .services import reallocate_and_delete


class ReallocationServiceTests(TestCase):
	def setUp(self):
		self.actor = User.objects.create_user('admin', is_staff=True)
		self.curriculum = Curriculum.objects.create(code='844', name='8-4-4')
		self.source_grade = GradeLevel.objects.create(
			curriculum=self.curriculum, level_type='FORM', level_number=1,
			name='Form 1', order=1,
		)
		self.destination_grade = GradeLevel.objects.create(
			curriculum=self.curriculum, level_type='FORM', level_number=2,
			name='Form 2', order=2,
		)
		self.source_stream = Stream.objects.create(
			name='East', code='1E', grade_level=self.source_grade,
		)
		self.destination_stream = Stream.objects.create(
			name='West', code='2W', grade_level=self.destination_grade,
		)
		self.year = AcademicYear.objects.create(
			name='2026', year=2026, start_date=date(2026, 1, 1),
			end_date=date(2026, 12, 31),
		)
		self.teacher_user = User.objects.create_user('teacher')
		self.teacher = TeacherProfile.objects.create(
			user=self.teacher_user, staff_number='T001', first_name='A',
			last_name='Teacher', gender='M', date_of_birth=date(1980, 1, 1),
			phone_number='0700000000', email='teacher@example.com',
			employment_date=date(2020, 1, 1), qualification='Degree',
		)
		self.class_teacher = ClassTeacher.objects.create(
			teacher=self.teacher, grade_level=self.source_grade,
			stream=self.source_stream, academic_year=self.year,
		)
		self.student = Student.objects.create(
			admission_number='S001', first_name='Test', last_name='Student',
			date_of_birth=date(2010, 1, 1), gender='M', admission_date=date(2024, 1, 1),
			curriculum=self.curriculum, current_grade_level=self.source_grade,
			current_stream=self.source_stream, academic_year=self.year,
		)
		StudentHistory.objects.create(
			student=self.student, academic_year=self.year,
			grade_level=self.source_grade, stream=self.source_stream, is_current=True,
		)

	def test_stream_reallocation_moves_student_history_and_class_teacher(self):
		reallocate_and_delete(
			self.source_stream, self.destination_grade, self.destination_stream, self.actor,
		)

		self.student.refresh_from_db()
		self.assertEqual(self.student.current_grade_level_id, self.destination_grade.id)
		self.assertEqual(self.student.current_stream_id, self.destination_stream.id)
		self.assertFalse(Stream.objects.filter(pk=self.source_stream.id).exists())
		self.assertFalse(StudentHistory.objects.filter(student=self.student, is_current=False).count() == 0)
		self.assertTrue(StudentHistory.objects.filter(
			student=self.student, grade_level=self.destination_grade,
			stream=self.destination_stream, is_current=True,
		).exists())
		self.class_teacher.refresh_from_db()
		self.assertEqual(self.class_teacher.stream_id, self.destination_stream.id)
		self.assertTrue(AuditLog.objects.filter(model_name='Student', object_id=str(self.student.id)).exists())

	def test_setup_grade_delete_requires_and_uses_destination(self):
		self.client.force_login(self.actor)
		response = self.client.post(
			f'/school/grade-level/{self.source_grade.id}/delete/',
			{
				'target_grade': self.destination_grade.id,
				'target_stream': self.destination_stream.id,
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertFalse(GradeLevel.objects.filter(pk=self.source_grade.id).exists())
		self.student.refresh_from_db()
		self.assertEqual(self.student.current_stream_id, self.destination_stream.id)

	def test_grade_edit_can_reallocate_students_to_new_grade(self):
		self.client.force_login(self.actor)
		response = self.client.post(
			f'/school/grade-level/{self.source_grade.id}/edit/',
			{
				'curriculum': self.curriculum.id,
				'level_type': 'FORM',
				'level_number': 1,
				'name': 'Form 1A',
				'order': 1,
				'reallocate_students': 'on',
				'target_grade': self.destination_grade.id,
				'target_stream': self.destination_stream.id,
			},
		)

		self.assertEqual(response.status_code, 302)
		self.student.refresh_from_db()
		self.assertEqual(self.student.current_grade_level_id, self.destination_grade.id)
		self.assertEqual(self.student.current_stream_id, self.destination_stream.id)
		self.source_grade.refresh_from_db()
		self.assertEqual(self.source_grade.name, 'Form 1A')

	def test_stream_edit_can_reallocate_students_to_new_stream(self):
		self.client.force_login(self.actor)
		new_stream = Stream.objects.create(name='North', code='1N', grade_level=self.source_grade)
		response = self.client.post(
			f'/school/stream/{self.source_stream.id}/edit/',
			{
				'grade_level': self.source_grade.id,
				'name': 'South',
				'code': '1S',
				'capacity': 40,
				'reallocate_students': 'on',
				'target_stream': new_stream.id,
			},
		)

		self.assertEqual(response.status_code, 302)
		self.student.refresh_from_db()
		self.assertEqual(self.student.current_stream_id, new_stream.id)
		self.assertEqual(self.student.current_grade_level_id, self.source_grade.id)
		self.source_stream.refresh_from_db()
		self.assertEqual(self.source_stream.name, 'South')

