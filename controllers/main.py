from odoo import http
from odoo.http import request


class UniversityWebsite(http.Controller):
    """Handles external website routing for university assets."""

    @http.route(['/universidad'], type='http', auth='public', website=True)
    def list_universities(self, **kw):
        """
        Renders the public catalog of all universities.
        sudo(): public route — no authenticated user.
        """
        universities = request.env['university.university'].sudo().search([], limit=100)
        return request.render('university.website_uni_list', {
            'universities': universities
        })

    @http.route(['/universidad/<int:uni_id>'], type='http', auth='public', website=True)
    def list_professors(self, uni_id, **kw):
        """
        Renders the professor directory for a given university.
        Internal users see all professors; public/portal users see only published ones.

        Args:
            uni_id (int): Database ID of the university.
        """
        
        uni = request.env['university.university'].sudo().browse(uni_id)
        if not uni.exists():
            return request.not_found()
            
        professors = request.env['university.professor'].sudo().search([
            ('university_id', '=', uni.id)
        ], limit=100)
        # Prefetch image and department in batch to avoid N+1 during template rendering
        professors.mapped('image_128')
        professors.mapped('department_id')

        return request.render('university.website_prof_list', {
            'university': uni,
            'professors': professors
        })
