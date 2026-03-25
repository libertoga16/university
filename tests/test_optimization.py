from odoo.tests.common import TransactionCase, tagged

@tagged('university')
class TestUniversityCounts(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.university = cls.env['university.university'].create({'name': 'Test University'})
        cls.department = cls.env['university.department'].create({
            'name': 'Test Department',
            'university_id': cls.university.id
        })
        cls.professor = cls.env['university.professor'].create({
            'name': 'Test Professor',
            'university_id': cls.university.id,
            'department_id': cls.department.id
        })
        cls.subject = cls.env['university.subject'].create({
            'name': 'Test Subject',
            'code': 'TES101',
            'university_id': cls.university.id,
            'department_id': cls.department.id,
            'professor_ids': [(4, cls.professor.id)]
        })
        cls.student = cls.env['university.student'].create({
            'name': 'Test Student',
            'email': 'test_student_opt@example.com',
            'university_id': cls.university.id
        })
        cls.enrollment = cls.env['university.enrollment'].create({
            'student_id': cls.student.id,
            'subject_id': cls.subject.id,
            'professor_id': cls.professor.id,
            'university_id': cls.university.id
        })
        cls.grade = cls.env['university.grade'].create({
            'enrollment_id': cls.enrollment.id,
            'score': 10.0
        })

    def test_counts(self):
        """Test that computed counts are correct"""
        # University Counts
        self.assertEqual(self.university.professor_count, 1, "University should have 1 professor")
        self.assertEqual(self.university.student_count, 1, "University should have 1 student")
        self.assertEqual(self.university.enrollment_count, 1, "University should have 1 enrollment")
        self.assertEqual(self.university.department_count, 1, "University should have 1 department")
        
        # Department Counts
        self.assertEqual(self.department.professor_count, 1, "Department should have 1 professor")
        
        # Professor Counts
        self.assertEqual(self.professor.enrollment_count, 1, "Professor should have 1 enrollment")
        
        # Student Counts
        self.assertEqual(self.student.enrollment_count, 1, "Student should have 1 enrollment")
        self.assertEqual(self.student.grade_count, 1, "Student should have 1 grade")
        
        # Subject Counts
        self.assertEqual(self.subject.enrollment_count, 1, "Subject should have 1 enrollment")
