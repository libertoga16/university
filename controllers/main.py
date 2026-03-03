from odoo import http
from odoo.http import request


class UniversityWebsite(http.Controller):
    """Handles external website routing for university assets."""

    @http.route(['/', '/universidad'], type='http', auth='public', website=True)
    def list_universities(self, **kw):
        """
        Outputs the master catalog of institutions enforcing full bypass queries over public constraints.
        """
        universities = request.env['university.university'].sudo().search([])
        return request.render('university.website_uni_list', {
            'universities': universities
        })

    @http.route(['/universidad/<int:uni_id>'], type='http', auth='public', website=True)
    def list_professors(self, uni_id, **kw):
        """
        Renders the directory of registered professionals validating exposure via publication flags.

        Args:
            uni_id (int): Absolute database ID of the institution.
        """
        uni = request.env['university.university'].sudo().browse(uni_id)
        if not uni.exists():
            return request.not_found()

        if request.env.user.has_group('base.group_user'):
            professors = uni.professor_ids
        else:
            professors = uni.professor_ids.filtered(lambda p: p.is_published)
            
        return request.render('university.website_prof_list', {
            'university': uni,
            'professors': professors
        })
