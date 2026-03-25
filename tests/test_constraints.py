from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class TestConstraints(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.uni_1 = cls.env['university.university'].create({
            'name': 'Uni Test 1'
        })
        cls.uni_2 = cls.env['university.university'].create({
            'name': 'Uni Test 2'
        })

        cls.dept_1 = cls.env['university.department'].create({
            'name': 'Dept Test 1',
            'university_id': cls.uni_1.id
        })
        cls.dept_2 = cls.env['university.department'].create({
            'name': 'Dept Test 2',
            'university_id': cls.uni_2.id
        })

        cls.prof_1 = cls.env['university.professor'].create({
            'name': 'Prof Test 1',
            'university_id': cls.uni_1.id,
            'department_id': cls.dept_1.id
        })
        cls.prof_2 = cls.env['university.professor'].create({
            'name': 'Prof Test 2',
            'university_id': cls.uni_2.id,
            'department_id': cls.dept_2.id
        })

        cls.student_1 = cls.env['university.student'].create({
            'name': 'Student Test 1',
            'email': 'stu1_test_cons@example.com',
            'university_id': cls.uni_1.id
        })

        cls.subject_1 = cls.env['university.subject'].create({
            'name': 'Subj Test 1',
            'code': 'S1_TEST',
            'department_id': cls.dept_1.id
        })

    def test_director_constraint(self):
        """Test assigning a director from another university raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.uni_1.write({'director_id': self.prof_2.id})

    def test_department_manager_constraint(self):
        """Test assigning a department manager from another university raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.dept_1.write({'manager_id': self.prof_2.id})

    def test_student_tutor_constraint(self):
        """Test assigning a student tutor from another university raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.student_1.write({'tutor_id': self.prof_2.id})

    def test_subject_professor_constraint(self):
        """Test assigning a subject professor from another university raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.subject_1.write({'professor_ids': [(4, self.prof_2.id)]})

    def test_enrollment_student_constraint(self):
        """Test enrollment with student from a different university."""
        with self.assertRaises(ValidationError):
            self.env['university.enrollment'].create({
                'student_id': self.student_1.id,
                'university_id': self.uni_2.id,
                'subject_id': self.subject_1.id
            })

    def test_enrollment_professor_constraint(self):
        """Test enrollment with professor from a different university."""
        with self.assertRaises(ValidationError):
            self.env['university.enrollment'].create({
                'student_id': self.student_1.id,
                'university_id': self.uni_1.id,
                'subject_id': self.subject_1.id,
                'professor_id': self.prof_2.id
            })

    def test_enrollment_unique_student_subject_sql_constraint(self):
        """SQL UNIQUE(student_id, subject_id): duplicate enrollment must be rejected at DB level."""
        self.env['university.enrollment'].create({
            'student_id': self.student_1.id,
            'university_id': self.uni_1.id,
            'subject_id': self.subject_1.id,
        })
        with self.assertRaises(ValidationError):
            self.env['university.enrollment'].create({
                'student_id': self.student_1.id,
                'university_id': self.uni_1.id,
                'subject_id': self.subject_1.id,
            })

    def test_grade_score_below_zero_sql_constraint(self):
        """SQL CHECK(score >= 0 AND score <= 10): score below 0 must be rejected at DB level."""
        enrollment = self.env['university.enrollment'].create({
            'student_id': self.student_1.id,
            'university_id': self.uni_1.id,
            'subject_id': self.subject_1.id,
        })
        with self.assertRaises(ValidationError):
            self.env['university.grade'].create({
                'enrollment_id': enrollment.id,
                'score': -0.1,
            })

    def test_grade_score_above_ten_sql_constraint(self):
        """SQL CHECK(score >= 0 AND score <= 10): score above 10 must be rejected at DB level."""
        enrollment = self.env['university.enrollment'].create({
            'student_id': self.student_1.id,
            'university_id': self.uni_1.id,
            'subject_id': self.subject_1.id,
        })
        with self.assertRaises(ValidationError):
            self.env['university.grade'].create({
                'enrollment_id': enrollment.id,
                'score': 10.1,
            })
