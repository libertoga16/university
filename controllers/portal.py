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
            
            # The portal user can only see their own student profile due to ir.rule.
            student = request.env['university.student'].search([('user_id', '=', user.id)], limit=1)
            
            if student:
                # OPTIMIZADO: Ejecuta un SELECT COUNT() en SQL. Cero impacto en RAM.
                values['grade_count'] = request.env['university.grade'].search_count([('student_id', '=', student.id)])
            else:
                 values['grade_count'] = 0
                 
        return values

    @http.route(['/my/grades', '/my/grades/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_grades(self, page=1, sortby='date', **kw):
        values = self._prepare_portal_layout_values()
        grade_obj = request.env['university.grade']
        
        # El ir.rule se encarga de la seguridad. No necesitas buscar al estudiante ni armar dominios manuales.
        domain = [] 

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date desc'},
            'subject': {'label': _('Subject'), 'order': 'enrollment_id.subject_id.name'},
        }
        order = searchbar_sortings.get(sortby, searchbar_sortings['date'])['order']

        grade_count = grade_obj.search_count(domain)
        pager = portal_pager(url="/my/grades", total=grade_count, page=page, step=self._items_per_page)
        grades = grade_obj.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'grades': grades,
            'page_name': 'grade',
            'pager': pager,
            'default_url': '/my/grades',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("university.portal_my_grades", values)
