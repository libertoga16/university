from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class UniversityPortal(CustomerPortal):
    """Extends the customer portal to expose student grades under /my/grades."""

    def _prepare_home_portal_values(self, counters):
        """Injects is_student and grade_count into the portal homepage context."""
        values = super()._prepare_home_portal_values(counters)
        student = request.env['university.student'].search(
            [('user_id', '=', request.env.user.id)], limit=1
        )
        values['is_student'] = bool(student)
        if 'grade_count' in counters:
            values['grade_count'] = (
                request.env['university.grade'].search_count([('student_id', '=', student.id)])
                if student else 0
            )
        return values

    @http.route(['/my/grades', '/my/grades/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_grades(self, page=1, sortby='date', **kw):
        student = request.env['university.student'].search(
            [('user_id', '=', request.env.user.id)], limit=1
        )
        if not student:
            return request.redirect('/my')

        values = self._prepare_portal_layout_values()

        grade_obj = request.env['university.grade']
        domain = [('student_id', '=', student.id)]

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date desc'},
        }
        order = searchbar_sortings.get(sortby, searchbar_sortings['date'])['order']

        grade_count = grade_obj.search_count(domain)
        pager = portal_pager(url="/my/grades", total=grade_count, page=page, step=self._items_per_page)
        grades = grade_obj.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        # Prefetch relational chains accessed by the template to avoid N+1 per row
        grades.mapped('enrollment_id.subject_id')
        grades.mapped('enrollment_id.professor_id')

        values.update({
            'grades': grades,
            'page_name': 'grade',
            'pager': pager,
            'default_url': '/my/grades',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("university.portal_my_grades", values)