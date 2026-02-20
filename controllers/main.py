from odoo import http
from odoo.http import request

class UniversityWebsite(http.Controller):

    # Página 1: Universidades
    @http.route('/universidad', auth='public', website=True)
    def list_universities(self, **kw):
        # Obtenemos todas las universidades
        universities = request.env['university.university'].sudo().search([])
        return request.render('university.website_uni_list', {
            'universities': universities
        })

    # Profesores de una Universidad específica
    # Usamos el convertidor de URL <model(...)> para obtener el objeto directamente
    @http.route('/universidad/<model("university.university"):uni>', auth='public', website=True)
    def list_professors(self, uni, **kw):
        return request.render('university.website_prof_list', {
            'university': uni,
            'professors': uni.professor_ids # Asumiendo relación One2many en University
        })
