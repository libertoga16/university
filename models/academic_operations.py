import logging
from typing import Any

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

_ENROLLMENT_CODE_NEW = 'New'

# Subject
class Subject(models.Model):
    """Represents subjects taught at the university."""
    _name = 'university.subject'
    _inherit = ['batch.count.mixin']
    _description = 'Subject'

    name = fields.Char(string='Name', required=True, index=True)
    code = fields.Char(string='Code', required=True, index=True)

    department_id = fields.Many2one('university.department', string='Department', required=True, index=True, ondelete='cascade')
    university_id = fields.Many2one(
        'university.university',
        related='department_id.university_id',
        store=True,
        readonly=True,
        index=True,
    )
    professor_ids = fields.Many2many(
        'university.professor', 
        string='Professors',
        domain="[('university_id', '=', university_id)]"
    )
    enrollment_ids = fields.One2many('university.enrollment', 'subject_id', string='Enrollments')


    enrollment_count = fields.Integer(compute='_compute_counts', string='Enrollment Count')

    @api.depends('enrollment_ids')
    def _compute_counts(self) -> None:
        """Computes the number of enrollments for this subject."""
        counts = self._get_batch_counts('university.enrollment', 'subject_id')
        for record in self:
            record.enrollment_count = counts.get(record.id, 0)

    @api.constrains('professor_ids', 'university_id')
    def _check_professors_university(self) -> None:
        """
        Validates that all assigned professors belong to the same university as the subject.

        Raises:
            ValidationError: If any professor belongs to a different university.
        """
        for record in self:
            if record.university_id and any(prof.university_id != record.university_id for prof in record.professor_ids):
                raise ValidationError(_("All professors assigned to the subject must belong to the same university."))


# Enrollment
class Enrollment(models.Model):
    """Manages student enrollments in subjects."""
    _name = 'university.enrollment'
    _description = 'Enrollment'
    _rec_name = 'code'

    code = fields.Char(string='Code', required=True, default=_ENROLLMENT_CODE_NEW, copy=False, index=True)

    student_id = fields.Many2one(
        'university.student',
        string='Student',
        required=True,
        index=True,
        ondelete='cascade',
        domain="[('university_id', '=', university_id)]",
    )
    university_id = fields.Many2one('university.university', string='University', required=True, index=True)
    professor_id = fields.Many2one(
        'university.professor',
        string='Professor',
        index=True,
        domain="[('university_id', '=', university_id)]",
    )
    subject_id = fields.Many2one(
        'university.subject',
        string='Subject',
        required=True,
        index=True,
        ondelete='cascade',
        domain="[('university_id', '=', university_id)]",
    )
    grade_ids = fields.One2many('university.grade', 'enrollment_id', string='Grades')


    _sql_constraints = [
        ('unique_student_subject', 
         'UNIQUE(student_id, subject_id)', 
         'Integrity Error: A student cannot be enrolled more than once in the same subject.')
    ]

    @api.depends('code', 'student_id.name')
    def _compute_display_name(self) -> None:
        """Computes a descriptive name combining code and student."""
        for record in self:
            record.display_name = f"{record.code or ''} - {record.student_id.name or ''}"

    @api.model
    def default_get(self, fields_list):
        """Propagates university_id from professor or student context defaults."""
        res = super().default_get(fields_list)
        if 'university_id' not in res or not res.get('university_id'):
            professor_id = res.get('professor_id')
            student_id = res.get('student_id')
            if professor_id:
                professor = self.env['university.professor'].browse(professor_id)
                res['university_id'] = professor.university_id.id
            elif student_id:
                student = self.env['university.student'].browse(student_id)
                res['university_id'] = student.university_id.id
        return res

    @api.onchange('professor_id')
    def _onchange_professor_id(self) -> None:
        """Auto-fills university_id from the selected professor when not already set."""
        if self.professor_id and not self.university_id:
            self.university_id = self.professor_id.university_id

    @api.onchange('student_id')
    def _onchange_student_id(self) -> None:
        """Auto-fills university_id from the selected student when not already set."""
        if self.student_id and not self.university_id:
            self.university_id = self.student_id.university_id

    @api.constrains('professor_id', 'university_id')
    def _check_professor_university(self) -> None:
        """
        Validates that the assigned professor belongs to the same university.

        Raises:
            ValidationError: If the professor belongs to a different university.
        """
        for record in self:
            if record.professor_id and record.professor_id.university_id != record.university_id:
                raise ValidationError(_("The professor must belong to the same university as the enrollment."))

    @api.constrains('professor_id', 'subject_id')
    def _check_professor_teaches_subject(self) -> None:
        """
        Validates that the assigned professor is listed as a teacher of the enrolled subject.

        A professor can only supervise an enrollment if they appear in subject_id.professor_ids.

        Raises:
            ValidationError: If the professor does not teach the subject.
        """
        for record in self:
            if (
                record.professor_id
                and record.subject_id
                and record.professor_id not in record.subject_id.professor_ids
            ):
                raise ValidationError(_(
                    "Professor '%(professor)s' does not teach '%(subject)s'. "
                    "Only professors assigned to the subject can be selected.",
                    professor=record.professor_id.name,
                    subject=record.subject_id.name,
                ))

    @api.constrains('student_id', 'university_id')
    def _check_student_university(self) -> None:
        """
        Validates that the enrolled student belongs to the same university.

        Raises:
            ValidationError: If the student belongs to a different university.
        """
        for record in self:
            if (
                record.student_id
                and record.student_id.university_id
                and record.student_id.university_id != record.university_id
            ):
                raise ValidationError(_("The student must belong to the same university as the enrollment."))

    @api.constrains('subject_id', 'university_id')
    def _check_subject_university(self) -> None:
        """
        Validates that the subject belongs to the same university.

        Raises:
            ValidationError: If the subject belongs to a different university.
        """
        for record in self:
            if record.subject_id and record.subject_id.university_id != record.university_id:
                raise ValidationError(_("The subject must belong to the same university as the enrollment."))

    @api.model_create_multi
    def create(self, vals_list: list[dict[str, Any]]) -> Any:
        """
        Creates multiple enrollments with optimized sequence code assignment.

        Args:
            vals_list (list[dict[str, Any]]): Creation values.

        Returns:
            Any: Created enrollments.
        """
        # Extract unique subject IDs
        subject_ids = {
            vals['subject_id'] 
            for vals in vals_list 
            if vals.get('code', _ENROLLMENT_CODE_NEW) == _ENROLLMENT_CODE_NEW and vals.get('subject_id')
        }
        
        if subject_ids:
            subjects = self.env['university.subject'].browse(list(subject_ids))
            seq_map = {}
            
            # Find or create sequences — savepoint guards against TOCTOU race condition:
            # two concurrent requests may both find no sequence and attempt creation;
            # the savepoint rolls back the loser's INSERT and lets it re-read the winner's row.
            for subject in subjects:
                seq_code = f"enrollment.subject.{subject.id}"
                seq = self.env['ir.sequence'].sudo().search([('code', '=', seq_code)], limit=1)

                if not seq:
                    prefix_str = (subject.name[:3].upper() if subject.name else 'UNK')
                    try:
                        with self.env.cr.savepoint():
                            seq = self.env['ir.sequence'].sudo().create({
                                'name': f'Enrollment Sequence {subject.name}',
                                'code': seq_code,
                                'prefix': f"{prefix_str}/%(year)s/",
                                'padding': 4,
                                'use_date_range': True,
                            })
                    except Exception:
                        # Concurrent transaction won the race; discard and re-read
                        seq = self.env['ir.sequence'].sudo().search([('code', '=', seq_code)], limit=1)
                if not seq:
                    raise UserError(_("Could not create or find sequence for subject '%s'. Please retry.") % subject.name)
                seq_map[subject.id] = seq

            # Assign codes in memory
            for vals in vals_list:
                if vals.get('code', _ENROLLMENT_CODE_NEW) == _ENROLLMENT_CODE_NEW and vals.get('subject_id'):
                    vals['code'] = seq_map[vals['subject_id']].next_by_id()
                    
        return super().create(vals_list)


# Grade
class Grade(models.Model):
    """Records grades obtained in enrollments."""
    _name = 'university.grade'
    _description = 'Grade'

    enrollment_id = fields.Many2one('university.enrollment', string='Enrollment', required=True, index=True, ondelete='cascade')
    student_id = fields.Many2one(
        'university.student',
        related='enrollment_id.student_id',
        store=True,
        index=True,
    )

    score = fields.Float(string='Score', index=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)

    _sql_constraints = [
        # Database-level enforcement: faster, atomic, race-condition-proof
        ('score_range', 'CHECK(score >= 0 AND score <= 10)', 'Score must be between 0 and 10.'),
    ]

    @api.depends('student_id.name', 'score')
    def _compute_display_name(self) -> None:
        """Generates the display name with student and score."""
        for record in self:
            record.display_name = f"{record.student_id.name or ''} - {record.score or 0.0}"
