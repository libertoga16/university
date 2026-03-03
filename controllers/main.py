from odoo import http
from odoo.http import request

class UniversityWebsite(http.Controller):

    # Page 1: Universities
    @http.route('/universidad', auth='public', website=True)
    def list_universities(self, **kw):
        # ORM applies group_public security automatically. Zero sudo().
        universities = request.env['university.university'].search([])
        return request.render('university.website_uni_list', {
            'universities': universities
        })

    # Professors of a specific University
    # Use <model(...)> URL converter to get object directly
    @http.route('/universidad/<model("university.university"):uni>', auth='public', website=True)
    def list_professors(self, uni, **kw):
        # Block access if university is unpublished and user is external
        if not request.env.user.has_group('base.group_user') and not uni.is_published:
            return request.not_found()

        # Internal users see all; public only published ones.
        if request.env.user.has_group('base.group_user'):
            professors = uni.professor_ids
        else:
            professors = uni.professor_ids.filtered(lambda p: p.is_published)
            
        return request.render('university.website_prof_list', {
            'university': uni,
            'professors': professors
        })
