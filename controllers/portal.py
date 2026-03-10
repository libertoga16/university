from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import logging

_logger = logging.getLogger(__name__)

class UniversityPortal(CustomerPortal):
    """Hardened student portal handling strictly routed academic histories."""

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        """
        Bloquea el acceso al formulario nativo de edición de cuenta de Odoo.
        Cualquiera que intente entrar por URL será expulsado al inicio del portal.
        """
        _logger.warning("Intento de acceso denegado a /my/account por el usuario: %s", request.env.user.login)
        return request.redirect('/my')

   
    def _prepare_home_portal_values(self, counters):
        values = super(UniversityPortal, self)._prepare_home_portal_values(counters)
        if 'grade_count' in counters:
            student = request.env['university.student'].search([('user_id', '=', request.env.user.id)], limit=1)
            
            if student:
                values['grade_count'] = request.env['university.grade'].search_count([('student_id', '=', student.id)])
            else:
                 values['grade_count'] = 0
                 
        return values

    @http.route(['/my/grades', '/my/grades/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_grades(self, page=1, sortby='date', **kw):
        user = request.env.user

        student = request.env['university.student'].search([('user_id', '=', user.id)], limit=1)
        
        if not student:
            return request.redirect('/my')

        values = self._prepare_portal_layout_values()
        
        grade_obj = request.env['university.grade'] 
        domain = [('student_id', '=', student.id)] 

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