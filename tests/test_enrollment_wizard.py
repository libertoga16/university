from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('university')
class TestEnrollmentWizard(TransactionCase):
    
    def setUp(self):
        super(TestEnrollmentWizard, self).setUp()
        self.university = self.env['university.university'].create({'name': 'Test University'})
        self.department = self.env['university.department'].create({
            'name': 'Test Department',
            'university_id': self.university.id
        })
        self.professor = self.env['university.professor'].create({
            'name': 'Test Professor',
            'university_id': self.university.id,
            'department_ids': [(4, self.department.id)]
        })
        self.subject = self.env['university.subject'].create({
            'name': 'Test Subject',
            'university_id': self.university.id,
            'department_id': self.department.id,
            'professor_ids': [(4, self.professor.id)]
        })
        self.student1 = self.env['university.student'].create({
            'name': 'Student 1',
            'university_id': self.university.id
        })
        self.student2 = self.env['university.student'].create({
            'name': 'Student 2',
            'university_id': self.university.id
        })

    def test_wizard_defaults(self):
        """Test that the wizard defaults are set correctly"""
        wizard = self.env['university.enrollment.wizard'].create({
            'university_id': self.university.id,
            'subject_id': self.subject.id,
            'professor_id': self.professor.id,
            'student_ids': [(6, 0, [self.student1.id, self.student2.id])]
        })
        self.assertEqual(wizard.university_id, self.university)
        self.assertEqual(wizard.subject_id, self.subject)
        self.assertEqual(wizard.professor_id, self.professor)
        self.assertIn(self.student1, wizard.student_ids)
        self.assertIn(self.student2, wizard.student_ids)

    def test_action_enroll_batch(self):
        """Test batch enrollment creation"""
        wizard = self.env['university.enrollment.wizard'].create({
            'university_id': self.university.id,
            'subject_id': self.subject.id,
            'professor_id': self.professor.id,
            'student_ids': [(6, 0, [self.student1.id, self.student2.id])]
        })
        
        action = wizard.action_enroll()
        
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'university.enrollment')
        
        enrollments = self.env['university.enrollment'].search([('id', 'in', action['domain'][0][2])])
        self.assertEqual(len(enrollments), 2)
        
        for enrollment in enrollments:
            self.assertEqual(enrollment.university_id, self.university)
            self.assertEqual(enrollment.subject_id, self.subject)
            self.assertEqual(enrollment.professor_id, self.professor)
            self.assertTrue(enrollment.code.startswith('TES'))  # Prefix from subject name 'Test Subject'
