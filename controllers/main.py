# -*- coding: utf-8 -*-
from typing import Any

from odoo import http
from odoo.http import request


class UniversityController(http.Controller):
    """
    Website controller for the University module.

    Handles public routes for listing universities and professors.
    """

    @http.route('/university', type='http', auth='public', website=True)
    def index(self, **kw: Any) -> Any:
        """
        Render the list of universities.
        """
        universities = request.env['university.university'].search([])
        return request.render('university.university_list', {
            'universities': universities
        })

    @http.route('/university/<model("university.university"):university>', type='http', auth='public', website=True)
    def university_professors(self, university: Any, **kw: Any) -> Any:
        """
        Render the list of professors for a specific university.

        :param university: The university record.
        """
        professors = request.env['university.professor'].search([
            ('university_id', '=', university.id)
        ])
        return request.render('university.university_professor_list', {
            'university': university,
            'professors': professors
        })
