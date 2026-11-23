from decimal import Decimal
from django.db.models import Q, Avg, Count
from .models import (
    PerformanceLevel, AssessmentType, Rubric, RubricCriterion,
    RubricDescriptor, AssessmentComponent, ComponentAggregation,
    StudentCBAAssessment, StudentOverallCBA
)
from marks.models import MarkEntry

class CBCEngine:
    """CBC/CBA Assessment Engine"""
    
    def __init__(self, examination, grade_level=None, stream=None):
        self.examination = examination
        self.grade_level = grade_level
        self.stream = stream
        self.scheme = self._get_scheme()
        self.performance_levels = self._get_performance_levels()
        self.rubrics = self._get_rubrics()
    
    def _get_scheme(self):
        """Get the assessment scheme for CBC"""
        from .models import AssessmentScheme
        scheme = AssessmentScheme.objects.filter(
            curriculum='CBC',
            is_active=True
        ).first()
        return scheme
    
    def _get_performance_levels(self):
        """Get performance levels"""
        if not self.scheme:
            return {}
        
        levels = PerformanceLevel.objects.filter(
            scheme=self.scheme,
            is_active=True
        ).order_by('order')
        
        return {level.level_code: level for level in levels}
    
    def _get_rubrics(self):
        """Get rubrics for the grade level"""
        if not self.scheme:
            return {}
        
        if self.grade_level:
            rubrics = Rubric.objects.filter(
                scheme=self.scheme,
                grade_level=self.grade_level,
                is_active=True
            ).prefetch_related('criteria__descriptors')
        else:
            rubrics = Rubric.objects.filter(
                scheme=self.scheme,
                is_active=True
            ).prefetch_related('criteria__descriptors')
        
        return {rubric.id: rubric for rubric in rubrics}
    
    def get_performance_level(self, code):
        """Get performance level by code"""
        return self.performance_levels.get(code)
    
    def process_student_rubric(self, student, rubric, criterion_results):
        """Process a student's rubric-based assessment"""
        # Validate all criteria have results
        criteria = rubric.criteria.filter(is_active=True)
        if len(criterion_results) != criteria.count():
            return None
        
        # Map results to levels
        level_counts = {}
        for criterion in criteria:
            level_code = criterion_results.get(f"criterion_{criterion.id}")
            if level_code in self.performance_levels:
                level_counts[level_code] = level_counts.get(level_code, 0) + 1
        
        # Determine overall level (majority rule)
        overall_level_code = None
        max_count = 0
        for level_code, count in level_counts.items():
            if count > max_count:
                max_count = count
                overall_level_code = level_code
        
        overall_level = self.performance_levels.get(overall_level_code)
        
        # Create or update assessment
        assessment, created = StudentCBAAssessment.objects.update_or_create(
            student=student,
            examination=self.examination,
            rubric=rubric,
            subject=rubric.subject,
            defaults={
                'criterion_results': criterion_results,
                'overall_level': overall_level
            }
        )
        
        return {
            'rubric': rubric.name,
            'criterion_results': criterion_results,
            'overall_level': overall_level,
            'level_code': overall_level_code
        }
    
    def process_student_components(self, student):
        """Process a student's assessment components"""
        # Get all assessments for this student
        assessments = StudentCBAAssessment.objects.filter(
            student=student,
            examination=self.examination
        )
        
        if not assessments.exists():
            return None
        
        # Get aggregation configuration
        aggregation = ComponentAggregation.objects.filter(
            scheme=self.scheme,
            is_active=True
        ).first()
        
        if not aggregation:
            return None
        
        # Group by component
        component_scores = {}
        for assessment in assessments:
            if assessment.component:
                component_id = assessment.component_id
                if component_id not in component_scores:
                    component_scores[component_id] = {
                        'scores': [],
                        'weight': assessment.component.weight
                    }
                
                # Convert performance level to score
                if assessment.overall_level and assessment.overall_level.numeric_value:
                    component_scores[component_id]['scores'].append(
                        assessment.overall_level.numeric_value
                    )
        
        # Calculate component averages
        component_results = {}
        total_score = 0
        total_weight = 0
        
        for comp_id, data in component_scores.items():
            if data['scores']:
                avg_score = sum(data['scores']) / len(data['scores'])
                weighted_score = avg_score * (data['weight'] / 100)
                component_results[comp_id] = {
                    'average': avg_score,
                    'weighted': weighted_score,
                    'weight': data['weight']
                }
                total_score += weighted_score
                total_weight += data['weight']
        
        # Calculate overall
        if total_weight > 0:
            overall_total = total_score
        else:
            overall_total = 0
        
        # Determine overall performance level
        overall_level = self._get_level_from_score(overall_total)
        
        # Save overall result
        overall, _created = StudentOverallCBA.objects.update_or_create(
            student=student,
            examination=self.examination,
            defaults={
                'overall_level': overall_level,
                'component_scores': component_results,
                'total_score': overall_total,
                'total_weighted_score': overall_total
            }
        )
        
        return {
            'component_results': component_results,
            'total_score': overall_total,
            'overall_level': overall_level
        }
    
    def _get_level_from_score(self, score):
        """Convert score to performance level"""
        levels = sorted(
            self.performance_levels.values(),
            key=lambda x: x.numeric_value or 0,
            reverse=True
        )
        
        for level in levels:
            if level.numeric_value and score >= level.numeric_value:
                return level
        
        return self.performance_levels.get('PL1')
    
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
            # Process rubrics
            for rubric_id, rubric in self.rubrics.items():
                # In real implementation, criterion_results would come from teacher input
                # Here we're using a placeholder
                criterion_results = {}
                for criterion in rubric.criteria.all():
                    # Simulate random PL levels for demonstration
                    import random
                    level_codes = ['PL4', 'PL3', 'PL2', 'PL1']
                    criterion_results[f"criterion_{criterion.id}"] = random.choice(level_codes)
                
                self.process_student_rubric(student, rubric, criterion_results)
            
            # Process components
            result = self.process_student_components(student)
            if result:
                results.append(result)
        
        return results
    
    def get_class_statistics(self):
        """Get class statistics for CBC results"""
        overalls = StudentOverallCBA.objects.filter(
            examination=self.examination
        ).select_related('overall_level')
        
        if not overalls.exists():
            return None
        
        total_students = overalls.count()
        
        # Level distribution
        level_distribution = {}
        for overall in overalls:
            level_code = overall.overall_level.level_code if overall.overall_level else 'N/A'
            level_distribution[level_code] = level_distribution.get(level_code, 0) + 1
        
        # Average score
        avg_score = overalls.aggregate(Avg('total_score'))['total_score__avg'] or 0
        
        # Top students
        top_students = overalls.order_by('-total_score')[:10]
        
        return {
            'total_students': total_students,
            'average_score': avg_score,
            'level_distribution': level_distribution,
            'top_students': top_students
        }
