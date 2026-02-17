from odoo.tests.common import TransactionCase
import logging

_logger = logging.getLogger(__name__)

class TestDataCheck(TransactionCase):
    def setUp(self):
        super(TestDataCheck, self).setUp()

    def test_check_data_counts(self):
        prof_count = self.env['university.professor'].search_count([])
        dept_count = self.env['university.department'].search_count([])
        student_count = self.env['university.student'].search_count([])
        
        print(f"\n\nDATA_CHECK_RESULT: Professors={prof_count}, Departments={dept_count}, Students={student_count}\n\n")
