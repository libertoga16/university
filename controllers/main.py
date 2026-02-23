from odoo import http
from odoo.http import request

class UniversityWebsite(http.Controller):

    # Página 1: Universidades
    @http.route('/universidad', auth='public', website=True)
    def list_universities(self, **kw):
        # El ORM aplica la seguridad de group_public automáticamente. Cero sudo().
        universities = request.env['university.university'].search([])
        return request.render('university.website_uni_list', {
            'universities': universities
        })

    # Profesores de una Universidad específica
    # Usamos el convertidor de URL <model(...)> para obtener el objeto directamente
    @http.route('/universidad/<model("university.university"):uni>', auth='public', website=True)
    def list_professors(self, uni, **kw):
        # El usuario interno ve a todos; el público solo a los publicados.
        if request.env.user.has_group('base.group_user'):
            professors = uni.professor_ids
        else:
            professors = uni.professor_ids.filtered(lambda p: p.is_published)
            
        return request.render('university.website_prof_list', {
            'university': uni,
            'professors': professors
        })
