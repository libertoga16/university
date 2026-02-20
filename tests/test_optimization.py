from odoo.tests.common import TransactionCase, tagged

@tagged('university')
class TestUniversityCounts(TransactionCase):
    
    def setUp(self):
        super(TestUniversityCounts, self).setUp()
        self.university = self.env['university.university'].create({'name': 'Test University'})
        self.department = self.env['university.department'].create({
            'name': 'Test Department',
            'university_id': self.university.id
        })
        self.professor = self.env['university.professor'].create({
            'name': 'Test Professor',
            'university_id': self.university.id,
            'department_id': self.department.id
        })
        self.subject = self.env['university.subject'].create({
            'name': 'Test Subject',
            'code': 'TES101',
            'university_id': self.university.id,
            'department_id': self.department.id,
            'professor_ids': [(4, self.professor.id)]
        })
        self.student = self.env['university.student'].create({
            'name': 'Test Student',
            'university_id': self.university.id
        })
        self.enrollment = self.env['university.enrollment'].create({
            'student_id': self.student.id,
            'subject_id': self.subject.id,
            'professor_id': self.professor.id,
            'university_id': self.university.id
        })
        self.grade = self.env['university.grade'].create({
            'enrollment_id': self.enrollment.id,
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
