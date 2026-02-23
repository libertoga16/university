{
    'name': 'University Management',
    'version': '19.0.1.1.0',
    'category': 'Education',
    'summary': 'Comprehensive University Management System',
    'description': """
University Management System
============================

This module provides a complete solution for managing university operations:
* **Academic Entities**: Universities, Departments, Professors, Students.
* **Academic Operations**: Subjects, Enrollments, Grades.
* **Reporting**: Analytics for student performance.
* **Portal**: Web interface for public listing.

Key Features:
-------------
* Multi-university support
* Professor and Student management
* Automatic Enrollment numbering
* Grade tracking and reporting
    """,
    'author': 'Liberto',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'website',
        'portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir.rule.xml',
        'data/university_sequence.xml',
        'data/ir_cron_data.xml',
        'reports/student_report.xml',
        'data/mail_template_data.xml',
        'views/university_actions.xml',
        'views/enrollment_views.xml',
        'views/grade_views.xml',
        'views/professor_views.xml',
        'views/department_views.xml',
        'views/student_views.xml',
        'views/subject_views.xml',
        'views/report_views.xml',
        'views/website_templates.xml',
        'views/portal_templates.xml',
        'wizards/enrollment_wizard_views.xml',
        'views/university_views.xml',
        'views/university_menus.xml',
        ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'university/static/src/js/student_email_widget.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
