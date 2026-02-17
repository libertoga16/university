{
    'name': 'University Management',
    'version': '1.0',
    'summary': 'Module for managing universities, departments, professors, and students',
    'description': """
        This module allows you to manage:
        - Universities
        - Departments
        - Professors
        - Subjects
        - Students
        - Enrollments
        - Grades
    """,
    'category': 'Education',
    'author': 'Liberto',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/grade_views.xml',
        'views/enrollment_views.xml',
        'views/subject_views.xml',
        'views/student_views.xml',
        'views/professor_views.xml',
        'views/department_views.xml',
        'views/report_views.xml',
        'views/university_views.xml',
        'views/university_menus.xml',
        'data/test_data.xml',
        'reports/student_report.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
