import logging
from typing import Any, Dict, List, Optional
import base64

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


# ============================================================================
# Department
# ============================================================================
class Department(models.Model):
    """
    Architectural entity representing a University Department.

    Organizes academic activities and personnel (professors) within a specific
    discipline or administrative unit.
    """
    _name = 'university.department'
    _inherit = ['batch.count.mixin']
    _description = 'Department'

    # === CORE FIELDS ===
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help="Name of the department."
    )

    # === RELATIONAL FIELDS ===
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        required=True,
        index=True,
        help="University this department belongs to."
    )
    manager_id = fields.Many2one(
        comodel_name='university.professor',
        string='Manager',
        index=True,
        help="Professor managing this department."
    )
    professor_ids = fields.Many2many(
        comodel_name='university.professor',
        relation='university_prof_dept_rel',
        column1='dept_id',
        column2='prof_id',
        string='Professors',
        help="Professors affiliated with this department."
    )

    # === COMPUTED FIELDS ===
    professor_count = fields.Integer(
        compute='_compute_counts',
        string='Professor Count',
        help="Number of professors in this department."
    )

    @api.depends('professor_ids')
    def _compute_counts(self) -> None:
        """
        Compute the number of professors in the department.
        """
        prof_map = self._get_batch_counts('university.professor', 'department_ids')
        for record in self:
            record.professor_count = prof_map.get(record.id, 0)

    def action_view_professors(self) -> Dict[str, Any]:
        """
        Open the list of professors for this department.

        Returns:
            Dict[str, Any]: Action dictionary to open the view.
        """
        self.ensure_one()
        return {
            'name': 'Professors',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,list,form',
            'res_model': 'university.professor',
            'domain': [('department_ids', 'in', self.id)],
            'context': {'default_department_ids': [self.id]},
        }


# ============================================================================
# Professor
# ============================================================================
class UniversityProfessor(models.Model):
    """
    Architectural entity representing a University Professor.

    Academic staff member responsible for teaching subjects and managing
    departments. Links recursively to enrollments and departments.
    """
    _name = 'university.professor'
    _inherit = ['image.mixin', 'batch.count.mixin']
    _description = 'University Professor'

    # === CORE FIELDS ===
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help="Full name of the professor."
    )
    email = fields.Char(
        string='Email',
        index=True,
        help="Professor's email address."
    )

    # === RELATIONAL FIELDS ===
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        required=True,
        index=True,
        help="University affliation."
    )
    department_ids = fields.Many2many(
        comodel_name='university.department',
        relation='university_prof_dept_rel',
        # Correctly referencing reverse relationship defined in Department
        column1='prof_id',
        column2='dept_id',
        string='Departments',
        help="Departments this professor is a member of."
    )
    subject_ids = fields.Many2many(
        comodel_name='university.subject',
        string='Subjects',
        help="Subjects taught by this professor."
    )
    enrollment_ids = fields.One2many(
        comodel_name='university.enrollment',
        inverse_name='professor_id',
        string='Enrollments',
        help="Student enrollments in courses taught by this professor."
    )

    # === COMPUTED FIELDS ===
    enrollment_count = fields.Integer(
        compute='_compute_counts',
        string='Enrollment Count',
        help="Total number of student enrollments managed."
    )

    @api.depends('enrollment_ids')
    def _compute_counts(self) -> None:
        """
        Compute the number of enrollments associated with the professor.
        """
        enrollment_map = self._get_batch_counts('university.enrollment', 'professor_id')
        for record in self:
            record.enrollment_count = enrollment_map.get(record.id, 0)


# ============================================================================
# Student
# ============================================================================
class UniversityStudent(models.Model):
    """
    Architectural entity representing a student within the university system.

    This model serves as the central node for student academic lifecycle management,
    aggregating enrollments, grades, and personal data. It integrates with the
    mail system for communication and report dissemination.
    """
    _name = 'university.student'
    _inherit = ['image.mixin', 'mail.thread', 'mail.activity.mixin', 'batch.count.mixin']
    _description = 'University Student'

    # === CORE FIELDS ===
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help="Full name of the student."
    )
    email = fields.Char(
        string='Email',
        index=True,
        help="Primary email address for communication and reporting."
    )

    # === ADDRESS FIELDS ===
    street = fields.Char(
        string='Street',
        help="Street address."
    )
    city = fields.Char(
        string='City',
        index=True,
        help="City."
    )
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        help="Country."
    )
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State',
        domain="[('country_id', '=', country_id)]",
        help="State or province."
    )
    zip_code = fields.Char(
        string='Zip Code',
        help="Postal code."
    )

    # === RELATIONAL FIELDS ===
    university_id = fields.Many2one(
        comodel_name='university.university',
        string='University',
        required=True,
        index=True,
        help="The university the student is currently registered with."
    )
    tutor_id = fields.Many2one(
        comodel_name='university.professor',
        string='Tutor',
        index=True,
        help="Assigned academic tutor for the student."
    )
    enrollment_ids = fields.One2many(
        comodel_name='university.enrollment',
        inverse_name='student_id',
        string='Enrollments',
        help="List of course enrollments for this student."
    )
    grade_ids = fields.One2many(
        comodel_name='university.grade',
        inverse_name='student_id',
        string='Grades',
        help="List of academic grades received by this student."
    )

    # === COMPUTED FIELDS ===
    enrollment_count = fields.Integer(
        compute='_compute_counts',
        string='Enrollment Count',
        help="Total number of active enrollments."
    )
    grade_count = fields.Integer(
        compute='_compute_counts',
        string='Grade Count',
        help="Total number of recorded grades."
    )

    @api.depends('enrollment_ids', 'grade_ids')
    def _compute_counts(self) -> None:
        """
        Compute the number of enrollments and grades for the student.
        """
        enrollment_map = self._get_batch_counts('university.enrollment', 'student_id')
        grade_map = self._get_batch_counts('university.grade', 'student_id')

        for record in self:
            record.enrollment_count = enrollment_map.get(record.id, 0)
            record.grade_count = grade_map.get(record.id, 0)

    def action_send_email(self) -> Dict[str, Any]:
        """
        Opens a wizard to compose an email, with the template pre-loaded.

        Returns:
            Dict[str, Any]: The action dictionary to open the mail composition wizard.
        """
        self.ensure_one()
        # Architectural Decision: Using Walrus operator for clean template resolution
        template = self.env.ref('university.email_template_student_report', raise_if_not_found=False)
        template_id = template.id if template else False

        ctx: Dict[str, Any] = {
            'default_model': 'university.student',
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True,
        }

        # --- ODOO 19 COMPATIBILITY ---
        # Manually generate PDF and attach it since mail.template does not support it directly anymore.
        
        # 1. Get the report action
        report_action = self.env.ref('university.action_report_student', raise_if_not_found=False)
        
        if report_action:
            # 2. Render the PDF
            # _render_qweb_pdf returns (pdf_content, content_type)
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report_action, [self.id])
            
            # 3. Create the attachment
            attachment = self.env['ir.attachment'].create({
                'name': f"Student Report - {self.name}.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'university.student',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            
            # 4. Add attachment to the wizard context
            ctx['default_attachment_ids'] = [(4, attachment.id)]

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
