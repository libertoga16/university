from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import logging

_logger = logging.getLogger(__name__)

class UniversityPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(UniversityPortal, self)._prepare_home_portal_values(counters)
        if 'grade_count' in counters:
            # Match student by user_id linkage (Exercise 9)
            user = request.env.user
            _logger.info(f"PORTAL DEBUG: Current User: {user.name} (ID: {user.id})")
            
            student = request.env['university.student'].sudo().search([('user_id', '=', user.id)], limit=1)
            _logger.info(f"PORTAL DEBUG: Found Linked Student: {student.name if student else 'None'}")
            
            if student:
                values['grade_count'] = len(student.grade_ids)
            else:
                 # Ensure count is 0 not None so t-if works, or simple don't set it? 
                 # If we don't set it, we need a way to tell the template to hide the tile.
                 # Let's set it to 0 and handle visibility in template or just only set if student exists.
                 values['grade_count'] = 0
                 
        return values

    @http.route(['/my/grades', '/my/grades/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_grades(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        
        user = request.env.user
        _logger.info(f"PORTAL DEBUG (Grades Page): User ID: {user.id}")
        
        # Linkage check
        student = request.env['university.student'].sudo().search([('user_id', '=', user.id)], limit=1)
        _logger.info(f"PORTAL DEBUG (Grades Page): Student found: {student}")
        
        # Security: If no student linked, they shouldn't access this page conceptually,
        # but showing empty is safer than 403. However requirement says "no debe poder ver el menú y el acceso".
        # We will handle menu visibility in template. Here just robust query.

        domain = [('student_id', '=', student.id)] if student else [('id', '=', -1)]

        grade_obj = request.env['university.grade']
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date desc'},
            'subject': {'label': _('Subject'), 'order': 'enrollment_id.subject_id.name'},
        }
        
        # default sort
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # pager
        grade_count = grade_obj.sudo().search_count(domain)
        pager = portal_pager(
            url="/my/grades",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=grade_count,
            page=page,
            step=self._items_per_page
        )

        grades = grade_obj.sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'date': date_begin,
            'grades': grades,
            'page_name': 'grade',
            'pager': pager,
            'default_url': '/my/grades',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'student': student,
        })
        return request.render("university.portal_my_grades", values)
