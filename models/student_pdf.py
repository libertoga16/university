from odoo import models, api


class StudentReportParser(models.AbstractModel):
    """Parser to inject computed data into the students report QWeb."""
    _name = 'report.university.report_student_template'
    _description = 'Student Report Parser'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['university.student'].browse(docids)

        # Prefetch the full grade → enrollment → subject/professor chain for Section 2
        # to avoid N+1 queries when the QWeb template iterates o.grade_ids.
        docs.mapped('grade_ids.enrollment_id.subject_id')
        docs.mapped('grade_ids.enrollment_id.professor_id')

        groups = self.env['university.grade']._read_group(
            domain=[('student_id', 'in', docids)],
            groupby=['student_id', 'enrollment_id'],
            aggregates=['score:avg']
        )

        # Prefetch subject_id and professor_id in batch before iteration to avoid N+1 queries
        enrollment_ids = [enrollment.id for _, enrollment, _ in groups]
        if enrollment_ids:
            prefetched = self.env['university.enrollment'].browse(enrollment_ids)
            prefetched.mapped('subject_id.name')
            prefetched.mapped('professor_id.name')

        summary_by_student = {doc_id: [] for doc_id in docids}
        for student, enrollment, avg_score in groups:
            summary_by_student[student.id].append({
                'subject': enrollment.subject_id.name,
                'professor': enrollment.professor_id.name or 'N/A',
                'average': avg_score or 0.0
            })

        return {
            'docs': docs,
            'student_summaries': summary_by_student,
        }
