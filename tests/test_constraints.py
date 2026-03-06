from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class TestConstraints(TransactionCase):
    def setUp(self):
        super(TestConstraints, self).setUp()
        
        # We need a company
        self.company = self.env.user.company_id
        
        self.uni_1 = self.env['university.university'].create({
            'name': 'Uni Test 1',
            'company_id': self.company.id
        })
        self.uni_2 = self.env['university.university'].create({
            'name': 'Uni Test 2',
            'company_id': self.company.id
        })

        self.dept_1 = self.env['university.department'].create({
            'name': 'Dept Test 1', 
            'university_id': self.uni_1.id,
            'company_id': self.company.id
        })
        self.dept_2 = self.env['university.department'].create({
            'name': 'Dept Test 2', 
            'university_id': self.uni_2.id,
            'company_id': self.company.id
        })

        self.prof_1 = self.env['university.professor'].create({
            'name': 'Prof Test 1', 
            'university_id': self.uni_1.id, 
            'department_id': self.dept_1.id,
            'company_id': self.company.id
        })
        self.prof_2 = self.env['university.professor'].create({
            'name': 'Prof Test 2', 
            'university_id': self.uni_2.id, 
            'department_id': self.dept_2.id,
            'company_id': self.company.id
        })

        self.student_1 = self.env['university.student'].create({
            'name': 'Student Test 1', 
            'email': 'stu1_test_cons@example.com', 
            'university_id': self.uni_1.id,
            'company_id': self.company.id
        })
        
        self.subject_1 = self.env['university.subject'].create({
            'name': 'Subj Test 1', 
            'code': 'S1_TEST', 
            'department_id': self.dept_1.id,
            'company_id': self.company.id
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
                'subject_id': self.subject_1.id,
                'company_id': self.company.id
            })

    def test_enrollment_professor_constraint(self):
        """Test enrollment with professor from a different university."""
        with self.assertRaises(ValidationError):
            self.env['university.enrollment'].create({
                'student_id': self.student_1.id,
                'university_id': self.uni_1.id,
                'subject_id': self.subject_1.id,
                'professor_id': self.prof_2.id,
                'company_id': self.company.id
            })
