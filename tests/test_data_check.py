from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)

class TestDataCheck(TransactionCase):
    def setUp(self):
        super(TestDataCheck, self).setUp()

    def test_check_data_counts(self):
        prof_count = self.env['university.professor'].search_count([])
        dept_count = self.env['university.department'].search_count([])
        student_count = self.env['university.student'].search_count([])
        
        self.assertGreaterEqual(prof_count, 0, "Professor count should not be negative")
        self.assertGreaterEqual(dept_count, 0, "Department count should not be negative")
        self.assertGreaterEqual(student_count, 0, "Student count should not be negative")
        _logger.info("DATA_CHECK_RESULT: Professors=%d, Departments=%d, Students=%d", prof_count, dept_count, student_count)

    def test_portal_security_access(self):
        """Test that a portal user cannot read grades belonging to someone else."""
        student1 = self.env['university.student'].create({
            'name': 'Test Student One',
            'email': 'student1_test@example.com',
        })
        student2 = self.env['university.student'].create({
            'name': 'Test Student Two',
            'email': 'student2_test@example.com',
        })

        # Test user creation
        self.assertTrue(student1.user_id, "Portal user should be automatically created")
        
        university = self.env['university.university'].create({'name': 'Test Uni Security'})
        dept = self.env['university.department'].create({'name': 'Test Dept Sec', 'university_id': university.id})
        subject = self.env['university.subject'].create({
            'name': 'Test Subject Sec',
            'code': 'TEST_SEC',
            'department_id': dept.id
        })
        
        enroll_2 = self.env['university.enrollment'].create({
            'student_id': student2.id,
            'university_id': university.id,
            'subject_id': subject.id,
        })
        grade_2 = self.env['university.grade'].create({
            'enrollment_id': enroll_2.id,
            'score': 9.0
        })

        # Student 1 tries to read Student 2's grade
        with self.assertRaises(AccessError):
            grade_2.with_user(student1.user_id).read(['score'])

