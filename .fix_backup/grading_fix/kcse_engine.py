from django.db.models import Q, Sum, Avg, Count
from decimal import Decimal
from .models import KCSEGradeRule, KCSEOverallCalculation, StudentKCSEGrade, StudentOverallKCSE
from marks.models import MarkEntry

class KCSEEngine:
    """KCSE/8-4-4 Grading Engine"""
    
    def __init__(self, examination, grade_level=None, stream=None):
        self.examination = examination
        self.grade_level = grade_level
        self.stream = stream
        self.scheme = self._get_scheme()
        self.grade_rules = self._get_grade_rules()
        self.calculation = self._get_calculation()
    
    def _get_scheme(self):
        """Get the assessment scheme for KCSE"""
        from .models import AssessmentScheme
        scheme = AssessmentScheme.objects.filter(
            curriculum='844',
            is_active=True
        ).first()
        return scheme
    
    def _get_grade_rules(self):
        """Get KCSE grade rules"""
        if not self.scheme:
            return {}
        
        rules = KCSEGradeRule.objects.filter(
            scheme=self.scheme,
            is_active=True
        ).order_by('order')
        
        # Organize by subject
        subject_rules = {}
        all_rules = []
        
        for rule in rules:
            if rule.subject_scope == 'ALL':
                all_rules.append(rule)
            else:
                if rule.subject_id not in subject_rules:
                    subject_rules[rule.subject_id] = []
                subject_rules[rule.subject_id].append(rule)
        
        return {
            'all': all_rules,
            'subject': subject_rules
        }
    
    def _get_calculation(self):
        """Get KCSE overall calculation methodology"""
        if not self.scheme:
            return None
        
        return KCSEOverallCalculation.objects.filter(
            scheme=self.scheme,
            is_active=True
        ).first()
    
    def get_grade_and_points(self, score, subject_id=None):
        """Get grade and points for a raw mark"""
        rules = []
        
        # Try subject-specific rules first
        if subject_id and subject_id in self.grade_rules['subject']:
            rules = self.grade_rules['subject'][subject_id]
        
        # Fall back to general rules
        if not rules:
            rules = self.grade_rules['all']
        
        for rule in rules:
            if rule.min_score <= score <= rule.max_score:
                return {
                    'grade': rule.grade,
                    'grade_name': rule.grade_name,
                    'points': float(rule.points),
                    'descriptor': rule.descriptor
                }
        
        return {'grade': 'E', 'grade_name': 'Poor', 'points': 1, 'descriptor': 'Below minimum'}
    
    def process_student(self, student):
        """Process a single student's KCSE results"""
        # Get marks for this student
        marks = MarkEntry.objects.filter(
            student=student,
            examination=self.examination,
            is_active=True
        ).select_related('subject')
        
        if not marks.exists():
            return None
        
        grades = []
        total_points = 0
        core_subjects = []
        best_subjects = []
        
        # Process each subject
        for mark in marks:
            score = float(mark.score or 0)
            grade_result = self.get_grade_and_points(score, mark.subject_id)
            
            # Determine if this is a core subject
            is_core = False
            if self.calculation:
                is_core = self.calculation.core_subjects.filter(id=mark.subject_id).exists()
            
            student_grade, _created = StudentKCSEGrade.objects.update_or_create(
                student=student,
                examination=self.examination,
                subject=mark.subject,
                defaults={
                    'raw_mark': score,
                    'grade': grade_result['grade'],
                    'points': grade_result['points'],
                    'is_core': is_core,
                }
            )
            
            grades.append({
                'subject': mark.subject,
                'raw_mark': score,
                'grade': grade_result['grade'],
                'points': grade_result['points'],
                'is_core': is_core
            })
            
            if is_core:
                core_subjects.append(grade_result['points'])
            else:
                best_subjects.append(grade_result['points'])
        
        # Calculate overall
        if self.calculation:
            return self._calculate_overall(student, grades, core_subjects, best_subjects)
        else:
            return grades
    
    def _calculate_overall(self, student, grades, core_subjects, best_subjects):
        """Calculate overall KCSE result"""
        # Sort best subjects by points descending
        best_subjects.sort(reverse=True)
        
        # Take the required number of best subjects
        if self.calculation:
            best_count = min(self.calculation.best_subject_count, len(best_subjects))
            selected_best = best_subjects[:best_count]
        else:
            selected_best = best_subjects[:5]
        
        # Total points = core subjects + best subjects
        total_points = sum(core_subjects) + sum(selected_best)
        total_subjects_used = len(core_subjects) + len(selected_best)
        
        # Calculate mean grade
        if total_subjects_used > 0:
            mean_score = total_points / total_subjects_used
            mean_grade = self._get_mean_grade(mean_score)
        else:
            mean_grade = 'E'
            mean_score = 0
        
        # Save overall result
        overall, _created = StudentOverallKCSE.objects.update_or_create(
            student=student,
            examination=self.examination,
            defaults={
                'total_points': total_points,
                'mean_grade': mean_grade,
                'mean_score': mean_score,
                'core_subjects_count': len(core_subjects),
                'best_subjects_count': len(selected_best),
                'total_subjects_used': total_subjects_used,
            }
        )
        
        return {
            'total_points': total_points,
            'mean_score': mean_score,
            'mean_grade': mean_grade,
            'core_count': len(core_subjects),
            'best_count': len(selected_best),
            'total_used': total_subjects_used,
            'grades': grades
        }
    
    def _get_mean_grade(self, mean_score):
        """Convert mean score to KCSE grade"""
        # Use the grade boundaries from the calculation
        if self.calculation and self.calculation.grade_boundaries:
            boundaries = self.calculation.grade_boundaries
            for grade, min_score in boundaries.items():
                if mean_score >= min_score:
                    return grade
        
        # Default boundaries
        if mean_score >= 80:
            return 'A'
        elif mean_score >= 75:
            return 'A-'
        elif mean_score >= 70:
            return 'B+'
        elif mean_score >= 65:
            return 'B'
        elif mean_score >= 60:
            return 'B-'
        elif mean_score >= 55:
            return 'C+'
        elif mean_score >= 45:
            return 'C'
        elif mean_score >= 40:
            return 'C-'
        elif mean_score >= 35:
            return 'D+'
        elif mean_score >= 30:
            return 'D'
        elif mean_score >= 25:
            return 'D-'
        else:
            return 'E'
    
    def process_class(self):
        """Process all students in the class"""
        from students.models import Student
        
        if self.grade_level and self.stream:
            students = Student.objects.filter(
                current_grade_level=self.grade_level,
                current_stream=self.stream,
                is_active=True
            )
        else:
            students = Student.objects.filter(
                current_grade_level=self.examination.grade_level,
                is_active=True
            )
        
        results = []
        for student in students:
            result = self.process_student(student)
            if result:
                results.append(result)
        
        return results
    
    def get_class_statistics(self):
        """Get class statistics for KCSE results"""
        overalls = StudentOverallKCSE.objects.filter(
            examination=self.examination
        )
        
        if not overalls.exists():
            return None
        
        total_students = overalls.count()
        
        # Calculate statistics
        avg_score = overalls.aggregate(Avg('mean_score'))['mean_score__avg'] or 0
        highest_score = overalls.aggregate(Max('mean_score'))['mean_score__max'] or 0
        lowest_score = overalls.aggregate(Min('mean_score'))['mean_score__min'] or 0
        
        # Grade distribution
        grade_distribution = {}
        for overall in overalls:
            grade = overall.mean_grade or 'N/A'
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        # Top students
        top_students = overalls.order_by('-mean_score')[:10]
        
        return {
            'total_students': total_students,
            'average_score': avg_score,
            'highest_score': highest_score,
            'lowest_score': lowest_score,
            'grade_distribution': grade_distribution,
            'top_students': top_students
        }
