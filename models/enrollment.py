from odoo import models, fields, api
from datetime import datetime

class Enrollment(models.Model):
    _name = 'university.enrollment'
    _description = 'Enrollment'
    _rec_name = 'code'

    code = fields.Char(string='Code', required=True, default=lambda self: 'New', copy=False)
    student_id = fields.Many2one('university.student', string='Student', required=True)
    university_id = fields.Many2one('university.university', string='University', required=True)
    professor_id = fields.Many2one('university.professor', string='Professor')
    subject_id = fields.Many2one('university.subject', string='Subject', required=True)
    
    grade_ids = fields.One2many('university.grade', 'enrollment_id', string='Grades')

    def _compute_display_name(self):
        """
        Compute the display name for the enrollment.
        Format: [Code] - [Student Name]
        """
        for record in self:
            record.display_name = f"{record.code} - {record.student_id.name}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('subject_id'):
                subject = self.env['university.subject'].browse(vals['subject_id'])
                if subject:
                    prefix = subject.name[:3].upper()
                    year = datetime.now().year
                    pattern = f"{prefix}/{year}/%"
                    
                    # Find last sequence for this subject and year
                    last_enrollment = self.search([('code', 'like', pattern)], order='code desc', limit=1)
                    
                    if last_enrollment:
                        try:
                            # Extract sequence number (last 4 digits)
                            last_seq = int(last_enrollment.code.split('/')[-1])
                            new_seq = last_seq + 1
                        except ValueError:
                            new_seq = 1
                    else:
                        new_seq = 1
                    
                    vals['code'] = f"{prefix}/{year}/{new_seq:04d}"
        
        return super(Enrollment, self).create(vals_list)
